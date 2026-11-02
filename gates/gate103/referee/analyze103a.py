"""Scores Gate 103a's registered predictions from runs/g103_replay/*.json."""
import glob, json
rs = [json.load(open(p)) for p in sorted(glob.glob('runs/g103_replay/*.json'))]
bad = lambda r: r['hidden'] < r['of'] - 3        # a failed flight: below 24 of 27 / 26 of 29
flag = lambda r: bool(r['result'] and r['result']['failing'])
for r in rs:
    x = r['result']; print(f"{r['flight']:16} hidden {r['hidden']}/{r['of']}  rules {r['rules']:2}  " +
          (f"checks {x['checks']:2} failing {len(x['failing'])} ${x['cost'] or 0:.2f}" if x else 'did not run'))
fails = [r for r in rs if bad(r)]; good = [r for r in rs if not bad(r) and r['hidden'] >= r['of'] - 1]
ran = [r for r in rs if r['result']]
f1f3 = [r for r in rs if r['flight'] in ('g101_day2_F1', 'g101_day2_F3')]
fa = sum(flag(r) for r in good); cost = sum((r['result'] or {}).get('cost') or 0 for r in ran) / max(1, len(ran))
print(f"\nfailed flights flagged {sum(flag(r) for r in fails)}/{len(fails)}; good (>= of-1) flagged {fa}/{len(good)}; ran {len(ran)}/{len(rs)}; mean ${cost:.2f}")
print('R1 F1 and F3 both flagged ->', 'held' if all(flag(r) for r in f1f3) and len(f1f3) == 2 else 'failed')
print('R2 good flights flagged <= 20% ->', 'held' if fa <= 0.2 * len(good) else 'failed', f'({fa}/{len(good)})')
print('R3 failed flights flagged >= 3 of 5 ->', 'held' if sum(flag(r) for r in fails) >= 3 else 'failed')
print('R4 mean cost <= $0.40 ->', 'held' if cost <= 0.40 else 'failed')
