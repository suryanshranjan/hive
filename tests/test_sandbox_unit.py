"""hive/sandbox.py without Docker: what goes into a builder's container and what never does (the audit, Nov 15).
The real thing, with Docker: tests/test_sandbox.sh.   usage: python3 tests/test_sandbox_unit.py"""
import os, subprocess, sys, tempfile
sys.path.insert(0, os.getcwd())
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home
for k in ('HIVE_SANDBOX', 'HIVE_SANDBOX_CUSTOM', 'HIVE_HOST', 'IS_SANDBOX'):
    os.environ.pop(k, None)
from hive import sandbox, PY

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))

run = os.path.join(home, 'runs', 'r1'); work = os.path.join(run, 'work', 'w1'); os.makedirs(work)
subprocess.run(['git', 'init', '-q', work]); subprocess.run(['git', '-C', work, 'remote', 'add', 'origin', os.path.join(run, 'up.git')])
base = {'ANTHROPIC_API_KEY': 'sk-ant', 'OPENAI_API_KEY': 'sk-oa', 'TELEGRAM_BOT_TOKEN': 'bot', 'GITHUB_TOKEN': 'gh',
        'HIVE_MASTER_KEY': 'mk', 'HIVE_FAST_KEY': 'fk', 'HIVE_SUITE_TIMEOUT': '60', 'AWS_SECRET_ACCESS_KEY': 'aws',
        'PATH': '/usr/bin', 'HIVE_RUN': run}
env = sandbox.env_for(base, 'w1')
check('model keys and run settings go in', (env['ANTHROPIC_API_KEY'], env['OPENAI_API_KEY'], env['HIVE_SUITE_TIMEOUT']),
      ('sk-ant', 'sk-oa', '60'))
check('his secrets and this computer\'s paths never do', [k for k in ('TELEGRAM_BOT_TOKEN', 'GITHUB_TOKEN', 'HIVE_MASTER_KEY',
      'HIVE_FAST_KEY', 'AWS_SECRET_ACCESS_KEY', 'PATH') if k in env], [])
check('the run is /hive-run inside', (env['HIVE_RUN'], env['HIVE_GUARD_CACHE'], env['HIVE_WORKER']),
      ('/hive-run', '/hive-run/guard_cache', 'w1'))

prompt = f'Work in {work}. Log to {os.path.join(run, "logs", "w1.log")}. Run `{PY} -m hive land w1 "msg"`.'
inner = sandbox.inside(prompt, run)
check('the prompt names the container\'s paths, not this computer\'s', (run in inner, '/hive-run/work/w1' in inner,
      'python3 -m hive land' in inner), (False, True, True))

os.makedirs(os.path.join(home, '.claude')); open(os.path.join(home, '.claude', '.credentials.json'), 'w').write('{"t": 1}')
open(os.path.join(home, '.claude', 'history.jsonl'), 'w').write('his other sessions')
cmd, denv = sandbox.command(run, 'w1', 'claude -p', base, agent='claude')
flat = ' '.join(cmd)
check('one container per builder, removed when done, named for the board', ('--rm' in cmd, sandbox.name(run, 'w1') in cmd), (True, True))
check('it sees the run folder and Hive\'s code read-only, nothing of his home', (f'{sandbox.host_path(run)}:/hive-run' in flat,
      ':/opt/hive/hive:ro' in flat, f'{sandbox.host_path(home)}:' in flat.replace(sandbox.host_path(run), '')), (True, True, False))
check('its login is a copy, with only the login in it', (os.path.exists(os.path.join(run, '.logins', 'claude', '.claude', '.credentials.json')),
      os.path.exists(os.path.join(run, '.logins', 'claude', '.claude', 'history.jsonl'))), (True, False))
check('no key value on the docker command line', any(v in flat for v in ('sk-ant', 'sk-oa', 'bot', 'gh', 'mk')), False)
check('the upstream is mapped to /hive-run/up.git, and the run folder trusted', ('insteadOf' in cmd[-1], "safe.directory '*'" in cmd[-1]), (True, True))
penv = sandbox.popen_env(dict(base, SYSTEMROOT='C:/Windows'), denv)
check('the docker process gets what it passes in, plus PATH; not his other secrets',
      ('TELEGRAM_BOT_TOKEN' in penv, penv.get('ANTHROPIC_API_KEY'), 'PATH' in penv), (False, 'sk-ant', True))
sandbox.forget_logins(run)
check('the copies go with the run', os.path.exists(os.path.join(run, '.logins')), False)

said = []
for mode in ('off', 'auto', 'docker'):
    os.environ['HIVE_SANDBOX'] = mode
    sandbox.running = lambda: False
    try:
        sandbox.decide(run, 't', 'j', base, said.append)
        stopped = False
    except SystemExit:
        stopped = True
    check(f'{mode}: no unisolated fallback', stopped, True)
try:
    sandbox.decide(run, 't', 'j', base, said.append, custom=True)
    stopped = False
except SystemExit:
    stopped = True
check('custom workers cannot bypass isolation', stopped, True)
sys.exit(fail)
