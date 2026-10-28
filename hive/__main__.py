"""hive: run silent coding-agent swarms on any repository with tests.

usage:
  python -m hive                                            # just start: Hive asks what to build and does the rest
  python -m hive start [--workers 4] [--goal <text or file>] [--minutes 40] [--overnight]
  python -m hive morning                                    # after an overnight build: check its assumptions (--phone: on Telegram)
  python -m hive telegram setup                             # once: questions and reviews come to your phone
  python -m hive init --test-cmd "<command that runs all tests and writes JUnit XML to .hive/junit.xml>"
  python -m hive claim <short_name> <area>[,<area>...] "<what you will build>"
  python -m hive land <short_name> "<commit message>"      # or: python -m hive land <short_name> --continue
  python -m hive areas                                      # every area and who holds it
  python -m hive run --repo <repo> --run <new folder> --workers N --goal <goal.md or text> [--minutes 40] [--max-parallel N]
                    [--examples <examples.md>] [--questions N]     # the owner's examples; the team's question budget (0: none)
                    [--assumptions]                                # workers record every default they apply
  python -m hive owner --run <run>                          # the owner answers questions live
  python -m hive review --run <run>                         # the owner checks the workers' assumptions; writes corrections.md
  python -m hive ask "<question>"   /   python -m hive answers   (workers, inside a run)
  python -m hive assume [--technical] "<default>" / python -m hive assumptions   (workers, inside a run)
"""
import argparse, json, os, sys

from . import claims, guard, owner, start, swarm, telegram

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
    sub = ap.add_subparsers(dest='cmd')
    st = sub.add_parser('start'); st.add_argument('--workers', type=int, default=4); st.add_argument('--goal')
    st.add_argument('--minutes', type=int, default=40)
    st.add_argument('--overnight', action='store_true')   # no questions; check the assumptions later with `hive morning`
    mo = sub.add_parser('morning'); mo.add_argument('name', nargs='?'); mo.add_argument('--phone', action='store_true')
    tg = sub.add_parser('telegram'); tg.add_argument('action', choices=['setup', 'test'])
    i = sub.add_parser('init'); i.add_argument('--test-cmd', required=True); i.add_argument('--junit', default='.hive/junit.xml')
    c = sub.add_parser('claim'); c.add_argument('name'); c.add_argument('areas'); c.add_argument('desc')
    l = sub.add_parser('land'); l.add_argument('name'); l.add_argument('message', nargs='?')
    l.add_argument('--continue', dest='cont', action='store_true')   # after fixing a conflict or a blocked landing
    sub.add_parser('areas')
    r = sub.add_parser('run'); r.add_argument('--repo', default='.'); r.add_argument('--run', required=True)
    r.add_argument('--workers', type=int, required=True); r.add_argument('--goal', required=True)
    r.add_argument('--minutes', type=int, default=40); r.add_argument('--max-parallel', type=int, default=0)
    r.add_argument('--examples'); r.add_argument('--questions', type=int); r.add_argument('--assumptions', action='store_true')
    o = sub.add_parser('owner'); o.add_argument('--run', required=True)
    q = sub.add_parser('ask'); q.add_argument('question'); q.add_argument('--timeout', type=int, default=30)
    sub.add_parser('answers')
    v = sub.add_parser('review'); v.add_argument('--run', required=True)
    s_ = sub.add_parser('assume'); s_.add_argument('text'); s_.add_argument('--technical', action='store_true')
    sub.add_parser('assumptions')
    a = ap.parse_args(argv)
    if a.cmd in (None, 'start'):
        return start.start('.', getattr(a, 'workers', 4), getattr(a, 'goal', None), getattr(a, 'minutes', 40),
                           getattr(a, 'overnight', False))
    if a.cmd == 'morning':
        return start.morning(a.name, a.phone)
    if a.cmd == 'telegram':
        return telegram.setup() if a.action == 'setup' else telegram.test()
    if a.cmd == 'init':
        return init(a.test_cmd, a.junit)
    if a.cmd == 'claim':
        return claims.claim(a.name, a.areas, a.desc)
    if a.cmd == 'land':
        if not a.cont and not a.message:
            ap.error('land needs a commit message, or --continue')
        return guard.land(a.name, '--continue' if a.cont else a.message)
    if a.cmd == 'areas':
        return claims.status()
    if a.cmd == 'run':
        swarm.prepare(a.repo, a.run, a.workers, a.goal, a.minutes, a.examples, a.questions, a.assumptions)
        return swarm.launch(a.run, a.max_parallel)
    if a.cmd == 'owner':
        return owner.serve(a.run)
    if a.cmd == 'ask':
        return owner.ask(a.question, a.timeout)
    if a.cmd == 'answers':
        return owner.answers()
    if a.cmd == 'review':
        return owner.review(a.run)
    if a.cmd == 'assume':
        return owner.assume(a.text, a.technical)
    if a.cmd == 'assumptions':
        return owner.assumptions()

if __name__ == '__main__':
    sys.exit(main())
