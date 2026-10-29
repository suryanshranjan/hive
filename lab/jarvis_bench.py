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
from hive import assistant, memory, telegram
from test_telegram_fake import FakeTelegram, ME, tap, say
memory.DIR = os.path.join(home, '.hive', 'rules'); assistant.RUNS = os.path.join(home, '.hive', 'runs')
telegram.BUSY = os.path.join(home, '.hive', 'telegram.busy'); telegram.CONVERSATION = os.path.join(home, 'conv.json')
assistant.PIDFILE = os.path.join(home, 'listen.pid')

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
    started = []
    repo = os.path.join(home, 'shop')
    if not os.path.isdir(repo):
        subprocess.run(['git', 'init', '-q', '-b', 'main', repo])
        subprocess.run(['git', '-C', repo, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'i'])
    assistant.BUILD.clear()

    def start_build(rp, goal):   # a stub build: it "runs" until told to fail or is stopped
        started.append(goal)
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
            if k in fails and assistant.BUILD.get('proc'):   # the build stops on "unsaved changes"
                assistant.BUILD['proc'].kill(); assistant.BUILD['proc'].wait()
                open(assistant.BUILD['log'], 'w').write('You have unsaved changes. Commit or stash them first.\n')
                ch.send("⚠️ The build stopped before it finished.\n\nYou have unsaved changes. Commit or stash them first.")
            flush()
            batch = step(f)
            for _, text, data, _ in batch:
                transcript.append(('Owner', text if text else f'[taps {data}]'))
            return batch
        return deliver
    fake.script = [owner(k, step) for k, step in enumerate(fake.script)]
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
    return transcript, started

JUDGE = """You are grading a software assistant, Hive, that a busy founder talks to on his phone. It should behave like
J.A.R.V.I.S. with Tony Stark: understands what he means (typos, Hindi-English, references to earlier messages), takes the
right action, keeps context, is brief (a few sentences), calm and courteous, never robotic, never invents facts, and never
asks needless questions. Its humour is dry and understated: at most a light touch when things are calm, none when
something failed or he is frustrated, never at his expense. It points out a risk once, with a spine, and owns its
mistakes without grovelling.

Scenario: {name}
What a good assistant does here: {expect}
Actions Hive took (builds started, with their goals): {started}

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
