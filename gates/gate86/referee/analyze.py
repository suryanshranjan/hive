"""G86 analysis. Written after the runs (the predictions were registered in prompts/PREDICTIONS.md, but no analysis code
was committed with them); it applies those predictions as worded.
    python3 gates/gate86/referee/analyze.py
P1 F >= 7 of 10   P2 N <= F - 2   P3 S >= N + 2   P4 S >= F - 1   P5 S's median owner prompts <= 15   Claim: P3 and P4"""
import csv, glob, json, os
from statistics import median
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ids = json.load(open(os.path.join(ROOT, 'private', 'g86', 'valid.json')))
R = {}
for f in glob.glob(os.path.join(ROOT, 'runs', 'g86', '*', 'result.json')):
    d = json.load(open(f)); R[(d['arm'], d['instance'])] = d
pub = {s: {r['instance_id']: r['claude_sonnet3.5'] for r in csv.DictReader(open(os.path.join(ROOT, 'private', 'g86', f'{s}.csv')))}
       for s in ('fully-specified', 'underspecified', 'interaction')}
print(f"{'issue':24s} F N S | Ambig-SWE Sonnet 3.5 full/hidden/asking | S: prompts, Hive's own $, builders $, minutes")
for i in ids:
    g = lambda a: int(R[(a, i)]['resolved'])
    s = R[('S', i)]
    print(f"{i:24s} {g('F')} {g('N')} {g('S')} | {pub['fully-specified'].get(i, '-')}/{pub['underspecified'].get(i, '-')}/{pub['interaction'].get(i, '-')} | "
          f"{s['owner_prompts']}, {s['hive_own']}, {s['build_cost']}, {s['minutes']}")
n = {a: sum(int(R[(a, i)]['resolved']) for i in ids) for a in 'FNS'}
pp = {k: sum(int(v.get(i, 0) or 0) for i in ids) for k, v in pub.items()}
mp = median(R[('S', i)]['owner_prompts'] for i in ids)
cost = {a: sum(R[(a, i)]['build_cost'] + R[(a, i)].get('hive_own', 0) for i in ids) for a in 'FNS'}
print(f"\nresolved: F {n['F']}, N {n['N']}, S {n['S']} of 10; published (Sonnet 3.5): full {pp['fully-specified']}, hidden {pp['underspecified']}, asking {pp['interaction']}")
print(f"S median owner prompts {mp}; total cost F ${cost['F']:.2f}, N ${cost['N']:.2f}, S ${cost['S']:.2f}")
res = [('P1', 'F >= 7', n['F'] >= 7), ('P2', 'N <= F - 2', n['N'] <= n['F'] - 2), ('P3', 'S >= N + 2', n['S'] >= n['N'] + 2),
       ('P4', 'S >= F - 1', n['S'] >= n['F'] - 1), ('P5', f'S median prompts <= 15 ({mp})', mp <= 15)]
res.append(('Claim', 'P3 and P4', res[2][2] and res[3][2]))
print('\npredictions')
for t, x, ok in res: print(f'{t} {x} -> {"held" if ok else "failed"}')
