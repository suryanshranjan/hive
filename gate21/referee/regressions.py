"""Regressions that reached main, from evaluate.py's per-commit replay. Run from the repo root:
    python gate21/referee/regressions.py <eval.json[.gz]> [agents.csv]
A regression: a visible test that passes at one commit on main (first-parent, after the run starts) and fails at the next.
Prints the number of commits with a regression, the tests involved, and whether each was fixed by the end."""
import csv, gzip, json, sys

p = sys.argv[1]
rows = json.load(gzip.open(p) if p.endswith('.gz') else open(p))
start = min(int(r['start']) for r in csv.DictReader(open(sys.argv[2]))) if len(sys.argv) > 2 else min(r['t'] for r in rows if '-w' in r['author'])
run = [r for r in rows if r['t'] >= start - 5 and r.get('visible_res')]
events, tests = 0, set()
for a, b in zip(run, run[1:]):
    lost = {k for k, v in a['visible_res'].items() if v and not b['visible_res'].get(k)}
    if lost:
        events += 1; tests |= lost
        print(f'  {b["author"]:10s} {b["subject"][:70]:70s} broke {len(lost)}: {sorted(lost)[:4]}')
final = run[-1]['visible_res'] if run else {}
print(f'commits {len(run)}; commits that broke a passing test: {events}; tests broken {len(tests)}; still broken at the end {sum(1 for t in tests if not final.get(t))}')
