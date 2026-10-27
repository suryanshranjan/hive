"""Where questions point (post-hoc, Gate 12). Run from the repo root: python gates/gate12/referee/targeting.py
1. Share of asked values that are generic invalid inputs: an argument that is NULL, empty/blank text, or text
   with no letters-or-digits pattern a spec would accept (a word like 'garbage', 'abc', 'not a date', 'xyz', 'invalid').
2. Unreached errors: N0 edge errors still wrong in all of Q1, Q2 and Q4 (the same call fails for every team)."""
import gzip, json, re

GENERIC = re.compile(r"\bNULL\b|''|'\s+'|'(?:garbage|abc|xyz|invalid|not a date|n/a|foo|bar|nan|none|null|-|\?)'", re.I)

def call_args(sql):
    # split 'SELECT F(a), F(b), F(c)' into the three argument strings (good enough for these logs)
    return re.findall(r'[A-Z_]+\((.*?)\)(?:,\s*(?=[A-Z_]+\()|$)', sql.strip())

for arm in ('Q1', 'Q2', 'Q4'):
    n = g = 0
    for l in open(f'gates/gate12/results/asks_{arm}.log'):
        r = json.loads(l)
        if not r.get('charged'): continue
        for a in call_args(r['sql']):
            n += 1; g += bool(GENERIC.search(a))
    print(f'{arm}: {n} asked values, {g} generic invalid ({g / n:.0%})')

P = {a: json.load(gzip.open(f'gates/gate12/results/probe_{a}.json.gz')) for a in ('N0', 'Q1', 'Q2', 'Q4')}
key = lambda r: (r['cat'], r['test'], r['q'])
wrong = {a: {key(r) for r in P[a] if r['kind'] == 'edge' and not r['ok']} for a in P}
e0 = len(wrong['N0']); stuck = wrong['N0'] & wrong['Q1'] & wrong['Q2'] & wrong['Q4']
print(f'N0 edge errors {e0}; still wrong in every asking team {len(stuck)} ({len(stuck) / e0:.0%}); '
      f'wrong in Q4 {len(wrong["Q4"])}, of which unreached by all {len(stuck & wrong["Q4"]) / max(1, len(wrong["Q4"])):.0%}')
