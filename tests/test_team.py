"""The builders from the phone: the board (who, which agent, doing what, landed what), Jarvis knowing it, choosing the
team for the next build, and stopping one builder (its claim is freed). A real git upstream and real processes; a fake
Telegram and a stand-in model.
usage: python3 tests/test_team.py   (run from the hive repo root)"""
import json, os, subprocess, sys, tempfile, time
sys.path.insert(0, os.getcwd())
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home
from hive import assistant, explain, memory, team, telegram
explain.CMD = '"' + sys.executable.replace(chr(92), '/') + '" tests/fake_explain.py'
memory.DIR = os.path.join(home, '.hive', 'rules'); telegram.BUSY = os.path.join(home, '.hive', 'telegram.busy')
team.RUNS = os.path.join(home, '.hive', 'runs'); team.TEAM = os.path.join(home, '.hive', 'team.json')
sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
from test_telegram_fake import FakeTelegram, ME, tap, say

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))
ch = lambda fake: telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake)
git = lambda cwd, *a: subprocess.run(['git', '-C', cwd, *a], capture_output=True, text=True)

# a build in progress: w1 (Claude) landed a fees module and finished; w2 (Codex) holds the refund page and is working
run = os.path.join(team.RUNS, 'refunds-1029-1500', 'build'); os.makedirs(run)
seed = os.path.join(home, 'seed'); os.makedirs(os.path.join(seed, 'current_tasks'))
open(os.path.join(seed, 'current_tasks', '.keep'), 'w').close()
git(seed, 'init', '-q', '-b', 'main'); git(seed, 'add', '.'); git(seed, '-c', 'user.name=hive', '-c', 'user.email=h@h', 'commit', '-qm', 'hive: settings')
subprocess.run(['git', 'clone', '-q', '--bare', seed, os.path.join(run, 'up.git')])
w = os.path.join(home, 'w'); subprocess.run(['git', 'clone', '-q', os.path.join(run, 'up.git'), w])
open(os.path.join(w, 'fees.py'), 'w').write('FEE = 0.1\n'); git(w, 'add', '.')
git(w, '-c', 'user.name=w1', '-c', 'user.email=w1@h', 'commit', '-qm', 'Platform fee of 10% on every campaign')
open(os.path.join(w, 'current_tasks', 'refunds.txt'), 'w').write('w2: the refund page for brands\nareas: refunds\n')
git(w, 'add', '.'); git(w, '-c', 'user.name=w2', '-c', 'user.email=w2@h', 'commit', '-qm', 'Lock: refunds (refunds)')
git(w, 'push', '-q', 'origin', 'HEAD:main')
json.dump({'repo': seed, 'branch': 'main', 'workers': 2, 'started': int(time.time()) - 600}, open(os.path.join(run, 'run.json'), 'w'))
p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'])
json.dump({'w1': {'agent': 'claude', 'state': 'finished', 'started': int(time.time()) - 600, 'ended': int(time.time()) - 60},
           'w2': {'agent': 'codex', 'state': 'working', 'pid': p.pid, 'started': int(time.time()) - 540}},
          open(os.path.join(run, 'builders.json'), 'w'))

# speaking up unprompted: a builder working 20 minutes with nothing new landed is reported once; new work resets it
seen = {}
t0 = time.time()
check('nobody is stuck at the first look', team.stuck(run, seen, now=t0), [])
check('after 20 minutes with nothing landed, the working builder is reported',
      [r['name'] for r in team.stuck(run, seen, now=t0 + 21 * 60)], ['w2'])
check('...and only once', team.stuck(run, seen, now=t0 + 40 * 60), [])
os.environ.update(HIVE_WATCH_SECONDS='0.2', HIVE_STUCK_MINUTES='0.005', HIVE_BUILD_CMD=f'"{sys.executable}" -c "import time; time.sleep(3)"')
fake = FakeTelegram([])
assistant.background_build(seed, 'a refund page', ch(fake))
time.sleep(3.5)
for k in ('HIVE_WATCH_SECONDS', 'HIVE_STUCK_MINUTES', 'HIVE_BUILD_CMD'):
    os.environ.pop(k)
assistant.BUILD.clear()
check('during a build, he is told unprompted when a builder seems stuck, and what he can do',
      sum('w2 (codex) may be stuck, sir.' in m['text'] and 'stop w2' in m['text'] for m in fake.sent), 1)
text = team.board_text(run)
check('the board says each builder, its agent, and what it is doing', (
    'w1 (claude): finished' in text, 'landed 1 piece of work (latest: Platform fee of 10% on every campaign)' in text,
    'w2 (codex): working for 9 min; now building: the refund page for brands' in text), (True, True, True))
check('"which builder" is understood several ways', [team.find(run, s) for s in
      ('stop w2', 'builder 1', 'the second one', 'stop the codex one', 'the gemini one')], ['w2', 'w1', 'w2', 'w2', None])
check('a build running: the status counts only builders that really finished (Codex writes output as it goes)',
      '1 of 2 have finished' in telegram.status_of(run), True)

# Jarvis knows it: the board is part of what it knows while a build runs
assistant.BUILD.update(proc=p, goal='a refund page for brands', started=time.time() - 600)
check('Jarvis has the board in mind while a build runs', 'w2 (codex): working' in assistant.facts(seed), True)

_ask_json = explain.ask_json
def reads(**got):   # the model's reading of his message
    explain.ask_json = lambda prompt: got if 'newest message' in prompt else _ask_json(prompt)

reads(intent='team')
fake = FakeTelegram([])
r = assistant.handle(ch(fake), seed, "who's doing what?", poll=1)
check('"who\'s doing what?" answers from the board', (r, any('refund page' in m['text'] for m in fake.sent)), ('team', True))

reads(intent='set_team', agent='claude,codex', workers=4)
fake = FakeTelegram([])
r = assistant.handle(ch(fake), seed, 'use 2 claude and 2 codex from now on', poll=1)
check('he chooses the team for the next builds', (r, team.chosen(), any(
      '4 builders, on Claude and Codex in turn' in m['text'] and 'keeps its team' in m['text'] for m in fake.sent)),
      ('team_set', {'agent': 'claude,codex', 'workers': 4}, True))
reads(intent='set_team', agent='gpt9', workers=0)
fake = FakeTelegram([])
check('an agent Hive does not know is refused, with the choices', (assistant.handle(ch(fake), seed, 'use gpt9', poll=1),
      any('claude, codex, gemini, antigravity' in m['text'] for m in fake.sent)), ('team_unknown', True))
cmd = []
_popen = subprocess.Popen
class Spy:
    def __init__(self, c, **k): cmd.extend(c); self.pid = 0
    def wait(self): return 0
    def poll(self): return 0
subprocess.Popen = Spy
assistant.background_build(seed, 'a payouts page')
subprocess.Popen = _popen
check('the next build is started with his team', (cmd[cmd.index('--agent') + 1], cmd[cmd.index('--workers') + 1]),
      ('claude,codex', '4'))
assistant.BUILD.update(proc=p, goal='a refund page for brands', started=time.time() - 600)

reads(intent='stop_builder', builder='the codex one')
fake = FakeTelegram([])
r = assistant.handle(ch(fake), seed, 'stop the codex one, it is going in circles', poll=1)
time.sleep(1)
locks = subprocess.run(['git', '--git-dir', os.path.join(run, 'up.git'), 'ls-tree', '--name-only', 'main:current_tasks'],
                       capture_output=True, text=True).stdout.split()
check('stopping one builder: it stops, its claimed work is freed, and he is told what it was on',
      (r, p.poll() is not None, 'refunds.txt' in locks, os.path.exists(os.path.join(run, 'stopped', 'w2')),
       any('Stopped w2 (codex), which was building the refund page for brands' in m['text'] and
           'Another builder can take that work up.' in m['text'] for m in fake.sent)),
      ('builder_stopped', True, False, True, True))
# "I don't need that": the stopped builder's work is not handed to the others; they are told to leave it out
p3 = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
b = json.load(open(os.path.join(run, 'builders.json'))); b['w1'].update(state='working', pid=p3.pid)
json.dump(b, open(os.path.join(run, 'builders.json'), 'w'))
w3 = os.path.join(home, 'w3'); subprocess.run(['git', 'clone', '-q', os.path.join(run, 'up.git'), w3])
open(os.path.join(w3, 'current_tasks', 'fees.txt'), 'w').write('w1: a fee report\nareas: fees\n')
git(w3, 'add', '.'); git(w3, '-c', 'user.name=w1', '-c', 'user.email=w1@h', 'commit', '-qm', 'Lock: fees'); git(w3, 'push', '-q')
reads(intent='stop_builder', builder='w1', drop_work=True)
fake = FakeTelegram([])
assistant.handle(ch(fake), seed, "stop w1, I don't need the fee report", poll=1)
told = subprocess.run(['git', '--git-dir', os.path.join(run, 'up.git'), 'show', 'main:OWNER.md'], capture_output=True, text=True).stdout
check('work he no longer wants is dropped, not handed to the others',
      ('do not build it: a fee report' in told, any("told the others to leave that out" in m['text'] for m in fake.sent)),
      (True, True))
p3.wait()
reads(intent='stop_builder', builder='')
fake = FakeTelegram([])
check('with no builder working, it says so rather than stopping anything',
      (assistant.handle(ch(fake), seed, 'stop that builder', poll=1), fake.sent[-1]['text']),
      ('which_builder', 'No builder is working right now.'))
# the law at the top of the chain: his tests took 60 s last build, so the law says 2; asked for 12, he hears it first
json.dump({'repo': seed, 't_g': 60}, open(os.path.join(team.RUNS, 'refunds-1029-1500', 'state.json'), 'w'))
reads(intent='set_team', agent='', workers=12)
fake = FakeTelegram([tap('law|n')])
r = assistant.handle(ch(fake), seed, 'use 12 builders', poll=1)
check('asked for 12, he first hears the law (2, from his 60 s tests); "use the law" takes 2',
      (r, team.chosen().get('workers'), any('the law says 2 builders' in m['text'] and "won't finish any sooner" in m['text']
                                             for m in fake.sent)), ('team_set', 2, True))
fake = FakeTelegram([say('as I said')])
assistant.handle(ch(fake), seed, 'use 12 builders', poll=1)
check('...and if he insists, it is his call', team.chosen().get('workers'), 12)
reads(intent='set_team', agent='', workers=2)
fake = FakeTelegram([])
assistant.handle(ch(fake), seed, 'use 2 builders', poll=1)
check('a choice the law agrees with is simply taken', (team.chosen().get('workers'), any('law' in m['text'] for m in fake.sent)), (2, False))
reads(intent='set_team', agent='', workers=0)
assistant.handle(ch(FakeTelegram([])), seed, 'let the law decide how many', poll=1)
check('"let the law decide" hands the number back to the law', 'workers' in team.chosen(), False)

# a new direction mid-build reaches the running builders through the shared branch; so does a new standing rule
p2 = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
assistant.BUILD.update(proc=p2, goal='a refund page for brands', started=time.time() - 300)
b = json.load(open(os.path.join(run, 'builders.json')))   # w3 joins, working with nothing claimed yet
b['w3'] = {'agent': 'claude', 'state': 'working', 'pid': p2.pid, 'started': int(time.time()) - 120}
json.dump(b, open(os.path.join(run, 'builders.json'), 'w'))
reads(intent='instruct', rule='also show refunds per month on the page', builder='')
fake = FakeTelegram([])
r = assistant.handle(ch(fake), seed, 'also show refunds per month on the page', poll=1)
owner_md = lambda: subprocess.run(['git', '--git-dir', os.path.join(run, 'up.git'), 'show', 'main:OWNER.md'],
                                  capture_output=True, text=True).stdout
check('a mid-build instruction goes to one builder, the one with least on its plate (OWNER.md on the shared branch)',
      (r, 'to w3: also show refunds per month on the page' in owner_md(), any('Passed to w3' in m['text'] for m in fake.sent)),
      ('instructed', True, True))
# routed by the work it touches: the model reads the board and names the builder, with a reason he sees
reads(intent='instruct', rule='make the refund total bold', builder='')
_reads = explain.ask_json
explain.ask_json = lambda prompt: ({'builder': 'w3', 'why': 'since it is building the refund page'}
                                   if 'Which ONE working builder' in prompt else _reads(prompt))
fake = FakeTelegram([])
assistant.handle(ch(fake), seed, 'make the refund total bold', poll=1)
check('a task goes to the builder whose work it touches, and he is told why',
      any('Passed to w3, since it is building the refund page' in m['text'] for m in fake.sent), True)
explain.ask_json = lambda prompt: ({'builder': 'w9'} if 'Which ONE working builder' in prompt else _reads(prompt))
check('a builder that is not working is never chosen; the least busy is', assistant.route(run, 'anything'), ('w3', ''))
reads(intent='instruct', rule='do the CSV export instead', builder='w1')
r = assistant.handle(ch(FakeTelegram([])), seed, 'w1, do the CSV export instead', poll=1)
check("one addressed to a builder names it, and the newest comes first",
      owner_md().split(chr(10))[2].endswith('to w1: do the CSV export instead'), True)
reads(intent='rule', rule='Refunds over 5,000 rupees need my approval')
fake = FakeTelegram([tap('upd|no')])
assistant.handle(ch(fake), seed, 'from now on refunds over 5,000 rupees need my approval', poll=1)
check('a standing rule given mid-build reaches the builders working now',
      ('A new standing rule from the owner: Refunds over 5,000 rupees need my approval' in owner_md(),
       any('The builders working now have it too.' in m['text'] for m in fake.sent)), (True, True))
p2.kill(); p2.wait(); assistant.BUILD.clear()
reads(intent='instruct', rule='a page of refunds per month', builder='')
started = []
r = assistant.handle(ch(FakeTelegram([tap('bld|yes')])), seed, 'add a page of refunds per month', poll=1,
                     start_build=lambda rp, goal: started.append(goal))
check('with no build running, an instruction becomes a build request (confirmed first)', (r, started),
      ('built', ['a page of refunds per month']))
explain.ask_json = _ask_json; assistant.BUILD.clear()
sys.exit(fail)
