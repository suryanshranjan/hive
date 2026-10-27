"""hive: run silent coding-agent swarms on any repository with tests.

usage:
  python -m hive init --test-cmd "<command that runs all tests and writes JUnit XML to .hive/junit.xml>"
  python -m hive claim <short_name> <area>[,<area>...] "<what you will build>"
  python -m hive land <short_name> "<commit message>"      # or: python -m hive land <short_name> --continue
  python -m hive areas                                      # every area and who holds it
  python -m hive run --repo <repo> --run <new folder> --workers N --goal <goal.md or text> [--minutes 40] [--max-parallel N]
"""
import argparse, json, os, sys

from . import claims, guard, swarm

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
    c = sub.add_parser('claim'); c.add_argument('name'); c.add_argument('areas'); c.add_argument('desc')
    l = sub.add_parser('land'); l.add_argument('name'); l.add_argument('message')
    sub.add_parser('areas')
    r = sub.add_parser('run'); r.add_argument('--repo', default='.'); r.add_argument('--run', required=True)
    r.add_argument('--workers', type=int, required=True); r.add_argument('--goal', required=True)
    r.add_argument('--minutes', type=int, default=40); r.add_argument('--max-parallel', type=int, default=0)
    a = ap.parse_args(argv)
    if a.cmd == 'init':
        return init(a.test_cmd, a.junit)
    if a.cmd == 'claim':
        return claims.claim(a.name, a.areas, a.desc)
    if a.cmd == 'land':
        return guard.land(a.name, a.message)
    if a.cmd == 'areas':
        return claims.status()
    if a.cmd == 'run':
        swarm.prepare(a.repo, a.run, a.workers, a.goal, a.minutes)
        return swarm.launch(a.run, a.max_parallel)

if __name__ == '__main__':
    sys.exit(main())
