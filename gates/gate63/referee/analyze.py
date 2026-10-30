"""G63 registered analysis (committed with the predictions, before the run):
    python3 gates/gate63/referee/analyze.py runs/g63a runs/g63b
Pooled over both runs (50 declared decisions; labels from Gate 63's judge, which saw SL, CB, CA and R together).
H1  CA states >= 3 more decisions right than CB          H2  hidden CA >= CB + 3 (mean over runs)
H3  CA spoils <= 1 decision CB had right                  H4  the skimmer corrects >= 20% of the touched-part cases
Ship (spot checks cover every part, touched or not): H1 and H2.   Kill: CA <= CB on decisions and on hidden."""
import collections, gzip, json, os, random, sys
def load(p):
    return json.load(gzip.open(p + '.gz')) if os.path.exists(p + '.gz') else json.load(open(p))
def per_fn(P):
    t = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in P: t[r['cat']][r['test']].append(r['ok'])
    return {c: sum(all(v) for v in t[c].values()) / len(t[c]) for c in t}
tot = collections.Counter(); hp = collections.defaultdict(list); diffs = []
for d in sys.argv[1:]:
    w = json.load(open(os.path.join(d, 'sheet.json'))); L = w['labels']
    F = {a: per_fn(load(os.path.join(d, f'probe_{a}.json'))) for a in ('SL', 'CB', 'CA')}
    cats = sorted(F['CB'])
    for a in F: hp[a].append(100 * sum(F[a].values()) / len(cats))
    diffs += [100 * (F['CA'][c] - F['CB'][c]) for c in cats]
    for a in ('SL', 'CB', 'CA', 'R'):
        tot[(a, 'right')] += sum(x[a] == 'right' for x in L)
    tot['n'] += len(L); tot['spoiled'] += sum(x['CB'] == 'right' and x['CA'] != 'right' for x in L)
    tot['shown'] += len(w['shown']); tot['fixes'] += len(w['fixes']); tot['confirmed'] += sum(1 for f in w['fixes'] if f.get('confirmed'))
    print(f"== {d} ({w['src']}): touched {len(w['touched'])} functions; {len(w['shown'])} cases, {len(w['fixes'])} corrected; right "
          + ', '.join(f"{a} {sum(x[a] == 'right' for x in L)}" for a in ('SL', 'CB', 'CA', 'R'))
          + '; hidden ' + ', '.join(f'{a} {hp[a][-1]:.1f}%' for a in ('SL', 'CB', 'CA')))
mean = {a: sum(v) / len(v) for a, v in hp.items()}
rng = random.Random(63); bs = sorted(sum(rng.choice(diffs) for _ in diffs) / len(diffs) for _ in range(4000))
print(f"\npooled: right SL {tot[('SL', 'right')]}, CB {tot[('CB', 'right')]}, CA {tot[('CA', 'right')]} of {tot['n']}; hidden "
      + ', '.join(f'{a} {v:.1f}%' for a, v in mean.items())
      + f"; CA − CB {sum(diffs) / len(diffs):+.1f} (95% CI {bs[100]:+.1f} to {bs[3899]:+.1f}); cases {tot['shown']}, corrected {tot['fixes']}, "
        f"confirmed {tot['confirmed']}")
fx = tot['fixes'] / max(1, tot['shown'])
res = [('H1', f"CA ≥ CB + 3 decisions: {tot[('CA', 'right')]} vs {tot[('CB', 'right')]}", tot[('CA', 'right')] >= tot[('CB', 'right')] + 3),
       ('H2', f"hidden CA ≥ CB + 3: {mean['CA'] - mean['CB']:+.1f}", mean['CA'] - mean['CB'] >= 3),
       ('H3', f"CA spoils ≤ 1 of CB's right decisions: {tot['spoiled']}", tot['spoiled'] <= 1),
       ('H4', f'the skimmer corrects ≥ 20% of the touched-part cases: {fx:.2f}', fx >= .2)]
print('\npredictions')
for tag, text, held in res:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
print(f"Ship (spot checks on every part): {'FIRED' if res[0][2] and res[1][2] else 'did not fire'}")
print(f"Kill: {'FIRED' if tot[('CA', 'right')] <= tot[('CB', 'right')] and mean['CA'] <= mean['CB'] else 'did not fire'}")
