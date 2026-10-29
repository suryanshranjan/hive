"""The builders, from the owner's phone: who is on which agent, what each is doing now, what each has landed; stop one;
and choose the team for the next build (the owner: "from Telegram I should be able to coordinate all the builders").

Everything is read from the run folder a build writes (builders.json from hive/swarm.py, the shared branch in up.git),
so it works from `hive listen` while `hive start` runs in another process."""
import glob, json, os, signal, subprocess, tempfile, time

from . import swarm

RUNS = os.path.join(os.path.expanduser('~'), '.hive', 'runs')   # hive/start.py keeps each build's folders here
TEAM = os.path.join(os.path.expanduser('~'), '.hive', 'team.json')   # the team he chose for his next builds

def current_run():
    """The run folder of the build that is running or ran last (a build, or a fix round), or None."""
    runs = glob.glob(os.path.join(RUNS, '*', '*', 'run.json'))
    return os.path.dirname(max(runs, key=os.path.getmtime)) if runs else None

def _git(up, *a):
    return subprocess.run(['git', '--git-dir', up, *a], capture_output=True, text=True, encoding='utf-8',
                          errors='replace').stdout

def board(run):
    """[{name, agent, state, minutes, holding, landed, last}] for every builder of this run."""
    try:
        meta = json.load(open(os.path.join(run, 'run.json')))
    except (OSError, ValueError):
        return []
    try:
        b = json.load(open(os.path.join(run, 'builders.json')))
    except (OSError, ValueError):
        b = {}
    up, branch = os.path.join(run, 'up.git'), meta.get('branch', 'main')
    holding = {}
    for f in _git(up, 'ls-tree', '--name-only', f'{branch}:current_tasks').split():
        if f.endswith('.txt'):
            first = _git(up, 'show', f'{branch}:current_tasks/{f}').split('\n', 1)[0]
            who, _, what = first.partition(':')
            holding.setdefault(who.strip(), []).append(what.strip() or f[:-4])
    landed = {}
    for line in _git(up, 'log', '--format=%an\t%s', branch).splitlines():
        who, _, subj = line.partition('\t')
        if subj.startswith(('Lock:', 'hive:', 'Withdraw lock', 'Release lock')) or who == 'hive':
            continue
        landed.setdefault(who, []).append(subj)
    names = sorted(set(b) | {f'w{k}' for k in range(1, meta.get('workers', 0) + 1)}, key=lambda n: (len(n), n))
    out = []
    for n in names:
        r = b.get(n, {})
        start, end = r.get('started'), r.get('ended') or time.time()
        state = r.get('state', 'queued')
        if os.path.exists(os.path.join(run, 'stopped', n)):   # he stopped it; the swarm may not have noticed yet
            state = 'stopped'
        out.append(dict(name=n, agent=r.get('agent', 'claude'), state=state,
                        minutes=int((end - start) / 60) if start else 0, holding=holding.get(n, []),
                        landed=len(landed.get(n, [])), last=(landed.get(n) or [''])[0]))
    return out

def stuck(run, seen, now=None, minutes=None):
    """Builders that have worked for `minutes` (default HIVE_STUCK_MINUTES, 20) without landing anything new, each told
    about once. `seen` is the caller's memory between checks: {name: [landed count, since when, told]}. Returns the
    board rows of builders to tell him about now."""
    now = now or time.time()
    minutes = minutes or float(os.environ.get('HIVE_STUCK_MINUTES', 20))
    out = []
    for r in board(run):
        mark = seen.get(r['name'])
        if r['state'] != 'working':
            seen.pop(r['name'], None); continue
        if not mark or mark[0] != r['landed']:   # new work landed: the clock starts again
            seen[r['name']] = [r['landed'], now, False]; continue
        if not mark[2] and now - mark[1] >= minutes * 60:
            mark[2] = True; out.append(r)
    return out

def board_text(run):
    """The board in plain lines, for Jarvis's facts and for "who's doing what"."""
    rows = board(run)
    if not rows:
        return ''
    word = {'working': 'working', 'finished': 'finished', 'stopped': 'stopped by you', 'queued': 'waiting to start',
            'waiting': "paused until its agent's usage limit resets"}
    lines = []
    for r in rows:
        line = f"{r['name']} ({r['agent']}): {word.get(r['state'], r['state'])}"
        if r['state'] == 'working' and r['minutes']:
            line += f" for {r['minutes']} min"
        if r['holding']:
            line += f"; now building: {'; '.join(r['holding'])[:160]}"
        line += f"; landed {r['landed']} piece{'s' if r['landed'] != 1 else ''} of work"
        if r['last']:
            line += f" (latest: {r['last'][:100]})"
        lines.append(line + '.')
    return '\n'.join(lines)

def find(run, said):
    """Which builder he means: "w2", "builder 2", "the second one", "the codex one" (when only one is), or None."""
    import re
    rows = board(run); t = said.lower()
    m = re.search(r'\b(?:w|worker|builder|number|no\.?|#)\s*(\d+)\b', t) or re.search(r'\b(\d+)\b', t)
    if m and any(r['name'] == f'w{m.group(1)}' for r in rows):
        return f'w{m.group(1)}'
    for k, word in enumerate(('first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth'), 1):
        if word in t and any(r['name'] == f'w{k}' for r in rows):
            return f'w{k}'
    for agent in swarm.AGENTS:
        mine = [r['name'] for r in rows if r['agent'] == agent and r['state'] == 'working']
        if agent in t and len(mine) == 1:
            return mine[0]
    return None

def stop_builder(run, me):
    """Stop one builder, and free the work it had claimed so another builder can take it. True if it was stopped."""
    try:
        r = json.load(open(os.path.join(run, 'builders.json'))).get(me, {})
    except (OSError, ValueError):
        return False
    if r.get('state') != 'working' or not r.get('pid'):
        return False
    os.makedirs(os.path.join(run, 'stopped'), exist_ok=True)
    open(os.path.join(run, 'stopped', me), 'w').write(str(int(time.time())))   # the swarm reports it as stopped
    try:
        if os.name == 'nt':
            subprocess.run(['taskkill', '/F', '/T', '/PID', str(r['pid'])], capture_output=True)
        else:
            os.kill(r['pid'], signal.SIGTERM)
    except OSError:
        pass
    _release(run, me)
    return True

def _release(run, me):
    """Remove the stopped builder's claims from the shared branch (they would block that work for everyone)."""
    meta = json.load(open(os.path.join(run, 'run.json'))); b = meta.get('branch', 'main')
    tmp = tempfile.mkdtemp()
    for k in range(5):   # builders push too: on a lost race, start again from the new tip
        c = os.path.join(tmp, f'c{k}')
        subprocess.run(['git', 'clone', '-q', '-b', b, os.path.join(run, 'up.git'), c], capture_output=True)
        g = lambda *a: subprocess.run(['git', '-C', c, *a], capture_output=True, text=True)
        mine = [f for f in glob.glob(os.path.join(c, 'current_tasks', '*.txt'))
                if open(f, encoding='utf-8', errors='replace').read().startswith(me + ':')]
        if not mine:
            return
        g('rm', '-q', *[os.path.relpath(f, c) for f in mine])
        g('-c', 'user.name=hive', '-c', 'user.email=hive@local', 'commit', '-q', '-m', f'Release lock: {me} was stopped by the owner')
        if g('push', '-q', 'origin', f'HEAD:{b}').returncode == 0:
            return

OWNER_FILE = 'OWNER.md'   # his instructions to a running swarm; builders read it at every sync (hive/templates/worker.md)

def instruct(run, text, builder=None):
    """Give the running builders a new instruction from him (a change of direction, more work, one builder's new job).
    It is committed to OWNER.md on the shared branch, newest first, so every builder sees it at its next sync. True if
    it reached the shared branch."""
    meta = json.load(open(os.path.join(run, 'run.json'))); b = meta.get('branch', 'main')
    line = f"- {time.strftime('%H:%M')} {'to ' + builder + ': ' if builder else ''}{text.strip()}"
    tmp = tempfile.mkdtemp()
    for k in range(5):   # builders push too: on a lost race, start again from the new tip
        c = os.path.join(tmp, f'c{k}')
        subprocess.run(['git', 'clone', '-q', '-b', b, os.path.join(run, 'up.git'), c], capture_output=True)
        g = lambda *a: subprocess.run(['git', '-C', c, *a], capture_output=True, text=True)
        path = os.path.join(c, OWNER_FILE)
        old = open(path, encoding='utf-8').read().split('\n', 2)[2] if os.path.exists(path) else ''
        open(path, 'w', encoding='utf-8').write("# The owner's instructions (newest first; they override the goal where "
                                                 "they differ)\n\n" + line + '\n' + old)
        g('add', OWNER_FILE)
        g('-c', 'user.name=hive', '-c', 'user.email=hive@local', 'commit', '-q', '-m', f'hive: the owner says: {text.strip()[:80]}')
        if g('push', '-q', 'origin', f'HEAD:{b}').returncode == 0:
            return True
    return False

def pick(run):
    """The builder to give a new task to: a working one with nothing claimed, else the one holding least. A task meant
    for everyone was done twice in the live test (both Codex builders built the same report), so one builder owns it."""
    rows = [r for r in board(run) if r['state'] == 'working']
    return min(rows, key=lambda r: (len(r['holding']), r['landed']))['name'] if rows else None

def law_advice(repo, workers):
    """What the swarm law says about his chosen number of builders for this project: (n, why) when it would pick a
    different number, else None. Uses the test time measured by his last build; None before any build measured it."""
    from . import law
    homes = sorted(glob.glob(os.path.join(RUNS, '*', 'state.json')), key=os.path.getmtime)
    for h in reversed(homes):
        try:
            st = json.load(open(h))
        except (OSError, ValueError):
            continue
        if os.path.abspath(st.get('repo', '')) == os.path.abspath(repo) and st.get('t_g'):
            n, why = law.builders(st['t_g'])
            return (n, why) if n != int(workers) else None
    return None

def chosen():
    """The team he chose for his next builds: {'agent': 'claude,codex', 'workers': 4}, either part optional."""
    try:
        return json.load(open(TEAM))
    except (OSError, ValueError):
        return {}

def choose(agent=None, workers=None):
    """Remember his choice for the next builds; returns it. agent is one agent or a mix ("claude,codex")."""
    t = chosen()
    if agent:
        swarm.agents(agent)   # an agent Hive does not know is refused here, with the choices
        t['agent'] = ','.join(swarm.agents(agent))
    if workers == 'auto':   # the law picks the number for each build again
        t.pop('workers', None)
    elif workers:
        t['workers'] = max(1, min(int(workers), 24))
    os.makedirs(os.path.dirname(TEAM), exist_ok=True)
    json.dump(t, open(TEAM, 'w'))
    return t

def describe(t):
    """His chosen team in words: "4 builders, taking Claude and Codex in turn"."""
    names = {'claude': 'Claude', 'codex': 'Codex', 'gemini': 'Gemini', 'antigravity': 'Antigravity'}
    agents = [names.get(a, a) for a in (t.get('agent') or 'claude').split(',')]
    who = agents[0] if len(agents) == 1 else ' and '.join([', '.join(agents[:-1]), agents[-1]]) + ' in turn'
    n = t.get('workers')
    return (f"{n} builder{'s' if n != 1 else ''}" if n else 'as many builders as the law picks for each job') + f', on {who}'
