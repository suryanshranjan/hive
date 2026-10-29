"""hive: a team of AI builders you direct by talking. It asks in plain words, never breaks what works,
and hands back a tested branch.

For the owner:
  hive                                   start: Hive asks what to build and does the rest
  hive start [--docs <folder>] [--overnight] [--no-interview] [--workers N] [--goal <text or file>] [--minutes 40]
             [--agent claude|codex|gemini|antigravity] [--save-agent]   which coding agent builds (default Claude Code)
  hive morning [--phone]                 after an overnight build: check its decisions (on Telegram with --phone)
  hive listen                            stay on Telegram: change your mind, "build: ...", "status"
  hive rules [forget <n>]                your standing rulings for this project
  hive name ["Sunny Shop"]               what Hive calls this project (your startup's name)
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

class Parser(argparse.ArgumentParser):
    """argparse, with plain answers to mistakes: the closest real option ("did you mean --goal?") and this command's
    usage (a comment once swallowed --goal, and every build from the phone failed on "unrecognized arguments")."""
    def parse_args(self, args=None, namespace=None):
        self._argv = list(sys.argv[1:] if args is None else args)
        a = super().parse_args(args, namespace)
        if getattr(a, 'cmd', None) == 'cloud':   # one thing at a time: make, delete, move to a server, or bring back
            chosen = [n for n, on in (('--new', a.new), ('--stop', a.stop), ('--to', a.to), ('pull', a.action == 'pull')) if on]
            if len(chosen) > 1:
                self._argv = ['cloud']
                self.error(f"choose one of {', '.join(chosen)}, not several")
        return a

    def error(self, message):
        import difflib, re
        known = [o for a in self._actions for o in a.option_strings]
        subs = next((a.choices for a in self._actions if isinstance(a, argparse._SubParsersAction)), {})
        cmd = next((w for w in getattr(self, '_argv', []) if w in subs), None)
        if cmd:   # an option the subcommand does not know is reported up here: suggest from the subcommand's own
            known += [o for a in subs[cmd]._actions for o in a.option_strings]
            self.prog = f'{self.prog} {cmd}'
        hints = []
        for bad in re.findall(r'(--?[\w-]+)', message.split(':', 1)[-1]) if 'unrecognized' in message else []:
            close = difflib.get_close_matches(bad, known, n=1, cutoff=0.6)
            if close:
                hints.append(f'Did you mean {close[0]} (not {bad})?')
        wrong = re.search(r"invalid choice: '([^']+)'", message)
        if wrong:   # "hive strat": the closest command, not the whole list
            choices = list(subs) or [c.strip(" '()") for c in message.split('choose from', 1)[-1].split(',')]
            close = difflib.get_close_matches(wrong.group(1), [c for c in choices if isinstance(c, str)], n=1, cutoff=0.5)
            if close:
                opt = re.search(r'argument (--?[\w-]+)', message)   # a value for an option: suggest it with the option
                message = (f"'{wrong.group(1)}' is not a hive command" if subs else
                           f"'{wrong.group(1)}' is not one of: {', '.join(choices)}")
                hints.append(f'Did you mean `{self.prog} {opt.group(1) + " " if opt else ""}{close[0]}`?')
        self.print_usage(sys.stderr)
        sys.stderr.write(f"{self.prog}: {message}\n" + ''.join(h + '\n' for h in hints) +
                         f"Run `{self.prog} --help` to see every option.\n")
        sys.exit(2)

def positive(text):
    """A whole number of at least 1 (builders, minutes, questions)."""
    try:
        n = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{text}' is not a whole number")
    if n < 1:
        raise argparse.ArgumentTypeError(f"it must be at least 1 (got {n})")
    return n

def existing(text):
    """A file or folder that is there."""
    if not os.path.exists(text):
        raise argparse.ArgumentTypeError(f"there is no file or folder at '{text}'")
    return text

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

def _start(a):
    if getattr(a, 'agent', None):   # builders run on the chosen agent (swarm.builder_cmd reads it)
        os.environ['HIVE_AGENT'] = a.agent
        if getattr(a, 'save_agent', False):
            os.makedirs(os.path.join(os.path.expanduser('~'), '.hive'), exist_ok=True)
            open(os.path.join(os.path.expanduser('~'), '.hive', 'agent'), 'w').write(a.agent)
    return start.start('.', getattr(a, 'workers', None), getattr(a, 'goal', None), getattr(a, 'minutes', 40),
                           getattr(a, 'overnight', False), not getattr(a, 'no_interview', False), getattr(a, 'docs', None))

def build_parser():
    ap = Parser(prog='hive', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', parser_class=Parser)
    st = sub.add_parser('start'); st.add_argument('--goal')
    st.add_argument('--workers', type=positive)   # default: the swarm law decides (a comment here once swallowed --goal)
    st.add_argument('--minutes', type=positive, default=40)
    st.add_argument('--docs', type=existing)   # the company's own documents: a file or a folder
    st.add_argument('--agent', choices=['claude', 'codex', 'gemini', 'antigravity'])   # which coding agent builds
    st.add_argument('--save-agent', action='store_true')   # remember --agent for every build on this computer
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
    sub.add_parser('name').add_argument('name', nargs='*')
    ru = sub.add_parser('rules'); ru.add_argument('action', nargs='?', choices=['forget']); ru.add_argument('n', nargs='?', type=int)
    i = sub.add_parser('init'); i.add_argument('--test-cmd', required=True); i.add_argument('--junit', default='.hive/junit.xml')
    c = sub.add_parser('claim'); c.add_argument('name'); c.add_argument('areas'); c.add_argument('desc')
    l = sub.add_parser('land'); l.add_argument('name'); l.add_argument('message', nargs='?')
    l.add_argument('--continue', dest='cont', action='store_true')   # after fixing a conflict or a blocked landing
    l.add_argument('--note', help='one line the other builders should know (a shared helper, a changed interface)')
    nt = sub.add_parser('notes'); nt.add_argument('-n', type=int, default=8)
    sub.add_parser('areas')
    r = sub.add_parser('run'); r.add_argument('--repo', default='.'); r.add_argument('--run', required=True)
    r.add_argument('--workers', type=positive, required=True); r.add_argument('--goal', required=True)
    r.add_argument('--minutes', type=positive, default=40); r.add_argument('--max-parallel', type=int, default=0)
    r.add_argument('--examples'); r.add_argument('--questions', type=int); r.add_argument('--assumptions', action='store_true')
    o = sub.add_parser('owner'); o.add_argument('--run', required=True)
    q = sub.add_parser('ask'); q.add_argument('question'); q.add_argument('--timeout', type=int, default=30)
    sub.add_parser('answers')
    v = sub.add_parser('review'); v.add_argument('--run', required=True)
    s_ = sub.add_parser('assume'); s_.add_argument('text'); s_.add_argument('--technical', action='store_true')
    sub.add_parser('assumptions')
    return ap

def main(argv=None):
    ap = build_parser()
    a = ap.parse_args(argv)
    if a.cmd in (None, 'start'):
        try:
            return _start(a)
        except telegram.Stopped:   # he said "stop" mid-question; he has been told
            return 0
    if a.cmd == 'listen':
        from . import assistant
        from . import cloud_aws
        return assistant.listen('.', apply_build=start.apply_ruling,
                                start_build=lambda repo, goal: assistant.background_build(repo, goal),   # Hive keeps answering meanwhile
                                cloud=lambda repo, on, login=True: cloud_aws.new(repo, with_login=login) if on else
                                cloud_aws.stop(ask=lambda q: 'y' if q.startswith(('Delete the Hive machine', 'Power this')) else 'n',
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
    if a.cmd == 'name':
        from . import memory
        if a.name:
            memory.set_name('.', ' '.join(a.name)); print(f"Got it: I'll call this project {' '.join(a.name)}."); return 0
        n = memory.project_name('.')
        print(f'This project is {n}.' if n else "No name yet. Tell me your startup's name: hive name \"Sunny Shop\""); return 0
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
