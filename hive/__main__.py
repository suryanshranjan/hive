"""hive: run silent coding-agent swarms on any repository with tests.

usage:
  python -m hive init --test-cmd "<command that runs all tests and writes JUnit XML to .hive/junit.xml>"
  python -m hive land <short_name> "<commit message>"      # or: python -m hive land <short_name> --continue
"""
import argparse, json, os, sys

from . import guard

def init(test_cmd, junit):
    os.makedirs('.hive', exist_ok=True); os.makedirs(guard.LOCK_DIR, exist_ok=True)
    path = os.path.join('.hive', 'config.json')
    cfg = json.load(open(path)) if os.path.exists(path) else {}
    cfg.update({'test_cmd': test_cmd, 'junit': junit}); cfg.setdefault('snapshot_links', []); cfg.setdefault('areas', {})
    json.dump(cfg, open(path, 'w'), indent=1)
    keep = os.path.join(guard.LOCK_DIR, '.keep'); open(keep, 'a').close()
    ignore = open('.gitignore').read() if os.path.exists('.gitignore') else ''
    if junit not in ignore.split('\n'):
        open('.gitignore', 'a').write(('' if ignore.endswith('\n') or not ignore else '\n') + junit + '\n')
    print(f'wrote {path}; lock folder {guard.LOCK_DIR}/; {junit} ignored by git')

def main(argv=None):
    ap = argparse.ArgumentParser(prog='hive', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    i = sub.add_parser('init'); i.add_argument('--test-cmd', required=True); i.add_argument('--junit', default='.hive/junit.xml')
    l = sub.add_parser('land'); l.add_argument('name'); l.add_argument('message')
    a = ap.parse_args(argv)
    if a.cmd == 'init':
        return init(a.test_cmd, a.junit)
    if a.cmd == 'land':
        return guard.land(a.name, a.message)

if __name__ == '__main__':
    sys.exit(main())
