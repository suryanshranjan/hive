"""He is stepping away (the owner: "if the founder says I'm feeling sleepy, Hive should say: shall we move to the cloud so
you can shut your computer and I carry on, or proceed another way"). A fake Telegram, a stand-in cloud and build.
usage: python3 tests/test_away.py   (run from the hive repo root)"""
import json, os, subprocess, sys, tempfile, time
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home
from hive import assistant, explain, logins, memory, telegram
logins.ensure = lambda ch, service, poll=20: True   # signed in (renewal itself: tests/test_logins.py)
explain.CMD = '"' + sys.executable.replace(chr(92), '/') + '" tests/fake_explain.py'
memory.DIR = os.path.join(home, '.hive', 'rules'); telegram.BUSY = os.path.join(home, '.hive', 'telegram.busy')
assistant.RUNS = os.path.join(home, '.hive', 'runs')
from test_telegram_fake import FakeTelegram, ME, tap, say

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))
ch = lambda fake: telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake)
repo = os.path.join(home, 'shop'); subprocess.run(['git', 'init', '-q', '-b', 'main', repo])
subprocess.run(['git', '-C', repo, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'shop'])

def running(goal='a referral page'):
    p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'], start_new_session=os.name != 'nt')
    assistant.BUILD.clear()
    assistant.BUILD.update(proc=p, goal=goal, started=time.time(), log=os.path.join(home, 'b.log'), stopped=False)
    return p

def idle():
    assistant.BUILD.clear(); assistant.PLAN.clear()

# 1. what counts as stepping away, and what is a request
for t, want in (("hive i am feeling sleepy", True), ("good night", True), ("I'm shutting my laptop now", True),
                ("so raha hoon", True), ("neend aa rahi hai", True), ("going to bed, carry on", True),
                ("add a good night message to emails", False), ("make the sleep timer page", False),
                ("show me the night menu", False)):
    check(f'away? {t!r}', assistant.is_away(t.lower()), want)

# 2. nothing running, no cloud: he can shut his computer; something overnight is offered
idle()
fake = FakeTelegram([tap('awy|none')])
r = assistant.handle(ch(fake), repo, "I'm feeling sleepy", poll=1)
texts = [m['text'] for m in fake.sent]
check('nothing running: he may shut it, and something overnight is offered',
      (r, 'Nothing is running' in texts[0], 'build something while you sleep' in texts[0]), ('away_none', True, True))
fake = FakeTelegram([tap('awy|night')])
check('"build something overnight" asks what', (assistant.handle(ch(fake), repo, 'good night', poll=1),
      'What would you like ready by morning?' in fake.sent[-1]['text']), ('away_night', True))
fake = FakeTelegram([say('build: a referral page for office workers'), tap('bld|no')])
started = []
r = assistant.handle(ch(fake), repo, 'good night', poll=1, start_build=lambda rp, g, interview=True: started.append(g))
check('answering with the thing to build goes to the usual build proposal, his yes needed',
      (any('Shall I build this?' in m['text'] for m in fake.sent), r, started), (True, 'not_built', []))

# 3. a build running and a cloud: the cloud is recommended; the work is handed over, then stopped here
p = running()
seen = {}
def cloud_ok(rp, on, login=True):
    seen['resume'] = json.load(open(assistant.RESUME(), encoding='utf-8'))   # written before the move, so it travels
    seen['alive_during_move'] = p.poll() is None
    return 0
fake = FakeTelegram([tap('awy|cloud')])
r = assistant.handle(ch(fake), repo, "I'm sleepy, shutting my laptop", poll=1, cloud=cloud_ok)
texts = [m['text'] for m in fake.sent]
check('with work running, the cloud is recommended first', ('My suggestion: let me move to the cloud' in texts[0],
      fake.sent[0]['reply_markup']['inline_keyboard'][0][0]['callback_data']), (True, 'awy|cloud'))
check('the work is handed to the cloud, and kept running here until the move is done',
      (seen['resume']['goal'], seen['alive_during_move']), ('a referral page', True))
time.sleep(1)
check('once moved, the build here is stopped and he is told he can shut his computer',
      (r, p.poll() is not None, "You can shut your computer now" in texts[-1]), ('moved', True, True))

# 4. the move fails: nothing is lost, the work carries on here, and he is asked to leave the computer on
p = running()
fake = FakeTelegram([tap('awy|cloud')])
r = assistant.handle(ch(fake), repo, 'going to bed', poll=1, cloud=lambda rp, on, login=True: 1)
check('a failed move keeps the work running here and says so',
      (r, p.poll() is None, os.path.exists(assistant.RESUME()), 'leave your computer on' in fake.sent[-1]['text']),
      ('away_cloud_failed', True, False, True))

# 4b. his AWS sign-in expired and he says "not now": nothing moves, the work carries on here, he is told
p = running()
logins.ensure = lambda ch, service, poll=20: False
fake = FakeTelegram([tap('awy|cloud')])
r = assistant.handle(ch(fake), repo, 'going to bed', poll=1, cloud=lambda rp, on, login=True: 0)
check('no sign-in: nothing moves, the work goes on here, and he is asked to leave the computer on',
      (r, p.poll() is None, os.path.exists(assistant.RESUME()), 'leave your computer on' in fake.sent[-1]['text']),
      ('away_login_needed', True, False, True))
logins.ensure = lambda ch, service, poll=20: True

# 5. carry on here / stop for tonight
fake = FakeTelegram([tap('awy|here')])
check('"carry on here" keeps it running', (assistant.handle(ch(fake), repo, 'good night', poll=1, cloud=cloud_ok),
      p.poll() is None), ('away_here', True))
fake = FakeTelegram([tap('awy|stop')])
r = assistant.handle(ch(fake), repo, 'good night', poll=1, cloud=cloud_ok)
time.sleep(1)
check('"stop for tonight" stops it, and says how to pick it up', (r, p.poll() is not None,
      'build again' in fake.sent[-1]['text']), ('away_stopped', True, True))

# 6. without a cloud, the advice is plain: leave it on, or stop
p = running()
fake = FakeTelegram([tap('awy|here')])
assistant.handle(ch(fake), repo, 'good night', poll=1)
check('no cloud: no cloud button, and the advice says the computer must stay on',
      ([b['callback_data'] for row in fake.sent[0]['reply_markup']['inline_keyboard'] for b in row],
       'needs this computer on and awake' in fake.sent[0]['text'].replace('I need this computer', 'needs this computer')),
      (['awy|here', 'awy|stop'], True))
assistant._stop(p)

# 7. already in the cloud: just good night
os.environ['HIVE_IN_CLOUD'] = '1'
fake = FakeTelegram([])
check('in the cloud: good night, the computer can be off', (assistant.handle(ch(fake), repo, 'good night', poll=1),
      'your computer can be off' in fake.sent[-1]['text']), ('away_cloud', True))
del os.environ['HIVE_IN_CLOUD']

# 8. the cloud copy, on waking, picks the handed-over work up and says so
idle()
json.dump({'goal': 'a referral page', 'said': 'a referral page'}, open(assistant.RESUME(), 'w'))
os.environ['HIVE_BUILD_CMD'] = f'"{sys.executable}" -c "import time; time.sleep(1)"'
fake = FakeTelegram([])
got = assistant.resume_here(ch(fake), repo)
check('on waking, the handed-over work restarts and he hears it once', (got, os.path.exists(assistant.RESUME()),
      "picking up where your computer left off" in fake.sent[0]['text'], assistant.BUILD.get('goal')),
      ('a referral page', False, True, 'a referral page'))
check('with nothing handed over, waking says nothing', assistant.resume_here(ch(FakeTelegram([])), repo), '')
time.sleep(2)

sys.exit(fail)
