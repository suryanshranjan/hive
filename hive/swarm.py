"""hive run: a silent swarm on a copy of a repository (from lab/make_swarm.py and lab/launch.py).

The repository at --repo (with .hive/config.json committed) is cloned into a bare upstream under the run folder;
every worker gets its own clone, a rendered prompt, and the same environment. The source repository is never pushed
to: the swarm's result is the shared branch of <run>/up.git.

Workers run $HIVE_WORKER_CMD (default: headless Claude Code) inside their clone with the prompt on stdin. They execute
shell commands, so run swarms in a container or a throwaway VM."""
import csv, json, os, shutil, subprocess, sys, time

from . import argv, PY, config, law, owner
from .guard import sh

DEFAULT_CMD = 'claude -p --output-format json --permission-mode acceptEdits --allowedTools Bash Read Edit Write Glob Grep'

# Any coding agent can be a builder (the owner: "Hive can work with any"). Each runs unattended in its own clone and
# reads its instructions on stdin; agents that take the task as an argument get it from stdin through `sh -c`.
# Builders push to the shared upstream outside their folder, so sandboxed agents need write access beyond it: run
# Hive in a container. Codex was run for real (0.160.1, reads stdin); Gemini's and Antigravity's flags are as
# documented in Oct 2026, and Antigravity's approval flag is unverified (sources disagree).
AGENTS = {
    'claude': (DEFAULT_CMD, 'claude'),
    'codex': ('codex exec --json --skip-git-repo-check --sandbox danger-full-access -', 'codex'),   # verified, 0.160.1
    'gemini': ("""sh -c 'gemini --yolo --output-format json -p "$(cat)"'""", 'gemini'),
    'antigravity': ("""sh -c 'agy --output-format json --approve all -p "$(cat)"'""", 'agy'),
}

def agents(spec=None):
    """The chosen agents, in order: 'claude', or a mix such as 'claude,codex' (the builders take them in turn)."""
    spec = (spec or os.environ.get('HIVE_AGENT') or config_agent() or 'claude').lower()
    names = [s.strip() for s in spec.replace('+', ',').split(',') if s.strip()] or ['claude']
    for n in names:
        if n not in AGENTS:
            raise SystemExit(f"Hive doesn't know the agent '{n}'. Choose one of: {', '.join(AGENTS)} (or a mix such as "
                             "claude,codex), or set HIVE_WORKER_CMD to any command that reads its task on stdin.")
    return names

def builder_cmd(agent=None, k=1):
    """The command that runs builder k (1-based): HIVE_WORKER_CMD if set, else its agent's preset (default Claude Code).
    In a mixed swarm the builders take the agents in turn: with claude,codex, w1 is Claude, w2 Codex, w3 Claude..."""
    if os.environ.get('HIVE_WORKER_CMD'):
        return os.environ['HIVE_WORKER_CMD']
    return AGENTS[builder_agent(agent, k)][0]

def builder_agent(agent=None, k=1):
    """The agent builder k runs on ('custom' under HIVE_WORKER_CMD)."""
    if os.environ.get('HIVE_WORKER_CMD'):
        return 'custom'
    names = agents(agent)
    return names[(k - 1) % len(names)]

def config_agent():
    """The builder agent saved in ~/.hive/agent (set with `hive start --agent ... --save-agent`)."""
    try:
        return open(os.path.join(os.path.expanduser('~'), '.hive', 'agent')).read().strip()
    except OSError:
        return None
HIVE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _usage(path):
    try:
        d = json.load(open(path))
    except Exception:
        d = {}
        try:   # Codex writes one event per line; its usage comes on "turn.completed" (cached input is part of input)
            for line in open(path, encoding='utf-8', errors='replace'):
                if line.startswith('{') and '"usage"' in line:
                    u = json.loads(line).get('usage') or {}
                    d = {'usage': {'input_tokens': u.get('input_tokens'), 'output_tokens': u.get('output_tokens')}}
        except Exception:
            pass
        if not d:
            return '', '', ''
    u = d.get('usage') or {}
    tok = sum(int(u.get(k) or 0) for k in ('input_tokens', 'output_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens'))
    err = d.get('api_error_status') or (('auth' if 'authenticat' in str(d.get('result', '')).lower() else 'error')
                                        if d.get('is_error') and d.get('terminal_reason') == 'api_error' else '')
    return tok or '', d.get('total_cost_usd', ''), err

RESUME = ("\n\n# You are picking up again\n\nYou were stopped partway by Claude's usage limit; it has reset now. Your clone "
          "still has everything you did, and others may have landed work since. Read the end of your log, commit or "
          "discard anything half-done, pull, check your lock, and carry on from where you stopped. Do not redo work "
          "that has already landed.\n")

def _limit_hit(path):
    """When a worker stopped on Claude's usage limit: the time it resets (a Unix time; 0 if not said); -1 when Claude's
    login expired (it picks up once the owner logs in again); else None."""
    try:
        d = json.load(open(path))
    except Exception:
        return None
    text = str(d.get('result') or '')
    if d.get('is_error') and 'authenticat' in text.lower():
        return -1
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
    if reset == -1:   # waiting for a fresh login: check again every few minutes
        return time.time() + max(floor, float(os.environ.get("HIVE_LOGIN_WAIT", 300)))
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
    sh('git', 'clone', '-q', '-c', 'core.autocrlf=false', '--bare', '--branch', b, repo, up)
    sh('git', '-C', up, 'symbolic-ref', 'HEAD', f'refs/heads/{b}')
    template = open(os.path.join(HIVE_ROOT, 'hive', 'templates', 'worker.md'), encoding='utf-8').read()
    notes_on, _ = law.notes(workers)   # Gates 43-44: silence is enough below about 10 builders
    notes_text = ("\n## Team notes\nThis swarm is large enough that builders may change the same code. At each sync, "
                  "`python3 -m hive notes` shows what the others said. When you land something others must know about (a "
                  "shared helper, a changed interface, a file many will touch), add `--note \"<one line>\"` to `hive land`. "
                  "One line, only when it matters.\n") if notes_on else ""
    goal_text = open(goal, encoding='utf-8').read().strip() if os.path.exists(goal) else goal
    for k in range(1, workers + 1):
        me = f'w{k}'; work = os.path.join(run, 'work', me)
        sh('git', 'clone', '-q', '-c', 'core.autocrlf=false', up, work)
        sh('git', '-C', work, 'config', 'user.name', me); sh('git', '-C', work, 'config', 'user.email', f'{me}@hive.local')
        for link in cfg.get('snapshot_links', []):   # dependency folders, shared read-only from the source checkout
            src, dst = os.path.join(repo, link), os.path.join(work, link)
            if os.path.exists(src) and not os.path.exists(dst):
                os.symlink(src, dst)
        text = (template.replace('{ME}', me).replace('{N}', str(workers)).replace('{WORK}', work).replace('{BRANCH}', b)
                .replace('{LOG}', os.path.join(run, 'logs', f'{me}.log')).replace('{GOAL}', goal_text)
                .replace('{TEST_CMD}', cfg['test_cmd']).replace('{AREAS}', _areas_text(cfg)).replace('{OWNER}', owner_text)
                .replace('{MINUTES}', str(minutes)).replace('{NOTES}', notes_text))
        open(os.path.join(run, 'prompts', f'{me}.md'), 'w', encoding='utf-8').write(text.replace('python3 -m hive', f'{PY} -m hive'))
    json.dump(dict(repo=repo, branch=b, workers=workers, started=None), open(os.path.join(run, 'run.json'), 'w'), indent=1)
    return run

def launch(run, max_parallel=0, say=lambda m: print(m, flush=True)):
    """Run every worker (at most max_parallel at once), wait for all, and write <run>/agents.csv."""
    run = os.path.abspath(run)
    agents(); kth = lambda me: int(me[1:]) if me[1:].isdigit() else 1   # an unknown agent stops here, before any start
    env =dict(os.environ, PYTHONPATH=HIVE_ROOT + os.pathsep + os.environ.get('PYTHONPATH', ''),
               HIVE_GUARD_CACHE=os.path.join(run, 'guard_cache'), HIVE_RUN=run)
    queue = sorted(f[:-3] for f in os.listdir(os.path.join(run, 'prompts')) if f.endswith('.md'))
    meta = json.load(open(os.path.join(run, 'run.json'))); meta['started'] = int(time.time())
    json.dump(meta, open(os.path.join(run, 'run.json'), 'w'), indent=1)

    tries = int(os.environ.get('HIVE_RESUME_TRIES', 8))   # about 6 hours of waiting at most
    attempts, spent, first = {}, {}, {}   # per worker: limit stops so far, tokens and cost of earlier attempts, start

    def start(me):
        out = open(os.path.join(run, 'out', f'{me}.json'), 'w')
        p = subprocess.Popen(argv(builder_cmd(k=kth(me))), cwd=os.path.join(run, 'work', me), stdin=subprocess.PIPE, stdout=out,
                             stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace',   # Windows: "₹" in a goal
                             env=dict(env, HIVE_WORKER=me, PYTHONIOENCODING='utf-8'))
        try:
            p.stdin.write(open(os.path.join(run, 'prompts', f'{me}.md'), encoding='utf-8').read() + (RESUME if attempts.get(me) else ''))
            p.stdin.close()
        except BrokenPipeError:
            pass
        say(f'{"picked up" if attempts.get(me) else "launched"} {me}' + (f' ({builder_agent(k=kth(me))})' if len(agents()) > 1 else ''))
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
                say((f"{me} stopped: Claude's login has expired. Run claude and log in again (/login); I'll try again "
                     f"at {time.strftime('%H:%M', time.localtime(when))} and keep trying.") if reset == -1 else
                    f"{me} stopped: Claude's usage limit was reached. I'll pick up again at "
                    f"{time.strftime('%H:%M', time.localtime(when))}; its work so far is kept.")
                continue
            if queue:
                live.append(start(queue.pop(0)))
            t, c = spent.get(me, (0, 0.0))
            tok = (int(tok or 0) + t) or tok; cost = round(float(cost or 0) + c, 6) if (cost or c) else cost
            rows.append(dict(worker=me, agent=builder_agent(k=kth(me)), start=int(first[me]), end=int(time.time()),
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
