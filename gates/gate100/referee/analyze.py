"""G100 registered analysis (committed with the predictions, before any run):
    python3 gates/gate100/referee/analyze.py
10 harder Django issues (private/g86/valid100.json). Arms: F one builder, full issue; N one builder, summary; S hive start
on the summary, the simulated reporter at the keyboard (Gate 94's technical path: builders may ask him).
A1 N <= F - 3 (on this sample the summary hurts today's builder too)
A2 S >= N + 2 (Hive's flow recovers part of it, through builders asking the reporter)
A3 S's builders ask the reporter at least one question on >= 5 of the 10 issues
A4 S's median reporter prompts <= 5
Claim: A1 and A2."""
import json, os
from statistics import median
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ids = json.load(open(os.path.join(ROOT, 'private', 'g86', 'valid100.json')))
def res(a): return {i: json.load(open(os.path.join(ROOT, 'runs', 'g100', f'{a}_{i}', 'result.json'))) for i in ids}
F, N, S = res('F'), res('N'), res('S')
def asked(i):
    t = os.path.join(ROOT, 'runs', 'g100', f'S_{i}', 'terminal.txt')
    return open(t).read().count('Your answer') + open(t).read().count('question from builder') if os.path.exists(t) else 0
for i in ids:
    print(f"{i}: F {int(F[i]['resolved'])} N {int(N[i]['resolved'])} S {int(S[i]['resolved'])} | S prompts {S[i]['owner_prompts']}, "
          f"cost ${S[i]['build_cost'] + S[i]['hive_own']:.2f}")
n = {k: sum(int(r['resolved']) for r in R.values()) for k, R in (('F', F), ('N', N), ('S', S))}
mp = median(S[i]['owner_prompts'] for i in ids)
asks = sum(1 for i in ids if S[i]['owner_prompts'] >= 2)   # the fast/cheap question is 1; any more is a builder's question
print(f"\nresolved {n}; S median prompts {mp}; issues where S's builders asked: {asks}")
res_ = [('A1', 'N <= F - 3', n['N'] <= n['F'] - 3), ('A2', 'S >= N + 2', n['S'] >= n['N'] + 2),
        ('A3', 'builders asked on >= 5 issues', asks >= 5), ('A4', f'S median prompts <= 5 ({mp})', mp <= 5)]
res_.append(('Claim', 'A1 and A2', res_[0][2] and res_[1][2]))
print('\npredictions')
for t, x, h in res_: print(f'{t} {x} -> {"held" if h else "failed"}')
