"""Gate 79: plant 12 bugs in sqlglot 30.27.0 (MIT) from a fixed seed, and write each as a user's bug report.
usage: python3 pick79.py <sqlglot_src> <out.json>
Candidates: module-level functions with 8-60 body lines in sqlglot/ (not optimizer/, executor/, planner.py: slow tests).
One small mutation per function, chosen at random (seed 79) among those the code allows: a comparison flipped (== and !=,
< and <=, > and >=, is and is not, in and not in), `and` and `or` swapped, a `not` dropped, or an integer constant + 1.
A bug qualifies if the package imports, 1-12 fast-suite test methods fail, and the first failing assertion gives a report
(the case, what sqlglot gives, what it should give). 12 are kept, at most 2 per file."""
import ast, json, os, random, re, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
import xml.etree.ElementTree as ET
SRC, OUT = sys.argv[1], sys.argv[2]
FAST = ['--ignore=tests/test_parser.py', '--ignore=tests/test_executor.py', '--ignore=tests/test_optimizer.py']
FLIP = {ast.Eq: ('==', '!='), ast.NotEq: ('!=', '=='), ast.Lt: ('<', '<='), ast.LtE: ('<=', '<'), ast.Gt: ('>', '>='),
        ast.GtE: ('>=', '>'), ast.IsNot: ('is not', 'is'), ast.Is: ('is', 'is not'), ast.NotIn: ('not in', 'in'), ast.In: ('in', 'not in')}

def offset(lines, ln, col):
    return sum(len(l) + 1 for l in lines[:ln - 1]) + col

def mutations(text, fn):
    lines = text.split('\n'); out = []
    for n in ast.walk(fn):
        if isinstance(n, ast.Compare) and len(n.ops) == 1 and type(n.ops[0]) in FLIP:
            a, b = offset(lines, n.left.end_lineno, n.left.end_col_offset), offset(lines, n.comparators[0].lineno, n.comparators[0].col_offset)
            seg = text[a:b]; old, new = FLIP[type(n.ops[0])]
            m = re.fullmatch(r'(\s*)' + re.escape(old).replace(r'\ ', r'\s+') + r'(\s*)', seg)
            if m: out.append(('compare', a, b, m.group(1) + new + m.group(2), n.lineno))
        elif isinstance(n, ast.BoolOp) and len(n.values) == 2:
            a, b = offset(lines, n.values[0].end_lineno, n.values[0].end_col_offset), offset(lines, n.values[1].lineno, n.values[1].col_offset)
            seg = text[a:b]; old, new = ('and', 'or') if isinstance(n.op, ast.And) else ('or', 'and')
            m = re.fullmatch(r'(\s*)' + old + r'(\s+)', seg)
            if m: out.append(('boolop', a, b, m.group(1) + new + m.group(2), n.lineno))
        elif isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
            a, b = offset(lines, n.lineno, n.col_offset), offset(lines, n.operand.lineno, n.operand.col_offset)
            if re.fullmatch(r'not\s+', text[a:b]): out.append(('not', a, b, '', n.lineno))
        elif isinstance(n, ast.Constant) and type(n.value) is int and n.lineno == n.end_lineno:
            a, b = offset(lines, n.lineno, n.col_offset), offset(lines, n.end_lineno, n.end_col_offset)
            if text[a:b].isdigit(): out.append(('int', a, b, str(n.value + 1), n.lineno))
    return out

def candidates():
    out = []
    for root, _, files in os.walk(os.path.join(SRC, 'sqlglot')):
        for f in sorted(files):
            p = os.path.join(root, f); rel = os.path.relpath(p, SRC)
            if not f.endswith('.py') or '/optimizer/' in rel or '/executor/' in rel or rel.endswith('planner.py'): continue
            text = open(p).read()
            for n in ast.parse(text).body:
                if isinstance(n, ast.FunctionDef) and 8 <= n.end_lineno - n.lineno <= 60:
                    for m in mutations(text, n):
                        out.append(dict(file=rel, name=n.name, kind=m[0], a=m[1], b=m[2], new=m[3], line=m[4], old=text[m[1]:m[2]]))
    return sorted(out, key=lambda c: (c['file'], c['name'], c['a']))

def apply(root, c):
    p = os.path.join(root, c['file']); t = open(p).read()
    assert t[c['a']:c['b']] == c['old']
    open(p, 'w').write(t[:c['a']] + c['new'] + t[c['b']:])

HARNESS = r'''
import json, sys, unittest
first = {}
cur = [None]
orig_sub = unittest.TestCase.subTest
import contextlib
@contextlib.contextmanager
def sub(self, msg=None, **kw):
    prev = cur[0]; cur[0] = msg
    try:
        with orig_sub(self, msg, **kw): yield
    finally: cur[0] = prev
unittest.TestCase.subTest = sub
orig_eq = unittest.TestCase.assertEqual
def eq(self, a, b, msg=None):
    if a != b and self.id() not in first and isinstance(a, str) and isinstance(b, str):
        first[self.id()] = dict(case=cur[0], got=a, want=b)
    return orig_eq(self, a, b, msg)
unittest.TestCase.assertEqual = eq
ids = json.load(open(sys.argv[1]))
suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(i) for i in ids)
unittest.TextTestRunner(stream=open('/dev/null', 'w')).run(suite)
json.dump(first, open(sys.argv[2], 'w'))
'''

def failing(root):
    j = os.path.join(root, 'junit.xml')
    subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', 'tests', *FAST, f'--junitxml={j}'], cwd=root, capture_output=True)
    if not os.path.exists(j): return None
    return sorted({f"{tc.get('classname')}::{tc.get('name')}" for tc in ET.parse(j).iter('testcase')
                   if tc.find('failure') is not None or tc.find('error') is not None})

def report(root, bad):
    ids = [b.replace('::', '.') for b in bad]
    json.dump(ids, open(os.path.join(root, 'ids.json'), 'w')); open(os.path.join(root, 'h.py'), 'w').write(HARNESS)
    subprocess.run([sys.executable, 'h.py', 'ids.json', 'first.json'], cwd=root, capture_output=True, timeout=600)
    f = json.load(open(os.path.join(root, 'first.json'))) if os.path.exists(os.path.join(root, 'first.json')) else {}
    for i in ids:
        if i in f and f[i]['case'] and len(f[i]['got']) < 400 and len(f[i]['want']) < 400:
            return f[i]
    return None

def trial(c):
    d = tempfile.mkdtemp(dir=os.environ.get('G79_TMP'))
    try:
        shutil.copytree(SRC, os.path.join(d, 's'), ignore=shutil.ignore_patterns('.git', '__pycache__'))
        root = os.path.join(d, 's'); apply(root, c)
        if subprocess.run([sys.executable, '-c', 'import sqlglot, sqlglot.dialects'], cwd=root, capture_output=True).returncode:
            return dict(c, failing=None, report=None)
        bad = failing(root) or []
        rep = report(root, bad) if 1 <= len(bad) <= 12 else None
        return dict(c, failing=bad, report=rep)
    finally:
        shutil.rmtree(d, ignore_errors=True)

if __name__ == '__main__':
    cands = candidates(); rng = random.Random(79)
    byfn = {}
    for c in cands: byfn.setdefault((c['file'], c['name']), []).append(c)
    keys = sorted(byfn); rng.shuffle(keys)
    order = [rng.choice(byfn[k]) for k in keys]
    print(len(cands), 'mutations in', len(keys), 'functions', flush=True)
    chosen, per, tried = [], {}, []
    with ThreadPoolExecutor(2) as ex:
        for k in range(0, len(order), 8):
            batch = [c for c in order[k:k + 8] if per.get(c['file'], 0) < 2]
            for r in ex.map(trial, batch):
                tried.append(r); n = len(r['failing'] or [])
                print(f"{r['file']}::{r['name']} {r['kind']} L{r['line']} failing {n} report {bool(r['report'])}", flush=True)
                if r['report'] and per.get(r['file'], 0) < 2 and len(chosen) < 12:
                    chosen.append(r); per[r['file']] = per.get(r['file'], 0) + 1
            json.dump(dict(chosen=chosen, tried=tried), open(OUT, 'w'), indent=1)
            if len(chosen) >= 12: break
    print('chosen:', [(c['file'], c['name'], c['kind'], len(c['failing'])) for c in chosen])
