"""Fit the question curve on Gate 6, predict Gate 8 (held out). Run from the repo root:
    python gates/gate8/referee/curve_fit.py
Per function: a0 = N0 edge accuracy, a = NQ edge accuracy (all edge calls), q = allowed questions.
  linear:   a - a0 = s*q
  headroom: a - a0 = (1 - a0) * (1 - (1-p)**q)   each answer fixes a share p of the remaining edge errors
  head_lin: a - a0 = (1 - a0) * min(1, k*q)      each answer fixes a share k of the original edge errors
Each has one parameter, fitted by least squares on Gate 6 only."""
import gzip, json, random

def edge_acc(path):
    # every edge call counts, as in the official scorer (aggregate calls share query text but not data)
    d = {}
    for r in json.load(gzip.open(path)):
        if r['kind'] == 'edge':
            d.setdefault(r['cat'], []).append(r['ok'])
    return {c: sum(v) / len(v) for c, v in d.items()}

def gate(g, allow):
    a0, a = edge_acc(f'{g}/results/probe_N0.json.gz'), edge_acc(f'{g}/results/probe_NQ.json.gz')
    al = json.load(open(f'{g}/results/{allow}'))
    al = al.get('allow', al)
    return [(al[f], a0[f], a[f]) for f in al]

MODELS = {
    'linear': lambda q, a0, x: x * q,
    'headroom': lambda q, a0, x: (1 - a0) * (1 - (1 - x) ** q),
    'head_lin': lambda q, a0, x: (1 - a0) * min(1, x * q),     # headroom, but no diminishing returns until full
}

def fit(rows, m):
    grid = [i / 1000 for i in range(1001)]
    return min(grid, key=lambda x: sum((a - a0 - MODELS[m](q, a0, x)) ** 2 for q, a0, a in rows))

def by_level(rows, f=lambda q, a0, a: a - a0):
    out = {}
    for r in rows:
        out.setdefault(r[0], []).append(f(*r))
    return {q: 100 * sum(v) / len(v) for q, v in sorted(out.items())}

def boot_ci(rows, m, n=4000, seed=1):
    rnd = random.Random(seed)
    xs = sorted(fit([rnd.choice(rows) for _ in rows], m) for _ in range(n))
    return xs[int(.025 * n)], xs[int(.975 * n)]

if __name__ == '__main__':
    g6, g8 = gate('gates/gate6', 'analysis.json'), gate('gates/gate8', 'allowance.json')
    print('observed mean gain by level, Gate 6:', {q: round(v, 1) for q, v in by_level(g6).items()})
    print('observed mean gain by level, Gate 8:', {q: round(v, 1) for q, v in by_level(g8).items()})
    for m in MODELS:
        x = fit(g6, m)
        lo, hi = boot_ci(g6, m)
        pred = by_level(g8, lambda q, a0, a: MODELS[m](q, a0, x))
        obs = by_level(g8)
        rmse = (sum((pred[q] - obs[q]) ** 2 for q in obs) / len(obs)) ** .5
        sse_f = sum((a - a0 - MODELS[m](q, a0, x)) ** 2 for q, a0, a in g8)
        print(f'{m:9s} fit on G6: {x:.3f} (95% CI {lo:.3f}-{hi:.3f}); '
              f'G8 predicted {dict((q, round(v, 1)) for q, v in pred.items())}; '
              f'level RMSE {rmse:.1f} pts; per-function SSE {sse_f:.3f}; refit on G8: {fit(g8, m):.3f}')
