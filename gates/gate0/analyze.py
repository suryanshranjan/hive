"""Gate 0 analysis: regressions on a hidden external suite across the C compiler's history.
A regression = a test that passed at an earlier sampled commit and fails now.
Reports: pass curve, regressions introduced, lifetime (tau), tests broken per event (k),
live-regression count over time (Little's law check L = X*f*tau), and red-main share."""
import sys, os, glob, collections, statistics as st, math, json

def load(resdir):
    rows = {}
    for line in open(os.path.join(resdir, 'log.txt')):
        p = line.split()
        if len(p) < 4 or p[0] == 'DONE':
            continue
        i, h, t, status = int(p[0]), p[1], int(p[2]), p[3]
        res = None
        if status == 'OK':
            res = {}
            for ext, tag in (('txt', 'cts:'), ('tor', 'tor:')):
                f = os.path.join(resdir, f'{i}.{ext}')
                if os.path.exists(f):
                    res.update({tag + l.split()[0]: l.split()[1] == 'PASS' for l in open(f) if len(l.split()) == 2})
        rows[i] = dict(i=i, h=h, t=t, status=status, res=res)
    return sorted(rows.values(), key=lambda r: r['t'])

def analyze(rows, label, per_commit_gap):
    rows = [r for r in rows if r['res'] is not None]
    if len(rows) < 3:
        print(label, 'too few builds'); return None
    tests = sorted(set().union(*[set(r['res']) for r in rows]))
    t0 = rows[0]['t']
    ever = set(); live = {}; events = []; L = []
    for idx, r in enumerate(rows):
        hrs = (r['t'] - t0) / 3600
        new_fail = []
        for tn in tests:
            ok = r['res'].get(tn, False)
            if ok:
                ever.add(tn)
                if tn in live:
                    ev = live.pop(tn); ev['fixed_at'] = hrs; ev['fixed_idx'] = idx; events.append(ev)
            else:
                if tn in ever and tn not in live:
                    live[tn] = dict(test=tn, intro_at=hrs, intro_idx=idx, commit_i=r['i'])
                    new_fail.append(tn)
        L.append(dict(hrs=hrs, commit=r['i'], passing=sum(r['res'].values()), live=len(live), new=len(new_fail)))
    open_ev = list(live.values())
    # group simultaneous introductions into one event (same sampled commit)
    byc = collections.defaultdict(list)
    for ev in events + open_ev: byc[ev['commit_i']].append(ev)
    ks = [len(v) for v in byc.values()]
    taus_h = [ev['fixed_at'] - ev['intro_at'] for ev in events]
    taus_c = [(ev['fixed_idx'] - ev['intro_idx']) * per_commit_gap for ev in events]
    span_h = L[-1]['hrs']; nbuilds = len(rows)
    nevents = len(byc)
    landings = nbuilds * per_commit_gap
    f = nevents / landings
    red = sum(1 for x in L if x['live'] > 0) / len(L)
    out = dict(label=label, builds=nbuilds, span_h=span_h, tests=len(tests), final_pass=L[-1]['passing'],
               events=nevents, test_regressions=len(events) + len(open_ev), still_open=len(open_ev),
               f_per_landing=f, k_median=st.median(ks) if ks else None, k_max=max(ks) if ks else None,
               tau_h_median=st.median(taus_h) if taus_h else None, tau_h_mean=st.mean(taus_h) if taus_h else None,
               tau_commits_median=st.median(taus_c) if taus_c else None,
               live_mean=st.mean(x['live'] for x in L), live_max=max(x['live'] for x in L), red_share=red,
               curve=L, events_detail=[dict(test=e['test'], intro_h=round(e['intro_at'], 1), life_h=round(e['fixed_at'] - e['intro_at'], 1)) for e in events])
    # Little's law: L = (events per hour) * mean lifetime (in test-regressions)
    if taus_h:
        rate = (len(events) + len(open_ev)) / span_h
        out['little_pred_live'] = rate * st.mean(taus_h)
    return out

if __name__ == '__main__':
    base = os.path.dirname(os.path.abspath(__file__))
    results = {}
    for name, gap in (('res2_coarse', 20), ('res2_fine', 1)):
        d = os.path.join(base, name)
        if not os.path.exists(os.path.join(d, 'log.txt')):
            continue
        rows = load(d)
        for suite in ('cts', 'tor', 'both'):
          sub = [dict(r, res=None if r['res'] is None else {k: v for k, v in r['res'].items() if suite == 'both' or k.startswith(suite)}) for r in rows]
          out = analyze(sub, name + ':' + suite, gap)
          if out:
            results[name + ':' + suite] = out
            print(f"\n== {name}: {out['builds']} builds over {out['span_h']:.0f} h, final pass {out['final_pass']}/{out['tests']}")
            print(f"   regression events {out['events']} ({out['test_regressions']} test-regressions, {out['still_open']} still open at end)")
            print(f"   f = {out['f_per_landing']:.4f} regression events per landing; tests broken per event: median {out['k_median']}, max {out['k_max']}")
            print(f"   lifetime tau: median {out['tau_h_median']} h, mean {out['tau_h_mean'] and round(out['tau_h_mean'],1)} h, median {out['tau_commits_median']} commits")
            print(f"   live regressions: mean {out['live_mean']:.2f}, max {out['live_max']}, main red {out['red_share']:.0%} of samples; Little's law predicts mean live {out.get('little_pred_live', float('nan')):.2f}")
            print('   pass curve (h: passing/live):', ' '.join(f"{x['hrs']:.0f}:{x['passing']}/{x['live']}" for x in out['curve'][::max(1, len(out['curve'])//25)]))
            if out['events_detail']:
                print('   events:', out['events_detail'][:40])
    json.dump(results, open(os.path.join(base, 'gate0_results.json'), 'w'), indent=1)
