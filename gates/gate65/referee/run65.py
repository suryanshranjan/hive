#!/usr/bin/env python3
"""Gate 65: a stronger model for Hive's own judgement call. Spot checks chosen by an Opus spotter against today's
(Sonnet) spotter, with the same skimming owner, from Gate 60's records.

usage: run65.py <g60 run: g60a | g60b> <oracle.py>      (from the repo root)

From Gate 60's run: the same N0 build, sheet D, the owner's list review SL, policy and owner brief.
  CS  SL, then the spot checks Gate 60's (Sonnet) spotter wrote from N0's code, on every function (Gate 63's hand-over:
      functions the list left as they were first, then the ones it changed)
  CO  SL, then the spot checks an Opus spotter writes now from the same code with the same brief, in the same order
Each in a fresh owner session; each correction applied alone and re-shown (Gate 58's machinery). A judge labels D, SL,
CS, CO and R together; 3 fresh builders build CS and CO from Gate 60's starting repo; both probed on Gate 60's hidden
suite. The oracle is used only by the judge and the probe."""
import json, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
for g in ('gate55', 'gate56', 'gate57', 'gate58', 'gate60'):
    sys.path.insert(0, os.path.join(ROOT, 'gates', g, 'referee'))
import review60 as r60, review55 as r55, review58 as r58
from review55 import wt, intent, say
import run_gate

P = os.path.join(ROOT, 'gates', 'gate65', 'prompts'); P60 = os.path.join(ROOT, 'gates', 'gate60', 'prompts')
OPUS = wt.AGENT + ['--model', 'opus']

def ordered(spots, D, SL):
    touched = {s.get('function') for s in spots
               if any(D[n - 1] != SL[n - 1] for n in r58.about(D, s.get('function')) if n <= len(SL))}
    return [s for s in spots if s.get('function') not in touched] + [s for s in spots if s.get('function') in touched]

def main(src, oracle):
    run_gate.prereg_check('gates/gate65/prompts/PREDICTIONS.md')
    name = 'g65' + src[-1]; run = os.path.join(ROOT, 'runs', name); priv = os.path.join(ROOT, 'private', name)
    shutil.rmtree(run, ignore_errors=True); os.makedirs(run); os.makedirs(priv, exist_ok=True)
    w = json.load(open(os.path.join(ROOT, 'runs', src, 'sheet.json')))
    R, D, SL, spots_s = w['R'], w['D'], w['reviews']['SL']['rules'], w['spots']
    o = intent.load_oracle(oracle); spec = wt.spec_lines(o, intent.Gen(o).CATS)
    sd = os.path.join(priv, 'spotter_opus'); shutil.rmtree(sd, ignore_errors=True); os.makedirs(sd)
    shutil.copytree(os.path.join(ROOT, 'runs', src, 'final_N0'), os.path.join(sd, 'repo'), ignore=shutil.ignore_patterns('.git'))
    _, c_spot = wt.agent(OPUS, sd, open(os.path.join(P60, 'spotter_brief.md')).read().replace('{BASE}', os.path.join(sd, 'repo'))
                         .replace('{OUT}', sd).replace('{SPEC}', spec), os.path.join(sd, 'spotter.log'))
    spots_o = [s for s in json.load(open(os.path.join(sd, 'spots.json'))) if isinstance(s, dict) and s.get('say')]
    assert spots_o, 'the Opus spotter wrote no spot checks'
    say(f'{name}: Sonnet spotter {len(spots_s)} cases (Gate 60), Opus spotter {len(spots_o)} cases (${c_spot:.2f})')
    r58.P = P60
    skim = open(os.path.join(P60, 'owner_skim.md')).read().replace('{POLICY}', '\n'.join(f'- {r}' for r in R))
    out = {}
    for arm, spots in (('CS', spots_s), ('CO', spots_o)):
        shown = ordered(spots, D, SL)
        rules, fixes, rec = r60.review_round(SL, shown, skim, priv, arm, f'Now {len(shown)} quick checks on what the build does in real cases.')
        out[arm] = dict(rules=rules, fixes=fixes, shown=shown, review=rec)
        say(f'{name} {arm}: {len(shown)} cases, {len(fixes)} corrected, {sum(1 for f in fixes if f.get("confirmed"))} confirmed')
    jd = os.path.join(priv, 'judge'); shutil.rmtree(jd, ignore_errors=True); os.makedirs(jd)
    shutil.copy(oracle, os.path.join(jd, 'oracle.py'))
    json.dump(dict(D=D, SL=SL, CS=out['CS']['rules'], CO=out['CO']['rules'], R=R), open(os.path.join(jd, 'sheets.json'), 'w'), indent=1)
    _, c_judge = wt.agent(wt.AGENT, jd, open(os.path.join(P, 'judge_brief.md')).read().replace('{DIR}', jd), os.path.join(jd, 'judge.log'))
    labels = json.load(open(os.path.join(jd, 'labels.json')))['labels']
    asks = os.path.join(run, 'ask_texts.md'); open(asks, 'w').write(r55.section('CS', out['CS']['rules']) + r55.section('CO', out['CO']['rules']))
    subprocess.run([sys.executable, os.path.join(ROOT, 'lab', 'make_swarm.py'), '--run', name, '--seed', os.path.join(ROOT, 'runs', src, 'seed'),
                    '--prompt', os.path.join(P60, 'prompt_builder.md'), '--ask-texts', asks,
                    '--example-file', os.path.join(ROOT, 'runs', src, 'example.txt'), '--arm', 'CS:3:none', '--arm', 'CO:3:none'], check=True, cwd=ROOT)
    subprocess.run([sys.executable, os.path.join(ROOT, 'lab', 'launch.py'), '--run', name, '--arm', 'CS', '--arm', 'CO'], check=True, cwd=ROOT)
    seed = json.load(open(os.path.join(ROOT, 'lab', 'experiments', f'{src}_wings.json')))['hidden_seed']
    for arm in ('CS', 'CO'):
        fin = os.path.join(run, f'final_{arm}'); shutil.rmtree(fin, ignore_errors=True)
        subprocess.run(['git', 'clone', '-q', os.path.join(run, f'up{arm}.git'), fin], check=True)
        subprocess.run([sys.executable, os.path.join(ROOT, 'lab', 'intent.py'), 'probe', oracle, fin, os.path.join(run, f'probe_{arm}.json'),
                        str(seed)], check=True, cwd='/')
    json.dump(dict(src=src, arms={a: dict(shown=v['shown'], fixes=v['fixes'], review=v['review'], rules=v['rules']) for a, v in out.items()},
                   labels=labels, cost_usd=dict(spotter_opus=c_spot, owner_CS=out['CS']['review']['cost'],
                                                owner_CO=out['CO']['review']['cost'], judge=c_judge)),
              open(os.path.join(run, 'sheet.json'), 'w'), indent=1)
    say(f'{name} done')

if __name__ == '__main__':
    main(sys.argv[1], os.path.abspath(sys.argv[2]))
