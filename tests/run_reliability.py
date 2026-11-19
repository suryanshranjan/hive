"""Repeatable local regression run, using only controlled fixtures and fake services.

--fixture-execution permits the suites' known temporary test programs to run in
the test process. It does not validate Docker isolation or run Hive against accounts.
"""
import argparse
import os
import re
import subprocess
import sys

SUITES = ('reliability', 'tasks', 'action_boundaries', 'adaptive', 'dispatcher', 'connectors', 'store', 'memory2', 'tools', 'office', 'router', 'pulse', 'brief', 'telegram',
          'google', 'calendar', 'sandbox_unit', 'ship', 'deploy', 'audit', 'runlimit', 'vault', 'render',
          'register', 'plan')
EXTRA = ('schedules', 'handoff', 'gateway', 'build_receipts', 'assistant', 'explain', 'law', 'cli', 'team', 'visual', 'complaint', 'gaps', 'access', 'onboard',
         'devices', 'away', 'logins', 'trydeploy', 'fast', 'aws_limit', 'voice')
SHELL = ('guard', 'claims', 'run', 'owner', 'assume', 'start', 'doctor', 'cloud')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture-execution', action='store_true')
    parser.add_argument('--all', action='store_true', help='Include every Python regression script')
    parser.add_argument('--shell', action='store_true', help='Also run the legacy shell fixture suites')
    parser.add_argument('--shell-suite', action='append', choices=SHELL, help='Run only selected shell suites')
    parser.add_argument('--suite', action='append', choices=SUITES + EXTRA, help='Run only selected suites')
    args = parser.parse_args()
    env = dict(os.environ, HIVE_EMBED='0', HIVE_TTS='off', PYTHONIOENCODING='utf-8')
    if args.fixture_execution:
        env['IS_SANDBOX'] = '1'
    failures = []
    suites = args.suite or (SUITES + EXTRA if args.all else SUITES)
    commands = [(name, [sys.executable, '-B', f'tests/test_{name}.py'], 120) for name in suites]
    if args.shell or args.shell_suite:
        commands += [(f'shell/{name}', ['bash', f'tests/test_{name}.sh'], 300) for name in args.shell_suite or SHELL]
    for name, command, timeout in commands:
        try:
            result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8',
                                    errors='replace', env=env, timeout=timeout)
            if result.returncode:
                failures.append(name)
                print(f'FAIL {name}\n{result.stdout}\n{result.stderr}', flush=True)
            else:
                count = re.search(r'Ran (\d+) tests', result.stderr)
                suffix = f' ({count[1]} tests)' if count else ''
                print(f'PASS {name}{suffix}', flush=True)
        except subprocess.TimeoutExpired:
            failures.append(name)
            print(f'TIMEOUT {name}', flush=True)
    print(f'{len(commands) - len(failures)}/{len(commands)} suites passed. Failed: {", ".join(failures) or "none"}', flush=True)
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
