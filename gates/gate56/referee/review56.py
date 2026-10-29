#!/usr/bin/env python3
"""Gate 56 steps: a short sheet for the skimming owner.

usage: review56.py pre   <run dir> <oracle.py>              the owner's policy in prose (R), the ask text for N0
       review56.py after <run dir> <oracle.py> <N0's repo>  two describers read N0's code (never the oracle): D in full
                                                           (Gate 55's brief) and DS, business choices only (at most 30
                                                           rules); the same skimming owner reviews each, separately, as a
                                                           rule list in a terminal: SF (from D) and SS (from DS).
Gate 55's review functions are reused unchanged. The judge labels D, DS, SF, SS and R before any stage-2 build."""
import json, os, shutil, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'gates', 'gate55', 'referee'))
import review55 as r55
from review55 import wt, intent, interview, say

P = os.path.join(ROOT, 'gates', 'gate56', 'prompts')

def pre(run, oracle_path):
    r55.P = P; r55.pre(run, oracle_path)

def describe(brief, dd, repo, spec):
    shutil.rmtree(dd, ignore_errors=True); os.makedirs(dd); shutil.copytree(repo, os.path.join(dd, 'repo'))
    _, c = wt.agent(wt.AGENT, dd, open(os.path.join(P, brief)).read().replace('{BASE}', os.path.join(dd, 'repo'))
                    .replace('{OUT}', dd).replace('{SPEC}', spec), os.path.join(dd, 'describer.log'))
    rules = [r.strip() for r in json.load(open(os.path.join(dd, 'rules.json'))) if isinstance(r, str) and r.strip()]
    assert rules, f'{brief} wrote no rules'
    return rules, c

def after(run, oracle_path, base_repo):
    name = os.path.basename(run); priv = os.path.join(ROOT, 'private', name)
    o = intent.load_oracle(oracle_path); spec = wt.spec_lines(o, intent.Gen(o).CATS)
    pre_rec = json.load(open(os.path.join(run, 'pre.json'))); R = pre_rec['R']; cost = dict(pre_rec['cost_usd'])
    D, cost['describer_full'] = describe('describer_brief.md', os.path.join(priv, 'describer_full'), base_repo, spec)
    DS, cost['describer_short'] = describe('describer_short_brief.md', os.path.join(priv, 'describer_short'), base_repo, spec)
    say(f'D: {len(D)} rules in full; DS: {len(DS)} business choices')
    skim = open(os.path.join(P, 'owner_skim.md')).read().replace('{POLICY}', '\n'.join(f'- {r}' for r in R))
    out = {}
    for arm, sheet in (('SF', D), ('SS', DS)):
        t0 = time.time()
        try:
            C, rec = r55.terminal_review(sheet, skim, priv, arm)
        except Exception:
            import traceback; C, rec = list(sheet), dict(replies=None, cost=None, error=traceback.format_exc())
        rec['minutes'] = round((time.time() - t0) / 60, 1); rec['rules'] = C; out[arm] = rec; cost[f'owner_{arm}'] = rec.get('cost')
        say(f'{arm}: {len(sheet)} rules shown, {len(C)} after review, {rec.get("replies")} replies, {rec["minutes"]} min')
    jd = os.path.join(priv, 'judge'); shutil.rmtree(jd, ignore_errors=True); os.makedirs(jd)
    shutil.copy(oracle_path, os.path.join(jd, 'oracle.py'))
    json.dump(dict(D=D, DS=DS, SF=out['SF']['rules'], SS=out['SS']['rules'], R=R), open(os.path.join(jd, 'sheets.json'), 'w'), indent=1)
    say('judge labelling every declared decision...')
    _, cost['judge'] = wt.agent(wt.AGENT, jd, open(os.path.join(P, 'judge_brief.md')).read().replace('{DIR}', jd),
                                os.path.join(jd, 'judge.log'))
    labels = json.load(open(os.path.join(jd, 'labels.json')))['labels']
    with open(os.path.join(run, 'ask_texts.md'), 'a') as f:
        f.write(''.join(r55.section(a, out[a]['rules']) for a in ('SF', 'SS')))
    json.dump(dict(R=R, D=D, DS=DS, reviews=out, cost_usd=cost, labels=labels), open(os.path.join(run, 'sheet.json'), 'w'), indent=1)
    say('ask texts for SF and SS written')

if __name__ == '__main__':
    {'pre': lambda: pre(sys.argv[2], sys.argv[3]), 'after': lambda: after(sys.argv[2], sys.argv[3], sys.argv[4])}[sys.argv[1]]()
