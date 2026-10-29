"""hive: a team of AI builders you direct by talking. It asks in plain words, never breaks what works,
and hands back a tested branch.

For the owner:
  hive                                   start: Hive asks what to build and does the rest
  hive start [--docs <folder>] [--overnight] [--no-interview] [--workers N] [--goal <text or file>] [--minutes 40]
  hive morning [--phone]                 after an overnight build: check its decisions (on Telegram with --phone)
  hive listen                            stay on Telegram: change your mind, "build: ...", "status"
  hive rules [forget <n>]                your standing rulings for this project
  hive setup                             first run: checks, then your phone, voice and a backup model
  hive doctor                            check this machine and project are ready
  hive telegram setup | test | call <name>   connect your phone; how Hive addresses you
  hive llm setup                         optional: a backup model (e.g. NVIDIA NIM) for plain words
  hive cloud --new [--size t3.large]     one step: make a machine on your AWS account and move Hive there
  hive cloud --stop                      delete that machine (nothing left running or billing)
  hive cloud --to user@host [--with-login]   move this project's Hive to a server you already have
  hive cloud pull [--from user@host]     bring the result branches back

Step by step (scripts and experiments):
  hive init --test-cmd "<runs all tests, writes JUnit XML to .hive/junit.xml>"
  hive run --repo <repo> --run <new folder> --workers N --goal <goal.md or text> [--minutes 40]
           [--max-parallel N] [--examples <examples.md>] [--questions N] [--assumptions]
  hive owner --run <run>                 answer the builders' questions live
  hive review --run <run>                check the builders' decisions; writes corrections.md

For the builders, inside a run:
  hive claim <name> <area>[,<area>...] "<what you will build>"     hive areas
  hive land <name> "<commit message>" [--note "<one line for the team>"]   (or: hive land <name> --continue)
  hive notes                             the latest team notes on the shared branch
  hive ask "<question>"                  hive answers
  hive assume [--technical] "<default>"  hive assumptions
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
    st = sub.add_parser('start'); st.add_argument('--workers', type=int)   # default: the swarm law decides; st.add_argument('--goal')
    st.add_argument('--minutes', type=int, default=40)
    st.add_argument('--docs')   # the company's own documents: a file or a folder
    st.add_argument('--overnight', action='store_true'); st.add_argument('--no-interview', action='store_true')   # no questions; check the assumptions later with `hive morning`
    sub.add_parser('doctor'); sub.add_parser('setup')
    sub.add_parser('listen')
    cl = sub.add_parser('cloud'); cl.add_argument('action', nargs='?', choices=['pull']); cl.add_argument('--to')
    cl.add_argument('--from', dest='frm'); cl.add_argument('--with-login', action='store_true'); cl.add_argument('--no-start', action='store_true')
    cl.add_argument('--new', action='store_true'); cl.add_argument('--stop', action='store_true')   # make / delete an AWS machine
    cl.add_argument('--no-login', action='store_true')   # --new brings the Claude login (builders work there) unless this
    cl.add_argument('--size', default='t3.large'); cl.add_argument('--region'); cl.add_argument('--profile')
    mo = sub.add_parser('morning'); mo.add_argument('name', nargs='?'); mo.add_argument('--phone', action='store_true')
    tg = sub.add_parser('telegram'); tg.add_argument('action', choices=['setup', 'test', 'call', 'ask', 'verdicts'])
    tg.add_argument('address', nargs='?'); tg.add_argument('--out'); tg.add_argument('--intro')
    lm = sub.add_parser('llm'); lm.add_argument('action', choices=['setup'])
    ru = sub.add_parser('rules'); ru.add_argument('action', nargs='?', choices=['forget']); ru.add_argument('n', nargs='?', type=int)
    i = sub.add_parser('init'); i.add_argument('--test-cmd', required=True); i.add_argument('--junit', default='.hive/junit.xml')
    c = sub.add_parser('claim'); c.add_argument('name'); c.add_argument('areas'); c.add_argument('desc')
    l = sub.add_parser('land'); l.add_argument('name'); l.add_argument('message', nargs='?')
    l.add_argument('--continue', dest='cont', action='store_true')   # after fixing a conflict or a blocked landing
    l.add_argument('--note', help='one line the other builders should know (a shared helper, a changed interface)')
    nt = sub.add_parser('notes'); nt.add_argument('-n', type=int, default=8)
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
        return start.start('.', getattr(a, 'workers', None), getattr(a, 'goal', None), getattr(a, 'minutes', 40),
                           getattr(a, 'overnight', False), not getattr(a, 'no_interview', False), getattr(a, 'docs', None))
    if a.cmd == 'listen':
        from . import assistant
        from . import cloud_aws
        return assistant.listen('.', apply_build=start.apply_ruling,
                                start_build=lambda repo, goal: assistant.background_build(repo, goal),   # Hive keeps answering meanwhile
                                cloud=lambda repo, on, login=True: cloud_aws.new(repo, with_login=login) if on else
                                cloud_aws.stop(ask=lambda q: 'y' if q.startswith('Delete the Hive machine') else 'n',
                                               relisten=False))   # this listener is already here   # never 'lose the work'
    if a.cmd == 'cloud':
        from . import cloud
        if a.action == 'pull':
            return cloud.pull('.', a.frm)
        if a.new or a.stop:
            from . import cloud_aws
            return cloud_aws.stop() if a.stop else cloud_aws.new('.', a.size, a.region, a.profile, not a.no_login, not a.no_start)
        return cloud.go('.', a.to, a.with_login, not a.no_start)
    if a.cmd in ('doctor', 'setup'):
        from . import doctor
        return doctor.main('.') if a.cmd == 'doctor' else doctor.setup('.')
    if a.cmd == 'morning':
        return start.morning(a.name, a.phone)
    if a.cmd == 'rules':
        from . import memory
        return memory.forget('.', a.n or 0) if a.action == 'forget' else memory.show('.')
    if a.cmd == 'llm':
        from . import explain
        return explain.setup_backup()
    if a.cmd == 'telegram':
        if a.action == 'call':
            return telegram.call(a.address or '')
        if a.action == 'ask':
            return telegram.ask_cli(a.address or '', a.out or 'answers.json')
        if a.action == 'verdicts':
            return telegram.verdicts_cli(a.address, a.out or 'verdicts.json', a.intro)
        return telegram.setup() if a.action == 'setup' else telegram.test()
    if a.cmd == 'init':
        return init(a.test_cmd, a.junit)
    if a.cmd == 'claim':
        return claims.claim(a.name, a.areas, a.desc)
    if a.cmd == 'land':
        if not a.cont and not a.message:
            ap.error('land needs a commit message, or --continue')
        return guard.land(a.name, '--continue' if a.cont else a.message, a.note)
    if a.cmd == 'notes':
        return guard.show_notes(a.n)
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
