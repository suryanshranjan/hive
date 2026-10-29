"""G47 correction to the registered analysis (written after the run, disclosed in RESULTS.md):
    python3 gates/gate47/referee/recount.py runs/g47
The registered analyze.py replayed the seed's own history (Gates 1-2: 15 commits, up to 362 visible tests) as if it
were team work. The seed's last commit, which cut the engine back to the 9-test skeleton, is authored "hive", and the
replay skips that author, so every team's first landing (9 tests) looked like a fall from 362: one false "break" per
team, and 15 unattributed landings. This counts only commits made after the team started, from 9 tests."""
import collections, csv, json, os, sys

d = sys.argv[1]
T = json.load(open(os.path.join(d, 'teams.json')))
ag = {r['worker']: r['agent'] for r in csv.DictReader(open(os.path.join(d, 'agents.csv')))}
for t, v in T.items():
    if v.get('lead_agent'):
        ag[f'{t}-lead'] = v['lead_agent']
print('team  landings by agent           codex share  breaks (a landing after which >= 20 more tests fail)')
for team, v in T.items():
    t0, prev, breaks, lands = v['team_start'], 9, [], collections.Counter()
    for p in v['progress']:
        if p['t'] < t0 or p['visible'] is None:
            continue
        a = ag.get(p['who'], '?')
        if not p['subject'].startswith('BRAIN'):
            lands[a] += 1
        if p['visible'] <= prev - 20:
            breaks.append(f"{p['who']} ({a}) {prev} -> {p['visible']}")
        prev = p['visible']
    share = f"{100 * lands['codex'] / sum(lands.values()):.0f}%" if lands['codex'] else '-'
    print(f'{team:4s}  {str(dict(lands)):26s}  {share:>11s}  {breaks or "none"}')
