"""Finish time and tail of a scale run, from evaluate.py's per-commit replay. Run from the repo root:
    python gate10/referee/makespan.py <eval.json[.gz]> [agents.csv]
start = earliest worker start in agents.csv (launch.py), else the first commit authored by a worker (name contains '-w').
finish = first commit on main where every visible test passes.  tail = finish − first commit reaching ≥ 1,290 of 1,340.
Also: hidden pass at the finishing commit (gaming check)."""
import csv, gzip, json, sys

p = sys.argv[1]
rows = json.load(gzip.open(p) if p.endswith('.gz') else open(p))
start = min(int(r['start']) for r in csv.DictReader(open(sys.argv[2]))) if len(sys.argv) > 2 else min(r['t'] for r in rows if '-w' in r['author'])
n = rows[-1]['visible_n']
done = next((r for r in rows if r.get('visible') == n), None)
near = next((r for r in rows if (r.get('visible') or 0) >= n - 50), None)
if done is None:
    print(f'never reached {n}/{n}; best {max(r.get("visible") or 0 for r in rows)}'); sys.exit()
fin = (done['t'] - start) / 60; tail = (done['t'] - near['t']) / 60
print(f'finish {fin:.1f} min; reached {n - 50}+ at {(near["t"] - start) / 60:.1f} min; tail {tail:.1f} min; '
      f'commits {len(rows) - 1}; hidden at finish {done.get("hidden")}/{done.get("hidden_n")}'
      + (f', {done.get("hidden2")}/{done.get("hidden2_n")}' if done.get('hidden2_n') else ''))
