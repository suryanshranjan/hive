"""G82 registered analysis (committed with the predictions, before the flights):
    python3 gates/gate82/referee/analyze.py runs/g82_live runs/g82_overnight
Q1 live: no crash, one branch, >= 24 of 27 hidden
Q2 both flights: no part (refund, points_earned, sales_summary) built by 2+ builders (their own commits, landed or not)
Q3 both flights: every lock holds at most ceil(areas / builders) areas, and when there are at least as many areas as
   builders, at least 2 builders landed work
Q4 overnight: no crash, >= 22 of 27 after the morning, the fix round ran
Q5 both flights: the delivered branch has all three functions"""
import ast, glob, json, os, subprocess, sys
from collections import Counter
FUNCS = {'refund': 'shop/refunds.py', 'points_earned': 'shop/loyalty.py', 'sales_summary': 'shop/report.py'}

def body(src, name):
    try:
        for n in ast.walk(ast.parse(src)):
            if isinstance(n, ast.FunctionDef) and n.name == name: return ast.get_source_segment(src, n)
    except SyntaxError: return None

def show(w, rev, p):
    r = subprocess.run(['git', 'show', f'{rev}:{p}'], cwd=w, capture_output=True, text=True); return r.stdout if r.returncode == 0 else ''

def touched(work, me):
    out = set()
    for line in subprocess.run(['git', 'log', '--reflog', '--all', f'--author={me}', '--format=%H %P'], cwd=work, capture_output=True, text=True).stdout.splitlines():
        p = line.split()
        if len(p) < 2: continue
        for f, path in FUNCS.items():
            if body(show(work, p[0], path), f) != body(show(work, p[1], path), f) and body(show(work, p[0], path), f): out.add(f)
    return out

def flight(d):
    f = json.load(open(os.path.join(d, 'flight.json')))
    b = sorted(glob.glob(os.path.join(d, 'hive_state', 'runs', '*', 'build')))[-1]
    cfg = json.loads(subprocess.run(['git', '--git-dir', os.path.join(b, 'up.git'), 'show', 'HEAD:.hive/config.json'], capture_output=True, text=True).stdout or '{}')
    ps = sorted(glob.glob(os.path.join(b, 'prompts', '*.md')))
    biz = bool(ps) and 'Your role: the business builder' in open(ps[-1]).read()
    per = {os.path.basename(w): touched(w, os.path.basename(w)) for w in sorted(glob.glob(os.path.join(b, 'work', 'w*')))}
    c = Counter(x for s in per.values() for x in s)
    lands = Counter(l.split(':')[0] for l in subprocess.run(['git', '--git-dir', os.path.join(b, 'up.git'), 'log', '--format=%an:%s', 'HEAD'], capture_output=True, text=True).stdout.splitlines()
                    if not l.split(':', 1)[1].startswith('Lock'))
    qn = len(glob.glob(os.path.join(b, 'owner', 'questions', '*.json'))); fixed = os.path.isdir(os.path.join(os.path.dirname(b), 'fix'))
    return f, dict(areas=cfg.get('area_parts') or cfg.get('areas'), builders=len(ps), business_role=biz,
                   touched={w: sorted(s) for w, s in per.items()}, duplicated=sum(1 for x in c if c[x] >= 2),
                   commits_by=dict(lands), questions=qn, fixed=fixed)
L, l = flight(sys.argv[1]); N, n = flight(sys.argv[2])
import math, re
def locks_ok(d, info):
    b = sorted(glob.glob(os.path.join(d, 'hive_state', 'runs', '*', 'build')))[-1]
    subj = subprocess.run(['git', '--git-dir', os.path.join(b, 'up.git'), 'log', '--format=%s', 'HEAD'], capture_output=True, text=True).stdout.splitlines()
    sizes = [len(m.group(1).split(',')) for x in subj for m in [re.match(r'Lock: \S+ \((.*)\)', x)] if m]
    share = math.ceil(len(info['areas'] or {}) / max(1, info['builders'])) if info['areas'] else 99
    landers = [w for w, k in info['commits_by'].items() if w.startswith('w') and k > 0]
    enough = len(info['areas'] or {}) < info['builders'] or len(landers) >= 2
    return all(s <= share for s in sizes) and enough, sizes, share, landers
def has_all(f):
    br = f['branches'][-1] if f['branches'] else None
    return br
for name, F, i, d in (('live', L, l, sys.argv[1]), ('overnight', N, n, sys.argv[2])):
    ok, sizes, share, landers = locks_ok(d, i)
    print(f"{name}: rc {F['rc']}, {F['minutes']} min, after {F['after'].get('line')}, owner prompts {F['owner_replies']}, builders' cost ${F['build_cost']}")
    print(f"  areas {len(i['areas'] or {})}, builders {i['builders']}, split {i['business_role']}, lock sizes {sizes} (share {share}), landers {landers}, touched {i['touched']}, questions {i['questions']}")
    i['locks_ok'] = ok
def complete(d):
    t = os.path.join(d, 'delivered')
    return all(os.path.exists(os.path.join(t, p)) and f'def {fn}' in open(os.path.join(t, p)).read() for fn, p in FUNCS.items())
res = [('Q1', f"live: no crash, one branch, >= 24: {L['after'].get('passed')}", L['rc'] == 0 and not L['error'] and len(L['branches']) == 1 and (L['after'].get('passed') or 0) >= 24),
       ('Q2', f"no part built twice (live {l['duplicated']}, overnight {n['duplicated']})", l['duplicated'] == 0 and n['duplicated'] == 0),
       ('Q3', f"claims within an even share, and 2+ builders landed where the areas allow (live {l['locks_ok']}, overnight {n['locks_ok']})", l['locks_ok'] and n['locks_ok']),
       ('Q4', f"overnight: no crash, >= 22 after the morning ({N['after'].get('passed')}), fix ran ({n['fixed']})", N['rc'] == 0 and not N['error'] and (N['after'].get('passed') or 0) >= 22 and n['fixed']),
       ('Q5', f"all three functions delivered (live {complete(sys.argv[1])}, overnight {complete(sys.argv[2])})", complete(sys.argv[1]) and complete(sys.argv[2]))]
print('\npredictions')
for tag, text, ok in res: print(f'{tag} {text} -> {"held" if ok else "failed"}')
