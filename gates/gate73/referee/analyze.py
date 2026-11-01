"""G73 registered analysis (committed with the predictions, before any team runs):
    python3 gates/gate73/referee/analyze.py runs/g73a runs/g73b
t95 / tdone = minutes from the arm's start to the first landing after which >= 95% / all visible tests pass (1,360: the
engine's 1,340 and the business examples; inf if never); engine hidden as in Gate 50 (local-SQLite-disagreeing categories
left out); business hidden = the business functions' hidden tests passed (intent probe). Means over the two runs.
Questions = those put to the owner (a repeated question answered from an earlier one is not counted; Hive's own count).
Y1 S7Q's tdone <= 0.8x A1's     Y2 S7Q business hidden >= A1 - 2     Y3 S7D business hidden >= A1 - 2
Y4 S7D's questions <= 1.1x A1's
Claim (Hive's swarm, as fixed, beats one agent on a mixed job: sooner and as right): Y1 and Y2."""
import collections, csv, glob, json, math, os, sqlite3, sys
bad = {'median', 'percentile', 'transactions'}
cat = lambda tid: tid.rsplit('_', 1)[0]
M = collections.defaultdict(list)
for d in sys.argv[1:]:
    teams = json.load(open(os.path.join(d, 'teams.json')))
    rows = collections.defaultdict(float)
    for r in csv.DictReader(open(os.path.join(d, 'agents.csv'))): rows[r['worker'].split('-w')[0]] += float(r['cost_usd'] or 0)
    for arm, v in teams.items():
        t0 = v['team_start']; prog = [p for p in v['progress'] if p['visible'] is not None and p['t'] >= t0 - 5]
        total = len(v['visible'])
        first = lambda k: (min(p['t'] for p in prog if p['visible'] >= k) - t0) / 60 if any(p['visible'] >= k for p in prog) else math.inf
        h = {k: ok for k, ok in v['hidden'].items() if cat(k) not in bad}
        P = json.load(open(os.path.join(d, f'probe_{arm}.json'))); tests = collections.defaultdict(list)
        for r in P: tests[r['test']].append(r['ok'])
        q = sum(1 for _ in open(os.path.join(d, f'owner_{arm}.jsonl'))) if os.path.exists(os.path.join(d, f'owner_{arm}.jsonl')) else 0
        row = dict(t95=first(math.ceil(.95 * total)), tdone=first(total), visible=sum(v['visible'].values()), total=total,
                   engine=100 * sum(h.values()) / len(h), business=100 * sum(all(x) for x in tests.values()) / len(tests),
                   questions=q, cost=rows[arm], minutes=(v['team_end'] - t0) / 60)
        for k, x in row.items(): M[(arm, k)].append(x)
        print(f"== {d} {arm}: t95 {row['t95']:.1f}, tdone {row['tdone']:.1f}, wall {row['minutes']:.1f} min; visible {row['visible']}/{total}; "
              f"engine hidden {row['engine']:.1f}%, business hidden {row['business']:.1f}%; {q} questions; ${row['cost']:.2f}")
m = lambda a, k: sum(M[(a, k)]) / len(M[(a, k)])
print('\nmeans: ' + '; '.join(f"{a}: tdone {m(a, 'tdone'):.1f} min, engine {m(a, 'engine'):.1f}%, business {m(a, 'business'):.1f}%, "
                             f"{m(a, 'questions'):.1f} questions, ${m(a, 'cost'):.2f}" for a in ('A1', 'S7D', 'S7Q')))
res = [('Y1', f"S7Q tdone ≤ 0.8 × A1: {m('S7Q', 'tdone') / m('A1', 'tdone'):.2f}×", m('S7Q', 'tdone') <= .8 * m('A1', 'tdone')),
       ('Y2', f"S7Q business ≥ A1 − 2: {m('S7Q', 'business') - m('A1', 'business'):+.1f}", m('S7Q', 'business') - m('A1', 'business') >= -2),
       ('Y3', f"S7D business ≥ A1 − 2: {m('S7D', 'business') - m('A1', 'business'):+.1f}", m('S7D', 'business') - m('A1', 'business') >= -2),
       ('Y4', f"S7D asks ≤ 1.1 × A1: {m('S7D', 'questions') / max(1, m('A1', 'questions')):.2f}×", m('S7D', 'questions') <= 1.1 * m('A1', 'questions'))]
print('\npredictions')
for tag, text, held in res:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
print(f"Claim (Hive's swarm beats one agent on a mixed job: sooner and as right): {'FIRED' if res[0][2] and res[1][2] else 'did not fire'}")
