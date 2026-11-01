"""G81 registered analysis (committed with the predictions, before the flights):
    python3 gates/gate81/referee/analyze.py runs/g81_live runs/g81_overnight
R1 live: no crash, one branch, >= 24 of 27 hidden              R2 live: areas were derived from the goal (the build's
   shared config has area_parts, >= 2 areas) and the split engaged (business role on the last builder)
R3 live: no part built by 2+ builders (of refund, points_earned, sales_summary: the builders whose own commits, landed or
   not, changed that function's body)                          R4 live: <= 45 owner prompts
R5 overnight: no crash, >= 22 of 27 hidden after the morning, the morning fix ran
Also reported: each builder's landings (a builder with none had nothing it could claim)."""
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
print(f"live: rc {L['rc']}, error {bool(L['error'])}, {L['minutes']} min, branches {L['branches']}, after {L['after'].get('line')}, owner prompts {L['owner_replies']}, builders' cost ${L['build_cost']}")
print(f"  {l}")
print(f"overnight: rc {N['rc']}, error {bool(N['error'])}, {N['minutes']} min, night {N.get('night', {}).get('line')}, after the morning {N['after'].get('line')}, owner prompts {N['owner_replies']}")
print(f"  {n}")
res = [('R1', f"live: no crash, one branch, >= 24: {L['after'].get('passed')}", L['rc'] == 0 and not L['error'] and len(L['branches']) == 1 and (L['after'].get('passed') or 0) >= 24),
       ('R2', f"live: areas derived ({len(l['areas'] or {})}) and split engaged ({l['business_role']})", bool(l['areas']) and len(l['areas']) >= 2 and l['business_role']),
       ('R3', f"live: no part built by 2+ builders ({l['duplicated']})", l['duplicated'] == 0),
       ('R4', f"live: <= 45 owner prompts ({L['owner_replies']})", L['owner_replies'] <= 45),
       ('R5', f"overnight: no crash, >= 22 after the morning ({N['after'].get('passed')}), fix ran ({n['fixed']})", N['rc'] == 0 and not N['error'] and (N['after'].get('passed') or 0) >= 22 and n['fixed'])]
print('\npredictions')
for tag, text, ok in res: print(f'{tag} {text} -> {"held" if ok else "failed"}')
