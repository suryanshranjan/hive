"""Run fixtures in a disposable source copy, leaving a Windows checkout untouched."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main():
    source = Path(__file__).resolve().parent.parent
    with tempfile.TemporaryDirectory(prefix='hive_container_source_') as directory:
        target = Path(directory)
        for name in ('hive', 'tests', 'deploy'):
            shutil.copytree(source / name, target / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        # test_assistant compares the reader's intent vocabulary with its published
        # training protocol. Copy that one dependency, never the private lab data.
        fixture = Path('gates/gate48/referee/run48.py')
        (target / fixture).parent.mkdir(parents=True)
        shutil.copy2(source / fixture, target / fixture)
        for name in ('pyproject.toml', 'README.md', 'LICENSE', 'render.yaml', '.dockerignore', '.gitignore',
                     'install.sh', 'install.ps1'):
            if (source / name).exists():
                shutil.copy2(source / name, target / name)
        for script in target.rglob('*.sh'):
            script.write_bytes(script.read_bytes().replace(b'\r\n', b'\n'))
        env = dict(os.environ, PYTHONPATH=str(target))
        return subprocess.call([sys.executable, '-B', 'tests/run_reliability.py', '--fixture-execution', *sys.argv[1:]],
                               cwd=target, env=env)


if __name__ == '__main__':
    raise SystemExit(main())
