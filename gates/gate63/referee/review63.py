#!/usr/bin/env python3
"""Gate 63: spot checks on the parts the owner's list review touched, too (Gate 60's open question about the skip rule).

usage: review63.py <g60 run: g60a | g60b> <oracle.py>      (from the repo root; after Gate 60's run exists)

Gate 60's hand-over showed spot checks only for the functions the skimmer's list review left as they were (Gate 58's
rule, also Hive's). From Gate 60's own records (the same build, sheet D, spot checks and owner brief):
  g60a: the list touched 4 of 10 functions. CA = CB's sheet, then the spot checks of those 4 functions.
  g60b: the list touched all 10, so CB = SL. CA = SL's sheet, then the spot checks of all 10 functions.
Each correction is applied alone and re-shown (Gate 58's machinery). The judge relabels SL, CB, CA and R together. Then 3
fresh builders build CA from Gate 60's starting repo; its hidden pass is compared with Gate 60's CB build (same suite)."""
import json, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
for g in ('gate55', 'gate56', 'gate57', 'gate58', 'gate60'):
    sys.path.insert(0, os.path.join(ROOT, 'gates', g, 'referee'))
import review60 as r60, review55 as r55, review58 as r58
from review55 import wt, intent, say
import run_gate

P = os.path.join(ROOT, 'gates', 'gate63', 'prompts')

def main(src, oracle):
    run_gate.prereg_check('gates/gate63/prompts/PREDICTIONS.md')
    name = 'g63' + src[-1]; run = os.path.join(ROOT, 'runs', name); priv = os.path.join(ROOT, 'private', name)
    shutil.rmtree(run, ignore_errors=True); os.makedirs(run); os.makedirs(priv, exist_ok=True)
    w = json.load(open(os.path.join(ROOT, 'runs', src, 'sheet.json')))
    R, D, spots = w['R'], w['D'], w['spots']; SL = w['reviews']['SL']['rules']; CB = w['reviews']['CB']['rules']
    touched = set(w['reviews']['CB']['skipped_functions'])
    shown = [s for s in spots if s.get('function') in touched]
    r58.P = os.path.join(ROOT, 'gates', 'gate60', 'prompts')
    skim = open(os.path.join(ROOT, 'gates', 'gate60', 'prompts', 'owner_skim.md')).read().replace('{POLICY}', '\n'.join(f'- {r}' for r in R))
    say(f'{name}: {len(shown)} spot checks on the {len(touched)} functions the list touched, after CB\'s sheet')
    CA, fixes, rec = r60.review_round(CB, shown, skim, priv, 'CA', f'Now {len(shown)} quick checks on what the build does in real cases.')
    say(f'{name}: CA {len(fixes)} corrected, {sum(1 for f in fixes if f.get("confirmed"))} confirmed on re-show')
    jd = os.path.join(priv, 'judge'); shutil.rmtree(jd, ignore_errors=True); os.makedirs(jd)
    shutil.copy(oracle, os.path.join(jd, 'oracle.py'))
    json.dump(dict(D=D, SL=SL, CB=CB, CA=CA, R=R), open(os.path.join(jd, 'sheets.json'), 'w'), indent=1)
    _, jc = wt.agent(wt.AGENT, jd, open(os.path.join(P, 'judge_brief.md')).read().replace('{DIR}', jd), os.path.join(jd, 'judge.log'))
    labels = json.load(open(os.path.join(jd, 'labels.json')))['labels']
    asks = os.path.join(run, 'ask_texts.md'); open(asks, 'w').write(r55.section('CA', CA))
    subprocess.run([sys.executable, os.path.join(ROOT, 'lab', 'make_swarm.py'), '--run', name, '--seed', os.path.join(ROOT, 'runs', src, 'seed'),
                    '--prompt', os.path.join(ROOT, 'gates', 'gate60', 'prompts', 'prompt_builder.md'), '--ask-texts', asks,
                    '--example-file', os.path.join(ROOT, 'runs', src, 'example.txt'), '--arm', 'CA:3:none'], check=True, cwd=ROOT)
    subprocess.run([sys.executable, os.path.join(ROOT, 'lab', 'launch.py'), '--run', name, '--arm', 'CA'], check=True, cwd=ROOT)
    fin = os.path.join(run, 'final_CA'); shutil.rmtree(fin, ignore_errors=True)
    subprocess.run(['git', 'clone', '-q', os.path.join(run, 'upCA.git'), fin], check=True)
    seed = json.load(open(os.path.join(ROOT, 'lab', 'experiments', f'{src}_wings.json')))['hidden_seed']
    subprocess.run([sys.executable, os.path.join(ROOT, 'lab', 'intent.py'), 'probe', oracle, fin, os.path.join(run, 'probe_CA.json'), str(seed)],
                   check=True, cwd='/')
    for a in ('SL', 'CB'):
        shutil.copy(os.path.join(ROOT, 'runs', src, f'probe_{a}.json'), os.path.join(run, f'probe_{a}.json'))
    json.dump(dict(src=src, touched=sorted(touched), shown=shown, fixes=fixes, review=rec, CA=CA, labels=labels,
                   cost_usd=dict(owner=rec['cost'], judge=jc)), open(os.path.join(run, 'sheet.json'), 'w'), indent=1)
    say(f'{name} done')

if __name__ == '__main__':
    main(sys.argv[1], os.path.abspath(sys.argv[2]))   # the probes run from '/'
