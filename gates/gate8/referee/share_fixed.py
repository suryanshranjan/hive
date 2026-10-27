"""Headroom check across Gates 6 and 8. Run from the repo root:
    python gates/gate8/referee/share_fixed.py
Per allowance level: N0's edge errors (headroom), and the share of them NQ fixed,
against the one-parameter law share = 1 - (1-p)**q, with p fitted per gate and bootstrapped over functions."""
import gzip, json, random

def edge(path):
    d = {}
    for r in json.load(gzip.open(path)):
        if r['kind'] == 'edge':
            d.setdefault(r['cat'], []).append(r['ok'])
    return d

def gate(g, allow):
    e0, e1 = edge(f'{g}/results/probe_N0.json.gz'), edge(f'{g}/results/probe_NQ.json.gz')
    al = json.load(open(f'{g}/results/{allow}'))
    al = al.get('allow', al)
    # (questions, N0 errors, errors fixed by NQ, edge calls)
    return [(al[f], len(e0[f]) - sum(e0[f]), sum(e1[f]) - sum(e0[f]), len(e0[f])) for f in al]

def fit_p(rows):
    asked = [r for r in rows if r[0] > 0 and r[1] > 0]
    grid = [i / 1000 for i in range(1, 1000)]
    # least squares on errors fixed, i.e. weighted by each function's headroom
    return min(grid, key=lambda p: sum((fx - err * (1 - (1 - p) ** q)) ** 2 for q, err, fx, _ in asked))

if __name__ == '__main__':
    rnd = random.Random(1)
    for g, allow in (('gates/gate6', 'analysis.json'), ('gates/gate8', 'allowance.json')):
        rows = gate(g, allow)
        p = fit_p(rows)
        bs = sorted(fit_p([rnd.choice(rows) for _ in rows]) for _ in range(2000))
        print(f'{g}: p = {p:.2f} (95% CI {bs[50]:.2f}-{bs[1949]:.2f})')
        for q in sorted({r[0] for r in rows}):
            lv = [r for r in rows if r[0] == q]
            err, fx, calls = sum(r[1] for r in lv), sum(r[2] for r in lv), sum(r[3] for r in lv)
            print(f'  q={q}: {len(lv)} functions, N0 edge error rate {err / calls:.0%} ({err}/{calls}), '
                  f'share of errors fixed {fx / err:+.2f}, law {1 - (1 - p) ** q:.2f}')
