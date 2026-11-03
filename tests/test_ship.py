"""'Ship it' from the owner's phone (hive/ship.py): his latest build goes to his engineer as a pull request, after he
confirms; only hive/<name> is pushed, his main branch never. A local remote and a stand-in gh; a fake Telegram.
usage: python3 tests/test_ship.py   (run from the hive repo root)"""
import json, os, subprocess, sys, tempfile, time
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home
from hive import assistant, explain, memory, ship, team, telegram
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
git = lambda cwd, *a: subprocess.run(['git', '-C', cwd, *a], capture_output=True, text=True)
ch = lambda fake: telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake)

# his project, its online home (a bare repo standing in for GitHub), and a finished build on hive/invites-1103
origin = os.path.join(home, 'origin.git'); subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', origin])
repo = os.path.join(home, 'shop'); os.makedirs(repo); git(repo, 'init', '-q', '-b', 'main')
c = lambda *a: git(repo, '-c', 'user.name=t', '-c', 'user.email=t@t', *a)
open(os.path.join(repo, 'a.txt'), 'w').write('main'); git(repo, 'add', '.'); c('commit', '-qm', 'main')
git(repo, 'remote', 'add', 'origin', origin); git(repo, 'push', '-q', 'origin', 'main')
main_before = git(origin, 'rev-parse', 'main').stdout.strip()
git(repo, 'checkout', '-q', '-b', 'hive/invites-1103'); open(os.path.join(repo, 'b.txt'), 'w').write('built'); git(repo, 'add', '.')
c('commit', '-qm', 'built'); git(repo, 'checkout', '-q', 'main')
open(os.path.join(repo, 'a.txt'), 'w').write('his own unsaved main work')   # his main must not move or be pushed
st = {'repo': repo, 'name': 'invites-1103', 'branch': 'main', 'b': 'main', 'goal': 'An invite page at /invite, with a '
      'reward of Rs 500 each (his picture: .hive/refs/ref_1.jpg; open it and match what it shows)',
      'check': '5 tests, all passing. All 5 that passed before still pass.', 'cost': 0.42}
os.makedirs(os.path.join(assistant.RUNS, 'invites-1103')); json.dump(st, open(os.path.join(assistant.RUNS, 'invites-1103', 'state.json'), 'w'))

# 1. the words: read without a model, and not mistaken for "push it to main"
check('"ship it", "send it to my engineer", "open a PR" are read without a model',
      [bool(assistant.SHIP_WORDS.search(t)) for t in ('ship it', 'ok, ship it', 'send it to my engineer', 'open a pr',
                                                     'engineer ko bhej do', 'what does ship mean')], [True] * 5 + [False])
check('"push it straight to main" is still refused, never shipped', assistant.is_risky('push it straight to main'), True)
check('the remote kinds', (ship.web('git@github.com:acme/shop.git'), ship.web('https://gitlab.com/acme/shop')[0], ship.web(origin)),
      (('github', ('github.com', 'acme/shop')), 'gitlab', (None, None)))
check('the engineer reads what he asked, what was checked and what it cost; the picture marker is not in the title',
      (ship.title(st), 'what he asked for' in ship.body(st).lower(), '5 tests, all passing' in ship.body(st), '$0.42' in ship.body(st)),
      ('Hive: An invite page at /invite, with a reward of Rs 500 each', True, True, True))

# 2. he says "ship it", then "not now": nothing leaves his computer
fake = FakeTelegram([tap('shp|no')])
r = assistant.handle(ch(fake), repo, 'ship it', poll=1)
check('asked first; "not now" sends nothing', (r, 'Send this to your engineer?' in fake.sent[0]['text'],
      'hive/' in git(origin, 'branch', '--list').stdout), ('not_shipped', True, False))

# 3. he says yes: only Hive's branch goes up; main is untouched there and here
fake = FakeTelegram([tap('shp|yes')])
r = assistant.handle(ch(fake), repo, 'Ship it', poll=1)
check('yes: the build is uploaded as its own branch; his main version is not touched',
      (r, git(origin, 'rev-parse', 'hive/invites-1103').stdout.strip() == git(repo, 'rev-parse', 'hive/invites-1103').stdout.strip(),
       git(origin, 'rev-parse', 'main').stdout.strip() == main_before, open(os.path.join(repo, 'a.txt')).read(),
       'Uploaded' in fake.sent[-1]['text']), ('shipped', True, True, 'his own unsaved main work', True))

# 4. on GitHub with gh: a pull request is opened, with his words, once (a second "ship it" finds the open one)
calls = []
def fake_gh(cmd, cwd):
    calls.append(cmd)
    if cmd[:3] == ['gh', 'pr', 'view']:
        open_now = any(x[:3] == ['gh', 'pr', 'create'] for x in calls)
        return subprocess.CompletedProcess(cmd, 0 if open_now else 1, json.dumps({'url': 'https://github.com/acme/shop/pull/7', 'state': 'OPEN'}) if open_now else '', '')
    return subprocess.CompletedProcess(cmd, 0, 'https://github.com/acme/shop/pull/7\n', '')
ship._run = fake_gh
real_web, real_which = ship.web, ship.shutil.which
ship.web = lambda url: ('github', ('github.com', 'acme/shop')); ship.shutil.which = lambda n: '/usr/bin/' + n
r1 = ship.ship(repo, st); r2 = ship.ship(repo, st)
create = [x for x in calls if x[:3] == ['gh', 'pr', 'create']]
check('with gh: one pull request into his main branch, from hive/<name>; asked again, the same one',
      (r1['how'], r1['url'], len(create), create[0][create[0].index('--base') + 1], create[0][create[0].index('--head') + 1], r2.get('again')),
      ('pr', 'https://github.com/acme/shop/pull/7', 1, 'main', 'hive/invites-1103', True))

# 5. on GitHub without gh: the link that opens the pull request
ship.shutil.which = lambda n: None
check('without gh: one tap opens the pull request', ship.ship(repo, st)['url'],
      'https://github.com/acme/shop/compare/main...hive/invites-1103?expand=1')
ship.web, ship.shutil.which = real_web, real_which

# 6. no online home: told plainly; nothing built: told plainly
git(repo, 'remote', 'remove', 'origin')
fake = FakeTelegram([tap('shp|yes')])
check('no remote: he is told the branch his engineer can merge', (assistant.handle(ch(fake), repo, 'ship it', poll=1),
      'no online home' in fake.sent[-1]['text']), ('ship_failed', True))
other = os.path.join(home, 'other'); os.makedirs(other)
fake = FakeTelegram([])
check('nothing built yet: nothing to ship', assistant.handle(ch(fake), other, 'ship it', poll=1), 'nothing_to_ship')
sys.exit(fail)
