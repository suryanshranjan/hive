"""Real Docker boundary checks with stand-in code, no models or account credentials.

Run on the Docker host: python tests/test_sandbox_docker.py
"""
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, os.getcwd())
from hive import sandbox, run


def main():
    if not sandbox.running():
        raise SystemExit('Docker is required for this integration check')
    with tempfile.TemporaryDirectory(prefix='hive_docker_boundary_') as folder:
        root = Path(folder) / 'run'
        first, second = root / 'work' / 'w1', root / 'work' / 'w2'
        first.mkdir(parents=True); second.mkdir(parents=True)
        (first / 'own.txt').write_text('first')
        (second / 'own.txt').write_text('second')
        (root / '.logins').mkdir()
        (root / '.logins' / 'other-agent-secret').write_text('SHOULD-NOT-BE-VISIBLE')
        for work in (first, second):
            subprocess.run(['git', 'init', '-q', str(work)], check=True)
        code = """
import os
assert os.environ.get('TELEGRAM_BOT_TOKEN') is None
assert os.environ.get('HIVE_TTS_KEY') is None
assert not os.path.exists('/opt/hive/private')
assert not os.path.exists('/hive-run/.logins/other-agent-secret')
open('result.txt', 'w').write('my worktree is writable')
for path in ('/hive-run/work/w2/own.txt', '/opt/hive/hive/__init__.py'):
    try:
        with open(path, 'a') as f: f.write('not allowed')
    except OSError:
        pass
    else:
        raise AssertionError('unexpected write access: ' + path)
print('worker isolation passed')
"""
        with patch.dict(os.environ, {'HIVE_SANDBOX_CUSTOM': '0'}):
            cmd, env = sandbox.command(str(root), 'w1', 'python3 -c ' + shlex.quote(code),
                dict(os.environ, TELEGRAM_BOT_TOKEN='SENTINEL', HIVE_TTS_KEY='SENTINEL'), agent='none')
        result = run.run(cmd, 60, env=sandbox.popen_env(os.environ, env))
        assert result and result.returncode == 0, (result.stderr if result else 'worker timeout')
        assert (first / 'result.txt').exists()
        assert (second / 'own.txt').read_text() == 'second'
        print('PASS real worker: private data hidden, secrets filtered, sibling and package writes denied', flush=True)
        command = 'python3 -c ' + shlex.quote('import time; time.sleep(60)')
        removed = []
        original = sandbox._docker
        def recording(args, **kwargs):
            if args[:2] == ['rm', '-f']:
                removed.append(args[2])
            return original(args, **kwargs)
        with patch.object(sandbox, '_docker', side_effect=recording):
            assert sandbox.run_project(command, str(first), 2) is None
        assert removed
        active = sandbox._docker(['ps', '--filter', 'name=' + removed[-1], '--format', '{{.Names}}'])
        assert active and not active.stdout.strip(), 'timed-out verification container remained running'
        print('PASS real project timeout: verification container removed', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
