"""hive start (or just `hive`): one conversation from an idea to a tested branch.

Hive asks what to build, finds the project's tests on its own, puts builders to work on copies, brings their questions
and their assumptions to the owner in plain words, sends back what the owner corrects, checks the result, and hands
over a branch. The owner's own branches are never changed: the result arrives as a new branch, hive/<name>."""
import csv, glob, json, os, re, shlex, shutil, subprocess, threading, time

from . import junit, owner, swarm, telegram
from .guard import sh

RUNS = os.path.join(os.path.expanduser('~'), '.hive', 'runs')

def say(msg=''):
    print(msg, flush=True)

def _now():
    return time.strftime('%H:%M')

def _ask(prompt, default=''):
    say(prompt)
    try:
        ans = input('  > ').strip()
    except EOFError:
        ans = ''
    return ans or default

def _n(k, word):
    return f'{k} {word}' + ('' if k == 1 else 's')

def detect_tests(root):
    """(test command writing JUnit XML to .hive/junit.xml, plain description), or (None, None).
    When a project holds several suites, the one with the most test files wins."""
    found = []   # (number of test files, command, description)
    for pj in [os.path.join(root, 'package.json')] + sorted(glob.glob(os.path.join(root, '*', 'package.json'))):
        pdir = os.path.dirname(pj); d = os.path.relpath(pdir, root)
        try:
            script = json.load(open(pj)).get('scripts', {}).get('test', '')
        except Exception:
            continue
        back = '.hive/junit.xml' if d == '.' else os.path.join(os.path.relpath(root, pdir), '.hive', 'junit.xml')
        flags = f'--test-reporter=junit --test-reporter-destination={back}'
        files = [f for t in ('test', 'tests') for f in glob.glob(os.path.join(pdir, t, '**', '*.test.*js'), recursive=True)]
        if 'node --test' in script:
            cmd = script.replace('node --test', f'node --test {flags}', 1)
        elif files and any('node:test' in open(f, errors='ignore').read() for f in files[:20]):
            folder = 'tests' if glob.glob(os.path.join(pdir, 'tests', '*.test.*js')) else 'test'
            cmd = f'node --test {flags} {folder}/*.test.*js'
        else:
            continue
        found.append((len(files) or 1, cmd if d == '.' else f'cd {shlex.quote(d)} && {cmd}',
                      f'node --test in {"the project root" if d == "." else d}'))
    skip = ('node_modules', '.venv', 'venv', '.git')
    py = 0
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in skip]
        py += sum(1 for f in files if re.match(r'(test_.*|.*_test)\.py$', f))
    if py:
        found.append((py, 'python3 -m pytest -q -p no:cacheprovider --junitxml=.hive/junit.xml', 'pytest'))
    if not found:
        return None, None
    _, cmd, how = max(found, key=lambda x: x[0])
    return cmd, how

def detect_links(root):
    """Dependency folders the builders share read-only (they are not in git)."""
    found = [p for p in ('node_modules', '.venv', 'venv') if os.path.isdir(os.path.join(root, p))]
    found += [os.path.relpath(p, root) for p in glob.glob(os.path.join(root, '*', 'node_modules'))]
    return found

def run_tests(root, cmd, junit_rel='.hive/junit.xml'):
    """{test: passed} for the whole suite, run in root."""
    path = os.path.join(root, junit_rel)
    if os.path.exists(path):
        os.remove(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    subprocess.run(cmd, shell=True, cwd=root, capture_output=True)
    return junit.results(path) if os.path.exists(path) else {}

def _link(src_root, dst_root, links):
    for link in links:
        src, dst = os.path.join(src_root, link), os.path.join(dst_root, link)
        if os.path.exists(src) and not os.path.exists(dst):
            os.symlink(src, dst)

def _cost(run):
    try:
        return sum(float(r['cost_usd'] or 0) for r in csv.DictReader(open(os.path.join(run, 'agents.csv'))))
    except Exception:
        return 0.0

class Narrator:
    """Turns new commits on the shared branch into plain sentences."""
    def __init__(self, up, branch):
        self.up, self.branch = up, branch
        self.seen = set(self._log())

    def _log(self):
        out = sh('git', '-C', self.up, 'log', '--format=%H%x09%an%x09%s', self.branch).stdout
        return [line for line in out.splitlines() if line]

    def tick(self):
        for line in reversed(self._log()):
            if line in self.seen:
                continue
            self.seen.add(line)
            _, who, subject = line.split('\t', 2)
            m = re.match(r'Lock: (\S+) \(([^)]*)\)', subject)
            if m:
                say(f'  [{_now()}] Builder {who} picked up: {m.group(1).replace("-", " ")}.')
            elif not subject.startswith(('Release', 'Unlock')):
                short = subject if len(subject) <= 90 else subject[:87].rsplit(' ', 1)[0] + '...'
                say(f'  [{_now()}] Builder {who} landed: {short}')

def _phase(source, run, workers, goal, minutes, questions, assumptions, narrate_owner, phone=None):
    """One build: prepare, launch in the background, narrate progress and serve the owner until every builder is done."""
    swarm.prepare(source, run, workers, goal, minutes, None, questions, assumptions)
    meta = json.load(open(os.path.join(run, 'run.json')))
    log = open(os.path.join(run, 'hive.log'), 'w')
    result = {}
    t = threading.Thread(target=lambda: result.update(code=swarm.launch(run, 0, say=lambda m: (log.write(m + '\n'), log.flush()))),
                         daemon=True)
    t.start()
    narrator = Narrator(os.path.join(run, 'up.git'), meta['branch'])
    if narrate_owner and phone:
        telegram.bridge_questions(run, phone, until=lambda: not t.is_alive(), tick=narrator.tick)
    elif phone:   # no questions in this phase (overnight, or a fix round), but the owner can still ask for status
        telegram.listen(run, phone, until=lambda: not t.is_alive(), tick=narrator.tick)
    elif narrate_owner:
        owner.serve(run, until=lambda: not t.is_alive(), tick=narrator.tick, greet=False)
    while t.is_alive():
        narrator.tick(); time.sleep(3)
    narrator.tick(); log.close()
    return meta['branch'], result.get('code', 1)

def start(repo='.', workers=4, goal=None, minutes=40, overnight=False):
    repo = os.path.abspath(repo)
    say("\nHive here. What are we building today?")
    goal = goal or _ask("(Describe it in a sentence or two, or give the path of a file that describes it.)")
    if not goal:
        say('Nothing to build; come back any time.'); return 0
    goal_text = open(goal).read().strip() if os.path.exists(goal) else goal

    say('\nGot it. Let me look at your project.')
    if sh('git', '-C', repo, 'rev-parse', '--is-inside-work-tree').returncode != 0:
        say('  This folder is not a git repository. Run me inside your project folder.'); return 2
    branch = sh('git', '-C', repo, 'rev-parse', '--abbrev-ref', 'HEAD').stdout.strip()
    if sh('git', '-C', repo, 'status', '--porcelain').stdout.strip():
        say('  You have unsaved changes. Commit or stash them first, so the builders start from what you see.'); return 3
    cfg_path = os.path.join(repo, '.hive', 'config.json')
    cfg = json.load(open(cfg_path)) if os.path.exists(cfg_path) else {}
    test_cmd, how = cfg.get('test_cmd'), 'the command in your hive settings'
    if not test_cmd:
        test_cmd, how = detect_tests(repo)
    if not test_cmd:
        test_cmd = _ask("  I could not find your tests. What command runs them? It must write a JUnit report to "
                        ".hive/junit.xml.")
        how = 'your command'
        if not test_cmd:
            say('  Builders need tests to know when the work is right. Add some and run me again.'); return 4
    links = cfg.get('snapshot_links') or detect_links(repo)
    say(f'  Git repository on branch {branch}, no unsaved changes.')

    words = [w for w in re.findall(r'[a-z0-9]+', goal_text.lower()) if w not in ('goal', 'the', 'a', 'an')]
    slug = '-'.join(words[:4])[:40] or 'build'
    name = f'{slug}-{time.strftime("%m%d-%H%M")}'
    base, k = name, 2
    while os.path.exists(os.path.join(RUNS, name)):   # two builds of the same goal in the same minute
        name = f'{base}-{k}'; k += 1
    home = os.path.join(RUNS, name); os.makedirs(home)
    source = os.path.join(home, 'source')
    sh('git', 'clone', '-q', '--branch', branch, repo, source)
    sh('git', '-C', source, 'config', 'user.name', 'hive'); sh('git', '-C', source, 'config', 'user.email', 'hive@local')
    _link(repo, source, links)
    before = run_tests(source, test_cmd)
    passed, total = sum(before.values()), len(before)
    if total >= 20 and passed < 0.5 * total and how != 'your command':   # a fresh feature's few failing tests are normal
        say(f'  {total - passed} of your {total} tests fail before anyone has touched the code. That often means they need '
            'a setting, such as an environment variable.')
        exact = _ask('  If you run them with a particular command, type it here; otherwise press Enter and I will carry on.')
        if exact:
            test_cmd, how = exact, 'your command'
            before = run_tests(source, test_cmd); passed, total = sum(before.values()), len(before)
    if total == 0:
        say(f'  I ran your tests ({how}) but got no results. Check that they write .hive/junit.xml.'); return 4
    say(f'  Your tests: {how}. {total} tests, ' + ('all passing.' if passed == total else
        f'{passed} passing and {total - passed} not passing yet: the builders will work toward those, '
        'and will not break the ones that pass.'))
    cfg.update(test_cmd=test_cmd, snapshot_links=links, branch=branch); cfg.setdefault('junit', '.hive/junit.xml')
    cfg.setdefault('areas', {})
    os.makedirs(os.path.join(source, '.hive'), exist_ok=True); os.makedirs(os.path.join(source, 'current_tasks'), exist_ok=True)
    json.dump(cfg, open(os.path.join(source, '.hive', 'config.json'), 'w'), indent=1)
    open(os.path.join(source, 'current_tasks', '.keep'), 'a').close()
    ignore = os.path.join(source, '.gitignore')
    text = open(ignore).read() if os.path.exists(ignore) else ''
    if '.hive/junit.xml' not in text.split('\n'):
        open(ignore, 'a').write(('' if text.endswith('\n') or not text else '\n') + '.hive/junit.xml\n')
    sh('git', '-C', source, 'add', '.hive/config.json', 'current_tasks/.keep', '.gitignore')
    sh('git', '-C', source, 'commit', '-q', '-m', 'hive: settings for this build')

    say(f"\nI'll put {workers} builders on it. They work on copies, so your branches stay exactly as they are.")
    cfg_phone = telegram.load()
    phone = telegram.Channel(cfg_phone) if cfg_phone else None
    if overnight:
        say("You're away, so they won't ask you anything: they'll decide, and write down every business assumption "
            + ("for you. When they finish, I'll message you on Telegram to check them." if phone else
               "for you to check when you're back."))
    elif phone:
        say("If they need a decision only you can make, the question will come to your phone on Telegram.")
    else:
        say("If they need a decision only you can make, the question will appear right here.")
    say("(Builders run commands on this computer. For code you don't trust, run me in a container.)")
    say(f'\n[{_now()}] Starting.')
    state = dict(repo=repo, branch=branch, name=name, home=home, test_cmd=test_cmd, links=links, goal=goal_text,
                 workers=workers, minutes=minutes, before=before, started=time.time(), overnight=overnight)
    run1 = os.path.join(home, 'build')
    b, code = _phase(source, run1, workers, goal_text, minutes, 0 if overnight else 4 * workers, True, not overnight, phone)
    state.update(b=b, code=code, final=run1, cost=_cost(run1))
    json.dump(state, open(os.path.join(home, 'state.json'), 'w'), indent=1)
    say(f'\n[{_now()}] ' + (f'All {workers} builders are done.' if workers > 1 else 'The builder is done.'))
    found = owner._assumptions(os.path.join(run1, 'owner'), False)   # business defaults only; technical ones go to engineers
    if overnight and phone:
        rc = _deliver(state)
        if not found:
            phone.send(f"Welcome back{', ' + phone.name() if phone.name() else ''}. The build is finished. "
                       f"{state['check']} Nothing needs your attention. It's ready on branch hive/{name}.")
            return rc
        say(f'\n[{_now()}] Sent {_n(len(found), "assumption")} to your phone; waiting for your replies.')
        if _review_and_fix(state, phone):
            rc = _deliver(state)
            phone.send(f"Done{', ' + phone.name() if phone.name() else ''}. Your changes are in. {state['check']} It's ready on branch hive/{name} whenever you are.")
        else:
            phone.send(f"All set. It's ready on branch hive/{name} whenever you are.")
        return rc
    if overnight:
        rc = _deliver(state)
        if found:
            say(f"\nThey made {_n(len(found), 'assumption')} your description didn't cover. When you're back, type "
                f"`hive morning` to check {'it' if len(found) == 1 else 'them'}; I'll fix anything you correct and update "
                f"the branch.")
        return rc
    if found:
        n = len(found)
        say(f"Before I hand it over: they made {_n(n, 'assumption')} your description didn't cover. Let's check "
            f"{'it' if n == 1 else 'them'} together: press Enter if one is right, or say what should happen instead.")
        try:
            _review_and_fix(state)
        except RuntimeError as e:   # the plain-words step failed: hand over as built; `hive morning` can review later
            say(str(e) + " The build is handed over as is; run `hive morning` later to check its decisions.")
            state["overnight"] = True
    return _deliver(state)

def _review_and_fix(state, phone=None):
    """The owner checks the business assumptions (here, or on the phone); anything corrected goes back to the builders
    for one fix round. Returns True when a fix round ran."""
    run1 = os.path.join(state['home'], 'build')
    if phone:
        hour = time.localtime().tm_hour
        telegram.review(run1, phone, goal=state['goal'], check=state.get('check', ''),
                        greeting='Good morning' if 4 <= hour < 12 else 'Good afternoon' if hour < 17 else 'Good evening')
    else:
        owner.review(run1, intro=False, goal=state['goal'])
    fixes = [r for r in (json.load(open(p)) for p in glob.glob(os.path.join(run1, 'owner', 'reviews', '*.json'))) if not r['ok']]
    if not fixes:
        return False
    say(f'\n[{_now()}] Sending the builders back to fix {_n(len(fixes), "thing")}.')
    fsrc = os.path.join(state['home'], 'fix_source')
    sh('git', 'clone', '-q', '--branch', state['b'], os.path.join(run1, 'up.git'), fsrc)
    _link(state['repo'], fsrc, state['links'])
    corrections = open(os.path.join(run1, 'owner', 'corrections.md')).read()
    run2 = os.path.join(state['home'], 'fix')
    _phase(fsrc, run2, min(state['workers'], max(1, (len(fixes) + 1) // 2)), state['goal'] + '\n\n' + corrections,
           state['minutes'], 0, False, False, phone)
    state.update(final=run2, cost=state['cost'] + _cost(run2))
    json.dump(state, open(os.path.join(state['home'], 'state.json'), 'w'), indent=1)
    say(f'[{_now()}] Fixed.')
    return True

def _deliver(state):
    """Check every test on the result and hand it over as the branch hive/<name> (updated in place after a fix round)."""
    say('\nLet me check the result.')
    result = os.path.join(state['home'], 'result')
    if os.path.exists(result):
        shutil.rmtree(result)
    sh('git', 'clone', '-q', '--branch', state['b'], os.path.join(state['final'], 'up.git'), result)
    _link(state['repo'], result, state['links'])
    before = state['before']; passed = sum(before.values())
    after = run_tests(result, state['test_cmd'])
    p2, t2 = sum(after.values()), len(after)
    broken = [k for k, ok in before.items() if ok and not after.get(k)]
    state['check'] = (f'{_n(t2, "test")}, ' + ('all passing.' if p2 == t2 else f'{p2} passing.') +
                      ('' if not passed else f' All {passed} that passed before still pass.' if not broken else
                       f' {_n(len(broken), "test")} that passed before now fail: look before you merge.'))
    say('  ' + state['check'])
    json.dump(state, open(os.path.join(state['home'], 'state.json'), 'w'), indent=1)
    out = f"hive/{state['name']}"
    sh('git', '-C', state['repo'], 'fetch', '-q', '-f', os.path.join(state['final'], 'up.git'), f"+{state['b']}:{out}")
    mins = round((time.time() - state['started']) / 60)
    took = 'under a minute' if mins < 1 else _n(mins, 'minute')
    say(f'\nDone in {took}' + (f", about ${state['cost']:.2f}" if state['cost'] >= 0.01 else '') +
        f'. Your result is on branch {out}.')
    say(f"  See what changed:  git diff {state['branch']}...{out}")
    say(f'  Take it:           git merge {out}')
    say(f"(Everything from this build, including the questions and answers, is in {state['home']}.)")
    return 0 if not broken and state['code'] == 0 else 1

def morning(name=None, phone=False):
    """After an overnight build: check its assumptions (here, or on the phone with --phone), fix what the owner
    corrects, and update the branch."""
    homes = sorted((h for h in glob.glob(os.path.join(RUNS, '*')) if os.path.exists(os.path.join(h, 'state.json'))),
                   key=os.path.getmtime)
    if name:
        homes = [h for h in homes if os.path.basename(h) == name]
    homes = [h for h in homes if json.load(open(os.path.join(h, 'state.json'))).get('overnight')]
    if not homes:
        say('No overnight build is waiting for you.'); return 0
    state = json.load(open(os.path.join(homes[-1], 'state.json')))
    run1 = os.path.join(state['home'], 'build')
    todo = [a for a in owner._assumptions(os.path.join(run1, 'owner'), False)
            if not os.path.exists(os.path.join(run1, 'owner', 'reviews', a['id'] + '.json'))]
    from .explain import _goal_summary
    say(f"\nWelcome back. While you were away, the builders worked on: {_goal_summary(state['goal']).splitlines()[0][:120]}")
    if not todo:
        say('There is nothing left for you to check. The result is on branch hive/' + state['name'] + '.'); return 0
    state['started'] = time.time()
    ch = None
    if phone:
        cfg = telegram.load()
        if not cfg:
            say('Telegram is not connected yet: run hive telegram setup first.'); return 1
        ch = telegram.Channel(cfg)
        say("I'm preparing the decisions for your phone (putting them in plain words, most important first)...")
    else:
        say(f"They made {_n(len(todo), 'assumption')} your description didn't cover. Press Enter if one is right, or say "
            "what should happen instead.")
    try:
        fixed = _review_and_fix(state, ch)
    except RuntimeError as e:
        say(str(e)); return 1
    rc = _deliver(state)
    if ch:
        ch.send((f"Done{', ' + ch.name() if ch.name() else ''}. Your changes are in. {state['check']}" if fixed else 'All set.') +
                f" It's ready on branch hive/{state['name']} whenever you are.")
    return rc
