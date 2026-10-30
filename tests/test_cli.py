"""Hive's command line: every documented command and option parses (a comment once swallowed --goal and every build
from the phone failed), and every mistake gets a plain answer: the closest option or command, and checked values.
usage: python3 tests/test_cli.py   (run from the hive repo root)"""
import contextlib, io, os, sys, tempfile
sys.path.insert(0, os.getcwd())
from hive.__main__ import build_parser

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))

def parse(*argv):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        try:
            return build_parser().parse_args(list(argv)), ''
        except SystemExit:
            return None, err.getvalue()

docs = tempfile.mkdtemp()
# every usage line of `hive --help`, with each of its options
ok = [
    (['start'], {'cmd': 'start'}),
    (['start', '--goal', 'a refund page', '--workers', '3', '--minutes', '20', '--docs', docs, '--overnight', '--no-interview'],
     {'goal': 'a refund page', 'workers': 3, 'minutes': 20, 'docs': docs, 'overnight': True, 'no_interview': True}),
    (['start', '--agent', 'codex', '--save-agent'], {'agent': 'codex', 'save_agent': True}),
    (['morning', 'b1', '--phone'], {'name': 'b1', 'phone': True}),
    (['listen'], {'cmd': 'listen'}), (['rules'], {'cmd': 'rules'}), (['rules', 'forget', '3'], {'action': 'forget', 'n': 3}),
    (['setup'], {'cmd': 'setup'}), (['doctor'], {'cmd': 'doctor'}),
    (['telegram', 'setup'], {'action': 'setup'}), (['telegram', 'test'], {'action': 'test'}),
    (['telegram', 'call', 'sir'], {'action': 'call', 'address': 'sir'}),
    (['llm', 'setup'], {'action': 'setup'}),
    (['name'], {'cmd': 'name', 'name': []}), (['name', 'Sunny', 'Shop'], {'name': ['Sunny', 'Shop']}),
    (['cloud', '--new', '--size', 't3.medium', '--region', 'ap-south-1', '--profile', 'p', '--no-login'],
     {'new': True, 'size': 't3.medium', 'region': 'ap-south-1', 'profile': 'p', 'no_login': True}),
    (['cloud', '--stop'], {'stop': True}),
    (['cloud', '--to', 'me@host', '--with-login', '--no-start'], {'to': 'me@host', 'with_login': True, 'no_start': True}),
    (['cloud', 'pull', '--from', 'me@host'], {'action': 'pull', 'frm': 'me@host'}),
    (['init', '--test-cmd', 'pytest'], {'test_cmd': 'pytest'}),
    (['run', '--repo', '.', '--run', 'r1', '--workers', '4', '--goal', 'g.md', '--minutes', '30', '--max-parallel', '2',
      '--examples', 'e.md', '--questions', '10', '--assumptions'],
     {'run': 'r1', 'workers': 4, 'goal': 'g.md', 'max_parallel': 2, 'questions': 10, 'assumptions': True}),
    (['owner', '--run', 'r1'], {'run': 'r1'}), (['review', '--run', 'r1'], {'run': 'r1'}),
    (['claim', 'w1-fees', 'fees,tips', 'build fees'], {'name': 'w1-fees', 'areas': 'fees,tips'}),
    (['land', 'w1-fees', 'implement fees', '--note', 'fees.py has a shared helper'], {'message': 'implement fees', 'note': 'fees.py has a shared helper'}),
    (['land', 'w1-fees', '--continue'], {'cont': True}),
    (['notes'], {'cmd': 'notes'}), (['areas'], {'cmd': 'areas'}),
    (['ask', 'Is a tip charged?'], {'question': 'Is a tip charged?'}), (['answers'], {'cmd': 'answers'}),
    (['assume', '--technical', 'Blank cities are allowed'], {'technical': True}), (['assumptions'], {'cmd': 'assumptions'}),
]
for argv, want in ok:
    a, err = parse(*argv)
    check(f"parses: hive {' '.join(argv[:3])}{' ...' if len(argv) > 3 else ''}",
          (a is not None) and all(getattr(a, k, None) == v for k, v in want.items()), True)

# mistakes get plain answers
mistakes = [
    (['start', '--gaol', 'x'], 'Did you mean --goal (not --gaol)?'),
    (['strat'], 'Did you mean `hive start`?'),
    (['cloud', '--nwe'], 'Did you mean --new (not --nwe)?'),
    (['telegram', 'setpu'], 'Did you mean `hive telegram setup`?'),
    (['start', '--workers', '0'], 'it must be at least 1 (got 0)'),
    (['start', '--workers', 'four'], "'four' is not a whole number"),
    (['start', '--docs', os.path.join(docs, 'missing')], 'there is no file or folder at'),
    (['cloud', '--new', '--stop'], 'choose one of --new, --stop, not several'),
    (['start', '--agent', 'codx'], 'codex`?'),
]
for argv, said in mistakes:
    a, err = parse(*argv)
    check(f"a mistake gets a plain answer: hive {' '.join(argv)}", (a is None, said in err, 'Run `hive' in err), (True, True, True))
# any coding agent can build: presets, a saved choice, and HIVE_WORKER_CMD above all
from hive import swarm
os.environ.pop('HIVE_WORKER_CMD', None); os.environ.pop('HIVE_AGENT', None)
check('the default builder is Claude Code', swarm.builder_cmd().startswith('claude -p'), True)
check('--agent codex runs Codex unattended', 'codex exec' in swarm.builder_cmd('codex'), True)
os.environ['HIVE_AGENT'] = 'gemini'
check('a chosen agent is used for every builder', 'gemini --yolo' in swarm.builder_cmd(), True)
os.environ['HIVE_WORKER_CMD'] = 'my-agent --run'
check('HIVE_WORKER_CMD still overrides any preset (any other agent)', swarm.builder_cmd('codex'), 'my-agent --run')
os.environ.pop('HIVE_WORKER_CMD'); os.environ.pop('HIVE_AGENT')
# an agent that is not installed is named before any builder starts, with how to get it (Oct 31: the Antigravity IDE
# has no command-line mode, so the antigravity preset cannot run here)
import shutil as _sh
_which = _sh.which
_sh.which = lambda exe: None if exe in ('agy', 'gemini') else _which(exe)
check('agents missing here are found before a build', swarm.missing_agents('claude,antigravity,gemini'), ['antigravity', 'gemini'])
check('and Antigravity says why, pointing to Gemini', 'use --agent gemini' in swarm.AGENT_HELP['antigravity'], True)
_sh.which = _which
# a mixed swarm: Claude and Codex builders in one build, taking the agents in turn
check('claude,codex gives w1 Claude, w2 Codex, w3 Claude', [swarm.builder_agent('claude,codex', k) for k in (1, 2, 3)],
      ['claude', 'codex', 'claude'])
check("a mixed builder runs its own agent's command", 'codex exec' in swarm.builder_cmd('claude+codex', 2), True)
check('--agent claude,codex is accepted', parse('start', '--agent', 'Claude,Codex')[0].agent, 'claude,codex')
a, err = parse('start', '--agent', 'claude,codx')
check('a typo inside a mix is pointed out', (a is None, 'hive start --agent claude,codex`?' in err), (True, True))
try:
    swarm.builder_cmd('nope'); said = ''
except SystemExit as e:
    said = str(e)
check('an unknown agent is refused with the choices', 'Choose one of: claude, codex, gemini, antigravity' in said, True)

# the startup's name, not the folder's ("name the project {startupname}")
import subprocess
from hive import memory, argv
proj = tempfile.mkdtemp(); memory.DIR = os.path.join(tempfile.mkdtemp(), 'rules')
subprocess.run(['git', 'init', '-q', proj]); open(os.path.join(proj, 'README.md'), 'w').write('# sunny-shop' + chr(10))
subprocess.run(['git', '-C', proj, 'add', '.']); subprocess.run(['git', '-C', proj, '-c', 'user.email=a@b', '-c', 'user.name=a', 'commit', '-qm', 'i'])
check("until he names it, the README's title is the guess", memory.project_name(proj), 'Sunny Shop')
open(os.path.join(proj, 'package.json'), 'w').write('{"name": "backend"}')
check('a generic package name is not taken for his startup', memory.project_name(proj), 'Sunny Shop')
memory.set_name(proj, 'Barter Co')
check('the name he gives is the one used', memory.project_name(proj), 'Barter Co')
empty = tempfile.mkdtemp(); subprocess.run(['git', 'init', '-q', empty])
check('no name rather than the folder name', memory.project_name(empty), '')
from hive import assistant
check("Hive's replies know the startup's name", 'called Barter Co' in assistant.facts(proj), True)
# Windows: claude and codex are .cmd files that subprocess cannot start by bare name; every model call failed there
check('a command line keeps its words', argv('claude -p --output-format json')[1:], ['-p', '--output-format', 'json'])
if os.name == 'nt':
    check('on Windows the tool is found with its .cmd', argv('python -V')[0].lower().endswith('.exe'), True)
sys.exit(fail)
