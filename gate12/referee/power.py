"""Pre-flight power for G12 (run before registering). python gate12/referee/power.py
20 functions, decisions d = 1..4 (5 each). Teams with 1, 2 and 4 questions on every function.
H1 (saturation tracks decisions): share fixed = c * min(1, q / d), c = 0.75.
H0 (shape independent of d): share fixed = mean over d of H1 at the same q.
Per-function noise: SD 0.41 / 0.39 / 0.15 at q = 1 / 2 / 4 (Gates 6, 8, 11, pooled), clipped to [-0.3, 1].
D1: mean share at q=1 over d in {1,2} minus over d in {3,4}.
D2: Spearman rho between d and q* (smallest q in {1,2,4} reaching 0.8 of the function's best share)."""
import random

C, SD = 0.75, {1: 0.41, 2: 0.39, 4: 0.15}
D = [d for d in (1, 2, 3, 4) for _ in range(5)]
H1 = lambda q, d: C * min(1, q / d)
H0 = lambda q, d: sum(H1(q, x) for x in (1, 2, 3, 4)) / 4

def rank(xs):
    s = sorted(range(len(xs)), key=lambda i: xs[i]); r = [0.0] * len(xs); i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and xs[s[j + 1]] == xs[s[i]]: j += 1
        for k in range(i, j + 1): r[s[k]] = (i + j) / 2
        i = j + 1
    return r

def spearman(a, b):
    ra, rb = rank(a), rank(b); n = len(a); ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** .5
    return num / den if den else 0.0

def sim(h, reps=20000, seed=1):
    rnd = random.Random(seed); d1 = d2 = k = 0
    for _ in range(reps):
        sh = [{q: max(-0.3, min(1.0, rnd.gauss(h(q, d), SD[q]))) for q in (1, 2, 4)} for d in D]
        lo = [s[1] for s, d in zip(sh, D) if d <= 2]; hi = [s[1] for s, d in zip(sh, D) if d >= 3]
        d1 += (sum(lo) / len(lo) - sum(hi) / len(hi)) >= 0.15
        keep = [(d, s) for d, s in zip(D, sh) if max(s.values()) > 0]
        qs = [min(q for q in (1, 2, 4) if s[q] >= 0.8 * max(s.values())) for d, s in keep]
        rho = spearman([d for d, _ in keep], qs)
        d2 += rho >= 0.3; k += rho <= 0
    return dict(D1_holds=round(d1 / reps, 3), D2_holds=round(d2 / reps, 3), rho_le_0=round(k / reps, 3))

for name, h in (('H1 saturation tracks decisions', H1), ('H0 shape independent of d', H0)):
    print(f'{name:32s}', sim(h))
