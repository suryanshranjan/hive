"""G43 registered analysis (committed with the predictions, before any team runs). Run from the repo root:
    python3 gates/gate43/referee/analyze.py runs/g43
Per team: finish = last landing on main (a commit not titled "Lock:" and not the seed's) minus the team's first start;
wall = last worker exit minus first start; cost from agents.csv; hidden pass on the gen2 suite, leaving out categories
where this machine's SQLite disagrees with the stored visible answers (Gate 10's rule; median and percentile always out);
messages = board lines; conflicts and guard blocks from the workers' HIVE_LOG files where they exported it.
S = mean of S1 and S2, T = mean of T1 and T2.
T1: 0.85 ≤ finish_T / finish_S ≤ 1.15 (talking neither speeds up nor slows down by more than 15%).
T2: cost_T ≥ 1.10 × cost_S.     T3: |hidden_T − hidden_S| ≤ 2 points.     T4: every talking team posts ≥ 6 messages.
T5: (conflicts + guard blocks) per landing, T ≤ S.
Ship: finish_T ≤ 0.80 × finish_S in both pairings (T1 vs S1, T2 vs S2) with cost_T ≤ 1.10 × cost_S → Hive offers a board.
Kill (for talking): finish_T ≥ finish_S and cost_T > cost_S → silent stays."""
import csv, collections, glob, json, os, sqlite3, sys

d = sys.argv[1]
teams = json.load(open(os.path.join(d, 'teams.json')))
rows = collections.defaultdict(list)
for r in csv.DictReader(open(os.path.join(d, 'agents.csv'))): rows[r['worker'].split('-w')[0]].append(r)
# categories where the local SQLite disagrees with the stored visible answers (seed tests, same for every team)
bad = {'median', 'percentile'}
con_tests = sorted(glob.glob(os.path.join(d, 'seed_S', 'tests', 'visible', '*.json')))
def norm(v):
    if isinstance(v, (int, float)) and not isinstance(v, bool): return ('n', round(float(v), 6))
    return ('0',) if v is None else ('s', str(v))
for f in con_tests:
    t = json.load(open(f))
    try:
        c = sqlite3.connect(':memory:')
        for s in t.get('setup', []): c.execute(s)
        got = [tuple(norm(v) for v in r) for r in c.execute(t['query']).fetchall()]
        exp = [tuple(norm(v) for v in r) for r in t['expected']]
        if (got if t.get('ordered') else sorted(got)) != (exp if t.get('ordered') else sorted(exp)): bad.add(t['category'])
    except Exception:
        bad.add(t['category'])
cat = lambda tid: tid.rsplit('_', 1)[0]
res = {}
for team, v in teams.items():
    start = min(int(r['start']) for r in rows[team]); end = max(int(r['end']) for r in rows[team])
    lands = [c for c in v['commits'] if not c['subject'].startswith('Lock:') and c['who'] not in ('hive',)
             and not c['subject'].startswith('tools/') and c['t'] >= start - 5]
    finish = (max(c['t'] for c in lands) - start) / 60 if lands else float('nan')
    h = {k: ok for k, ok in v['hidden'].items() if cat(k) not in bad}
    board = os.path.join(d, f'board_{team}.txt')
    msgs = open(board).read().splitlines() if os.path.exists(board) else []
    ev = collections.Counter()
    for lg in glob.glob(os.path.join(d, 'logs', f'{team}-w*.log')):
        for line in open(lg):
            p = line.split()
            if len(p) > 1: ev[p[1]] += 1
    res[team] = dict(finish=finish, wall=(end - start) / 60, cost=sum(float(r['cost_usd'] or 0) for r in rows[team]),
                     tokens=sum(int(r['tokens'] or 0) for r in rows[team]), landings=len(lands),
                     visible=sum(v['visible'].values()), visible_n=len(v['visible']),
                     hidden=100 * sum(h.values()) / len(h) if h else float('nan'), hidden_n=len(h), messages=len(msgs),
                     posters=len({m.split(' ', 2)[1] for m in msgs if len(m.split(' ', 2)) > 2}),
                     conflicts=ev['CONFLICT'], blocks=ev['BLOCKED_DUP'] + ev['BLOCKED_REGRESSION'], logged_lands=ev['LAND'])
print(f'hidden categories left out (local SQLite disagrees with stored answers): {sorted(bad)}')
print('team  finish  wall  cost   landings  visible     hidden   messages(posters)  conflicts  blocks  logged LAND')
for t in ('S1', 'T1', 'T2', 'S2'):
    r = res[t]
    print(f'{t:4s} {r["finish"]:6.1f} {r["wall"]:6.1f} ${r["cost"]:5.2f} {r["landings"]:6d}   {r["visible"]:4d}/{r["visible_n"]}  '
          f'{r["hidden"]:6.1f}%   {r["messages"]:4d} ({r["posters"]})        {r["conflicts"]:4d}   {r["blocks"]:4d}   {r["logged_lands"]:4d}')
m = lambda k, a: (res[a + '1'][k] + res[a + '2'][k]) / 2
fS, fT, cS, cT, hS, hT = m('finish', 'S'), m('finish', 'T'), m('cost', 'S'), m('cost', 'T'), m('hidden', 'S'), m('hidden', 'T')
print(f'\nmeans: finish S {fS:.1f} vs T {fT:.1f} min (ratio {fT / fS:.2f}); cost S ${cS:.2f} vs T ${cT:.2f} '
      f'(ratio {cT / cS:.2f}); hidden S {hS:.1f}% vs T {hT:.1f}%')
rate = lambda a: sum(res[a + k]['conflicts'] + res[a + k]['blocks'] for k in '12') / max(1, sum(res[a + k]['logged_lands'] for k in '12'))
print('\npredictions')
for tag, text, held in [
        ('T1', f'0.85 ≤ finish ratio ≤ 1.15: {fT / fS:.2f}', .85 <= fT / fS <= 1.15),
        ('T2', f'cost ratio ≥ 1.10: {cT / cS:.2f}', cT / cS >= 1.10),
        ('T3', f'|hidden T − S| ≤ 2: {hT - hS:+.1f}', abs(hT - hS) <= 2),
        ('T4', f'each talking team ≥ 6 messages: {res["T1"]["messages"]}, {res["T2"]["messages"]}', min(res['T1']['messages'], res['T2']['messages']) >= 6),
        ('T5', f'(conflicts + blocks) per logged landing T ≤ S: {rate("T"):.2f} vs {rate("S"):.2f}', rate('T') <= rate('S'))]:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
ship = all(res[t]['finish'] <= .8 * res[s]['finish'] for t, s in (('T1', 'S1'), ('T2', 'S2'))) and cT <= 1.1 * cS
print(f'Ship (T ≥ 20% faster in both pairings, cost ≤ 1.10×): {"FIRED" if ship else "did not fire"}')
print(f'Kill for talking (not faster and costlier): {"FIRED" if fT >= fS and cT > cS else "did not fire"}')
