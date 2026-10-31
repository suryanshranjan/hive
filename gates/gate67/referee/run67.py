#!/usr/bin/env python3
"""Gate 67: does Hive get better the more one owner uses it? Three features of one business, built one after another on
the same codebase, each with Hive's hand-over (code sheet, list review, spot checks on every part) by the same skimming
owner. The policy has 5 house conventions spread over all three features (prompts/rulegiver_brief.md).

usage: python3 gates/gate67/referee/run67.py [--skip-prereg-check]      (from the repo root; writes runs/g67, private/g67)

Feature 1 runs once (no memory yet) and is shared. From feature 2 on, three arms build on feature 1's final code:
  F  fresh: nothing carried over (each feature as if it were a new project)
  M  Hive as shipped: the owner's earlier corrections go to every later build as standing rulings (hive/memory.py's
     wording), and the code sheet leaves out rules that only repeat them (codesheet.split_known)
  C  M, plus house rules: after each hand-over, a model call distils the corrections so far into general house rules
     ("Across the business: ...", prompts/house_brief.md), which go to every later build too
Per feature and arm: a first build (3 builders), the describer's sheet D, the owner's list review then spot checks of
every function, a judge's labels (D and FINAL = what the second build is given), and a second build (3 builders) whose
hidden pass is scored; its code is the next feature's starting point."""
import argparse, io, json, os, shutil, subprocess, sys, threading, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
for g in ('gate55', 'gate56', 'gate57', 'gate58', 'gate60'):
    sys.path.insert(0, os.path.join(ROOT, 'gates', g, 'referee'))
sys.path.insert(0, os.path.join(ROOT, 'lab'))
import review55 as r55, review56 as r56, review58 as r58, review60 as r60
from review55 import wt, intent
import run_gate
from hive import codesheet, explain, interview

NAME = 'g67'; RUN = os.path.join(ROOT, 'runs', NAME); PRIV = os.path.join(ROOT, 'private', NAME)
P = os.path.join(ROOT, 'gates', 'gate67', 'prompts'); brief = lambda n: open(os.path.join(P, n)).read()
VSEED = {1: 67101, 2: 67102, 3: 67103}; HSEED = {1: 67200000, 2: 67300000, 3: 67400000}
LOCK = threading.Lock()

def say(m):
    with LOCK:
        print(f'[{time.strftime("%H:%M:%S")}] {m}', flush=True)

def sh(*a, cwd=None):
    r = subprocess.run(list(a), cwd=cwd, capture_output=True, text=True)
    if r.returncode: raise RuntimeError(f'failed: {" ".join(a)}\n{r.stdout}\n{r.stderr}')
    return r.stdout

WRAP = '''import importlib.util as _u, os as _os
_s = _u.spec_from_file_location('g67_full_policy', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'oracle.py'))
_m = _u.module_from_spec(_s); _s.loader.exec_module(_m)
_N = list(_m.FEATURES[{f!r}])
SPEC = {{k: _m.SPEC[k] for k in _N}}
SCALARS = {{k: _m.SCALARS[k] for k in _N}}
TYPICAL = {{k: _m.TYPICAL[k] for k in _N}}
EDGE = {{k: _m.EDGE[k] for k in _N}}
DECISIONS = {{k: _m.DECISIONS[k] for k in _N}}
DECISION_EXAMPLES = {{k: _m.DECISION_EXAMPLES[k] for k in _N}}
connect = _m.connect
'''

def memory_text(rulings, house):
    t = ''
    if rulings:   # hive/memory.py's wording, as shipped
        t += ("\n\n## The owner's standing rulings from earlier builds\nThe owner has already decided these. Follow them "
              "wherever they apply, do not ask about them again, and do not record them as your own assumptions. Do not "
              "stretch one beyond the situation it describes.\n\n" + '\n'.join(f'- {r}' for r in rulings) + '\n')
    if house:
        t += ("\n\n## The owner's house rules\nThese are how his business does things everywhere, learned from his earlier "
              "reviews. Apply them to the new functions too, wherever they fit, unless a rule above says otherwise.\n\n"
              + '\n'.join(f'- {h}' for h in house) + '\n')
    return t

def build(tag, seed, ask, workers=3):
    asks = os.path.join(RUN, f'ask_{tag}.md'); open(asks, 'w').write(f'## {tag}\n{ask}\n')
    sh(sys.executable, os.path.join(ROOT, 'lab', 'make_swarm.py'), '--run', NAME, '--seed', seed, '--prompt', os.path.join(P, 'prompt_builder.md'),
       '--ask-texts', asks, '--example-file', os.path.join(RUN, 'example.txt'), '--arm', f'{tag}:{workers}:none')
    subprocess.run([sys.executable, os.path.join(ROOT, 'lab', 'launch.py'), '--run', NAME, '--arm', tag], cwd=ROOT,
                   stdout=open(os.path.join(RUN, f'launch_{tag}.log'), 'w'), stderr=subprocess.STDOUT, check=True)
    fin = os.path.join(RUN, f'final_{tag}'); shutil.rmtree(fin, ignore_errors=True); sh('git', 'clone', '-q', os.path.join(RUN, f'up{tag}.git'), fin)
    return fin

def next_seed(k, final, arm):
    """Feature k's starting repo: the arm's last code, with feature k's spec and example tests."""
    o = intent.load_oracle(os.path.join(PRIV, f'oracle_f{k}.py')); g = intent.Gen(o)
    seed = os.path.join(RUN, f'seed_f{k}_{arm}'); shutil.rmtree(seed, ignore_errors=True); sh('git', 'clone', '-q', final, seed)
    for f in os.listdir(os.path.join(seed, 'current_tasks')):
        if f.endswith('.txt'): sh('git', 'rm', '-q', os.path.join('current_tasks', f), cwd=seed)
    intent.cmd_tests(os.path.join(PRIV, f'oracle_f{k}.py'), 'visible', os.path.join(seed, 'tests', 'visible'), VSEED[k])
    rows = [f"| `{o.SPEC[n].split(':', 1)[0].strip()}` | {o.SPEC[n].split(':', 1)[1].strip()} |" for n in g.CATS]
    rp = os.path.join(seed, 'README.md'); s = open(rp).read()
    i, j = s.index('| Function | Spec from the product team |'), s.index('`tools/ask.py` tells you')
    s = (s[:i] + '| Function | Spec from the product team |\n| --- | --- |\n' + '\n'.join(rows) + '\n\nThe functions built in earlier '
         'weeks are already in the engine; their tests must keep passing.\n\n' + s[j:])
    open(rp, 'w').write(s)
    sh('git', 'add', '-A', cwd=seed)
    sh('git', '-c', 'user.name=hive', '-c', 'user.email=hive@local', 'commit', '-q', '-m', f'Feature {k}: spec and example tests', cwd=seed)
    return seed

def feature(k, arm, seed, rulings, house, R):
    """One feature through Hive: first build, hand-over by the skimming owner, judge, second build. Returns its record."""
    tag = f'{k}{arm}'; priv = os.path.join(PRIV, f'f{tag}'); os.makedirs(priv, exist_ok=True)
    of = os.path.join(PRIV, f'oracle_f{k}.py'); o = intent.load_oracle(of); spec = wt.spec_lines(o, intent.Gen(o).CATS)
    mem = memory_text(rulings, house); rec = dict(feature=k, arm=arm, rulings_in=list(rulings), house_in=list(house), cost={})
    t0 = time.time()
    b1 = build(f'B{tag}', seed, r55.NO_RULES + mem)
    say(f'{tag}: first build done ({(time.time() - t0) / 60:.1f} min)')
    D, rec['cost']['describer'] = r56.describe('describer_brief.md', os.path.join(priv, 'describer'), b1, spec)
    shown, repeats = codesheet.split_known(D, rulings) if rulings else (list(D), [])
    sd = os.path.join(priv, 'spotter'); shutil.rmtree(sd, ignore_errors=True); os.makedirs(sd)
    shutil.copytree(b1, os.path.join(sd, 'repo'), ignore=shutil.ignore_patterns('.git'))
    _, rec['cost']['spotter'] = wt.agent(wt.AGENT, sd, brief('spotter_brief.md').replace('{BASE}', os.path.join(sd, 'repo'))
                                         .replace('{OUT}', sd).replace('{SPEC}', spec), os.path.join(sd, 'spotter.log'))
    spots = [s for s in json.load(open(os.path.join(sd, 'spots.json'))) if isinstance(s, dict) and s.get('say')]
    skim = brief('owner_skim.md').replace('{POLICY}', '\n'.join(f'- {r}' for r in R))
    SL, lrec = r55.terminal_review(shown, skim, priv, f'SL{tag}')
    touched = {s.get('function') for s in spots if any(shown[n - 1] != SL[n - 1] for n in r58.about(shown, s.get('function')) if n <= len(SL))}
    order = [s for s in spots if s.get('function') not in touched] + [s for s in spots if s.get('function') in touched]
    HV, fixes, srec = r60.review_round(SL, order, skim, priv, f'HV{tag}', f'Now {len(order)} quick checks on what the build does in real cases.')
    changed = [r for r in HV if r not in shown]
    say(f'{tag}: sheet {len(D)} rules ({len(repeats)} left out as repeats of his rulings), list {lrec["replies"]} replies, '
        f'{len(order)} cases, {len(fixes)} corrected, {len(changed)} rules changed')
    jd = os.path.join(priv, 'judge'); shutil.rmtree(jd, ignore_errors=True); os.makedirs(jd)
    shutil.copy(os.path.join(PRIV, 'oracle.py'), os.path.join(jd, 'oracle.py')); shutil.copy(of, os.path.join(jd, 'oracle_feature.py'))
    final_sheet = HV + [f'(standing ruling) {r}' for r in rulings] + [f'(house rule) {h}' for h in house]
    json.dump(dict(D=D, FINAL=final_sheet, R=R), open(os.path.join(jd, 'sheets.json'), 'w'), indent=1)
    _, rec['cost']['judge'] = wt.agent(wt.AGENT, jd, brief('judge_brief.md').replace('{DIR}', jd), os.path.join(jd, 'judge.log'))
    labels = json.load(open(os.path.join(jd, 'labels.json')))['labels']
    b2 = build(f'H{tag}', seed, r55.section('X', HV).split('\n', 2)[2] + mem)
    probe = os.path.join(RUN, f'probe_{tag}.json')
    sh(sys.executable, os.path.join(ROOT, 'lab', 'intent.py'), 'probe', of, b2, probe, str(HSEED[k]))
    P_ = json.load(open(probe)); tests = {}
    for r in P_: tests.setdefault(r['test'], []).append(r['ok'])
    rec.update(decisions=o.DECISIONS, D=D, shown=shown, repeats=repeats, SL=SL, HV=HV, spots=spots, shown_cases=order, fixes=fixes, changed=changed,
               list_review=lrec, spot_review=srec, labels=labels, hidden_tests=sum(all(v) for v in tests.values()), hidden_total=len(tests),
               minutes=round((time.time() - t0) / 60, 1))
    rec['cost'].update(owner_list=lrec['cost'], owner_spots=srec['cost'])
    json.dump(rec, open(os.path.join(RUN, f'feature_{tag}.json'), 'w'), indent=1, default=str)
    say(f'{tag}: hidden {rec["hidden_tests"]}/{rec["hidden_total"]}; done in {rec["minutes"]} min')
    return rec, b2

def house_rules(rulings):
    got = explain.ask_json(brief('house_brief.md').replace('{RULINGS}', '\n'.join(f'- {r}' for r in rulings)))
    return [h.strip() for h in (got or {}).get('house', []) if isinstance(h, str) and h.strip()] if isinstance(got, dict) else []

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--skip-prereg-check', action='store_true'); ap.add_argument('--resume', action='store_true')
    a = ap.parse_args()
    if not a.skip_prereg_check: run_gate.prereg_check('gates/gate67/prompts/PREDICTIONS.md')
    os.makedirs(RUN, exist_ok=True); os.makedirs(PRIV, exist_ok=True)
    full = os.path.join(PRIV, 'oracle.py')
    if not os.path.exists(full):
        say('rule-giver writing one business\'s policy (15 functions, 3 features, 5 house conventions)...')
        with open(os.path.join(PRIV, 'rulegiver.json'), 'w') as out:
            subprocess.run(wt.AGENT, cwd=PRIV, input=brief('rulegiver_brief.md').replace('{DIR}', PRIV), stdout=out, stderr=subprocess.STDOUT, text=True)
    o = intent.load_oracle(full)
    assert set(o.FEATURES) == {'f1', 'f2', 'f3'} and sorted(sum(o.FEATURES.values(), [])) == sorted(o.SCALARS), 'FEATURES must split the 15 functions'
    conv = [c for c in o.CONVENTIONS]
    for c in conv:
        used = {f for f, ls in o.DECISIONS.items() if f'convention: {c}' in ls}
        assert len(used) >= 4 and all(any(f in o.FEATURES[k] for f in used) for k in o.FEATURES), f'convention {c!r} must span 4+ functions in every feature'
    run_gate.check_rules(full)
    for k in (1, 2, 3):
        open(os.path.join(PRIV, f'oracle_f{k}.py'), 'w').write(WRAP.format(f=f'f{k}'))
    say('policy checked: ' + '; '.join(f'{k}: {", ".join(v)}' for k, v in o.FEATURES.items()))
    pre = os.path.join(RUN, 'pre.json')
    if not os.path.exists(pre):
        r55.P = P; r55.pre(RUN, full)
    R = json.load(open(pre))['R']; r56.P = P; r58.P = P
    # feature 1: shared by every arm (nothing to remember yet)
    f1 = os.path.join(RUN, 'feature_1S.json')
    if a.resume and os.path.exists(f1):
        rec1 = json.load(open(f1)); fin1 = os.path.join(RUN, 'final_H1S')
    else:
        sh(sys.executable, os.path.join(ROOT, 'lab', 'new_intent_gate.py'), '--name', NAME, '--oracle', os.path.join(PRIV, 'oracle_f1.py'),
           '--visible-seed', str(VSEED[1]), '--hidden-seed', str(HSEED[1]))
        rec1, fin1 = feature(1, 'S', os.path.join(RUN, 'seed'), [], [], R)
    mem = {'F': ([], []), 'M': (list(rec1['changed']), []), 'C': (list(rec1['changed']), house_rules(rec1['changed']))}
    say(f"after feature 1: {len(rec1['changed'])} rulings; house rules for C: {mem['C'][1]}")
    def arm_chain(arm):
        rulings, house = mem[arm]; fin = fin1
        for k in (2, 3):
            seed = next_seed(k, fin, arm)
            rec, fin = feature(k, arm, seed, rulings, house, R)
            if arm in ('M', 'C'):
                rulings = rulings + rec['changed']
            if arm == 'C':
                house = house_rules(rulings)
                say(f'C after feature {k}: {len(house)} house rules')
    ts = [threading.Thread(target=arm_chain, args=(arm,)) for arm in ('F', 'M', 'C')]
    [t.start() for t in ts]; [t.join() for t in ts]
    say('done: python3 gates/gate67/referee/analyze.py runs/g67')

if __name__ == '__main__':
    main()
