"""hive/run.py: a time limit that holds, children included (the audit, Nov 15: the test suite and builders had none).
usage: python3 tests/test_runlimit.py   (run from the hive repo root)"""
import os, subprocess, sys, tempfile, time
sys.path.insert(0, os.getcwd())
from hive import run, swarm

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))

py = sys.executable
p = run.run([py, '-c', 'print("hi")'], timeout=30)
check('a quick command: its output, as subprocess.run gives it', (p.returncode, p.stdout.strip()), (0, 'hi'))

# a shell that starts a child which outlives it: both must stop at the limit, and the call must return
d = tempfile.mkdtemp(); mark = os.path.join(d, 'child_still_running')
child = f'import time; time.sleep(6); open(r"{mark}", "w").write("x")'
t0 = time.time()
got = run.run(f'"{py}" -c "import subprocess, sys, time; subprocess.Popen([sys.executable, \'-c\', {child!r}]); time.sleep(60)"',
              timeout=2, shell=True)
took = time.time() - t0
check('past its limit: None, returned within seconds', (got, took < 20), (None, True))
time.sleep(7)
check('the child it started was stopped too', os.path.exists(mark), False)

try:
    run.run([py, '-c', 'pass'], timeout=0); refused = False
except ValueError:
    refused = True
check('a run without a time limit is refused', refused, True)
os.environ['HIVE_X_SECONDS'] = 'nonsense'
check('a bad limit in the environment falls back to the default', run.seconds('HIVE_X_SECONDS', 30), 30)

# builders never see Hive's own secrets; they keep the model keys they run on
env = swarm.builder_env({'ANTHROPIC_API_KEY': 'a', 'OPENAI_API_KEY': 'o', 'TELEGRAM_BOT_TOKEN': 't', 'GITHUB_TOKEN': 'g',
                         'AWS_SECRET_ACCESS_KEY': 's', 'HIVE_MASTER_KEY': 'm', 'HIVE_FAST_KEY': 'f', 'PATH': '/bin'})
check('builders: model keys and PATH kept, Hive\'s secrets removed', sorted(env), ['ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'PATH'])
# Codex builds are priced, so they count against his cap; past it, no more builders are started (the audit, Nov 15)
check('Codex tokens priced: 1M in, 100k out at the default 1.25/10', swarm.codex_cost(1_000_000, 100_000), 2.25)
h = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = h
from hive import budget
budget.PATH = os.path.join(h, '.hive', 'budget.json')
check('no cap: never stops', swarm.over_budget(500), None)
budget.set_cap(10)
check('within the cap and its margin: carries on', swarm.over_budget(11.5), None)
check('past it: a plain sentence, and no more builders', 'not starting more builders' in (swarm.over_budget(12.5) or ''), True)
sys.exit(fail)
