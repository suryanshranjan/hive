"""Gate 78: build the job from sqlglot 30.27.0 (MIT) and the 12 functions pick78.py chose (seed 78).
usage: python3 seed78.py <sqlglot_src> <pick.json> <seed_dir> <hidden.json>
The seed is sqlglot with the 12 functions emptied, and with every fast-suite test method that then fails removed (the
hidden suite: those methods, run from the original test files). Writes .hive/config.json and commits."""
import ast, json, os, shutil, subprocess, sys
import xml.etree.ElementTree as ET
SRC, PICK, SEED, HIDDEN = sys.argv[1:5]
FAST = ['--ignore=tests/test_parser.py', '--ignore=tests/test_executor.py', '--ignore=tests/test_optimizer.py']
TEST_CMD = 'python3 -m pytest -q -p no:cacheprovider tests ' + ' '.join(FAST) + ' --junitxml=.hive/junit.xml'

def failing(root):
    j = os.path.abspath(os.path.join(root, '.junit_tmp.xml'))
    subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', 'tests', *FAST, f'--junitxml={j}'], cwd=root, capture_output=True)
    bad, n = set(), 0
    for tc in ET.parse(j).iter('testcase'):
        n += 1
        if tc.find('failure') is not None or tc.find('error') is not None:
            bad.add((tc.get('classname'), tc.get('name')))
    os.remove(j); return bad, n

shutil.rmtree(SEED, ignore_errors=True)
shutil.copytree(SRC, SEED, ignore=shutil.ignore_patterns('.git', '__pycache__', 'sqlglot.egg-info', 'sqlglotc', 'test_sqlglotc.py', 'junit*.xml'))
chosen = json.load(open(PICK))['chosen']
byfile = {}
for c in chosen: byfile.setdefault(c['file'], []).append(c)
for f, cs in byfile.items():
    p = os.path.join(SEED, f); L = open(p).read().split('\n')
    for c in sorted(cs, key=lambda c: -c['start']):
        L[c['start'] - 1:c['end']] = [' ' * c['col'] + 'raise NotImplementedError("emptied: rebuild this function")']
    open(p, 'w').write('\n'.join(L))
bad, n = failing(SEED)
print(f'{len(bad)} of {n} fast-suite test methods fail with the 12 emptied')
by = {}
for cls, name in bad:
    mod = cls.rsplit('.', 1)[0]; by.setdefault(mod.replace('.', '/') + '.py', []).append((cls.rsplit('.', 1)[1], name))
for f, items in by.items():
    p = os.path.join(SEED, f); text = open(p).read(); L = text.split('\n'); cut = []
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.ClassDef):
            for m in node.body:
                if isinstance(m, ast.FunctionDef) and (node.name, m.name) in items:
                    start = min([m.lineno] + [d.lineno for d in m.decorator_list])
                    cut.append((start, m.end_lineno))
    for s, e in sorted(cut, reverse=True):
        del L[s - 1:e]
    open(p, 'w').write('\n'.join(L))
left, n2 = failing(SEED)
assert not left, f'still failing: {sorted(left)[:5]}'
print(f'visible: {n2} test methods, all pass')
os.makedirs(os.path.join(SEED, '.hive'), exist_ok=True)
json.dump({'test_cmd': TEST_CMD, 'branch': 'main', 'junit': '.hive/junit.xml'}, open(os.path.join(SEED, '.hive', 'config.json'), 'w'), indent=1)
open(os.path.join(SEED, '.gitignore'), 'a').write('\n.hive/junit.xml\n.hive/guard_cache/\n__pycache__/\n')
for c in (['init', '-q', '-b', 'main'], ['add', '-A'], ['-c', 'user.name=referee', '-c', 'user.email=referee@local', 'commit', '-qm', 'sqlglot 30.27.0 with 12 functions emptied']):
    subprocess.run(['git', *c], cwd=SEED, check=True)
json.dump(dict(hidden=sorted(f'{c}::{m}' for c, m in bad), functions=[f"{c['file']}::{c['name']}" for c in chosen]), open(HIDDEN, 'w'), indent=1)
