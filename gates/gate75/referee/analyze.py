"""G75 registered analysis (committed with the predictions, before any team runs):
    python3 gates/gate75/referee/analyze.py runs/g75a:private/g75a/oracle.py:75200000 runs/g75b:private/g75b/oracle.py:75400000
Time to accuracy: every landing on the arm's main is probed on the business functions' hidden tests (intent probe);
T_acc = minutes from the arm's start to the first landing after which >= 99% of visible tests pass AND >= 90% of the
business hidden tests pass (the arm's wall minutes if never). Final engine hidden as in Gate 50; final business hidden.
V1 S7B's T_acc <= 0.6x A1's (mean over runs)    V2 S7B final business >= A1 - 3    V3 S7B final engine >= A1 - 1
Claim (Hive's split swarm reaches the same accuracy much sooner): V1 and V2."""
import collections, csv, json, math, os, shutil, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
bad = {'median', 'percentile', 'transactions'}; cat = lambda tid: tid.rsplit('_', 1)[0]
def business(up, h, oracle, seed):
    with tempfile.TemporaryDirectory() as t:
        w = os.path.join(t, 'w'); subprocess.run(['git', 'clone', '-q', up, w], check=True)
        subprocess.run(['git', 'checkout', '-q', h], cwd=w, check=True); out = os.path.join(t, 'p.json')
        subprocess.run([sys.executable, os.path.join(ROOT, 'lab', 'intent.py'), 'probe', os.path.abspath(oracle), w, out, str(seed)],
                       cwd='/', capture_output=True, timeout=900)
        try:
            P = json.load(open(out))
        except Exception:
            return 0.0
    t = collections.defaultdict(list)
    for r in P: t[r['test']].append(r['ok'])
    return 100 * sum(all(v) for v in t.values()) / len(t)
M = collections.defaultdict(list)
for arg in sys.argv[1:]:
    d, oracle, seed = arg.split(':'); teams = json.load(open(os.path.join(d, 'teams.json')))
    cost = collections.defaultdict(float)
    for r in csv.DictReader(open(os.path.join(d, 'agents.csv'))): cost[r['worker'].split('-w')[0]] += float(r['cost_usd'] or 0)
    for arm, v in teams.items():
        t0 = v['team_start']; total = len(v['visible']); tacc = None; series = []
        for p in v['progress']:
            if p['visible'] is None or p['t'] < t0 - 5: continue
            if p['visible'] >= math.ceil(.99 * total):
                b = business(os.path.join(d, f'up{arm}.git'), p['hash'], oracle, int(seed)); series.append(((p['t'] - t0) / 60, round(b, 1)))
                if b >= 90 and tacc is None:
                    tacc = (p['t'] - t0) / 60
        wall = (v['team_end'] - t0) / 60
        h = {k: ok for k, ok in v['hidden'].items() if cat(k) not in bad}
        P = json.load(open(os.path.join(d, f'probe_{arm}.json'))); tt = collections.defaultdict(list)
        for r in P: tt[r['test']].append(r['ok'])
        row = dict(tacc=tacc if tacc is not None else wall, reached=tacc is not None, wall=wall, engine=100 * sum(h.values()) / len(h),
                   business=100 * sum(all(x) for x in tt.values()) / len(tt), cost=cost[arm],
                   questions=sum(1 for _ in open(os.path.join(d, f'owner_{arm}.jsonl'))) if os.path.exists(os.path.join(d, f'owner_{arm}.jsonl')) else 0)
        for k, x in row.items(): M[(arm, k)].append(x)
        print(f"== {d} {arm}: T_acc {row['tacc']:.1f} min{'' if row['reached'] else ' (never reached; wall)'}, wall {wall:.1f}; final business "
              f"{row['business']:.1f}%, engine {row['engine']:.1f}%; {row['questions']} questions; ${row['cost']:.2f}; business at 99% visible: {series[:8]}")
m = lambda a, k: sum(M[(a, k)]) / len(M[(a, k)])
print('\nmeans: ' + '; '.join(f"{a}: T_acc {m(a, 'tacc'):.1f} min, business {m(a, 'business'):.1f}%, engine {m(a, 'engine'):.1f}%, "
                             f"{m(a, 'questions'):.1f} questions, ${m(a, 'cost'):.2f}" for a in ('A1', 'S7B')))
res = [('V1', f"S7B T_acc ≤ 0.6 × A1: {m('S7B', 'tacc') / m('A1', 'tacc'):.2f}×", m('S7B', 'tacc') <= .6 * m('A1', 'tacc')),
       ('V2', f"S7B business ≥ A1 − 3: {m('S7B', 'business') - m('A1', 'business'):+.1f}", m('S7B', 'business') - m('A1', 'business') >= -3),
       ('V3', f"S7B engine ≥ A1 − 1: {m('S7B', 'engine') - m('A1', 'engine'):+.1f}", m('S7B', 'engine') - m('A1', 'engine') >= -1)]
print('\npredictions')
for tag, text, held in res:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
print(f"Claim (the split swarm reaches the same accuracy much sooner): {'FIRED' if res[0][2] and res[1][2] else 'did not fire'}")
