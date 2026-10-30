"""G65 registered analysis (committed with the predictions, before the run):
    python3 gates/gate65/referee/analyze.py runs/g65a runs/g65b
Pooled over both runs (50 declared decisions; one judge per run saw D, SL, CS, CO and R together).
K1  CO states >= 3 more decisions right than CS          K2  hidden CO >= CS + 3 (mean over runs)
K3  the Opus spotter writes at most 1.3x as many cases     K4  CO spoils <= 1 decision SL had right
Ship (Hive's spotter runs on Opus): K1 and K2.    Kill: CO <= CS on decisions and on hidden."""
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
    F = {a: per_fn(load(os.path.join(d, f'probe_{a}.json'))) for a in ('CS', 'CO')}
    cats = sorted(F['CS'])
    for a in F: hp[a].append(100 * sum(F[a].values()) / len(cats))
    diffs += [100 * (F['CO'][c] - F['CS'][c]) for c in cats]
    for a in ('D', 'SL', 'CS', 'CO', 'R'): tot[(a, 'right')] += sum(x[a] == 'right' for x in L)
    tot['n'] += len(L); tot['spoiled'] += sum(x['SL'] == 'right' and x['CO'] != 'right' for x in L)
    for a in ('CS', 'CO'):
        v = w['arms'][a]; tot[(a, 'shown')] += len(v['shown']); tot[(a, 'fixes')] += len(v['fixes'])
    print(f"== {d} ({w['src']}): cases CS {len(w['arms']['CS']['shown'])}, CO {len(w['arms']['CO']['shown'])}; corrected CS "
          f"{len(w['arms']['CS']['fixes'])}, CO {len(w['arms']['CO']['fixes'])}; right " + ', '.join(f"{a} {sum(x[a] == 'right' for x in L)}"
          for a in ('D', 'SL', 'CS', 'CO', 'R')) + f"; hidden CS {hp['CS'][-1]:.1f}%, CO {hp['CO'][-1]:.1f}%; costs {w['cost_usd']}")
mean = {a: sum(v) / len(v) for a, v in hp.items()}
rng = random.Random(65); bs = sorted(sum(rng.choice(diffs) for _ in diffs) / len(diffs) for _ in range(4000))
rC, rO = tot[('CS', 'right')], tot[('CO', 'right')]; share = tot[('CO', 'shown')] / max(1, tot[('CS', 'shown')])
print(f"\npooled: right SL {tot[('SL', 'right')]}, CS {rC}, CO {rO} of {tot['n']}; hidden CS {mean['CS']:.1f}%, CO {mean['CO']:.1f}%; "
      f"CO − CS {sum(diffs) / len(diffs):+.1f} (95% CI {bs[100]:+.1f} to {bs[3899]:+.1f}); cases CS {tot[('CS', 'shown')]}, CO {tot[('CO', 'shown')]}; "
      f"corrected CS {tot[('CS', 'fixes')]}, CO {tot[('CO', 'fixes')]}")
res = [('K1', f'CO ≥ CS + 3 decisions: {rO} vs {rC}', rO >= rC + 3),
       ('K2', f"hidden CO ≥ CS + 3: {mean['CO'] - mean['CS']:+.1f}", mean['CO'] - mean['CS'] >= 3),
       ('K3', f'Opus cases ≤ 1.3× Sonnet\'s: {share:.2f}', share <= 1.3),
       ('K4', f"CO spoils ≤ 1 of SL's right decisions: {tot['spoiled']}", tot['spoiled'] <= 1)]
print('\npredictions')
for tag, text, held in res:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
print(f"Ship (the spotter on Opus): {'FIRED' if res[0][2] and res[1][2] else 'did not fire'}")
print(f"Kill: {'FIRED' if rO <= rC and mean['CO'] <= mean['CS'] else 'did not fire'}")
