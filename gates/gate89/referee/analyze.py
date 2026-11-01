"""G89 registered analysis (committed with the predictions, before any run):
    python3 gates/gate89/referee/analyze.py
Compares S2 (runs/g86/S2_<issue>: hive start after the change) with Gate 86's S (runs/g86/S_<issue>) on the same 10 issues,
and reads the planner check (runs/g89_plan.json).
K1 S2's median reporter prompts <= 8 (S: 23.5)          K2 S2 resolves >= 7 of 10 (S: 8)
K3 S2's total cost <= 0.4x S's                         K4 the planner finds >= 5 decisions in every call on both business goals
K5 the interview asks nothing on >= 8 of the 10 issues (S2's terminal has no "quick situations")
Claim: K1, K2, K3 and K4 -> the change ships."""
import glob, json, os
from statistics import median
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ids = json.load(open(os.path.join(ROOT, 'private', 'g86', 'valid.json')))
def res(arm): return {i: json.load(open(os.path.join(ROOT, 'runs', 'g86', f'{arm}_{i}', 'result.json'))) for i in ids}
S, T = res('S'), res('S2')
plan = json.load(open(os.path.join(ROOT, 'runs', 'g89_plan.json')))
asked = {i: 'quick situations where your own rules matter' in open(os.path.join(ROOT, 'runs', 'g86', f'S2_{i}', 'terminal.txt')).read() for i in ids}
for i in ids:
    print(f"{i}: S {int(S[i]['resolved'])} {S[i]['owner_prompts']}p ${S[i]['build_cost'] + S[i]['hive_own']:.2f} | "
          f"S2 {int(T[i]['resolved'])} {T[i]['owner_prompts']}p ${T[i]['build_cost'] + T[i]['hive_own']:.2f} interview {asked[i]} | planner {plan.get(i)}")
print('business goals, planner:', {k: v for k, v in plan.items() if k not in ids})
mp = median(T[i]['owner_prompts'] for i in ids); r2 = sum(int(T[i]['resolved']) for i in ids)
c1, c2 = sum(S[i]['build_cost'] + S[i]['hive_own'] for i in ids), sum(T[i]['build_cost'] + T[i]['hive_own'] for i in ids)
k4 = all(min(plan[g]) >= 5 for g in ('tiny_shop', 'invoices')); k5 = sum(not v for v in asked.values()) >= 8
print(f"\nS2: resolved {r2}, median prompts {mp}, cost ${c2:.2f} vs S ${c1:.2f}")
res_ = [('K1', f'median prompts <= 8 ({mp})', mp <= 8), ('K2', f'resolved >= 7 ({r2})', r2 >= 7), ('K3', f'cost <= 0.4x S ({c2/c1:.2f})', c2 <= 0.4 * c1),
        ('K4', 'business goals keep >= 5 decisions', k4), ('K5', f"no interview on >= 8 issues ({sum(not v for v in asked.values())})", k5)]
res_.append(('Claim', 'K1-K4', all(x[2] for x in res_[:4])))
print('\npredictions')
for t, x, ok in res_: print(f'{t} {x} -> {"held" if ok else "failed"}')
