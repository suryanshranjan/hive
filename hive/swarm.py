"""hive run: a silent swarm on a copy of a repository (from lab/make_swarm.py and lab/launch.py).

The repository at --repo (with .hive/config.json committed) is cloned into a bare upstream under the run folder;
every worker gets its own clone, a rendered prompt, and the same environment. The source repository is never pushed
to: the swarm's result is the shared branch of <run>/up.git.

Workers run $HIVE_WORKER_CMD (default: headless Claude Code) inside their clone with the prompt on stdin. They execute
shell commands, so run swarms in a container or a throwaway VM."""
import csv, json, os, shutil, subprocess, sys, time

from . import argv, PY, codemap, config, law, owner
from .guard import sh

DEFAULT_CMD = __import__('hive').claude_cmd(('Bash', 'Read', 'Edit', 'Write', 'Glob', 'Grep'), edits=True)

# Any coding agent can be a builder (the owner: "Hive can work with any"). Each runs unattended in its own clone and
# reads its instructions on stdin; agents that take the task as an argument get it from stdin through `sh -c`.
# Builders push to the shared upstream outside their folder, so sandboxed agents need write access beyond it: run
# Hive in a container. Codex was run for real (0.160.1, reads stdin); Gemini's flags are as documented in Oct 2026.
# Antigravity: the owner's machine has the Antigravity IDE (1.107.0), an editor whose agent runs inside its window; its
# command line (antigravity-ide) only opens files and manages extensions, so it cannot be run as a headless builder
# (checked Oct 31 2026). The preset expects a headless `agy`; without one, Hive says so and suggests Gemini, which runs
# the same Google models from the command line.
AGENT_HELP = {
    'antigravity': "The Antigravity IDE has no command-line mode Hive can run as a builder (its agent works inside the "
                   "editor window). For Google's models, use --agent gemini: npm install -g @google/gemini-cli, then run "
                   "gemini once to log in.",
    'gemini': 'Install it: npm install -g @google/gemini-cli, then run gemini once in a terminal to log in.',
    'codex': 'Install it: npm install -g @openai/codex, then run codex login.',
}
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

def missing_agents(spec=None):
    """The chosen agents whose command is not installed on this machine (none under HIVE_WORKER_CMD)."""
    import shutil
    if os.environ.get('HIVE_WORKER_CMD'):
        return []
    return [a for a in agents(spec) if not shutil.which(AGENTS[a][1])]

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
            if d:   # Codex says tokens, not dollars: priced here, so his monthly total counts Codex builders too
                d['total_cost_usd'] = codex_cost(d['usage'].get('input_tokens'), d['usage'].get('output_tokens'))
        except Exception:
            pass
        if not d:
            return '', '', ''
    u = d.get('usage') or {}
    tok = sum(int(u.get(k) or 0) for k in ('input_tokens', 'output_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens'))
    err = d.get('api_error_status') or (('auth' if 'authenticat' in str(d.get('result', '')).lower() else 'error')
                                        if d.get('is_error') and d.get('terminal_reason') == 'api_error' else '')
    return tok or '', d.get('total_cost_usd', ''), err

def codex_cost(inp, out):
    """Dollars for Codex tokens, an estimate at HIVE_CODEX_PRICE ("input,output" dollars per million tokens; default
    1.25,10, list prices as last known). The audit, Nov 15: Codex builds counted as $0 against his cap."""
    try:
        pin, pout = (float(x) for x in os.environ.get('HIVE_CODEX_PRICE', '1.25,10').split(','))
    except ValueError:
        pin, pout = 1.25, 10.0
    return round((int(inp or 0) * pin + int(out or 0) * pout) / 1e6, 6)

def over_budget(run_spent):
    """A plain sentence when this run has taken the month past his cap by more than HIVE_BUDGET_OVERRUN (default 20%
    over): no more builders are started or picked up. None otherwise, or when he set no cap."""
    from . import budget
    c = budget.cap()
    if not c:
        return None
    total = budget.spent_month() + run_spent
    if total <= c * float(os.environ.get('HIVE_BUDGET_OVERRUN', 1.2)):
        return None
    return (f"This month has reached ${total:.2f} against your ${c:g} limit, so I'm not starting more builders on this "
            "build. What has landed is kept. Raise the limit (say: set my budget to ...) to carry on.")

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
    named = cfg.get('area_parts', {})   # Gate 80: areas named from the goal's parts, with no tests of their own yet
    return '\n'.join(f'- `{a}`: ' + (f'tests matching {", ".join(f"`{g}`" for g in globs)}' if globs else
                      f'the goal\'s part "{named.get(a, a)}"') for a, globs in sorted(areas.items()))

SPLIT_FROM = 3   # Gate 74: from this many builders, with the owner there to answer, one builder owns his decisions

BUSINESS_ROLE = ("\n## Your role: the business builder\nYou alone own the parts of the goal that turn on the owner's business "
                 "decisions (who pays what, cut-offs, tiers, rounding, labels, what happens with blank, missing, negative or odd "
                 "information); your teammates build everything else and leave those parts to you. Start asking at once, "
                 "while they build. **Ask systematically**, part by part: (1) the rule itself, (2) rounding and the exact form "
                 "of the result, (3) boundaries and cut-offs, and (4) what happens with blank, missing, negative, zero or "
                 "oddly formatted information. Build each part to his answers, one or two parts at a time, and encode each "
                 "answer as a test before you land. Your teammates may land a business part's machinery with placeholders "
                 "for you (Gate 90): after each sync run `grep -rn -i placeholder --include=*.py .` (outside tests), and "
                 "fill every one to his answers before you stop. You may claim any area, including one already landed, and "
                 "more than an even share. You are done only when no placeholder is left.\n")
BUILDER_ROLE = ("\n## Your role: build the rest\nOne teammate, `{biz}`, owns every part of the goal that turns on the "
                "owner's business decisions (who pays what, cut-offs, tiers, rounding, labels, what happens with missing or "
                "odd information) and asks the owner about them. Do not ask the owner yourself, and do not claim or change "
                "those parts: build everything else, the machinery they stand on first, so `{biz}` can land on it. If "
                "something you build needs one of his decisions, leave a clear placeholder and let `{biz}` fill it.\n")

BUSINESS_ROLE_LATER = ("\n## Your role: the business builder\nYou alone own the parts of the goal that turn on the owner's "
                       "business decisions (who pays what, cut-offs, tiers, rounding, labels, what happens with blank, "
                       "missing, negative or odd information); your teammates build everything else and leave those parts "
                       "to you. The owner is away until the morning, so **record his questions systematically**, part by "
                       "part, before you build each one: (1) the rule itself, (2) rounding and the exact form of the result, "
                       "(3) boundaries and cut-offs, and (4) what happens with blank, missing, negative, zero or oddly "
                       "formatted information. Then build your best guess for each and encode it as a test, so his morning "
                       "answer is a small change.\n")
BUILDER_ROLE_LATER = ("\n## Your role: build the rest\nOne teammate, `{biz}`, owns every part of the goal that turns on the "
                      "owner's business decisions (who pays what, cut-offs, tiers, rounding, labels, what happens with "
                      "missing or odd information) and records the owner's questions about them for the morning. Do not "
                      "record questions yourself, and do not claim or change those parts: build everything else, the "
                      "machinery they stand on first, so `{biz}` can land on it. If something you build needs one of his "
                      "decisions, leave a clear placeholder and let `{biz}` fill it.\n")

def split_overnight():
    """Gate 77: split the night builders too. Tested: 25.7 vs 25.0 of 27 after the morning, 1.28x the morning questions;
    no gain worth it, so off unless HIVE_SPLIT_OVERNIGHT=1."""
    return os.environ.get('HIVE_SPLIT_OVERNIGHT') == '1'

def split_roles(workers, questions):
    """Gate 74: with the owner there to answer and 3 or more builders, the last builder owns his decisions and asks him
    systematically; the others build the rest. (Gates 72-73: with his decisions spread over the team, its business rules
    were 3-7 points less right than one agent's; split, 97.8 vs 95.2%, with the engineering as fast as before.)"""
    if questions == 'later':
        return workers >= SPLIT_FROM and split_overnight()
    return workers >= SPLIT_FROM and questions not in (0, None)

def prepare(repo, run, workers, goal, minutes=40, examples=None, questions=None, assumptions=False, code_map=None,
            map_guide=None, derive_areas=None):
    """Create <run>/up.git, one clone per worker in <run>/work, and one prompt per worker in <run>/prompts."""
    repo = os.path.abspath(repo); run = os.path.abspath(run)
    cfg = config.load(repo)
    b = cfg.get('branch') or sh('git', '-C', repo, 'rev-parse', '--abbrev-ref', 'HEAD').stdout.strip()
    if os.path.exists(run):
        raise SystemExit(f'{run} exists: choose a new run folder')
    for d in ('work', 'prompts', 'logs', 'out'):
        os.makedirs(os.path.join(run, d))
    owner_text = owner.setup(run, examples, None if questions == 'later' else questions, assumptions, later=questions == 'later')
    up = os.path.join(run, 'up.git')
    sh('git', 'clone', '-q', '-c', 'core.autocrlf=false', '--bare', '--branch', b, repo, up)
    sh('git', '-C', up, 'symbolic-ref', 'HEAD', f'refs/heads/{b}')
    if derive_areas is None:
        derive_areas = os.environ.get('HIVE_DERIVE_AREAS') != '0'
    configured = cfg.get('areas') and not cfg.get('area_parts')   # areas an earlier build derived are that goal's, not this one's
    if derive_areas and not configured and workers > 1:   # Gate 80: claim the goal's parts by name (duplicated work 5.7 -> 0 of 12)
        goal_text0 = open(goal, encoding='utf-8').read() if os.path.exists(goal) else goal
        names = law.part_names(goal_text0)
        if len(names) > 1:
            keys = law.area_names(names)
            tmp = os.path.join(run, 'areas_tmp'); sh('git', 'clone', '-q', up, tmp)
            path = os.path.join(tmp, '.hive', 'config.json'); c = json.load(open(path))
            c['areas'] = {k: [] for k in keys}; c['area_parts'] = dict(zip(keys, names))
            json.dump(c, open(path, 'w'), indent=1)
            sh('git', '-C', tmp, '-c', 'user.name=hive', '-c', 'user.email=hive@local', 'commit', '-q', '-am',
               "hive: the goal's parts, as areas to claim")
            sh('git', '-C', tmp, 'push', '-q', 'origin', f'HEAD:{b}'); shutil.rmtree(tmp, ignore_errors=True)
            cfg['areas'] = c['areas']; cfg['area_parts'] = c['area_parts']
    template = open(os.path.join(HIVE_ROOT, 'hive', 'templates', 'worker.md'), encoding='utf-8').read()
    notes_on, _ = law.notes(workers)   # Gates 43-44: silence is enough below about 10 builders
    notes_text = ("\n## Team notes\nThis swarm is large enough that builders may change the same code. At each sync, "
                  "`python3 -m hive notes` shows what the others said. When you land something others must know about (a "
                  "shared helper, a changed interface, a file many will touch), add `--note \"<one line>\"` to `hive land`. "
                  "One line, only when it matters.\n") if notes_on else ""
    goal_text = open(goal, encoding='utf-8').read().strip() if os.path.exists(goal) else goal
    split = split_roles(workers, questions)
    if code_map is None:
        code_map = codemap.wanted()
    built = os.path.join(run, 'map') if code_map and codemap.build(repo, os.path.join(run, 'map')) else None   # Gate 78
    for k in range(1, workers + 1):
        me = f'w{k}'; work = os.path.join(run, 'work', me)
        sh('git', 'clone', '-q', '-c', 'core.autocrlf=false', up, work)
        sh('git', '-C', work, 'config', 'user.name', me); sh('git', '-C', work, 'config', 'user.email', f'{me}@hive.local')
        for link in cfg.get('snapshot_links', []):   # dependency folders, shared read-only from the source checkout
            src, dst = os.path.join(repo, link), os.path.join(work, link)
            if os.path.exists(src) and not os.path.exists(dst):
                from . import link as _link
                _link(src, dst)
        text = (template.replace('{ME}', me).replace('{N}', str(workers)).replace('{WORK}', work).replace('{BRANCH}', b)
                .replace('{LOG}', os.path.join(run, 'logs', f'{me}.log')).replace('{GOAL}', goal_text)
                .replace('{TEST_CMD}', cfg['test_cmd']).replace('{AREAS}', _areas_text(cfg)).replace('{OWNER}', owner_text)
                .replace('{MINUTES}', str(minutes)).replace('{NOTES}', notes_text))
        if built:   # Gate 78: one map of the code, built once, in every clone
            codemap.install(built, work, map_guide); text = text.replace(owner_text, codemap.text() + owner_text) if owner_text else text + codemap.text()
        if split:   # Gate 74: one builder owns the owner's decisions, the rest build everything else
            biz = f'w{workers}'
            brole, rrole = (BUSINESS_ROLE_LATER, BUILDER_ROLE_LATER) if questions == 'later' else (BUSINESS_ROLE, BUILDER_ROLE)
            text = text.replace(owner_text, (brole + owner_text) if me == biz else rrole.format(biz=biz))
        open(os.path.join(run, 'prompts', f'{me}.md'), 'w', encoding='utf-8').write(text.replace('python3 -m hive', f'{PY} -m hive'))
    json.dump(dict(repo=repo, branch=b, workers=workers, started=None, business_builder=f'w{workers}' if split else None),
              open(os.path.join(run, 'run.json'), 'w'), indent=1)
    return run

# Builders get the model keys they run on, never Hive's own secrets: the owner's chat, other providers' keys, his
# GitHub, cloud and host logins (the audit, Nov 15: builders run with full access, so whatever is in their
# environment is theirs to read or leak).
BUILDER_HIDES = ('TELEGRAM_BOT_TOKEN', 'HIVE_FAST_KEY', 'HIVE_PAIR_CODE', 'GITHUB_TOKEN', 'GH_TOKEN', 'GITLAB_TOKEN',
                 'RENDER_API_KEY', 'VERCEL_TOKEN', 'NETLIFY_AUTH_TOKEN', 'RAILWAY_TOKEN', 'FLY_API_TOKEN',
                 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN', 'HIVE_MASTER_KEY',
                 'PGPASSWORD', 'DATABASE_URL', 'STRIPE_API_KEY', 'RAZORPAY_KEY_SECRET')

def builder_env(base=None):
    """The environment a builder runs in: this one without Hive's own secrets."""
    return {k: v for k, v in (os.environ if base is None else base).items() if k.upper() not in BUILDER_HIDES}

def launch(run, max_parallel=0, say=lambda m: print(m, flush=True)):
    """Run every worker (at most max_parallel at once), wait for all, and write <run>/agents.csv."""
    run = os.path.abspath(run)
    agents(); kth = lambda me: int(me[1:]) if me[1:].isdigit() else 1   # an unknown agent stops here, before any start
    env = dict(builder_env(), PYTHONPATH=HIVE_ROOT + os.pathsep + os.environ.get('PYTHONPATH', ''),
               HIVE_GUARD_CACHE=os.path.join(run, 'guard_cache'), HIVE_RUN=run)
    env = codemap.path_env(run, env)   # Gate 78-79: graphify on the builders' PATH when there is a map
    queue = sorted(f[:-3] for f in os.listdir(os.path.join(run, 'prompts')) if f.endswith('.md'))
    from . import sandbox   # in a container where Docker runs (the owner's choice, Nov 15); hive/sandbox.py says why
    w1 = os.path.join(run, 'work', 'w1'); boxed = False
    if os.path.isdir(w1):
        c = config.load(w1)
        boxed = sandbox.decide(run, c['test_cmd'], c.get('junit', '.hive/junit.xml'), env, say,
                               custom=bool(os.environ.get('HIVE_WORKER_CMD')))
    missing = [] if boxed else missing_agents()   # in the sandbox the agents come with the image
    if missing:   # an agent that is not here would fail every builder on it, one by one: say so once, before any start
        raise SystemExit(' '.join(f"{a} isn't installed here. {AGENT_HELP.get(a, '')}".strip() for a in missing))
    if boxed:
        say("Builders run in a sandbox: each sees only its own copy of the project, never your keys or files.")
    meta = json.load(open(os.path.join(run, 'run.json'))); meta['started'] = int(time.time())
    json.dump(meta, open(os.path.join(run, 'run.json'), 'w'), indent=1)

    board = {}   # <run>/builders.json: who runs on which agent, working or done, for the owner's phone (hive/team.py)

    def mark(me, **kw):
        board.setdefault(me, {'agent': builder_agent(k=kth(me))}).update(kw)
        try:
            json.dump(board, open(os.path.join(run, 'builders.json.tmp'), 'w'), indent=1)
            os.replace(os.path.join(run, 'builders.json.tmp'), os.path.join(run, 'builders.json'))
        except OSError:
            pass
    for me in queue:
        mark(me, state='queued')
    tries = int(os.environ.get('HIVE_RESUME_TRIES', 8))   # about 6 hours of waiting at most
    # one attempt's wall clock (the audit, Nov 15: a hung builder held an overnight run for ever); waiting out a usage
    # limit does not count, since each pick-up starts its own clock
    from . import run as _run
    limit = _run.seconds('HIVE_BUILDER_HOURS', 4) * 3600
    attempts, spent, first = {}, {}, {}   # per worker: limit stops so far, tokens and cost of earlier attempts, start

    def start(me):
        out = open(os.path.join(run, 'out', f'{me}.json'), 'w')
        group = ({'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == 'nt' else {'start_new_session': True})
        prompt = open(os.path.join(run, 'prompts', f'{me}.md'), encoding='utf-8').read() + (RESUME if attempts.get(me) else '')
        if boxed:
            sandbox.kill(run, me)   # a container left from an earlier attempt of this builder
            cmd, denv = sandbox.command(run, me, builder_cmd(k=kth(me)), env, agent=builder_agent(k=kth(me)))
            cmd[0] = shutil.which(cmd[0]) or cmd[0]
            penv, prompt = sandbox.popen_env(env, denv), sandbox.inside(prompt, run)
        else:
            cmd, penv = argv(builder_cmd(k=kth(me))), dict(env, HIVE_WORKER=me, PYTHONIOENCODING='utf-8')
        p = subprocess.Popen(cmd, cwd=os.path.join(run, 'work', me), stdin=subprocess.PIPE, stdout=out,
                             stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace',   # Windows: "₹" in a goal
                             env=penv, **group)
        try:
            p.stdin.write(prompt)
            p.stdin.close()
        except OSError:   # BrokenPipeError; on Windows a builder that already exited gives EINVAL instead
            pass
        say(f'{"picked up" if attempts.get(me) else "launched"} {me}' + (f' ({builder_agent(k=kth(me))})' if len(agents()) > 1 else ''))
        first.setdefault(me, time.time())
        mark(me, state='working', pid=p.pid, started=int(first[me]), **({'container': sandbox.name(run, me)} if boxed else {}))
        return [me, time.time(), p, out]

    cap = max_parallel or len(queue); live = []; rows = []; waiting = []   # waiting: [(when, worker)]
    told = []
    def stop_for_budget():
        """Past his monthly cap (plus the margin): say so once, and start nothing more (the audit, Nov 15: the cap
        was advice before a build only, never a stop)."""
        why = over_budget(sum(float(r.get('cost_usd') or 0) for r in rows) + sum(c for _, c in spent.values()))
        if why and not told:
            told.append(why); say(why)
            for q in queue:
                mark(q, state='budget')
            queue.clear()
        return bool(why)
    while queue and len(live) < cap:
        live.append(start(queue.pop(0)))
    while live or waiting:
        for when, me in list(waiting):   # usage limit has reset: the worker carries on in its own clone
            if time.time() >= when:
                waiting.remove((when, me))
                if stop_for_budget():
                    mark(me, state='budget'); continue
                live.append(start(me))
        for item in list(live):
            me, t0, p, out = item
            if p.poll() is None:
                if time.time() - t0 > limit:   # past its time: the builder and everything it started are stopped
                    from . import run as _run
                    _run._kill_tree(p); p.wait()
                    if boxed:
                        sandbox.kill(run, me)
                    open(os.path.join(run, 'out', f'{me}.timeout'), 'w').write(str(int(limit)))
                    say(f'{me} ran past {limit / 3600:g} h and was stopped (HIVE_BUILDER_HOURS); what it landed is kept.')
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
                mark(me, state='waiting', until=int(when))
                say((f"{me} stopped: Claude's login has expired. Run claude and log in again (/login); I'll try again "
                     f"at {time.strftime('%H:%M', time.localtime(when))} and keep trying.") if reset == -1 else
                    f"{me} stopped: Claude's usage limit was reached. I'll pick up again at "
                    f"{time.strftime('%H:%M', time.localtime(when))}; its work so far is kept.")
                continue
            t, c = spent.get(me, (0, 0.0))
            tok = (int(tok or 0) + t) or tok; cost = round(float(cost or 0) + c, 6) if (cost or c) else cost
            rows.append(dict(worker=me, agent=builder_agent(k=kth(me)), start=int(first[me]), end=int(time.time()),
                             minutes=round((time.time() - first[me]) / 60, 1), exit=p.returncode, tokens=tok,
                             cost_usd=cost, api_error=err, limit_stops=attempts.get(me, 0)))
            mark(me, state='stopped' if os.path.exists(os.path.join(run, 'stopped', me)) else
                 'timed out' if os.path.exists(os.path.join(run, 'out', f'{me}.timeout')) else 'finished',
                 ended=int(time.time()), exit=p.returncode)
            say(f'{me} finished: exit {p.returncode}, {rows[-1]["minutes"]} min, cost {cost}' + (f', API ERROR {err}' if err else ''))
            if queue and not stop_for_budget():   # after its cost is counted, so the cap sees it
                live.append(start(queue.pop(0)))
        time.sleep(2)
    if boxed:
        sandbox.forget_logins(run)   # the copies of the agents' logins go with the run
    with open(os.path.join(run, 'agents.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    errors = [r for r in rows if r['api_error']]
    if errors:
        say(f'WARNING: {len(errors)} worker(s) stopped on an API error (for example a usage limit); treat this run as incomplete.')
    b = meta['branch']
    say(f'result: {run}/up.git, branch {b}')
    say(sh('git', '-C', os.path.join(run, 'up.git'), 'log', '--oneline', '-8', b).stdout)
    return 1 if errors else 0
