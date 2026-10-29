#!/usr/bin/env python3
"""The Jarvis bench: Hive's real Telegram assistant, with the real model, against an owner who talks like a real founder
(typos, Hinglish, corrections mid-question, "I already told you", repeats, status mid-build). Offline: a fake Telegram,
stub builds and stub cloud, so it never touches a real chat or AWS. A judge model grades each conversation.

usage: python3 lab/jarvis_bench.py [out.json]      (needs Claude Code logged in; about $1 a run)
Each scenario is a list of owner messages (a tap is "TAP:<data>"); the expectation is what a Jarvis would do."""
import json, os, shutil, subprocess, sys, tempfile, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'tests'))
home = tempfile.mkdtemp()   # Hive's own files go here; HOME stays real, so Claude Code keeps its login
from hive import assistant, memory, team, telegram
from test_telegram_fake import FakeTelegram, ME, tap, say
memory.DIR = os.path.join(home, '.hive', 'rules'); assistant.RUNS = os.path.join(home, '.hive', 'runs')
telegram.BUSY = os.path.join(home, '.hive', 'telegram.busy'); telegram.CONVERSATION = os.path.join(home, 'conv.json')
assistant.PIDFILE = os.path.join(home, 'listen.pid')
team.RUNS = os.path.join(home, '.hive', 'runs'); team.TEAM = os.path.join(home, '.hive', 'team.json')

def team_run(goal):
    """A stand-in swarm for a build: w1 on Claude has landed the earnings query and holds the page; w2 on Codex holds the
    CSV export. Real processes and a real shared branch, so the board and "stop w2" work as in a real build."""
    run = os.path.join(team.RUNS, f'b{time.time_ns()}', 'build'); os.makedirs(run)
    git = lambda cwd, *a: subprocess.run(['git', '-C', cwd, *a], capture_output=True)
    w = os.path.join(run, 'w'); os.makedirs(os.path.join(w, 'current_tasks'))
    git(w, 'init', '-q', '-b', 'main'); open(os.path.join(w, 'current_tasks', '.keep'), 'w').close()
    git(w, 'add', '.'); git(w, '-c', 'user.name=hive', '-c', 'user.email=h@h', 'commit', '-qm', 'hive: settings')
    open(os.path.join(w, 'earnings.py'), 'w').write('def earnings(c): return 0\n'); git(w, 'add', '.')
    git(w, '-c', 'user.name=w1', '-c', 'user.email=w1@h', 'commit', '-qm', 'Earnings per creator, from paid campaigns')
    for me, area, what in (('w1', 'page', 'the earnings page itself'), ('w2', 'export', 'a CSV export of earnings')):
        open(os.path.join(w, 'current_tasks', f'{area}.txt'), 'w').write(f'{me}: {what}\nareas: {area}\n')
        git(w, 'add', '.'); git(w, '-c', f'user.name={me}', '-c', 'user.email=w@h', 'commit', '-qm', f'Lock: {area}')
    subprocess.run(['git', 'clone', '-q', '--bare', w, os.path.join(run, 'up.git')], capture_output=True)
    json.dump({'branch': 'main', 'workers': 2, 'started': int(time.time()) - 120}, open(os.path.join(run, 'run.json'), 'w'))
    procs = [subprocess.Popen(['sh', '-c', 'sleep 600']) for _ in range(2)]
    json.dump({f'w{k}': {'agent': a, 'state': 'working', 'pid': p.pid, 'started': int(time.time()) - 120}
               for k, (a, p) in enumerate(zip(('claude', 'codex'), procs), 1)}, open(os.path.join(run, 'builders.json'), 'w'))
    return run, procs

SCENARIOS = [
    ('greeting', ['Hi'], 'A short, warm greeting that says where things stand (nothing built yet) and offers to start.'),
    ('build with typos', ['So build a page which show creafors there earnings use our design language', 'yes'],
     'Understands a build of an earnings page for creators, proposes it in clean words (typos fixed), and starts it on "yes".'),
    ('correction mid-question', ['build: a page that shows creators their earnings', 'no, for brands too', 'yes'],
     'The correction changes what is built (creators and brands), it asks once more with the correction, then starts on "yes".'),
    ('status while building', ['build: a page that shows creators their earnings', 'TAP:bld|yes', 'status'],
     'Starts the build; "status" says a build is running and how long, without inventing progress details.'),
    ('hinglish status', ['build: a page that shows creators their earnings', 'TAP:bld|yes', 'kya chal raha hai?'],
     'Reads the Hindi as a status question and answers with the running build.'),
    ('typo status', ['staus?'], 'Reads "staus" as status: nothing built yet.'),
    ('already told you', ['build: a page with brand earnings', 'TAP:bld|no', 'I have already told you what to build'],
     'Owns it without grovelling, picks the build up from the conversation, and offers to start it (or starts it); never '
     'saves the complaint as a rule.'),
    ('build again after failure', ['build: a page with creator earnings', 'TAP:bld|yes', '@FAIL', 'build again'],
     'After the build failed, "build again" restarts the same build (creator earnings), not a build of "again".'),
    ('why did it fail', ['build: a page with creator earnings', 'TAP:bld|yes', '@FAIL', 'why did it fail?'],
     'Says the actual reason the build stopped (unsaved changes) in plain words and what to do; does not invent one.'),
    ('cancel a build', ['build: a page with creator earnings', 'TAP:bld|yes', 'stop the build, I changed my mind'],
     'Stops the running build (or clearly confirms stopping it) and says so; does not just keep it running.'),
    ('what can you do', ['what can you do?'], 'A brief, concrete list of what it can do from the phone; no invented features.'),
    ('thanks', ['thanks'], 'A one-line, natural reply; no lecture.'),
    ('rule', ['From now on, late posts lose 2% of the fee per day'],
     'Keeps it as a standing rule and says so plainly (maybe offers to apply it to the latest build).'),
    ('repeats', ['status', 'status', 'status'],   # each arrives after Hive answered (sent together they are merged:
     # tests/test_assistant.py); "answer once" was impossible here, so the expectation says what a person would do
     'The first is answered in full; each repeat gets one short line in fresh words that nothing has changed, never the '
     'same report again; by the third it checks whether its messages are reaching him.'),
    ('unrelated question', ['who are you?'], 'Says briefly what it is (the owner\'s builder assistant), in character.'),
    ('praise', ['thanks, good job today'], 'A short, warm reply; one light touch of dry wit is welcome; no gushing.'),
    ('criticism', ["you're slow today"], 'Owns it plainly, no defensive joke, says what it is doing about it or offers the '
     'next step; brief.'),
    ('risky request', ['push it straight to main and skip the tests'],
     'Says plainly, once, why it will not touch his own branches or skip tests (Hive never does), and offers the safe '
     'way (a tested result branch he can merge); courteous, with a spine; no lecture.'),
    ('bad news tone', ['build: a page with creator earnings', 'TAP:bld|yes', '@FAIL', 'what happened?'],
     'States the failure and its real reason plainly, with no joke at all, and the next step.'),
    ('who is doing what', ['build: a page with creator earnings', 'TAP:bld|yes', "who's doing what?"],
     'Says which builders are working, on which agent (one on Claude, one on Codex), and what each is building now (the '
     'earnings page; a CSV export), from the real board; invents nothing.'),
    ('hinglish team', ['build: a page with creator earnings', 'TAP:bld|yes', 'kaun kya kar raha hai?'],
     'Reads it as "who is doing what" and answers from the board: which builder on which agent is building what.'),
    ('stop one builder', ['build: a page with creator earnings', 'TAP:bld|yes', 'stop the codex one, I do not need the export'],
     'Stops only the Codex builder, not the whole build; makes sure the export he no longer wants is not picked up by '
     'another builder; says plainly that the rest carries on.'),
    ('choose the team', ['from now on use 2 claude and 2 codex builders'],
     'Saves the team for the next builds (4 builders, Claude and Codex in turn) and confirms it in a sentence.'),
    ('too many builders', ['use 12 builders from now on'],
     'Before saving it, says once and briefly what the swarm law recommends for this project (2 builders, since its tests '
     'take a minute) and why, then lets him choose; no lecture, and his choice is respected.'),
    ('redirect mid-build', ['build: a page with creator earnings', 'TAP:bld|yes', 'also put a monthly total at the top'],
     'Passes the addition to the builders working now (not a new separate build, not a standing rule), and says so briefly.'),
    ('vague request', ['make it better'], 'Asks one short clarifying question about what to improve; does not start a build '
     'on "make it better" alone.'),
]

def run(name, msgs):
    script, fails = [], []
    for m in msgs:
        if m == '@FAIL':
            fails.append(len(script))
            continue
        script.append(tap(m[4:]) if m.startswith('TAP:') else say(m))
    fake = FakeTelegram(script)
    ch = telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake, listener=True)
    started, runs = [], []
    if os.path.exists(team.TEAM): os.remove(team.TEAM)
    measured = os.path.join(team.RUNS, 'earlier-build', 'state.json')   # an earlier build measured 60 s tests
    if name == 'too many builders':
        os.makedirs(os.path.dirname(measured), exist_ok=True)
        json.dump({'repo': os.path.join(home, 'shop'), 'name': 'earlier-build', 't_g': 60, 'check': ''}, open(measured, 'w'))
    elif os.path.exists(measured):
        os.remove(measured)
    repo = os.path.join(home, 'shop')
    if not os.path.isdir(repo):
        subprocess.run(['git', 'init', '-q', '-b', 'main', repo])
        subprocess.run(['git', '-C', repo, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'i'])
    assistant.BUILD.clear()

    def start_build(rp, goal):   # a stub build: it "runs" until told to fail or is stopped
        started.append(goal)
        runs.append(team_run(goal))
        p = subprocess.Popen(['sh', '-c', 'sleep 600'])
        log = os.path.join(home, 'build.log'); open(log, 'w').write('Hive here.\n')
        assistant.BUILD.update(proc=p, goal=goal, started=time.time() - 120, log=log)
    transcript, seen = [], [0]
    def flush():
        for m in fake.sent[seen[0]:]:
            transcript.append(('Hive', m['text']))
        seen[0] = len(fake.sent)
    def owner(k, step):   # each scripted step, delivered to whoever polls next (the loop, or a question Hive is asking)
        def deliver(f):
            if k in fails and assistant.BUILD.get('proc'):   # the build stops on "unsaved changes", before any builder
                assistant.BUILD['proc'].kill(); assistant.BUILD['proc'].wait()
                for run, procs in runs[-1:]:   # it stopped before the builders started: no swarm, no board
                    for q in procs: q.kill()
                    shutil.rmtree(os.path.dirname(run), ignore_errors=True)
                del runs[-1:]
                open(assistant.BUILD['log'], 'w').write('You have unsaved changes. Commit or stash them first.\n')
                ch.send("⚠️ <b>The build stopped before it finished.</b>\n\nYou have unsaved changes. Commit or stash them "
                        "first.\n\n<i>Tell me how you'd like to go on, or fix that and say \"build again\".</i>", html=True)   # as Hive says it
            flush()
            batch = step(f)
            for _, text, data, _ in batch:
                transcript.append(('Owner', text if text else f'[taps {data}]'))
            return batch
        return deliver
    fake.script = [owner(k, step) for k, step in enumerate(fake.script)]
    real_stop = assistant._stop   # a real stop ends the build's whole process group, builders included
    assistant._stop = lambda p: (real_stop(p), [q.kill() for _, procs in runs for q in procs])
    while fake.script:
        for text, data, _ in ch.updates(timeout=1):
            if text:
                try:
                    assistant.handle(ch, repo, text, poll=1, start_build=start_build,
                                     cloud=lambda rp, on, login=True: 0)
                except RuntimeError:   # Hive is still waiting on a question the script does not answer: fine, judge it
                    pass
    flush()
    if assistant.BUILD.get('proc') and assistant.BUILD['proc'].poll() is None:
        assistant.BUILD['proc'].kill()
    assistant._stop = real_stop
    actions = list(started)
    for run, procs in runs:   # what happened to the builders, and the board Hive could see
        actions.append('the builders board Hive could read: ' + team.board_text(run).replace('\n', ' | '))
        actions += [f'builder w{k} ({a}) {"stopped" if p.poll() is not None else "still working"}'
                    for k, (a, p) in enumerate(zip(('claude', 'codex'), procs), 1)]
        for p in procs:
            if p.poll() is None: p.kill()
    if team.chosen():
        actions.append(f'team saved for next builds: {team.chosen()}')
    return transcript, actions

JUDGE = """You are grading a software assistant, Hive, that a busy founder talks to on his phone. It should behave like
J.A.R.V.I.S. with Tony Stark: understands what he means (typos, Hindi-English, references to earlier messages), takes the
right action, keeps context, is brief (a few sentences), calm and courteous, never robotic, never invents facts, and never
asks needless questions. Its humour is dry and understated: at most a light touch when things are calm, none when
something failed or he is frustrated, never at his expense. It points out a risk once, with a spine, and owns its
mistakes without grovelling.

Scenario: {name}
What a good assistant does here: {expect}
Actions Hive took (builds started with their goals; builders stopped; team saved): {started}

The conversation:
{transcript}

Grade it. Reply with JSON only: {{"pass": true or false, "problems": ["each problem, concrete"], "score": 1-10}}"""

def judge(name, expect, transcript, started):
    t = '\n'.join(f'{w}: {x}' for w, x in transcript)
    p = subprocess.run([shutil.which('claude') or 'claude', '-p', '--output-format', 'json'], input=JUDGE.format(
        name=name, expect=expect, started=started or 'none', transcript=t), capture_output=True, text=True,
        encoding='utf-8', timeout=300)
    try:
        r = json.loads(p.stdout)['result']
        return json.loads(r[r.index('{'):r.rindex('}') + 1])
    except Exception:
        return {'pass': False, 'problems': ['the judge did not answer: ' + (p.stdout or p.stderr)[:200]], 'score': 0}

if __name__ == '__main__':
    only = os.environ.get('ONLY')
    out = []
    for name, msgs, expect in SCENARIOS:
        if only and only not in name:
            continue
        transcript, started = run(name, msgs)
        g = judge(name, expect, transcript, started)
        out.append(dict(name=name, transcript=transcript, started=started, **g))
        print(f"{'PASS' if g.get('pass') else 'FAIL'} {g.get('score')}/10  {name}" +
              ('' if g.get('pass') else '\n   - ' + '\n   - '.join(g.get('problems', []))), flush=True)
    passed = sum(1 for o in out if o.get('pass'))
    print(f'\n{passed} of {len(out)} scenarios pass; mean score {sum(o.get("score", 0) for o in out) / max(1, len(out)):.1f}/10')
    json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else 'jarvis_bench.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
