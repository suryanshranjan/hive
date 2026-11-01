"""Gate 78: pick the functions to empty in sqlglot (Apache... MIT-licensed, 85k lines), from a fixed seed.
usage: python3 pick78.py <sqlglot_src_dir> <out.json>
Candidates: module-level functions with 8-40 body lines in sqlglot/ (not optimizer/, executor/, planner.py: their tests
are slow). Each is emptied alone and the fast suite run; a candidate qualifies if 1-12 test methods fail and the package
still imports. 12 are chosen at random (seed 78) from qualifying ones, at most 2 per file."""
import ast, json, os, random, subprocess, sys, tempfile, shutil, glob
from concurrent.futures import ThreadPoolExecutor
SRC, OUT = sys.argv[1], sys.argv[2]
FAST = ['--ignore=tests/test_parser.py', '--ignore=tests/test_executor.py', '--ignore=tests/test_optimizer.py']

def funcs():
    out = []
    for f in sorted(glob.glob(os.path.join(SRC, 'sqlglot', '**', '*.py'), recursive=True)):
        rel = os.path.relpath(f, SRC)
        if '/optimizer/' in rel or '/executor/' in rel or rel.endswith('planner.py'): continue
        t = ast.parse(open(f).read())
        for n in t.body:
            if isinstance(n, ast.FunctionDef) and not n.decorator_list:
                body = n.body[1:] if (n.body and isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], 'value', None), ast.Constant) and isinstance(n.body[0].value.value, str)) else n.body
                if not body: continue
                lines = n.end_lineno - body[0].lineno + 1
                if 8 <= lines <= 40 and not any(isinstance(x, (ast.Yield, ast.YieldFrom)) for x in ast.walk(n)):
                    out.append(dict(file=rel, name=n.name, start=body[0].lineno, end=n.end_lineno, lines=lines, col=body[0].col_offset))
    return out

def empty(root, c):
    p = os.path.join(root, c['file']); L = open(p).read().split('\n')
    pad = ' ' * c['col']
    L[c['start'] - 1:c['end']] = [pad + 'raise NotImplementedError("emptied for Gate 78: rebuild this function")']
    open(p, 'w').write('\n'.join(L))

def failing(root):
    j = os.path.join(root, 'junit.xml')
    r = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', 'tests', *FAST, f'--junitxml={j}'], cwd=root, capture_output=True, text=True)
    if not os.path.exists(j): return None
    import xml.etree.ElementTree as ET
    bad = set()
    for tc in ET.parse(j).iter('testcase'):
        if tc.find('failure') is not None or tc.find('error') is not None:
            bad.add(f"{tc.get('classname')}::{tc.get('name')}")
    ok = sum(1 for _ in ET.parse(j).iter('testcase'))
    return sorted(bad), ok

def trial(c):
    d = tempfile.mkdtemp(dir=os.environ.get('G78_TMP'))
    shutil.copytree(SRC, os.path.join(d, 's'), ignore=shutil.ignore_patterns('.git', '__pycache__'))
    root = os.path.join(d, 's'); empty(root, c)
    imp = subprocess.run([sys.executable, '-c', 'import sqlglot, sqlglot.dialects'], cwd=root, capture_output=True).returncode == 0
    res = failing(root) if imp else None
    shutil.rmtree(d)
    return dict(c, imports=imp, failing=(res[0] if res else None), total=(res[1] if res else None))

if __name__ == '__main__':
    cands = funcs(); rng = random.Random(78); rng.shuffle(cands)
    print(len(cands), 'candidates', flush=True)
    base = failing(SRC); assert base and not base[0], f'baseline fails: {base and base[0][:5]}'
    print('baseline fast suite:', base[1], 'tests, all pass', flush=True)
    chosen, per, tried = [], {}, []
    with ThreadPoolExecutor(2) as ex:
        for k in range(0, len(cands), 8):
            for r in ex.map(trial, cands[k:k + 8]):
                tried.append(r)
                n = len(r['failing'] or [])
                print(f"{r['file']}::{r['name']} lines {r['lines']} imports {r['imports']} failing {n}", flush=True)
                if r['imports'] and 1 <= n <= 12 and per.get(r['file'], 0) < 2 and len(chosen) < 12:
                    chosen.append(r); per[r['file']] = per.get(r['file'], 0) + 1
            if len(chosen) >= 12: break
    json.dump(dict(chosen=chosen, tried=tried), open(OUT, 'w'), indent=1)
    print('chosen:', [(c['file'], c['name'], len(c['failing'])) for c in chosen])
