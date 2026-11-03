"""The founder's gaps closed (Nov 3): a safety net for projects without tests, the price before the work and a monthly
cap, "undo that" at every stage, pull requests with screenshots and what changed, his code fetched from its address,
and the company brain (a document he sends). Stand-ins for Claude and the host tools; a fake Telegram.
usage: python3 tests/test_gaps.py   (run from the hive repo root)"""
import json, os, subprocess, sys, tempfile, time
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home
from hive import assistant, brain, budget, deploy, doctor, explain, memory, numbers, safety, ship, team, telegram
explain.CMD = '"' + sys.executable.replace(chr(92), '/') + '" tests/fake_explain.py'
memory.DIR = os.path.join(home, '.hive', 'rules'); telegram.BUSY = os.path.join(home, '.hive', 'telegram.busy')
telegram.PATH = os.path.join(home, '.hive', 'telegram.json'); numbers.DIR = os.path.join(home, '.hive', 'numbers')
deploy.DIR = os.path.join(home, '.hive', 'deploy'); budget.PATH = os.path.join(home, '.hive', 'budget.json')
safety.DIR = os.path.join(home, '.hive', 'safety')
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
open(os.path.join(repo, 'app.py'), 'w').write('def price(n):\n    return n * 100\n'); git(repo, 'add', '.'); c('commit', '-qm', 'app')

# 1. no tests: a safety net is written in a copy (his folder untouched), kept, and goes into each build
net_writer = os.path.join(home, 'net.py')
open(net_writer, 'w').write('import os, json\nos.makedirs("tests_hive", exist_ok=True)\n'
                            'open("tests_hive/test_price.py", "w").write("import sys, os\\nsys.path.insert(0, os.getcwd())\\n'
                            'from app import price\\ndef test_price(): assert price(2) == 200\\n")\n'
                            'print(json.dumps({"result": json.dumps({"tests": 1, "covers": "prices"}), "total_cost_usd": 0.2}))\n')
safety.CMD = f'"{sys.executable}" "{net_writer}"'
net = safety.make(repo)
check("a project with no tests gets a safety net that passes today; his folder is untouched",
      (net['ok'], net['tests'], safety.has(repo), os.path.exists(os.path.join(repo, 'tests_hive')), git(repo, 'status', '--porcelain').stdout),
      (True, 1, True, False, ''))
src = os.path.join(home, 'src'); subprocess.run(['git', 'clone', '-q', repo, src])
check('the net goes into a build, committed there', (safety.install(repo, src), 'safety net' in git(src, 'log', '-1', '--format=%s').stdout),
      (True, True))

# 2. the price before the work, from his own past builds; the cap
st = {'repo': repo, 'name': 'price-1103', 'branch': 'main', 'goal': 'Show prices in rupees', 'check': '1 test, all passing.',
      'cost': 0.8, 'home': os.path.join(assistant.RUNS, 'price-1103')}
os.makedirs(st['home']); json.dump(st, open(os.path.join(st['home'], 'state.json'), 'w'))
check('the estimate comes from his own builds; said as "about"', (budget.estimate(repo), budget.say(0.8), budget.say(0.05), budget.say(5.4)),
      (0.8, 'about $0.80', 'under $0.10', 'about $5'))
fake = FakeTelegram([])
check('"set my budget to $50 a month"', (assistant.handle(ch(fake), repo, 'set my budget to $50 a month', poll=1), budget.cap()), ('budget', 50.0))
budget.set_cap(1.0)
check('past his cap, he is told before the work', budget.over(0.8) is not None and 'past your $1 limit' in budget.over(0.8), True)
started = []
fake = FakeTelegram([tap('bld|no')])
assistant.handle(ch(fake), repo, 'build: a page listing every price in rupees', poll=1, start_build=lambda r, g, **k: started.append(g))
check('the confirmation says the price, and the cap', ('about $0.80' in fake.sent[0]['text'], '$1 limit' in fake.sent[0]['text'], started),
      (True, True, []))
os.remove(budget.PATH)

# 3. undo: a build not yet sent is set aside; the one before it is his latest again
fake = FakeTelegram([tap('und|yes')])
check('"undo that": set aside, his product exactly as it was', (assistant.handle(ch(fake), repo, 'undo that', poll=1),
      assistant.latest_build(repo)), ('undone', None))
st.pop('undone', None); json.dump(st, open(os.path.join(st['home'], 'state.json'), 'w'))
# ... sent to his engineer: the pull request is withdrawn
st['shipped'] = time.time(); json.dump(st, open(os.path.join(st['home'], 'state.json'), 'w'))
closed = []; ship.close = lambda repo, state: closed.append(state['name']) or True
fake = FakeTelegram([tap('und|yes')])
check('after "ship it": the pull request is withdrawn', (assistant.handle(ch(fake), repo, 'undo that', poll=1), closed,
      'withdrawn from your engineer' in fake.sent[-1]['text']), ('undone', ['price-1103'], True))
# ... live: the version before goes back live
st.pop('undone', None); json.dump(st, open(os.path.join(st['home'], 'state.json'), 'w'))
git(repo, 'checkout', '-q', '-b', 'hive/price-1103'); open(os.path.join(repo, 'app.py'), 'a').write('# rupees\n'); git(repo, 'add', '.')
c('commit', '-qm', 'built'); git(repo, 'checkout', '-q', 'main'); old = git(repo, 'rev-parse', 'HEAD').stdout.strip()
# 4. pull requests the engineer enjoys: screenshots and what changed, with his words
body = ship.body(dict(st, goal='Show prices in rupees'), repo, [('/', '.hive/screens/01_home.png')], ('github.com', 'acme/shop'))
check('the pull request shows how it looks and what changed', ('github.com/acme/shop/blob/hive/price-1103/.hive/screens/01_home.png?raw=true' in body,
      '**What changed**' in body, 'app.py' in body, 'Show prices in rupees' in body), (True, True, True, True))

check('his latest build, not merged yet: the next build goes on top of it (Gate 107)', (assistant._unmerged(repo) or {}).get('name'), 'price-1103')
c('merge', '-q', 'hive/price-1103')
check('once merged, the next build starts from his main', assistant._unmerged(repo), None)
deploy.setup(repo, 'vercel'); deploy.shutil.which = lambda n: '/usr/bin/' + n
ran = []
deploy._run = lambda cmd, cwd, timeout=900: ran.append(git(cwd, 'rev-parse', 'HEAD').stdout.strip()) or subprocess.CompletedProcess(cmd, 0, 'https://shop.acme.app\n', '')
deploy.live(repo, old); deploy.live(repo, 'main')   # what was live, then this build
fake = FakeTelegram([tap('und|yes')])
check('live: the version before goes back live', (assistant.handle(ch(fake), repo, 'undo that', poll=1), ran[-1] == old,
      'back to how it was' in fake.sent[-1]['text']), ('undone_live', True, True))

# 5. his code from its address: fetched once into its own folder, brought up to date after
here = doctor.fetch_repo(repo)
check('his code fetched from its address, then brought up to date', (os.path.isdir(os.path.join(here, '.git')), doctor.fetch_repo(repo) == here),
      (True, True))

# 6. the company brain: a document he sends is read; what lasts is kept, and rules plainly stated become his rules
doc = os.path.join(home, 'policy.md')
open(doc, 'w', encoding='utf-8').write('# Creator policy\nNew creators get ₹500 extra on their first completed deal.\nRefunds go back to the card.\n')
real = explain.ask_json
explain.ask_json = lambda prompt, **k: {'facts': ['New creators get ₹500 extra on their first completed deal.'],
                                       'rules': ['Refunds go back to the card.']} if 'Here is a document' in prompt else real(prompt, **k)
fake = FakeTelegram([])
r = assistant.handle(ch(fake), repo, f'our policy [document: {doc} | policy.md]', poll=1)
check('a document he sends: facts kept for plans, rules kept as his rules', (r, memory.notes(repo)[-1], [x['text'] for x in memory.load(repo)],
      'Read and kept' in fake.sent[-1]['text']),
      ('document', 'New creators get ₹500 extra on their first completed deal.', ['Refunds go back to the card.'], True))
explain.ask_json = real
check("a kind it can't read is said plainly", brain.learn(repo, os.path.join(home, 'x.bin')), None)
# 7. a build folded into a newer one is set aside (its pull request withdrawn), not offered again
st.pop('undone', None); st['shipped'] = 1; json.dump(st, open(os.path.join(st['home'], 'state.json'), 'w')); closed.clear()
assistant._fold(repo, st)
check('folded into a newer build: set aside, its pull request withdrawn', (assistant.latest_build(repo), closed), (None, ['price-1103']))
sys.exit(fail)
