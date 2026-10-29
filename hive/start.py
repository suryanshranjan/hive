"""hive start (or just `hive`): one conversation from an idea to a tested branch.

Hive asks what to build, finds the project's tests on its own, puts builders to work on copies, brings their questions
and their assumptions to the owner in plain words, sends back what the owner corrects, checks the result, and hands
over a branch. The owner's own branches are never changed: the result arrives as a new branch, hive/<name>."""
import csv, glob, json, os, re, shlex, shutil, subprocess, threading, time

from . import PY, codesheet, docs as docs_mod, interview, junit, law, memory, owner, swarm, telegram
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
        found.append((py, f'{PY} -m pytest -q -p no:cacheprovider --junitxml=.hive/junit.xml', 'pytest'))
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

def _rmtree(path):
    """Delete a folder, including git's read-only files (Windows refuses those: found running Hive natively there)."""
    import stat
    def writable(func, p, *_):
        os.chmod(p, stat.S_IWRITE); func(p)
    shutil.rmtree(path, onerror=writable)

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

    def heard(m):   # the launcher's log; a stop the owner must know about (a usage limit, an expired login) reaches him
        log.write(m + '\n'); log.flush()
        if ' stopped: ' in m:
            say(f'\n[{_now()}] {m.split(" stopped: ", 1)[1]}')
            if phone:
                try:
                    phone.send(('🔑 ' if 'login' in m else '⏳ ') + m.split(' stopped: ', 1)[1].replace('Run claude',
                               'On the computer running Hive, run claude'))
                except Exception:
                    pass
    t = threading.Thread(target=lambda: result.update(code=swarm.launch(run, 0, say=heard)), daemon=True)
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

def start(repo='.', workers=None, goal=None, minutes=40, overnight=False, interview_first=True, docs=None):
    repo = os.path.abspath(repo)
    say("\nHive here. What are we building today?")
    goal = goal or _ask("(Describe it in a sentence or two, or give the path of a file that describes it.)")
    if not goal:
        say('Nothing to build; come back any time.'); return 0
    goal_text = open(goal, encoding='utf-8').read().strip() if os.path.exists(goal) else goal
    papers = docs_mod.read(docs)
    if papers:   # the company's own documents: the interview skips what they settle; builders follow them
        say(f"  I'll read your documents ({len(papers) // 1000 or 1}k characters) and only ask about what they don't settle.")
        goal_text += docs_mod.instructions(papers)
    elif docs:
        say(f'  I found no text documents at {docs} (I read .md, .txt and .csv files); carrying on without them.')

    say('\nGot it. Let me look at your project.')
    if sh('git', '-C', repo, 'rev-parse', '--is-inside-work-tree').returncode != 0:
        say('  This folder is not a git repository. Run me inside your project folder.'); return 2
    branch = sh('git', '-C', repo, 'rev-parse', '--abbrev-ref', 'HEAD').stdout.strip()
    if sh('git', '-C', repo, 'status', '--porcelain', '--untracked-files=no').stdout.strip():
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
    sh('git', 'clone', '-q', '-c', 'core.autocrlf=false', '--branch', branch, repo, source)
    sh('git', '-C', source, 'config', 'user.name', 'hive'); sh('git', '-C', source, 'config', 'user.email', 'hive@local')
    _link(repo, source, links)
    t0 = time.time(); before = run_tests(source, test_cmd); t_g = time.time() - t0   # the gate term of the law
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

    auto = workers is None   # the swarm law picks the number from this project's measurements (hive/law.py)
    if auto:
        workers, why = law.builders(t_g)
        say(f"\nI'll put {_n(workers, 'builder')} on it ({why}). They work on copies, so your branches stay exactly "
            "as they are.")
    else:
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
    rules = memory.instructions(repo)
    if rules:
        k = len(memory.load(repo))
        say(f"I'll remind them of your {_n(k, 'earlier ruling')} on this project, so you won't be asked those again.")
    asked = []
    if interview_first and (phone or not overnight):   # the owner is here: ask him first (Gates 30-35)
        say("\nFirst, a few quick situations where your own rules matter" + (", on your phone." if phone else ":"))
        asked = interview.interview(goal_text, phone, [r['text'] for r in memory.load(repo)], ask=lambda p: _ask(p, ''),
                                    save=os.path.join(home, 'interview'))   # a stop never costs him his answers
        if asked:
            for r in asked:
                memory.add(repo, r, 'interview')
            rules += interview.instructions(asked)
            say(f"  Thank you. The builders will encode your {_n(len(asked), 'rule')} as tests before anything lands.")
            if auto:
                n, why = law.builders(t_g, decisions=len(asked))
                if n < workers:
                    workers = n
                    say(f"  For a job this size I'll use {_n(n, 'builder')} ({why}).")
    say(f'\n[{_now()}] Starting.')
    state = dict(repo=repo, branch=branch, name=name, home=home, test_cmd=test_cmd, links=links, goal=goal_text,
                 rules=rules, workers=workers, minutes=minutes, before=before, started=time.time(), overnight=overnight,
                 asked=asked)
    run1 = os.path.join(home, 'build')
    b, code = _phase(source, run1, workers, goal_text + rules, minutes, 0 if overnight else 4 * workers, True,
                     not overnight, phone)
    state.update(b=b, code=code, final=run1, cost=_cost(run1))
    json.dump(state, open(os.path.join(home, 'state.json'), 'w'), indent=1)
    say(f'\n[{_now()}] ' + (f'All {workers} builders are done.' if workers > 1 else 'The builder is done.'))
    found = owner._assumptions(os.path.join(run1, 'owner'), False)   # business defaults only; technical ones go to engineers
    if overnight and phone:
        rc = _deliver(state)
        if not found:
            phone.send(f"🐝 Welcome back{', ' + phone.name() if phone.name() else ''}. The build is finished. "
                       f"{state['check']} Nothing needs your attention. It's ready on branch hive/{name}.")
            handover(state, phone)
            return rc
        say(f'\n[{_now()}] Sent {_n(len(found), "assumption")} to your phone; waiting for your replies.')
        if _review_and_fix(state, phone):
            rc = _deliver(state)
            phone.send(f"🎉 Done{', ' + phone.name() if phone.name() else ''}. Your changes are in. {state['check']} It's ready on branch hive/{name} whenever you are.")
        else:
            phone.send(f"✅ All set. It's ready on branch hive/{name} whenever you are.")
        handover(state, phone)
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
    rc = _deliver(state)
    handover(state, phone)
    return rc

def _review_and_fix(state, phone=None):
    """The owner checks the business assumptions (here, or on the phone); anything corrected goes back to the builders
    for one fix round. Returns True when a fix round ran."""
    run1 = os.path.join(state['home'], 'build')
    if phone:
        hour = time.localtime().tm_hour
        telegram.review(run1, phone, goal=state['goal'], check=state.get('check', ''),
                        rulings=[r['text'] for r in memory.load(state['repo'])],
                        greeting='Good morning' if 4 <= hour < 12 else 'Good afternoon' if hour < 17 else 'Good evening')
    else:
        owner.review(run1, intro=False, goal=state['goal'], rulings=[r['text'] for r in memory.load(state['repo'])])
    fixes = [r for r in (json.load(open(p)) for p in glob.glob(os.path.join(run1, 'owner', 'reviews', '*.json'))) if not r['ok']]
    if not fixes:
        return False
    say(f'\n[{_now()}] Sending the builders back to fix {_n(len(fixes), "thing")}.')
    fsrc = os.path.join(state['home'], 'fix_source')
    sh('git', 'clone', '-q', '-c', 'core.autocrlf=false', '--branch', state['b'], os.path.join(run1, 'up.git'), fsrc)
    _link(state['repo'], fsrc, state['links'])
    corrections = open(os.path.join(run1, 'owner', 'corrections.md')).read()
    run2 = os.path.join(state['home'], 'fix')
    _phase(fsrc, run2, min(state['workers'], max(1, (len(fixes) + 1) // 2)), state['goal'] + state.get('rules', '') + '\n\n' + corrections,
           state['minutes'], 0, False, False, phone)
    state.update(final=run2, cost=state['cost'] + _cost(run2))
    json.dump(state, open(os.path.join(state['home'], 'state.json'), 'w'), indent=1)
    say(f'[{_now()}] Fixed.')
    _confirm_as_built(state, run2, phone)
    return True

def _confirm_as_built(state, run2, phone=None):
    """Gate 34b: the fix round can read an owner's sentence two ways. Each change comes back as one line of what the
    product now does; anything the owner says isn't quite right goes to one more short round."""
    built = owner._assumptions(os.path.join(run2, 'owner'), False)
    if not built:
        return
    lines = [a['text'] for a in built]
    if phone:
        cases = [{'id': a['id'], 'situation': f"As built: {a['text']}", 'options': ["Yes, that's it", 'Not quite']}
                 for a in built]
        got = telegram.verdicts(phone, cases, intro="One last look: here is what the product now does for each change "
                                                    "you asked for. Tap Yes, or tell me what isn't quite right.")
        wrong = [(a['text'], got[a['id']]) for a in built if got.get(a['id']) not in ("Yes, that's it", None)]
        wrong = [(t, '' if w == 'Not quite' else w) for t, w in wrong]
    else:
        say('\nOne last look: here is what the product now does for each change you asked for.')
        wrong = []
        for t in lines:
            say(f'  {t}')
            ans = _ask('  Right? Press Enter if yes, or say what is not quite right.', '')
            if ans and ans.lower().strip('. !') not in ('y', 'yes', 'ok', 'right'):
                wrong.append((t, ans))
    if not wrong:
        say('  All confirmed.'); return
    say(f'\n[{_now()}] One more short round for {_n(len(wrong), "change")}.')
    note = ("\n\n# The owner checked the changes as built\n\nThese are not quite right yet. Make the product do what the "
            "owner says, update the tests, leave everything else alone:\n\n" +
            '\n'.join(f'- Built: {t}\n  **The owner says:** {w or "Not quite right; follow the earlier correction exactly."}'
                      for t, w in wrong) + '\n')
    src = os.path.join(state['home'], 'fix2_source'); run3 = os.path.join(state['home'], 'fix2')
    sh('git', 'clone', '-q', '-c', 'core.autocrlf=false', '--branch', state['b'], os.path.join(run2, 'up.git'), src)
    _link(state['repo'], src, state['links'])
    corrections = open(os.path.join(state['home'], 'build', 'owner', 'corrections.md')).read()
    _phase(src, run3, 1, state['goal'] + state.get('rules', '') + '\n\n' + corrections + note, state['minutes'], 0,
           False, False, phone)
    state.update(final=run3, cost=state['cost'] + _cost(run3))
    json.dump(state, open(os.path.join(state['home'], 'state.json'), 'w'), indent=1)
    say(f'[{_now()}] Done.')

def _deliver(state):
    """Check every test on the result and hand it over as the branch hive/<name> (updated in place after a fix round)."""
    say('\nLet me check the result.')
    result = os.path.join(state['home'], 'result')
    if os.path.exists(result):
        _rmtree(result)
    sh('git', 'clone', '-q', '-c', 'core.autocrlf=false', '--branch', state['b'], os.path.join(state['final'], 'up.git'), result)
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
    kept = memory.record(state['repo'], os.path.join(state['home'], 'build'), state['goal'])
    if kept:
        say(f"  I've noted {_n(kept, 'new ruling')} of yours for the next build on this project.")
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
        ch.send((f"🎉 Done{', ' + ch.name() if ch.name() else ''}. Your changes are in. {state['check']}" if fixed else '✅ All set.') +
                f" It's ready on branch hive/{state['name']} whenever you are.")
    handover(state, ch)
    return rc

def handover(state, ch=None, poll=20, rounds=3):
    """The last step: show the owner what the product now does by his rules, and get a yes. Anything he says is
    different goes straight to a fix round on the same branch (Gate 37: his answer to one framing of a decision is not
    a settled rule, so he sees the whole result as rules and confirms it)."""
    sheet = _code_sheet(state)
    if sheet:   # Gate 42: the sheet from the built code is complete by construction; he marks only what is wrong
        known = (state.get('asked') or []) + [r['text'] for r in memory.load(state['repo'])]
        show, his = codesheet.split_known(sheet, known)   # what only repeats his own rules is not read again
        if not ch:
            say('\nHere is everything the build does now, written from its code' +
                (f" ({len(his)} more only repeat your own rules, so I left them out)." if his else '.'))
        elif his:
            ch.send(f"🐝 The build follows your {len(his)} rule{'s' if len(his) != 1 else ''} as you gave them, so I've "
                    "left those out. Here is the rest of what it does.")
        done = interview.confirm_sheet(show, ch, None if ch else (lambda p: _ask(p, '')), poll,
                                       title='What the build does now, as rules',
                                       note='Each one is what the product will do. Mark any that is not your policy.',
                                       missing=True)
        changed = [r for r in done if r not in sheet]
        if not changed:
            if ch:
                ch.send('🎉 Very good. It is yours.')
            return 0
        for r in changed:
            memory.add(state['repo'], r, 'handover')
        state.setdefault('asked', []).extend(changed)
        apply_ruling(state, '\n- '.join(changed), ch)
    rules = state.get('asked') or [r['text'] for r in memory.load(state['repo'])][-12:]
    listing = '\n'.join(f'{n}. {r}' for n, r in enumerate(rules[:12], 1))
    for _ in range(rounds):
        if ch:
            ch.send("📜 <b>What it does now, by your rules:</b>\n\n" + telegram.esc(listing or '(no rules of yours yet)') +
                    "\n\n<i>Looks right? If anything should be different, tell me and I'll have it changed.</i>",
                    html=True, buttons=[[('👍 Looks right', 'hand|ok')], [('✏️ Change something', 'hand|change')]])
            kind, got = telegram._wait(ch, poll, {'hand|ok', 'hand|change'})
            if got == 'hand|ok' or (kind == 'text' and interview.is_yes(got)):
                ch.send('🎉 Very good. It is yours.'); return 0
            if kind == 'tap':
                ch.send("✍️ What should be different? Your own words, or a 🎙 voice note.")
                got = telegram._wait(ch, poll, set())[1]
        else:
            if listing:
                say('\nWhat it does now, by your rules:\n' + '\n'.join('  ' + l for l in listing.splitlines()))
            got = _ask("Looks right? Press Enter, or say what should be different.")
            if not got or interview.is_yes(got):
                return 0
        memory.add(state['repo'], got, 'handover')
        state.setdefault('asked', rules).append(got); rules = state['asked']
        listing = '\n'.join(f'{n}. {r}' for n, r in enumerate(rules[-12:], 1))
        apply_ruling(state, got, ch)
    return 0

def _code_sheet(state):
    """Every business behaviour of the delivered build, as plain rules, written from its code ([] if unavailable)."""
    if not (state.get('final') and state.get('b')) or os.environ.get('HIVE_CODE_SHEET') == '0':
        return []
    src = os.path.join(state['home'], 'sheet_source'); shutil.rmtree(src, ignore_errors=True)
    try:
        sh('git', 'clone', '-q', '-c', 'core.autocrlf=false', '--branch', state['b'], os.path.join(state['final'], 'up.git'), src)
    except Exception:
        return []
    try:
        return codesheet.describe(src, state.get('goal', ''))
    finally:
        shutil.rmtree(src, ignore_errors=True)

def apply_ruling(state, rule, ch=None):
    """The owner changed his mind after a build: one fix round on the latest build so it follows the new ruling, then
    re-check every test and update the same branch (used by `hive listen`)."""
    home = state['home']; n = len(glob.glob(os.path.join(home, 'change*'))) + 1
    src = os.path.join(home, f'change{n}_source'); run = os.path.join(home, f'change{n}')
    sh('git', 'clone', '-q', '-c', 'core.autocrlf=false', '--branch', state['b'], os.path.join(state['final'], 'up.git'), src)
    _link(state['repo'], src, state['links'])
    note = ("\n\n# The owner changed his mind\n\nAfter this was built, the owner gave this ruling. Change the code to "
            "follow it, encode it as a test, change any existing test that asserts the old behaviour, and leave "
            f"everything else alone:\n\n- {rule}\n")
    _phase(src, run, 1, state['goal'] + memory.instructions(state['repo']) + note, state['minutes'], 0, False, False, ch)
    state.update(final=run, cost=state.get('cost', 0) + _cost(run), started=time.time())
    rc = _deliver(state)
    if ch:
        ch.send(f"🎉 Done. The build now follows your new ruling. {state['check']} It's on branch hive/{state['name']}.")
    return rc
