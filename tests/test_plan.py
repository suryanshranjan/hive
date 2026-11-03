"""A business goal in, a plan out, then built step by step (hive/plan.py, assistant.pursue and run_plan). A stand-in
planner and stand-in builds; a fake Telegram.
usage: python3 tests/test_plan.py   (run from the hive repo root)"""
import json, os, sys, tempfile
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home
from hive import assistant, explain, memory, plan, screens, team, telegram
explain.CMD = '"' + sys.executable.replace(chr(92), '/') + '" tests/fake_explain.py'
memory.DIR = os.path.join(home, '.hive', 'rules'); telegram.BUSY = os.path.join(home, '.hive', 'telegram.busy')
telegram.PATH = os.path.join(home, '.hive', 'telegram.json')
assistant.RUNS = team.RUNS = os.path.join(home, '.hive', 'runs'); team.TEAM = os.path.join(home, '.hive', 'team.json')
from test_telegram_fake import FakeTelegram, ME, tap, say

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))
ch = lambda fake: telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake)
repo = os.path.join(home, 'shop'); os.makedirs(repo)

# 1. a business outcome is read as one; a particular thing to build is not
check('business goals are read without a model; particular builds are not',
      [bool(assistant.GOAL_WORDS.search(t.lower())) for t in ('I want more creators signing up this month', 'sign-ups are low',
       'help me get more repeat buyers', 'creators badhana hai', 'add an invite page', 'make the button bigger')],
      [True, True, True, True, False, False])

# 2. a plan Hive can run: grounded steps only, at most 4, at most 2 questions for him
raw = {'finding': 'Sign-up asks for 9 things.', 'steps': [
    {'title': 'A shorter sign-up form', 'why': 'w', 'seen': 'signup.html: 9 fields', 'build': 'b1', 'decide': 'Can bank details wait until the first payout?', 'options': ['Yes, at first payout', 'No, keep at sign-up']},
    {'title': 'Show what creators earn', 'why': 'w', 'seen': 'index.html: no amounts', 'build': 'b2', 'look': True},
    {'title': 'An idea from nowhere', 'why': 'w', 'build': 'b3'},
    {'title': 'Reward the first deal', 'why': 'w', 'seen': 'deals.py', 'build': 'b4', 'decide': 'How much?', 'options': ['₹200', '₹500']},
    {'title': 'A third question', 'why': 'w', 'seen': 'x', 'build': 'b5', 'decide': 'Really?', 'options': ['a']},
    {'title': 'A fifth step', 'why': 'w', 'seen': 'y', 'build': 'b6'}]}
c = plan.clean(raw)
check('ungrounded steps dropped, at most 4 steps and 2 questions',
      ([s['title'] for s in c['steps']], sum(1 for s in c['steps'] if s['decide'])),
      (['A shorter sign-up form', 'Show what creators earn', 'Reward the first deal', 'A third question'], 2))
check("the builder is told the step, why, what to do, and his decision",
      plan.instruction(c['steps'][0], 'Yes, at first payout').endswith('Can bank details wait until the first payout? -> Yes, at first payout'), True)

# 3. he states the goal: the plan in his words, one yes, the one question asked now; his decision kept
three = dict(c, steps=c['steps'][:3])
plan.make = lambda *a, **k: three
real_run_plan = assistant.run_plan; assistant.run_plan = lambda *a, **k: None   # no real build thread in a test (Linux CI raced it)
fake = FakeTelegram([tap('pln|all'), tap('pq|0'), tap('pq|1')])
r = assistant.handle(ch(fake), repo, 'I want more creators signing up this month', poll=1)
check('the plan is shown in plain words, then he decides only what only he can', (r if r != 'planned' else 'planned',
      'Here\'s what I see, sir.' in fake.sent[1]['text'], '1. A shorter sign-up form: w' in fake.sent[1]['text'],
      [m['text'].split('\n')[0] for m in fake.sent if m['text'].startswith('❓')]),
      ('planned', True, True, ['❓ One thing only you can decide (A shorter sign-up form):', '❓ One thing only you can decide (Reward the first deal):']))
check('his decisions are kept for every later build', [r['text'] for r in memory.load(repo)],
      ['Can bank details wait until the first payout? Yes, at first payout', 'How much? ₹500'])
assistant.PLAN['running'] = False   # (the thread from handle: stopped below by stand-ins before it builds)

# 4. the plan is built: step 1 as a build, then fix rounds on the same branch; each shown; the end offers ship it
built, applied = [], []
class Done:
    def wait(self): return 0
assistant.background_build = lambda repo, goal, ch=None, interview=True, report=True, workers=None: built.append((goal, interview, report)) or Done()
st = {'repo': repo, 'name': 'signups-1103', 'branch': 'main', 'b': 'main', 'check': '12 tests, all passing.'}
assistant.latest_build = lambda r: st
screens.available = lambda: False
def apply_build(state, rule, ch):
    applied.append(rule); return 0
assistant.what_changed = lambda repo, ch=None: 'It now shows what creators earn.'
assistant.run_plan = real_run_plan
assistant.PLAN.update(goal='more sign-ups', steps=three['steps'], step=1, running=True, answers=['Yes, at first payout', '', '₹500'])
fake = FakeTelegram([])
r = assistant.run_plan(ch(fake), repo, apply_build)
texts = [m['text'] for m in fake.sent]
check('step 1 is a build without a quiz; later steps are fix rounds; each step is reported; then "ship it"',
      (r, len(built), built[0][1:], 'Yes, at first payout' in built[0][0], len(applied), '₹500' in applied[1],
       [t.split('.')[0] for t in texts if t.startswith('✅')], texts[-1].startswith("🎉 That's the plan done, sir."), 'ship it' in texts[-1],
       assistant.PLAN['running']),
      ('done', 1, (False, False), True, 2, True, ['✅ Step 1 of 3 done: A shorter sign-up form', '✅ Step 2 of 3 done: Show what creators earn',
                                                   '✅ Step 3 of 3 done: Reward the first deal'], True, True, False))

# 5. a step that fails its checks stops the plan, with what is safe
assistant.PLAN.update(step=1, running=True)
fake = FakeTelegram([])
r = assistant.run_plan(ch(fake), repo, lambda s, rule, c: 1)
check('a failing step stops the plan and says what is safe', (r, any("Everything before it is built and safe" in m['text'] for m in fake.sent)),
      ('failed', True))

# 6. while it runs, "status" knows which step
assistant.PLAN.update(step=2, running=True)
check('status knows the plan and its step', assistant._building().startswith('A build is running: his plan for "more sign-ups", step 2 of 3'), True)
assistant.PLAN['running'] = False

# 7. "not now" keeps the plan; "do the plan" later runs it
plan.make = lambda *a, **k: three
fake = FakeTelegram([tap('pln|no')])
check('"not now" holds the plan', assistant.handle(ch(fake), repo, 'help me get more creators', poll=1), 'plan_held')
assistant.run_plan = lambda *a, **k: 'done'
fake = FakeTelegram([])
check('"do the plan" runs the held plan', assistant.handle(ch(fake), repo, 'ok do the plan', poll=1), 'planned')
sys.exit(fail)
