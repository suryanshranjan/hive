"""A technical owner (hive/register.py): a technical instruction is caught and taken as it is ("Yes, let's do it",
restated in his terms), with only the normal questions an engineer would ask, no business situations quiz; Jarvis
then speaks his language. A plain owner keeps plain words. Stand-in code reader; a fake Telegram.
usage: python3 tests/test_register.py   (run from the hive repo root)"""
import os, sys, tempfile
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home
from hive import assistant, explain, memory, register, team, telegram
explain.CMD = '"' + sys.executable.replace(chr(92), '/') + '" tests/fake_explain.py'
memory.DIR = os.path.join(home, '.hive', 'rules'); telegram.BUSY = os.path.join(home, '.hive', 'telegram.busy')
telegram.PATH = os.path.join(home, '.hive', 'telegram.json'); register.PATH = os.path.join(home, '.hive', 'profile.json')
assistant.RUNS = team.RUNS = os.path.join(home, '.hive', 'runs'); team.TEAM = os.path.join(home, '.hive', 'team.json')
from test_telegram_fake import FakeTelegram, ME, tap, say

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))
ch = lambda fake: telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake)
repo = os.path.join(home, 'shop'); os.makedirs(repo)

# 1. caught: technical instructions; not: plain requests or everyday words
check('technical instructions are caught; plain requests and everyday words are not',
      [register.is_technical(t) for t in ('Add a Redis cache in front of /products with a 60s TTL',
       'make the products endpoint paginate, 20 per page', 'add an index on users.email', 'fix the null check in refunds.py',
       'I want more creators signing up', 'the rest of the page looks fine', 'put the queue of orders on the dashboard',
       'make the button bigger')], [True, True, True, True, False, False, False, False])

# 2. a technical build: his normal questions only where unclear, then "Yes, let's do it" in his terms; no quiz
asked = []
register.clarify = lambda repo, text: asked.append(text) or {'restated': 'Cache GET /products in Redis, 60 s TTL, invalidated on product update.',
                                                              'questions': [{'q': 'Cache prices too, or the list only?', 'options': ['List only', 'Prices too']}]}
started = []
fake = FakeTelegram([tap('tq|0'), tap('bld|yes')])
r = assistant.handle(ch(fake), repo, 'build: add a Redis cache in front of /products with a 60s TTL', poll=1,
                     start_build=lambda repo, goal, interview=True: started.append((goal, interview)))
texts = [m['text'] for m in fake.sent]
check('"Yes, let\'s do it", restated in his terms, after one normal question; built with his answer and no quiz',
      (r, texts[0], texts[1].startswith("👍 Yes, let's do it.\n\nCache GET /products in Redis, 60 s TTL"),
       started[0][1], 'Cache prices too, or the list only? -> List only' in started[0][0], 'Situation' in ' '.join(texts)),
      ('built', '❓ Cache prices too, or the list only?', True, False, True, False))

# 3. the same owner again: remembered as technical, and Jarvis's facts say to speak his language
register.notice('make the products endpoint paginate, 20 per page')
check('after two technical messages he is technical, and Jarvis is told to answer in his terms',
      (register.technical(), 'answer him in the same terms' in assistant.facts(repo)), (True, True))

# 4. a plain owner: plain words, the plain confirmation, the usual build
os.remove(register.PATH); assistant.CURRENT['text'] = ''
started.clear()
fake = FakeTelegram([tap('bld|yes')])
r = assistant.handle(ch(fake), repo, 'build: a page where creators can invite friends', poll=1,
                     start_build=lambda repo, goal, interview=True: started.append((goal, interview)))
check('a plain owner keeps the plain confirmation and Jarvis keeps plain words',
      (r, fake.sent[0]['text'].startswith('🏗 Shall I build this?'), started[0][1], register.line('')), ('built', True, True, ''))
sys.exit(fail)
