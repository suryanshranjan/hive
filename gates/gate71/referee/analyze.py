"""G71 registered analysis (committed with the predictions, before the run):
    python3 gates/gate71/referee/analyze.py runs/g71a runs/g71b
minutes = from the arm's first builder start to its last builder end (agents.csv); questions from the owner's log;
owner busy share = questions x 60 s / minutes. Means over the two runs.
T1 S7 takes <= 0.67x A1's minutes     T2 S7 hidden >= A1 - 3     T3 S7 asks <= 1.5x A1's questions
T4 the owner is S7's bottleneck: busy share >= 0.6
Claim (Hive's swarm keeps its speed on a big job with a busy owner): T1 and T2."""
import collections, csv, gzip, json, os, sys
def load(p):
    return json.load(gzip.open(p + '.gz')) if os.path.exists(p + '.gz') else json.load(open(p))
def per_fn(P):
    t = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in P: t[r['cat']][r['test']].append(r['ok'])
    return {c: sum(all(v) for v in t[c].values()) / len(t[c]) for c in t}
M = collections.defaultdict(list)
for d in sys.argv[1:]:
    rows = collections.defaultdict(list)
    for r in csv.DictReader(open(os.path.join(d, 'agents.csv'))): rows[r['worker'].split('-w')[0]].append(r)
    line = []
    for a in ('A1', 'S7'):
        F = per_fn(load(os.path.join(d, f'probe_{a}.json'))); hp = 100 * sum(F.values()) / len(F)
        mins = (max(int(r['end']) for r in rows[a]) - min(int(r['start']) for r in rows[a])) / 60
        p = os.path.join(d, f'owner_{a}.jsonl'); q = sum(1 for _ in open(p)) if os.path.exists(p) else 0
        cost = sum(float(r['cost_usd'] or 0) for r in rows[a]); busy = q * 60 / 60 / mins if mins else 0
        for k, v in (('hidden', hp), ('minutes', mins), ('questions', q), ('cost', cost), ('busy', busy)): M[(a, k)].append(v)
        line.append(f'{a}: hidden {hp:.1f}%, {mins:.1f} min, {q} questions, owner busy {busy:.2f}, ${cost:.2f}')
    print(f'== {d}: ' + '; '.join(line))
m = lambda a, k: sum(M[(a, k)]) / len(M[(a, k)])
print('\nmeans: ' + '; '.join(f"{a}: hidden {m(a, 'hidden'):.1f}%, {m(a, 'minutes'):.1f} min, {m(a, 'questions'):.1f} questions, "
                             f"busy {m(a, 'busy'):.2f}, ${m(a, 'cost'):.2f}" for a in ('A1', 'S7')))
res = [('T1', f"S7 ≤ 0.67 × A1's minutes: {m('S7', 'minutes') / m('A1', 'minutes'):.2f}×", m('S7', 'minutes') <= .67 * m('A1', 'minutes')),
       ('T2', f"S7 hidden ≥ A1 − 3: {m('S7', 'hidden') - m('A1', 'hidden'):+.1f}", m('S7', 'hidden') - m('A1', 'hidden') >= -3),
       ('T3', f"S7 asks ≤ 1.5 × A1: {m('S7', 'questions') / max(1, m('A1', 'questions')):.2f}×", m('S7', 'questions') <= 1.5 * m('A1', 'questions')),
       ('T4', f"S7's owner busy share ≥ 0.6: {m('S7', 'busy'):.2f}", m('S7', 'busy') >= .6)]
print('\npredictions')
for tag, text, held in res:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
print(f"Claim (the swarm keeps its speed with a busy owner): {'FIRED' if res[0][2] and res[1][2] else 'did not fire'}")
