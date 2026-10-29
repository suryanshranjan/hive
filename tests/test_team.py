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
       any('Stopped w2 (codex)' in m['text'] and 'free again' in m['text'] for m in fake.sent)),
      ('builder_stopped', True, False, True, True))
reads(intent='stop_builder', builder='')
fake = FakeTelegram([])
check('with no builder working, it says so rather than stopping anything',
      (assistant.handle(ch(fake), seed, 'stop that builder', poll=1), fake.sent[-1]['text']),
      ('which_builder', 'No builder is working right now.'))
explain.ask_json = _ask_json; assistant.BUILD.clear()
sys.exit(fail)
