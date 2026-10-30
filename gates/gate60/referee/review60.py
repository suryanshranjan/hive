#!/usr/bin/env python3
"""Gate 60 steps: two wings. Two independent builds of the same spec; the skimming owner sees only the cases where they
disagree (DG), against Gate 58's combined review (CB), both after the same list review (SL).

usage: review60.py pre   <run dir> <oracle.py>              the owner's policy in prose (R); ask texts for N0 and B
       review60.py after <run dir> <oracle.py> <N0's repo>  from the builds' code (never the oracle):
         D    the describer's sheet of N0's code (Gate 58's brief)
         spots  Gate 58's spotter on N0's code (2-5 cases per function)
         wings  a prober writes 30 calls per function from the spec alone (prompts/prober_brief.md); both builds (N0 and
                B, runs/<name>/final_B) run them (wings.py); a selector turns each function's disagreements into at
                most 4 plain cases (prompts/selector_brief.md)
       The same skimming owner, in separate sessions:
         SL   reviews D as a rule list (as Gates 55-58)
         CB   SL, then Gate 58's spot checks of every function the list left as it was, each correction applied alone
              and its case shown again
         DG   SL, then the disagreement cases of every function the list left as it was, handled exactly as CB's
       The judge labels D, SL, CB, DG and R before any stage-2 build. The oracle is used only by the judge here (and by
       analyze.py afterwards)."""
import io, json, os, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
for g in ('gate55', 'gate56', 'gate57', 'gate58', 'gate60'):
    sys.path.insert(0, os.path.join(ROOT, 'gates', g, 'referee'))
import review55 as r55, review56 as r56, review58 as r58
from review55 import wt, intent, say
from hive import explain
import wings

P = os.path.join(ROOT, 'gates', 'gate60', 'prompts')
brief = lambda name: open(os.path.join(P, name)).read()
PER_FN = 4

def pre(run, oracle_path):
    r55.P = P; r55.pre(run, oracle_path)
    with open(os.path.join(run, 'ask_texts.md'), 'a') as f:
        f.write('\n## B\n' + r55.NO_RULES + '\n')

def review_round(rules, cases, skim, priv, name, intro):
    """Gate 58's spot round (r58.spot_round) with its own folder and opening line, so CB and DG run identically."""
    od = os.path.join(priv, f'review_{name}'); shutil.rmtree(od, ignore_errors=True); os.makedirs(od)
    term, log, cost, fixes = io.StringIO(), [], [0.0], []
    term.write(f"Hive: {intro} Press Enter if a result is right, or say what should happen instead.\n")
    for k, s in enumerate(cases, 1):
        typed = r58.ask_owner(term, skim, od, log, f"\nCase {k} of {len(cases)}. {s['say']}\n  Right? (Enter = yes, or say what "
                                                    "should happen) > ", cost)
        say(f'{name} case #{k}: {typed[:80]!r}')
        if not typed:
            continue
        fix = dict(shown=s['say'], said=typed, function=s.get('function'), rounds=1)
        rules = r58.apply_one(rules, s.get('function'), s['say'], typed)
        now = r58.recheck(rules, s.get('function'), s['say'])
        fix['now'] = now
        if now:
            again = r58.ask_owner(term, skim, od, log, f"\n  With your correction: {now}\n  Right now? (Enter = yes, or say what "
                                                       "should happen) > ", cost)
            fix['confirmed'] = not again
            if again:
                fix['said_again'] = again; fix['rounds'] = 2
                rules = r58.apply_one(rules, s.get('function'), now, again)
        fixes.append(fix)
    return rules, fixes, dict(replies=len(log), cost=round(cost[0], 3), log=log, transcript=term.getvalue())

def run_build(target, calls_path, agg, out):
    subprocess.run([sys.executable, os.path.join(ROOT, 'gates', 'gate60', 'referee', 'wings.py'), 'run', os.path.abspath(target), os.path.abspath(calls_path), agg, out],
                   cwd='/', check=True, timeout=3600)
    return json.load(open(out))

def disagreement_cases(o, spec, priv, final_a, final_b, cost):
    """The prober's calls, run on both builds; each function's disagreements turned into at most PER_FN plain cases."""
    names = intent.Gen(o).CATS; agg = intent.Gen(o).AGG or ''
    wd = os.path.join(priv, 'wings'); shutil.rmtree(wd, ignore_errors=True); os.makedirs(wd)
    pd = os.path.join(wd, 'prober'); os.makedirs(pd)
    _, cost['prober'] = wt.agent(wt.AGENT, pd, brief('prober_brief.md').replace('{OUT}', pd).replace('{SPEC}', spec),
                                 os.path.join(pd, 'prober.log'))
    calls = [c for c in json.load(open(os.path.join(pd, 'calls.json'))) if isinstance(c, dict) and c.get('function') in names]
    assert calls, 'prober wrote no calls'
    cp = os.path.join(wd, 'calls.json'); json.dump(calls, open(cp, 'w'))
    A = run_build(final_a, cp, agg, os.path.join(wd, 'out_A.json'))
    B = run_build(final_b, cp, agg, os.path.join(wd, 'out_B.json'))
    lines = {l.split('`')[1].split('(')[0]: l for l in spec.splitlines() if '`' in l}
    cases, per = [], {}
    sel_cost0 = explain.SPENT[0]
    for f in names:
        diffs = [(c, a, b) for c, a, b in zip(calls, A, B) if c['function'] == f and a and b and not wings.same(a, b)]
        per[f] = dict(calls=sum(1 for c in calls if c['function'] == f), disagree=len(diffs))
        if not diffs:
            continue
        listing = '\n'.join(f"- {wings.label(c, agg)}; our build: {wings.shown(a)}; second build: {wings.shown(b)}"
                            for c, a, b in diffs[:40])
        got = explain.ask_json(brief('selector_brief.md').replace('{SPEC_LINE}', lines.get(f, f)).replace('{LIST}', listing))
        picked = [x for x in (got or {}).get('cases', []) if isinstance(x, dict) and isinstance(x.get('say'), str) and x['say'].strip()] \
            if isinstance(got, dict) else []
        for x in picked[:PER_FN]:
            cases.append(dict(function=f, call=str(x.get('call', '')), say=x['say'].strip()))
        per[f]['cases'] = len(picked[:PER_FN])
    cost['selector'] = round(explain.SPENT[0] - sel_cost0, 3)
    return cases, dict(calls=calls, A=A, B=B, per_function=per)

def after(run, oracle_path, base_repo):
    name = os.path.basename(run); priv = os.path.join(ROOT, 'private', name)
    o = intent.load_oracle(oracle_path); spec = wt.spec_lines(o, intent.Gen(o).CATS)
    pre_rec = json.load(open(os.path.join(run, 'pre.json'))); R = pre_rec['R']; cost = dict(pre_rec['cost_usd'])
    r56.P = P; r58.P = P
    D, cost['describer'] = r56.describe('describer_brief.md', os.path.join(priv, 'describer'), base_repo, spec)
    sd = os.path.join(priv, 'spotter'); shutil.rmtree(sd, ignore_errors=True); os.makedirs(sd); shutil.copytree(base_repo, os.path.join(sd, 'repo'))
    _, cost['spotter'] = wt.agent(wt.AGENT, sd, brief('spotter_brief.md').replace('{BASE}', os.path.join(sd, 'repo'))
                                  .replace('{OUT}', sd).replace('{SPEC}', spec), os.path.join(sd, 'spotter.log'))
    spots = [s for s in json.load(open(os.path.join(sd, 'spots.json'))) if isinstance(s, dict) and s.get('say')]
    assert spots, 'spotter wrote no spot checks'
    dg_cases, wing = disagreement_cases(o, spec, priv, base_repo, os.path.join(run, 'final_B'), cost)
    say(f'D: {len(D)} rules; {len(spots)} spot checks; {len(wing["calls"])} probe calls, '
        f'{sum(v["disagree"] for v in wing["per_function"].values())} disagree; {len(dg_cases)} disagreement cases')
    skim = brief('owner_skim.md').replace('{POLICY}', '\n'.join(f'- {r}' for r in R))
    out = {}
    t0 = time.time(); SL, rec = r55.terminal_review(D, skim, priv, 'SL'); rec['minutes'] = round((time.time() - t0) / 60, 1)
    rec['rules'] = SL; out['SL'] = rec; cost['owner_SL'] = rec['cost']
    say(f'SL: {len(SL)} rules after review, {rec["replies"]} replies, {rec["minutes"]} min')
    fns = {s.get('function') for s in spots} | {c['function'] for c in dg_cases}
    touched = {f for f in fns if any(D[n - 1] != SL[n - 1] for n in r58.about(D, f) if n <= len(SL))}
    for arm, cases, intro in (('CB', spots, 'Now {n} quick checks on what the build does in real cases.'),
                              ('DG', dg_cases, 'Now {n} quick checks on real cases where a second, independent build of the '
                                           'same spec came out differently.')):
        shown = [c for c in cases if c.get('function') not in touched]
        t0 = time.time()
        rules, fixes, rec_s = review_round(SL, shown, skim, priv, arm, intro.format(n=len(shown)))
        out[arm] = dict(rules=rules, spots=rec_s, fixes=fixes, shown=shown, skipped_functions=sorted(touched),
                        minutes=round((time.time() - t0) / 60, 1), replies=rec['replies'] + rec_s['replies'])
        cost[f'owner_{arm}'] = rec_s['cost']
        say(f'{arm}: {len(shown)} cases shown ({len(touched)} functions skipped as changed by the list), {len(fixes)} corrected, '
            f'{sum(1 for f in fixes if f.get("confirmed"))} confirmed on re-show')
    jd = os.path.join(priv, 'judge'); shutil.rmtree(jd, ignore_errors=True); os.makedirs(jd)
    shutil.copy(oracle_path, os.path.join(jd, 'oracle.py'))
    json.dump(dict(D=D, SL=SL, CB=out['CB']['rules'], DG=out['DG']['rules'], R=R), open(os.path.join(jd, 'sheets.json'), 'w'), indent=1)
    say('judge labelling every declared decision...')
    _, cost['judge'] = wt.agent(wt.AGENT, jd, brief('judge_brief.md').replace('{DIR}', jd), os.path.join(jd, 'judge.log'))
    labels = json.load(open(os.path.join(jd, 'labels.json')))['labels']
    with open(os.path.join(run, 'ask_texts.md'), 'a') as f:
        f.write(r55.section('SL', SL) + r55.section('CB', out['CB']['rules']) + r55.section('DG', out['DG']['rules']))
    json.dump(dict(R=R, D=D, reviews=out, spots=spots, dg_cases=dg_cases, wings=wing, cost_usd=cost, labels=labels),
              open(os.path.join(run, 'sheet.json'), 'w'), indent=1, default=str)
    say('ask texts for SL, CB and DG written')

if __name__ == '__main__':
    {'pre': lambda: pre(sys.argv[2], sys.argv[3]), 'after': lambda: after(sys.argv[2], sys.argv[3], sys.argv[4])}[sys.argv[1]]()
