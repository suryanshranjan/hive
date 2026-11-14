"""Onboarding on the phone (hive/onboard.py), with a fake Telegram and a stand-in model (no network, no tokens): the
first question is who he is (a business, a developer with a product, someone starting something new), each path asks
its own steps, every step can be skipped, a stop keeps what he gave and "set me up" picks up where he left off, and a
new idea goes to the usual build proposal. Also: the greeting offers it only to someone Hive has not met, and the
interview is told what he has already said.
usage: python3 tests/test_onboard.py   (run from the hive repo root)"""
import json, os, sqlite3, subprocess, sys, tempfile
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home
from hive import access, assistant, explain, interview, memory, onboard, telegram
from hive import logins as _logins; _logins.ensure = lambda ch, service, poll=20: True   # signed in (renewal: tests/test_logins.py)
explain.CMD = '"' + sys.executable.replace(chr(92), '/') + '" tests/fake_explain.py'
memory.DIR = os.path.join(home, '.hive', 'rules'); telegram.BUSY = os.path.join(home, '.hive', 'telegram.busy')
access.DIR = os.path.join(home, '.hive', 'access'); onboard.DIR = os.path.join(home, '.hive', 'onboarding')
assistant.RUNS = os.path.join(home, '.hive', 'runs')
from test_telegram_fake import FakeTelegram, ME, tap, say

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))
ch = lambda fake: telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake)
def project(name):
    r = os.path.join(home, name); subprocess.run(['git', 'init', '-q', '-b', 'main', r])
    subprocess.run(['git', '-C', r, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', f'init {name}'])   # its own first commit: Hive keys a project by it
    return r

# 1. someone new is offered setup when he says hello; someone known is not
shop = project('shop')
fake = FakeTelegram([])
assistant.handle(ch(fake), shop, 'hi', poll=1)
check('a hello from someone Hive has not met offers setup', 'set me up' in fake.sent[-1]['text'], True)

# 2. a business: who he is, then five steps; a database he gives is tried at once; skips work
db = os.path.join(home, 'shop.db'); c = sqlite3.connect(db)
c.execute('CREATE TABLE orders (id INTEGER)'); c.execute('CREATE TABLE payouts (id INTEGER)'); c.commit(); c.close()
fake = FakeTelegram([tap('onb|who|business'),
                     say('Sunny Shop. We sell handmade candles; our customers are gift buyers in Pune.'),
                     tap('onb|skip|2'),
                     say(f'our orders database {db}'), say('done'),
                     say('Refunds within 7 days, never on sale items.'), tap('onb|done|4'),
                     say("we're on vercel")])
r = assistant.handle(ch(fake), shop, 'set me up', poll=1)
texts = [m['text'] for m in fake.sent]
check('setup finishes', r, 'onboard_done')
check('the first question is who he is', 'which of these is you?' in texts[0], True)
check('his business is named from his words', memory.project_name(shop), 'Sunny Shop')
check('what he said about his business is kept', 'We sell handmade candles' in ' '.join(memory.notes(shop)), True)
check('his database is connected and tried at once', any('I can see 2 tables: orders, payouts.' in t for t in texts), True)
check('a few lines about how he runs things are kept', 'Refunds within 7 days, never on sale items.' in memory.notes(shop), True)
check('the steps are numbered for a business (5)', any(t.startswith('5 of 5. Hosting.') for t in texts), True)
check('the wrap-up tells him what he can ask now', ('All set, Sunny Shop.' in texts[-1], 'how many orders this week?' in texts[-1]),
      (True, True))
fake = FakeTelegram([])
assistant.handle(ch(fake), shop, 'hello', poll=1)
check('once set up, a hello no longer offers setup', 'set me up' in fake.sent[-1]['text'], False)

# 3. a developer with a product: his own path (how it is built, not policies); stop keeps what he gave
app = project('app')
fake = FakeTelegram([say("I'm a developer"), say('Tiny Notes, a notes app for students.'), say('stop')])
r = assistant.handle(ch(fake), app, 'onboard me', poll=1)
check("a developer's words choose his path, and stop pauses", r, 'onboard_paused')
check('...keeping what he gave', (memory.project_name(app), onboard.progress(app).get('who'), onboard.progress(app).get('step')),
      ('Tiny Notes', 'developer', 1))
fake = FakeTelegram([tap('onb|skip|2'), tap('onb|skip|3'),
                     say('Next.js and Postgres. Never touch the billing folder. Tests: npm test'), tap('onb|done|4'),
                     tap('onb|skip|5')])
r = assistant.handle(ch(fake), app, 'set me up', poll=1)
texts = [m['text'] for m in fake.sent]
check('"set me up" again picks up at the step he stopped at', (r, texts[0]), ('onboard_done', '🐝 Picking up where we left off: step 2 of 5.'))
check("a developer is asked how it is built, not for policies", (any('How it is built.' in t for t in texts),
      any('How you run things.' in t for t in texts)), (True, False))
check('his conventions are kept for the builders', any('Never touch the billing folder' in n for n in memory.notes(app)), True)
check("a developer's wrap-up suggests technical asks", 'add an index on users.email' in texts[-1], True)

# 4. something new: the idea and day one, then the usual build proposal (one "shall I?", with its price)
fresh = project('fresh')
started = []
fake = FakeTelegram([tap('onb|who|new'), say('A booking app for yoga teachers.'),
                     say('Teachers list classes\nStudents book and pay'), say('done'), tap('bld|no')])
r = assistant.handle(ch(fake), fresh, "let's get started", poll=1, start_build=lambda repo, goal: started.append(goal))
texts = [m['text'] for m in fake.sent]
check('the new path asks for the idea and day one only (2 steps)', any(t.startswith('2 of 2. Day one.') for t in texts), True)
check('then it proposes the build once, with what he said', (sum('Shall I build this?' in t for t in texts),
      any('Students book and pay' in t for t in texts if 'Shall I build this?' in t)), (1, True))
check('"not now" builds nothing', (r, started), ('not_built', []))
check('the goal carries his idea and his day-one list', onboard.goal_of(fresh),
      'A booking app for yoga teachers.\n\nOn day one it must:\n- Teachers list classes\n- Students book and pay')

# 5. who he is, from his own words
check('who: a shop owner', onboard.who_from('I have a small shop'), 'business')
check('who: a developer', onboard.who_from('I am a freelance developer'), 'developer')
check('who: something new', onboard.who_from('I want to build something from scratch'), 'new')
check('"let\'s start building the invite page" is a build, not setup', bool(onboard.START_WORDS.search("let's start building the invite page")), False)

# 6. the interview is told what he has already said, so it never asks it again
seen = {}
real = explain.ask_json
def spy(prompt):
    if 'short interview with a busy' in prompt:
        seen['prompt'] = prompt
    return real(prompt)
explain.ask_json = spy
interview.write_situations('Add refunds to Sunny Shop', ['A late post is paid in full.'], known=memory.notes(shop))
explain.ask_json = real
check("the interview knows what he told Hive and won't ask it", "don't ask what these settle" in seen.get('prompt', '') and
      'Refunds within 7 days, never on sale items.' in seen.get('prompt', ''), True)

# 7. a Hive process started from his project's folder can import Hive, installed or not (Gate 108: a plan's build died
# with "No module named hive", and he heard only "it stopped partway")
r = subprocess.run([sys.executable, '-c', 'import hive.start; print("ok")'], cwd=fresh, env=assistant.hive_env(),
                   capture_output=True, text=True)
check('a build started in his folder finds Hive', r.stdout.strip(), 'ok')

sys.exit(fail)
