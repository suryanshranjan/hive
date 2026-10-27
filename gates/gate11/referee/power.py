"""Pre-flight power for G11 (run before registering). python gates/gate11/referee/power.py
Pairs of functions matched on N0 edge errors E. Arm S gives (2, 1) questions per pair, arm B gives (3, 0).
R = errors fixed by S / errors fixed by B, summed over the 10 pairs.
Per-function noise: the share of errors fixed at q questions is drawn around the hypothesis' mean with the
spread seen per allowance level in Gates 6 and 8 (pooled residual SD per level), clipped to [-0.3, 1]."""
import json, random, statistics as st

rows = []
for g in ('g6', 'g8'):
    rows += [r for r in json.loads(open(f'gates/gate8/results/surprise_{g}.txt').read().splitlines()[-1]) if r['errors0']]
E = sorted(r['errors0'] for r in rows)                      # empirical headroom per function
sd = {q: st.pstdev([r['fixed'] for r in rows if r['allow'] == q]) for q in (1, 3)}
sd[2] = st.pstdev([r['fixed'] for r in rows if r['allow'] == 2]); sd[0] = 0.0
print('pooled per-function SD of share fixed:', {q: round(v, 2) for q, v in sorted(sd.items())})

HYP = {'law p=0.55': {q: 1 - 0.45 ** q for q in range(4)},
       'law p=0.40': {q: 1 - 0.60 ** q for q in range(4)},
       'convex (Gate 6 raw reading)': {0: 0, 1: 0.25, 2: 0.55, 3: 0.92},
       'linear in q, capped': {0: 0, 1: 0.30, 2: 0.60, 3: 0.90}}

def draw(m, q, rnd): return 0.0 if q == 0 else max(-0.3, min(1.0, rnd.gauss(m[q], sd[q])))

def sim(m, reps=20000, seed=1):
    rnd = random.Random(seed); out = []
    for _ in range(reps):
        es = sorted(rnd.choice(E) for _ in range(20)); pairs = [(es[2 * i], es[2 * i + 1]) for i in range(10)]
        s = b = 0.0
        for e1, e2 in pairs:
            hi, lo = (e1, e2) if rnd.random() < .5 else (e2, e1)
            s += hi * draw(m, 2, rnd) + lo * draw(m, 1, rnd)
            b += hi * draw(m, 3, rnd) + lo * draw(m, 0, rnd)
        out.append(s / b if b > 0 else float('inf'))
    out.sort()
    return dict(median=round(out[len(out) // 2], 2), p_ge_1_3=round(sum(x >= 1.3 for x in out) / reps, 3),
                p_le_1_0=round(sum(x <= 1.0 for x in out) / reps, 3), mid90=(round(out[reps // 20], 2), round(out[-reps // 20], 2)))

for k, m in HYP.items(): print(f'{k:30s}', sim(m))
