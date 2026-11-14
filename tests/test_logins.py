"""Expired logins renewed from the owner's phone (hive/logins.py), with stand-in AWS and GitHub sign-ins and a fake
Telegram: the link reaches him, the code he sends back finishes it, a different account is never switched silently,
GitHub's one-time code is shown, "not now" stops, and a working login is left alone.
usage: python3 tests/test_logins.py   (run from the hive repo root)"""
import os, sys, tempfile
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home
from hive import logins, telegram
telegram.BUSY = os.path.join(home, 'telegram.busy')
from test_telegram_fake import FakeTelegram, ME, tap, say

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))
ch = lambda fake: telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake)
PY = sys.executable
mark = os.path.join(home, 'signed_in')
answer = os.path.join(home, 'switch_answer')

def script(name, body):
    p = os.path.join(home, name); open(p, 'w').write(body); return p

check_py = script('check.py', f'import os, sys; sys.exit(0 if os.path.exists({mark!r}) else 255)')
aws_py = script('aws_login.py', f'''import sys
print("Open this URL on any device:"); print("https://signin.example.test/authorize?x=1", flush=True)
code = sys.stdin.readline().strip()
if {"'SWITCH'"} in code:
    print("Profile default is already configured to use session A. Do you want to overwrite it to use B instead? (y/n): ", end="", flush=True)
    ans = sys.stdin.readline().strip(); open({answer!r}, "w").write(ans)
    if ans != "y": sys.exit(255)
if code.startswith("GOOD"):
    open({mark!r}, "w").write("ok"); print("Updated profile default.")
else:
    print("aws: [ERROR]: invalid authorization code"); sys.exit(255)
''')
gh_py = script('gh_login.py', f'''import sys, time
print("! First copy your one-time code: ABCD-1234")
print("Press Enter to open https://github.com/login/device in your browser... ", flush=True)
sys.stdin.readline(); time.sleep(0.5); open({mark!r}, "w").write("ok"); print("Logged in as someone")
''')
logins.SERVICES['aws'].update(check=[PY, check_py], login=[PY, aws_py])
logins.SERVICES['github'].update(check=[PY, check_py], login=[PY, gh_py])

def reset():
    for f in (mark, answer):
        if os.path.exists(f):
            os.remove(f)

# 1. a working login is left alone: nothing sent, no sign-in started
open(mark, 'w').write('ok')
fake = FakeTelegram([])
check('a working login: nothing to do, nothing said', (logins.ensure(ch(fake), 'aws', poll=1), fake.sent), (True, []))

# 2. expired: the link reaches his phone, his code finishes it, and he hears it worked
reset()
fake = FakeTelegram([say('GOOD-12345')])
r = logins.ensure(ch(fake), 'aws', poll=1)
texts = [m['text'] for m in fake.sent]
check('AWS: the link goes to his phone and asks for the code',
      ('https://signin.example.test/authorize?x=1' in texts[0], 'Send me the code it shows you' in texts[0]), (True, True))
check('AWS: his code finishes the sign-in, checked, and he is told', (r, texts[-1]), (True, '✅ Signed in to AWS. Carrying on.'))

# 3. a different account is never switched silently: he is asked, and his answer goes to the sign-in
reset()
fake = FakeTelegram([say('GOOD-SWITCH-1'), tap('lgn|switch|aws')])
r = logins.ensure(ch(fake), 'aws', poll=1)
check('another account: he is asked, and "switch" is passed on', (r, any('different AWS account' in m['text'] for m in fake.sent),
      open(answer).read()), (True, True, 'y'))
reset()
fake = FakeTelegram([say('GOOD-SWITCH-2'), tap('lgn|keep|aws')])
r = logins.ensure(ch(fake), 'aws', poll=1)
check('another account, "keep the old one": nothing switched, and he hears it did not go through',
      (r, open(answer).read(), "didn't go through" in fake.sent[-1]['text']), (False, 'n', True))

# 4. a wrong code: said plainly, nothing pretends it worked
reset()
fake = FakeTelegram([say('WRONG-CODE')])
check('a wrong code: it says the sign-in did not go through', (logins.ensure(ch(fake), 'aws', poll=1),
      "didn't go through" in fake.sent[-1]['text']), (False, True))

# 5. "not now"
reset()
fake = FakeTelegram([tap('lgn|skip|aws')])
check('"not now" stops without signing in', (logins.ensure(ch(fake), 'aws', poll=1), fake.sent[-1]['text']),
      (False, "Very good. I'll leave it for now."))

# 6. GitHub: the one-time code and the address are shown; he approves on github.com; Hive carries on by itself
reset()
fake = FakeTelegram([])
r = logins.ensure(ch(fake), 'github', poll=1)
check('GitHub: one-time code and address shown, then done without a reply', (r, 'ABCD-1234' in fake.sent[0]['text'],
      'github.com/login/device' in fake.sent[0]['text'], fake.sent[-1]['text']),
      (True, True, True, '✅ Signed in to GitHub. Carrying on.'))

# 7. the tool itself missing: said plainly
logins.SERVICES['aws']['login'] = [os.path.join(home, 'no-such-aws'), 'login']
logins.SERVICES['aws']['check'] = [PY, check_py]
reset()
fake = FakeTelegram([])
check('no AWS command line: said plainly', (logins.ensure(ch(fake), 'aws', poll=1), 'isn\'t installed' in fake.sent[-1]['text']),
      (False, True))

# 8. Vercel, nothing on this computer: Hive installs the tool itself, sends the sign-in link (the code is in it), and
#    carries on once he approves on his phone; nobody at the computer (Gate 110)
reset()
installed = os.path.join(home, 'vercel_installed')
vercel_py = script('vercel.py', f'''import sys, time
if sys.argv[1] == 'whoami':
    import os; sys.exit(0 if os.path.exists({mark!r}) else 1)
print("  Visit https://vercel.com/oauth/device?user_code=WXYZ-1234", flush=True)
time.sleep(0.5); open({mark!r}, "w").write("ok"); print("Congratulations! You are now signed in.")
''')
install_py = script('install.py', f'open({installed!r}, "w").write("ok")')
real_exe = logins._exe
logins._exe = lambda cmd: (([PY, vercel_py] + list(cmd[1:])) if os.path.exists(installed) else None) if cmd[0] == 'vercel' \
    else [PY, install_py] if cmd[0] == 'npm' else real_exe(cmd)
fake = FakeTelegram([])
r = logins.ensure(ch(fake), 'vercel', poll=1)
texts = [m['text'] for m in fake.sent]
check('Vercel: installed by Hive, the link with its code sent, signed in without a reply',
      (r, 'Installing Vercel' in texts[0], 'user_code=WXYZ-1234' in texts[1], 'Check it shows this code' in texts[1],
       texts[-1]), (True, True, True, True, '✅ Signed in to Vercel. Carrying on.'))
logins._exe = real_exe

sys.exit(fail)
