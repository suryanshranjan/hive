"""hive run: a silent swarm on a copy of a repository (from lab/make_swarm.py and lab/launch.py).

The repository at --repo (with .hive/config.json committed) is cloned into a bare upstream under the run folder;
every worker gets its own clone, a rendered prompt, and the same environment. The source repository is never pushed
to: the swarm's result is the shared branch of <run>/up.git.

Workers run $HIVE_WORKER_CMD (default: headless Claude Code) inside their clone with the prompt on stdin. They execute
shell commands, so run swarms in a container or a throwaway VM."""
import csv, json, os, shlex, shutil, subprocess, sys, time

from . import config, owner
from .guard import sh

DEFAULT_CMD = 'claude -p --output-format json --permission-mode acceptEdits --allowedTools Bash Read Edit Write Glob Grep'
HIVE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _usage(path):
    try:
        d = json.load(open(path))
    except Exception:
        return '', '', ''
    u = d.get('usage') or {}
    tok = sum(int(u.get(k) or 0) for k in ('input_tokens', 'output_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens'))
    return tok or '', d.get('total_cost_usd', ''), d.get('api_error_status') or ''

RESUME = ("\n\n# You are picking up again\n\nYou were stopped partway by Claude's usage limit; it has reset now. Your clone "
          "still has everything you did, and others may have landed work since. Read the end of your log, commit or "
          "discard anything half-done, pull, check your lock, and carry on from where you stopped. Do not redo work "
          "that has already landed.\n")

def _limit_hit(path):
    """When a worker stopped on Claude's usage limit: the time it resets (a Unix time; 0 if not said), else None."""
    try:
        d = json.load(open(path))
    except Exception:
        return None
    text = str(d.get('result') or '')
    if str(d.get('api_error_status') or '') != '429' and 'limit' not in text.lower():
        return None
    if not (d.get('is_error') or d.get('api_error_status')):
        return None
    import re
    m = re.search(r'\|(\d{10})\b', text)   # the CLI says "usage limit reached|<reset time>"
    return int(m.group(1)) if m else 0

def _resume_at(reset, attempt):
    """When to try again: just after the reset time if Claude said it, else waits growing from 5 minutes to an hour."""
    floor = float(os.environ.get('HIVE_RESUME_MIN', 60))
    return max(reset + 60, time.time() + floor) if reset else time.time() + max(floor, min(3600, 300 * 2 ** attempt))

def _areas_text(cfg):
    areas = cfg.get('areas', {})
    if not areas:
        return 'No areas are configured: claim short names for the parts of the goal you build (for example `fees`, `payouts`).'
    return '\n'.join(f'- `{a}`: tests matching {", ".join(f"`{g}`" for g in globs)}' for a, globs in sorted(areas.items()))

def prepare(repo, run, workers, goal, minutes=40, examples=None, questions=None, assumptions=False):
    """Create <run>/up.git, one clone per worker in <run>/work, and one prompt per worker in <run>/prompts."""
    repo = os.path.abspath(repo); run = os.path.abspath(run)
    cfg = config.load(repo)
    b = cfg.get('branch') or sh('git', '-C', repo, 'rev-parse', '--abbrev-ref', 'HEAD').stdout.strip()
    if os.path.exists(run):
        raise SystemExit(f'{run} exists: choose a new run folder')
    for d in ('work', 'prompts', 'logs', 'out'):
        os.makedirs(os.path.join(run, d))
    owner_text = owner.setup(run, examples, questions, assumptions)
    up = os.path.join(run, 'up.git')
    sh('git', 'clone', '-q', '--bare', '--branch', b, repo, up)
    sh('git', '-C', up, 'symbolic-ref', 'HEAD', f'refs/heads/{b}')
    template = open(os.path.join(HIVE_ROOT, 'hive', 'templates', 'worker.md')).read()
    goal_text = open(goal).read().strip() if os.path.exists(goal) else goal
    for k in range(1, workers + 1):
        me = f'w{k}'; work = os.path.join(run, 'work', me)
        sh('git', 'clone', '-q', up, work)
        sh('git', '-C', work, 'config', 'user.name', me); sh('git', '-C', work, 'config', 'user.email', f'{me}@hive.local')
        for link in cfg.get('snapshot_links', []):   # dependency folders, shared read-only from the source checkout
            src, dst = os.path.join(repo, link), os.path.join(work, link)
            if os.path.exists(src) and not os.path.exists(dst):
                os.symlink(src, dst)
        text = (template.replace('{ME}', me).replace('{N}', str(workers)).replace('{WORK}', work).replace('{BRANCH}', b)
                .replace('{LOG}', os.path.join(run, 'logs', f'{me}.log')).replace('{GOAL}', goal_text)
                .replace('{TEST_CMD}', cfg['test_cmd']).replace('{AREAS}', _areas_text(cfg)).replace('{OWNER}', owner_text)
                .replace('{MINUTES}', str(minutes)))
        open(os.path.join(run, 'prompts', f'{me}.md'), 'w').write(text)
    json.dump(dict(repo=repo, branch=b, workers=workers, started=None), open(os.path.join(run, 'run.json'), 'w'), indent=1)
    return run

def launch(run, max_parallel=0, say=lambda m: print(m, flush=True)):
    """Run every worker (at most max_parallel at once), wait for all, and write <run>/agents.csv."""
    run = os.path.abspath(run)
    cmd = shlex.split(os.environ.get('HIVE_WORKER_CMD', DEFAULT_CMD))
    env = dict(os.environ, PYTHONPATH=HIVE_ROOT + os.pathsep + os.environ.get('PYTHONPATH', ''),
               HIVE_GUARD_CACHE=os.path.join(run, 'guard_cache'), HIVE_RUN=run)
    queue = sorted(f[:-3] for f in os.listdir(os.path.join(run, 'prompts')) if f.endswith('.md'))
    meta = json.load(open(os.path.join(run, 'run.json'))); meta['started'] = int(time.time())
    json.dump(meta, open(os.path.join(run, 'run.json'), 'w'), indent=1)

    tries = int(os.environ.get('HIVE_RESUME_TRIES', 8))   # about 6 hours of waiting at most
    attempts, spent, first = {}, {}, {}   # per worker: limit stops so far, tokens and cost of earlier attempts, start

    def start(me):
        out = open(os.path.join(run, 'out', f'{me}.json'), 'w')
        p = subprocess.Popen(cmd, cwd=os.path.join(run, 'work', me), stdin=subprocess.PIPE, stdout=out,
                             stderr=subprocess.STDOUT, text=True, env=dict(env, HIVE_WORKER=me))
        try:
            p.stdin.write(open(os.path.join(run, 'prompts', f'{me}.md')).read() + (RESUME if attempts.get(me) else ''))
            p.stdin.close()
        except BrokenPipeError:
            pass
        say(f'{"picked up" if attempts.get(me) else "launched"} {me}')
        first.setdefault(me, time.time())
        return [me, time.time(), p, out]

    cap = max_parallel or len(queue); live = []; rows = []; waiting = []   # waiting: [(when, worker)]
    while queue and len(live) < cap:
        live.append(start(queue.pop(0)))
    while live or waiting:
        for when, me in list(waiting):   # usage limit has reset: the worker carries on in its own clone
            if time.time() >= when:
                waiting.remove((when, me)); live.append(start(me))
        for item in list(live):
            me, t0, p, out = item
            if p.poll() is None:
                continue
            live.remove(item); out.close()
            path = os.path.join(run, 'out', f'{me}.json')
            tok, cost, err = _usage(path)
            reset = _limit_hit(path)
            if reset is not None and attempts.get(me, 0) < tries:
                n = attempts[me] = attempts.get(me, 0) + 1
                t, c = spent.get(me, (0, 0.0)); spent[me] = (t + int(tok or 0), c + float(cost or 0))
                shutil.copy(path, os.path.join(run, 'out', f'{me}.limit{n}.json'))
                when = _resume_at(reset, n - 1); waiting.append((when, me))
                say(f"{me} stopped: Claude's usage limit was reached. I'll pick up again at "
                    f"{time.strftime('%H:%M', time.localtime(when))}; its work so far is kept.")
                continue
            if queue:
                live.append(start(queue.pop(0)))
            t, c = spent.get(me, (0, 0.0))
            tok = (int(tok or 0) + t) or tok; cost = round(float(cost or 0) + c, 6) if (cost or c) else cost
            rows.append(dict(worker=me, start=int(first[me]), end=int(time.time()),
                             minutes=round((time.time() - first[me]) / 60, 1), exit=p.returncode, tokens=tok,
                             cost_usd=cost, api_error=err, limit_stops=attempts.get(me, 0)))
            say(f'{me} finished: exit {p.returncode}, {rows[-1]["minutes"]} min, cost {cost}' + (f', API ERROR {err}' if err else ''))
        time.sleep(2)
    with open(os.path.join(run, 'agents.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    errors = [r for r in rows if r['api_error']]
    if errors:
        say(f'WARNING: {len(errors)} worker(s) stopped on an API error (for example a usage limit); treat this run as incomplete.')
    b = meta['branch']
    say(f'result: {run}/up.git, branch {b}')
    say(sh('git', '-C', os.path.join(run, 'up.git'), 'log', '--oneline', '-8', b).stdout)
    return 1 if errors else 0
