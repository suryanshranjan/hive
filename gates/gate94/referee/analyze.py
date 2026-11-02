"""G94 registered analysis (committed with the predictions, before any run):
    python3 gates/gate94/referee/analyze.py
S3: hive start after the change (a goal with no business decisions gets neither the interview nor the business review),
on Gate 86's 10 Django issues, compared with S2 (Gate 89), S (Gate 86) and F (Gate 86: one builder, the full issue).
T1 S3's median reporter prompts <= 3            T2 S3 resolves >= 7 of 10
T3 S3's total cost <= 0.35x S2's                 T4 S3's delivered code breaks no stated interface (it was checked before delivery)
Claim: T1, T2 and T3."""
import json, os
from statistics import median
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ids = json.load(open(os.path.join(ROOT, 'private', 'g86', 'valid.json')))
def res(arm): return {i: json.load(open(os.path.join(ROOT, 'runs', 'g86', f'{arm}_{i}', 'result.json'))) for i in ids}
F, S, S2, S3 = res('F'), res('S'), res('S2'), res('S3')
cost = lambda R: sum(r['build_cost'] + (r.get('hive_own') or 0) for r in R.values())
for i in ids:
    print(f"{i}: F {int(F[i]['resolved'])} | S {int(S[i]['resolved'])} {S[i]['owner_prompts']}p | S2 {int(S2[i]['resolved'])} {S2[i]['owner_prompts']}p | "
          f"S3 {int(S3[i]['resolved'])} {S3[i]['owner_prompts']}p ${S3[i]['build_cost'] + S3[i]['hive_own']:.2f} {S3[i]['minutes']} min")
n = {k: sum(int(r['resolved']) for r in R.values()) for k, R in (('F', F), ('S', S), ('S2', S2), ('S3', S3))}
mp = median(S3[i]['owner_prompts'] for i in ids)
print(f"\nresolved {n}; S3 median prompts {mp}; cost F ${cost(F):.2f}, S ${cost(S):.2f}, S2 ${cost(S2):.2f}, S3 ${cost(S3):.2f}")
t4 = all('contract' not in json.dumps(S3[i]) or True for i in ids)
res_ = [('T1', f'median prompts <= 3 ({mp})', mp <= 3), ('T2', f"resolved >= 7 ({n['S3']})", n['S3'] >= 7),
        ('T3', f'cost <= 0.35x S2 ({cost(S3)/cost(S2):.2f})', cost(S3) <= 0.35 * cost(S2))]
res_.append(('Claim', 'T1, T2 and T3', all(x[2] for x in res_)))
print('\npredictions (T4 is read from the terminals by hand: any "changed ... your goal fixed" line)')
for t, x, ok in res_: print(f'{t} {x} -> {"held" if ok else "failed"}')
