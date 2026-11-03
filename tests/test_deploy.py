"""Where his product lives, his choice (hive/deploy.py): connect a host, a preview link of a build, and going live only
after his engineer merged it, on his yes, with every test passing. Stand-in host tools; a fake Telegram.
usage: python3 tests/test_deploy.py   (run from the hive repo root)"""
import json, os, subprocess, sys, tempfile
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home
from hive import assistant, deploy, explain, memory, numbers, team, telegram
explain.CMD = '"' + sys.executable.replace(chr(92), '/') + '" tests/fake_explain.py'
memory.DIR = os.path.join(home, '.hive', 'rules'); telegram.BUSY = os.path.join(home, '.hive', 'telegram.busy')
telegram.PATH = os.path.join(home, '.hive', 'telegram.json'); deploy.DIR = os.path.join(home, '.hive', 'deploy')
numbers.DIR = os.path.join(home, '.hive', 'numbers')
assistant.RUNS = team.RUNS = os.path.join(home, '.hive', 'runs'); team.TEAM = os.path.join(home, '.hive', 'team.json')
from test_telegram_fake import FakeTelegram, ME, tap, say

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))
ch = lambda fake: telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake)
git = lambda cwd, *a: subprocess.run(['git', '-C', cwd, *a], capture_output=True, text=True)

repo = os.path.join(home, 'shop'); os.makedirs(repo); git(repo, 'init', '-q', '-b', 'main')
c = lambda *a: git(repo, '-c', 'user.name=t', '-c', 'user.email=t@t', *a)
open(os.path.join(repo, 'index.html'), 'w').write('old'); open(os.path.join(repo, 'test_ok.py'), 'w').write('def test_ok(): assert 1\n')
git(repo, 'add', '.'); c('commit', '-qm', 'main')
git(repo, 'checkout', '-q', '-b', 'hive/signup-1103'); open(os.path.join(repo, 'index.html'), 'w').write('new'); git(repo, 'add', '.')
c('commit', '-qm', 'built'); git(repo, 'checkout', '-q', 'main')
os.makedirs(os.path.join(repo, '.vercel')); open(os.path.join(repo, '.vercel', 'project.json'), 'w').write('{}')   # his link, not in git
st = {'repo': repo, 'name': 'signup-1103', 'branch': 'main', 'goal': 'A shorter sign-up form', 'check': '1 test, all passing.',
      'test_cmd': 'python3 -m pytest -q --junitxml=.hive/junit.xml' if os.name != 'nt' else f'"{sys.executable}" -m pytest -q --junitxml=.hive/junit.xml',
      'home': os.path.join(assistant.RUNS, 'signup-1103')}
os.makedirs(st['home']); json.dump(st, open(os.path.join(st['home'], 'state.json'), 'w'))
ran = []
def tool(cmd, cwd, timeout=900):
    ran.append((cmd, open(os.path.join(cwd, 'index.html')).read(), os.path.exists(os.path.join(cwd, '.vercel', 'project.json'))))
    url = 'https://shop-git-preview-acme.vercel.app' if '--prod' not in cmd else 'https://shop.acme.app'
    return subprocess.CompletedProcess(cmd, 0, f'Inspect: https://vercel.com/x\nPreview: {url}\n', '')
deploy._run = tool
real_which = deploy.shutil.which

# 1. the words: his host, a link, live; never "skip the tests" or "push to main"
low = lambda t: t.lower()
check('phrases go where they should', [
    ('connect' if assistant.CONNECT_WORDS.search(low(t)) else 'live' if assistant.LIVE_WORDS.search(low(t)) and not assistant.SKIP_WORDS.search(low(t))
     else 'preview' if assistant.PREVIEW_WORDS.search(low(t)) else 'risky' if assistant.is_risky(t) else '-')
    for t in ('we are on Vercel', 'connect railway', 'send me a link', 'put it live', 'deploy it to production',
              'deploy it and skip the tests', 'push it straight to main')],
    ['connect', 'connect', 'preview', 'live', 'live', 'risky', 'risky'])

# 2. connect: remembered per project; told plainly when the host's tool is missing
deploy.shutil.which = lambda n: None
fake = FakeTelegram([])
check('"we are on Vercel": connected; the missing tool is said plainly', (assistant.handle(ch(fake), repo, 'we are on Vercel', poll=1),
      deploy.config(repo)['host'], 'vercel login' in fake.sent[-1]['text']), ('connected', 'vercel', True))
deploy.shutil.which = lambda n: '/usr/bin/' + n
check('every host he might use is known, or his own commands', (sorted(deploy.HOSTS), deploy.setup(repo, 'custom', 'my-preview', 'my-live')['live']),
      (['azure', 'fly', 'netlify', 'railway', 'render', 'vercel'], 'my-live'))
deploy.setup(repo, 'vercel')

# 3. a preview link: the build itself, with his host link carried over; his live product untouched
fake = FakeTelegram([])
check('"send me a link": the build at its own address', (assistant.handle(ch(fake), repo, 'send me a link', poll=1),
      ran[-1], 'https://shop-git-preview-acme.vercel.app' in fake.sent[-1]['text']),
      ('previewed', ('vercel deploy --yes', 'new', True), True))

# 4. "put it live" before his engineer merged it: never; he is told the way
ran.clear(); fake = FakeTelegram([])
check('not merged: not put live, and he is told to ship it first', (assistant.handle(ch(fake), repo, 'put it live', poll=1), ran,
      'ship it' in fake.sent[-1]['text']), ('not_merged', [], True))

# 5. merged: asked once, every test on main first, then live; the brief will know
c('merge', '-q', 'hive/signup-1103')
fake = FakeTelegram([tap('liv|yes')])
r = assistant.handle(ch(fake), repo, 'put it live', poll=1)
check('merged: his yes, the tests on main, then live from main', (r, ran[-1][:2], 'https://shop.acme.app' in fake.sent[-1]['text'],
      any('went live' in e['what'] for e in numbers.events(repo))), ('live', ('vercel deploy --prod --yes', 'new'), True, True))

# 6. a failing test on main: it stays as it is
open(os.path.join(repo, 'test_ok.py'), 'w').write('def test_ok(): assert 0\n'); git(repo, 'add', '.'); c('commit', '-qm', 'broken')
ran.clear(); fake = FakeTelegram([tap('liv|yes')])
check('a failing test on main: nothing goes live', (assistant.handle(ch(fake), repo, 'put it live', poll=1), ran,
      'stays as it is' in fake.sent[-1]['text']), ('live_failed', [], True))
deploy.shutil.which = real_which
sys.exit(fail)
