"""A test deploy on his own cloud machine (hive/trydeploy.py), with a stand-in machine and AWS (no network, no server):
static pages go up at a secret address for two hours, the port opens and closes, "take it down" ends it, a machine made
only for the test is deleted, expiry is noticed, and from the phone "send me a link" offers it when no host is set up.
usage: python3 tests/test_trydeploy.py   (run from the hive repo root)"""
import json, os, re, shutil, subprocess, sys, tempfile, time
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home
from hive import assistant, cloud_aws, explain, logins, memory, telegram, trydeploy
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
git = lambda cwd, *a: subprocess.run(['git', '-C', cwd, *a], capture_output=True, text=True)

aws_calls = []
cloud_aws._aws = lambda args, profile=None, region=None, check=True: aws_calls.append(args[1]) or {}
class Machine:   # the cloud machine: commands recorded, files copied into a folder
    def __init__(self):
        self.cmds, self.dir = [], tempfile.mkdtemp()
    def run(self, cmd, check=True):
        self.cmds.append(cmd); return subprocess.CompletedProcess(cmd, 0, '', '')
    def put(self, src, dst):
        os.makedirs(os.path.dirname(os.path.join(self.dir, dst)), exist_ok=True); shutil.copy(src, os.path.join(self.dir, dst))
box = Machine()
def machine_state(ip='3.110.0.7'):
    os.makedirs(cloud_aws.HOME(), exist_ok=True)
    json.dump({'name': 'hive-test', 'ip': ip, 'key': 'k.pem', 'group': 'sg-1', 'instance': 'i-1'}, open(cloud_aws.STATE(), 'w'))

def site(name, files):
    r = os.path.join(home, name); os.makedirs(r)
    for f, text in files.items():
        os.makedirs(os.path.dirname(os.path.join(r, f)) or r, exist_ok=True); open(os.path.join(r, f), 'w').write(text)
    git(r, 'init', '-q', '-b', 'main'); git(r, 'add', '-A'); git(r, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', name)
    git(r, 'branch', 'hive/b1')
    return r

# 1. where the pages are
plain = site('plain', {'index.html': '<h1>Dabba Days</h1>', 'plans.html': '<h1>Plans</h1>'})
built = site('built', {'package.json': '{}', 'dist/index.html': '<h1>Built</h1>'})
app = site('app', {'server.py': 'print(1)'})
check('pages at the top', trydeploy.static_root(plain), '')
check('pages in dist/', trydeploy.static_root(built), 'dist')
check('no pages', trydeploy.static_root(app), None)

# 2. up, on an existing machine: secret address, two-hour server, port opened, machine kept on "take it down"
machine_state()
r = trydeploy.up(plain, 'hive/b1', target=lambda m: box)
check('it goes up at a secret address on the machine', bool(r['ok'] and re.match(r'^http://3\.110\.0\.7:8080/[\w-]{16}/$', r['url'])), True)
check('the server stops by itself after two hours', any('timeout 7200 python3 -m http.server 8080' in c for c in box.cmds), True)
check('the port was opened', aws_calls[-1], 'authorize-security-group-ingress')
check('his pages were copied over', os.path.exists(os.path.join(box.dir, 'hive-try', 'site.tar')), True)
check('an existing machine is not marked as made for the test', trydeploy.state()['made_machine'], False)
msg = trydeploy.down(plain, target=lambda m: box)
check('"take it down": server stopped, port closed, machine kept', (aws_calls[-1], os.path.exists(trydeploy.STATE()),
      'stays' in msg, any('pkill -f "http.server 8080"' in c for c in box.cmds[-1:])),
      ('revoke-security-group-ingress', False, True, True))
r = trydeploy.up(built, 'hive/b1', target=lambda m: box)
check('a built site is served from its dist/ folder', r['url'].endswith('/dist/'), True)
trydeploy.down(built, target=lambda m: box)

# 3. not plain pages: said plainly, nothing made
os.remove(cloud_aws.STATE())
made = []
r = trydeploy.up(app, 'hive/b1', new_machine=lambda: made.append(1) or 0, target=lambda m: box)
check('no web pages: a plain no, and no machine made', (r['ok'], 'index.html' in r['say'], made), (False, True, []))

# 4. no machine yet: one is made for the test, and deleted when it is taken down
r = trydeploy.up(plain, 'hive/b1', new_machine=lambda: machine_state('13.200.1.2') or 0, target=lambda m: box)
check('a machine is made for the test when there is none', (r['ok'], r['made'], r['url'].startswith('http://13.200.1.2:8080/')),
      (True, True, True))
deleted = []
msg = trydeploy.down(plain, delete_machine=lambda: deleted.append(1) or 0, target=lambda m: box)
check('taken down: the machine made for it is deleted too', (deleted, 'nothing is left running' in msg), ([1], True))

# 5. two hours on, it is noticed
machine_state(); trydeploy.up(plain, 'hive/b1', target=lambda m: box)
check('within two hours: not expired', trydeploy.expired(), False)
st = trydeploy.state(); st['until'] = time.time() - 1; trydeploy._save(st)
check('past two hours: expired', trydeploy.expired(), True)
trydeploy.down(plain, target=lambda m: box)

# 6. from the phone: "send me a link" with no host offers it; "take it down" ends it
runs = os.path.join(assistant.RUNS, 'b1'); os.makedirs(runs)
json.dump({'repo': plain, 'name': 'b1', 'check': '2 tests, all passing.', 'home': runs}, open(os.path.join(runs, 'state.json'), 'w'))
real_which, real_ensure, real_up, real_down = shutil.which, logins.ensure, trydeploy.up, trydeploy.down
shutil.which = lambda tool, *a, **k: '/usr/bin/aws' if tool == 'aws' else real_which(tool, *a, **k)
logins.ensure = lambda ch_, service, poll=20: True
trydeploy.up = lambda repo, branch, say=print, **k: (trydeploy._save({'url': 'http://1.2.3.4:8080/s/', 'until': time.time() + 60})
                                                      or {'ok': True, 'url': 'http://1.2.3.4:8080/s/', 'made': True})
fake = FakeTelegram([tap('tdp|yes')])
r = assistant.handle(ch(fake), plain, 'send me a link', poll=1)
texts = [m['text'] for m in fake.sent]
check('no host: the test deploy is offered, with its cost and limits', ('test machine on your AWS' in texts[0],
      'two hours' in texts[0]), (True, True))
check('on yes: the private link, and how to end it', (r, 'http://1.2.3.4:8080/s/' in texts[-1], 'take it down' in texts[-1],
      'delete the test machine' in texts[-1]), ('test_deployed', True, True, True))
trydeploy.down = lambda repo, **k: (os.remove(trydeploy.STATE()) or 'The test page is down, and the test machine is deleted: nothing is left running or billing.')
fake = FakeTelegram([])
r = assistant.handle(ch(fake), plain, "I'm done testing, take it down", poll=1)
check('"take it down" ends it and says so', (r, 'nothing is left running' in fake.sent[-1]['text']), ('taken_down', True))
fake = FakeTelegram([])
check('"take it down" with nothing up is not taken as a take-down', assistant.handle(ch(fake), plain, 'take it down', poll=1) != 'taken_down', True)
shutil.which, logins.ensure, trydeploy.up, trydeploy.down = real_which, real_ensure, real_up, real_down

# 7. deleting the cloud machine forgets its test page
trydeploy._save({'url': 'http://x', 'until': time.time() + 60})
check('a test page is on record before the machine goes', os.path.exists(trydeploy.STATE()), True)

sys.exit(fail)
