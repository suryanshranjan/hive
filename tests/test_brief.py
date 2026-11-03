"""His numbers, the morning brief, the question about what the product can't show, and going live with one command
(hive/numbers.py, hive/brief.py, assistant.pursue, doctor.go_live). Stand-in model; a fake Telegram.
usage: python3 tests/test_brief.py   (run from the hive repo root)"""
import json, os, subprocess, sys, tempfile, time
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home
from hive import assistant, brief, doctor, explain, memory, numbers, plan, team, telegram
explain.CMD = '"' + sys.executable.replace(chr(92), '/') + '" tests/fake_explain.py'
memory.DIR = os.path.join(home, '.hive', 'rules'); telegram.BUSY = os.path.join(home, '.hive', 'telegram.busy')
telegram.PATH = os.path.join(home, '.hive', 'telegram.json'); numbers.DIR = os.path.join(home, '.hive', 'numbers')
brief.PATH = os.path.join(home, '.hive', 'brief.json'); assistant.PIDFILE = os.path.join(home, '.hive', 'listen.pid')
assistant.RUNS = team.RUNS = os.path.join(home, '.hive', 'runs'); team.TEAM = os.path.join(home, '.hive', 'team.json')
from test_telegram_fake import FakeTelegram, ME, tap, say

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))
ch = lambda fake: telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake)
repo = os.path.join(home, 'shop'); os.makedirs(repo)

# 1. numbers from a source he set up once; what Hive did is kept beside them; a later reading compares with before
open(os.path.join(repo, 'numbers.json'), 'w').write(json.dumps({'sign-ups this week': 120, 'first deals': 30, 'note': 'x'}))
numbers.set_source(repo, file='numbers.json')
check('a reading from his source keeps only numbers', numbers.refresh(repo), {'sign-ups this week': 120.0, 'first deals': 30.0})
time.sleep(0.01); numbers.mark(repo, '"A shorter sign-up form" went to your engineer')
time.sleep(0.01); numbers.mark(repo, 'a creator says the form is long', kind='complaint')
open(os.path.join(repo, 'numbers.json'), 'w').write(json.dumps({'sign-ups this week': 142, 'first deals': 30}))
time.sleep(0.01); numbers.refresh(repo)
today = time.strftime('%b %d').replace(' 0', ' ')
check('how each number moved since what Hive did (a complaint is not a cause)', numbers.changes(repo),
      [f'sign-ups this week: 142 (up 18% from 120 since "A shorter sign-up form" went to your engineer on {today})',
       f'first deals: 30 (no change from 30 since "A shorter sign-up form" went to your engineer on {today})'])
check('a source that fails gives nothing, never an error', (numbers.set_source(repo, cmd='exit 3'), numbers.fetch(repo)),
      ({'cmd': 'exit 3'}, {}))

# 2. the brief: once a day after the hour; it says what landed, what waits on him, what customers hit, the numbers
os.environ['HIVE_BRIEF_HOUR'] = '0'
check('the brief is due once a day', (brief.due(), (brief._sent(), brief.due())[1]), (True, False))
os.remove(brief.PATH)
st = {'repo': repo, 'name': 'signup-1103', 'branch': 'main', 'goal': 'A shorter sign-up form.\n\n# How to work on the look\nx',
      'check': '9 tests, all passing.', 'home': os.path.join(assistant.RUNS, 'signup-1103')}
os.makedirs(st['home']); json.dump(st, open(os.path.join(st['home'], 'state.json'), 'w'))
lines = brief.facts(repo, time.time() - 86400)
check('the brief has what landed, what waits on him, a complaint, the numbers', (
      any(l.startswith('What landed since the last brief: Built: A shorter sign-up form.') for l in lines),
      any('not yet sent to his engineer' in l for l in lines), any(l == 'A customer complained: a creator says the form is long' for l in lines),
      any(l.startswith('His numbers: sign-ups this week: 142 (up 18%') for l in lines)), (True, True, True, True))
fake = FakeTelegram([])
check('"what\'s new?" sends the brief now', (assistant.handle(ch(fake), repo, "what's new?", poll=1), fake.sent[-1]['text'].startswith('🐝')),
      ('brief', True))
check('with nothing to say, a quiet one', brief.compose(os.path.join(home, 'empty')).startswith('🐝 Good'), True)

# 3. the numbers he tells Jarvis are kept
real = explain.ask_json
explain.ask_json = lambda prompt, **k: {'numbers': {'sign-ups this week': 150}} if 'state numbers' in prompt else real(prompt, **k)
check('"we had 150 sign-ups this week" is kept as a reading', numbers.told(repo, 'we had 150 sign-ups this week'), {'sign-ups this week': 150.0})
explain.ask_json = real

# 4. before planning, the one thing the product can't show; his answer is kept and the plan is made again with it
calls = []
def make(repo_, goal, notes=(), rules=(), **k):
    calls.append(list(notes))
    return {'finding': 'f', 'missing': 'Do you already give new creators anything for their first deal?',
            'steps': [{'title': 'Show the first-deal reward', 'why': 'w', 'seen': 's', 'build': 'b', 'look': False, 'decide': '', 'options': []}]}
plan.make = make
fake = FakeTelegram([say('Yes, ₹500 extra on their first deal'), tap('pln|no')])
assistant.handle(ch(fake), repo, 'Creators who join never make their first deal. Help me get more of them to a first deal.', poll=1)
check("what the product can't show is asked first; his answer is kept and planned with",
      (any(m['text'].startswith("❓ Before I plan it, one thing your product can't tell me:") for m in fake.sent), len(calls),
       'Do you already give new creators anything for their first deal? Yes, ₹500 extra on their first deal' in calls[1]),
      (True, 2, True))
calls.clear(); fake = FakeTelegram([tap('pm|none'), tap('pln|no')])
assistant.handle(ch(fake), repo, 'I want more creators to invite their friends.', poll=1)
check('"nothing to add": planned once', len(calls), 1)

# 5. one command: live on his phone, saying hello; never a second listener
json.dump({'chat_id': ME, 'token': 'x', 'address': 'sir'}, open(telegram.PATH, 'w'))
started, said = [], []
real_popen = subprocess.Popen
doctor.subprocess.Popen = lambda *a, **k: started.append(a[0]) or real_popen([sys.executable, '-c', 'import time; time.sleep(5)'])
real_channel = telegram.Channel
telegram.Channel = lambda cfg, **k: real_channel(cfg, api=lambda m, **p: said.append(p.get('text', '')) or ({'first_name': 'Suryansh'} if m == 'getChat' else {'message_id': 1}))
check('hive up: listening in the background, and hello on his phone', (doctor.go_live(repo), started[0][-2:],
      any("At your service" in t and 'ship it' in t for t in said)), (0, ['hive', 'listen'], True))
p = real_popen([sys.executable, '-c', 'import time; time.sleep(5)']); open(assistant.PIDFILE, 'w').write(str(p.pid)); started.clear()
check('already listening: no second one', (doctor.go_live(repo), started), (0, []))
p.kill(); doctor.subprocess.Popen = real_popen; telegram.Channel = real_channel
sys.exit(fail)
