#!/usr/bin/env python3
"""Gate 57 steps: spot checks on concrete outcomes against the rule list, for the skimming owner.

usage: review57.py pre   <run dir> <oracle.py>              the owner's policy in prose (R), the ask text for N0
       review57.py after <run dir> <oracle.py> <N0's repo>  from N0's code (never the oracle): the describer writes D, and a
                                                           spotter runs the code on up to 30 concrete cases where it made a
                                                           non-obvious choice. The same skimming owner, in two separate
                                                           sessions:
         SL  reviews D as a rule list (interview.confirm_sheet, Gates 55-56)
         SP  sees the spot checks one at a time ("Case 3 of 30. <outcome>. Right? Enter = yes, or say what should
             happen"); his corrections are applied to D by one model call (prompts/apply_brief.md)
The judge labels D, SL, SP and R before any stage-2 build."""
import contextlib, io, json, os, shutil, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'gates', 'gate55', 'referee')); sys.path.insert(0, os.path.join(ROOT, 'gates', 'gate56', 'referee'))
import review55 as r55, review56 as r56
from review55 import wt, intent, say
from hive import explain

P = os.path.join(ROOT, 'gates', 'gate57', 'prompts')

def pre(run, oracle_path):
    r55.P = P; r55.pre(run, oracle_path)

def spot_review(spots, brief, priv):
    od = os.path.join(priv, 'review_SP'); shutil.rmtree(od, ignore_errors=True); os.makedirs(od)
    term, log, cost, fixes = io.StringIO(), [], [0.0], []
    term.write(f"Hive: Before I hand it over, {len(spots)} quick checks on what the build does in real cases. "
               "Press Enter if a result is right, or say what should happen instead.\n")
    for k, s in enumerate(spots, 1):
        prompt = f"\nCase {k} of {len(spots)}. {s['say']}\n  Right? (Enter = yes, or say what should happen) > "
        term.write(prompt)
        reply, c = r55.owner_reply(brief, term.getvalue(), od, log); cost[0] += c
        typed = '' if reply.strip('`').upper() in ('ENTER', '(ENTER)', '') or reply.lower().startswith(("yes, that's right", 'yes', 'right', 'correct')) and len(reply) < 25 else reply
        term.write(typed + '\n'); log.append(dict(case=s['say'], typed=typed))
        say(f'SP owner #{k}: {typed[:80]!r}')
        if typed:
            fixes.append(dict(shown=s['say'], said=typed, function=s.get('function'), call=s.get('call'), got=s.get('got')))
    return fixes, dict(replies=len(log), cost=round(cost[0], 3), log=log, transcript=term.getvalue())

def apply(D, fixes):
    if not fixes:
        return list(D)
    got = explain.ask_json(open(os.path.join(P, 'apply_brief.md')).read()
                           .replace('{RULES}', '\n'.join(f'{n}. {r}' for n, r in enumerate(D, 1)))
                           .replace('{CORRECTIONS}', '\n'.join(f'- Shown: {f["shown"]} He said: {f["said"]}' for f in fixes)))
    rules = [r for r in (got or {}).get('rules', []) if isinstance(r, str) and r.strip()]
    return rules if len(rules) >= len(D) * 0.8 else list(D) + [f'{f["shown"]} The owner says: {f["said"]}' for f in fixes]

def after(run, oracle_path, base_repo):
    name = os.path.basename(run); priv = os.path.join(ROOT, 'private', name)
    o = intent.load_oracle(oracle_path); spec = wt.spec_lines(o, intent.Gen(o).CATS)
    pre_rec = json.load(open(os.path.join(run, 'pre.json'))); R = pre_rec['R']; cost = dict(pre_rec['cost_usd'])
    r56.P = P
    D, cost['describer'] = r56.describe('describer_brief.md', os.path.join(priv, 'describer'), base_repo, spec)
    sd = os.path.join(priv, 'spotter'); shutil.rmtree(sd, ignore_errors=True); os.makedirs(sd); shutil.copytree(base_repo, os.path.join(sd, 'repo'))
    _, cost['spotter'] = wt.agent(wt.AGENT, sd, open(os.path.join(P, 'spotter_brief.md')).read()
                                  .replace('{BASE}', os.path.join(sd, 'repo')).replace('{OUT}', sd).replace('{SPEC}', spec),
                                  os.path.join(sd, 'spotter.log'))
    spots = [s for s in json.load(open(os.path.join(sd, 'spots.json'))) if isinstance(s, dict) and s.get('say')][:30]
    assert spots, 'spotter wrote no spot checks'
    say(f'D: {len(D)} rules; {len(spots)} spot checks')
    skim = open(os.path.join(P, 'owner_skim.md')).read().replace('{POLICY}', '\n'.join(f'- {r}' for r in R))
    out = {}
    t0 = time.time(); C, rec = r55.terminal_review(D, skim, priv, 'SL'); rec['minutes'] = round((time.time() - t0) / 60, 1)
    rec['rules'] = C; out['SL'] = rec; cost['owner_SL'] = rec['cost']
    say(f'SL: {len(C)} rules after review, {rec["replies"]} replies, {rec["minutes"]} min')
    t0 = time.time(); fixes, rec = spot_review(spots, skim, priv); SP = apply(D, fixes)
    rec.update(minutes=round((time.time() - t0) / 60, 1), rules=SP, fixes=fixes, spots=spots); out['SP'] = rec; cost['owner_SP'] = rec['cost']
    say(f'SP: {len(fixes)} of {len(spots)} outcomes corrected, {len(SP)} rules after applying, {rec["minutes"]} min')
    jd = os.path.join(priv, 'judge'); shutil.rmtree(jd, ignore_errors=True); os.makedirs(jd)
    shutil.copy(oracle_path, os.path.join(jd, 'oracle.py'))
    json.dump(dict(D=D, SL=out['SL']['rules'], SP=SP, R=R), open(os.path.join(jd, 'sheets.json'), 'w'), indent=1)
    say('judge labelling every declared decision...')
    _, cost['judge'] = wt.agent(wt.AGENT, jd, open(os.path.join(P, 'judge_brief.md')).read().replace('{DIR}', jd),
                                os.path.join(jd, 'judge.log'))
    labels = json.load(open(os.path.join(jd, 'labels.json')))['labels']
    with open(os.path.join(run, 'ask_texts.md'), 'a') as f:
        f.write(r55.section('SL', out['SL']['rules']) + r55.section('SP', SP))
    json.dump(dict(R=R, D=D, reviews=out, cost_usd=cost, labels=labels), open(os.path.join(run, 'sheet.json'), 'w'), indent=1)
    say('ask texts for SL and SP written')

if __name__ == '__main__':
    {'pre': lambda: pre(sys.argv[2], sys.argv[3]), 'after': lambda: after(sys.argv[2], sys.argv[3], sys.argv[4])}[sys.argv[1]]()
