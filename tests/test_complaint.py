"""A customer's complaint, linked to the owner's rules (hive/assistant.py complaint): his own rule at work (he can change
it in a message), or a fault (one tap fixes his latest build). A stand-in for Claude reading the code; a fake Telegram.
usage: python3 tests/test_complaint.py   (run from the hive repo root)"""
import json, os, sys, tempfile
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home
from hive import assistant, explain, memory, team, telegram
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
memory.add(repo, 'A refund goes back to the card it was paid with, never as store credit.')
memory.add(repo, 'Creators get their ₹500 only after their first deal is finished.')
st = {'repo': repo, 'name': 'refunds-1103', 'branch': 'main', 'b': 'main', 'goal': 'refunds', 'check': '9 tests, all passing.'}
os.makedirs(os.path.join(assistant.RUNS, 'refunds-1103')); json.dump(st, open(os.path.join(assistant.RUNS, 'refunds-1103', 'state.json'), 'w'))
asked = []
def stand_in(answer):
    def look(ch, repo, text):
        asked.append(text); return answer
    assistant.look = look

# 1. the words: plain complaints are read without a model; requests that only mention customers are not complaints
check('complaints read without a model; a page about complaints, or what users want, is not one',
      [bool(assistant.COMPLAINT_WORDS.search(t)) for t in (
          'a customer says she got store credit instead of her money back', 'customers are complaining about the invite page',
          'this creator never got his 500', 'build a complaints page', 'users want a dark mode, add it',
          'customer ne shikayat ki hai refund ki')], [True, True, True, False, False, True])

# 2. it's his own rule at work: he is told which, and how to change it
stand_in("She paid by card and asked for store credit; your product sent it back to her card, as it always does.\n"
         "VERDICT: rule 1")
fake = FakeTelegram([])
r = assistant.handle(ch(fake), repo, 'A customer says she wanted store credit but got her money back on the card', poll=1)
check("his rule at work: he hears what happened and which rule, in his words",
      (r, "That's your rule 1:" in fake.sent[-1]['text'], 'never as store credit' in fake.sent[-1]['text'],
       'VERDICT' in fake.sent[-1]['text']), ('complaint_rule', True, True, False))
check('Claude is given the complaint and his numbered rules', ('1. A refund goes back' in asked[-1], 'store credit but got' in asked[-1]), (True, True))

# 3. a fault: one tap fixes his latest build, with the customer's case as the instruction
stand_in("The creator finished his first deal on Monday but the ₹500 was never credited: the payout skips deals "
         "finished on a weekend day.\nVERDICT: bug")
applied = []
fake = FakeTelegram([tap('cmp|fix')])
r = assistant.handle(ch(fake), repo, "A creator says he never got his ₹500 after his first deal", poll=1,
                     apply_build=lambda state, rule, ch: applied.append(rule))
check('a fault: he is asked once, then the latest build is fixed with the customer case and a test',
      (r, len(applied), 'never got his ₹500' in applied[0] if applied else False, 'add a test' in applied[0] if applied else False,
       "it's a fault" in fake.sent[0]['text']), ('complaint_fixed', 1, True, True, True))

# 4. he says leave it: nothing changes
fake = FakeTelegram([tap('cmp|no')]); applied.clear()
r = assistant.handle(ch(fake), repo, "A creator says he never got his ₹500", poll=1, apply_build=lambda s, rule, c: applied.append(rule))
check('"leave it": nothing is changed', (r, applied), ('complaint_kept', []))

# 5. Claude can't say: he is asked for the steps, never told a guess
stand_in(None)
fake = FakeTelegram([])
check("can't trace it: he is asked for the customer's steps", (assistant.handle(ch(fake), repo, 'a customer complained about refunds', poll=1),
      'step by step' in fake.sent[-1]['text']), ('complaint_unclear', True))
sys.exit(fail)
