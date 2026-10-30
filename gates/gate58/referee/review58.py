#!/usr/bin/env python3
"""Gate 58 steps: the combined review for the skimming owner (Gate 57's conjecture): the rule list first, then spot checks
covering every function, each correction applied on its own and its case shown again.

usage: review58.py pre   <run dir> <oracle.py>              the owner's policy in prose (R), the ask text for N0
       review58.py after <run dir> <oracle.py> <N0's repo>  from N0's code (never the oracle): the describer writes D, and a
                                                           spotter runs the code on 2-5 cases per function. The same
                                                           skimming owner, in two separate sessions:
         SL  reviews D as a rule list (interview.confirm_sheet, as Gates 55-57)
         CB  continues from SL's list review (the same owner, so the spot checks' gain is measured alone): he sees the
             spot checks of every function whose rules the list left as they were, one at a time; each correction is applied by itself to that function's rules
             (prompts/apply_one_brief.md), and the case is worked out again from the new rules (prompts/recheck_brief.md)
             and shown once more ("Now: ... Right?"); a second correction is applied the same way
The judge labels D, SL, CB and R before any stage-2 build."""
import io, json, os, shutil, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
for g in ('gate55', 'gate56', 'gate57'):
    sys.path.insert(0, os.path.join(ROOT, 'gates', g, 'referee'))
import review55 as r55, review56 as r56
from review55 import wt, intent, say
from hive import explain

P = os.path.join(ROOT, 'gates', 'gate58', 'prompts')
brief = lambda name: open(os.path.join(P, name)).read()

def pre(run, oracle_path):
    r55.P = P; r55.pre(run, oracle_path)

def about(rules, fn):
    """Numbers (1-based) of the rules about one function."""
    return [n for n, r in enumerate(rules, 1) if fn and fn in r]

def apply_one(rules, fn, shown, said):
    """His one correction, applied to that function's rules only (Gate 57: one rewrite of the whole sheet lost detail)."""
    nums = about(rules, fn)
    got = explain.ask_json(brief('apply_one_brief.md').replace('{RULES}', '\n'.join(f'{n}. {rules[n - 1]}' for n in nums) or '(none)')
                           .replace('{SHOWN}', shown).replace('{SAID}', said))
    got = got if isinstance(got, dict) else {}
    out, changed = list(rules), 0
    for c in got.get('changes') or []:
        if isinstance(c, dict) and c.get('n') in nums and isinstance(c.get('rule'), str) and c['rule'].strip():
            out[c['n'] - 1] = c['rule'].strip(); changed += 1
    for r in got.get('new') or []:
        if isinstance(r, str) and r.strip():
            out.append(r.strip()); changed += 1
    if not changed:   # nothing could be read from it: his words go to the builders as said
        out.append(f'{shown} The owner says: {said}')
    return out

def recheck(rules, fn, case):
    got = explain.ask_json(brief('recheck_brief.md').replace('{RULES}', '\n'.join(rules[n - 1] for n in about(rules, fn)) or '(none)')
                           .replace('{CASE}', case))
    return got.get('say') if isinstance(got, dict) and isinstance(got.get('say'), str) and got['say'].strip() else None

def ask_owner(term, skim, od, log, prompt, cost):
    term.write(prompt)
    reply, c = r55.owner_reply(skim, term.getvalue(), od, log); cost[0] += c
    typed = '' if reply.strip('`').upper() in ('ENTER', '(ENTER)', '') or reply.lower().startswith(
        ("yes, that's right", 'yes', 'right', 'correct')) and len(reply) < 25 else reply
    term.write(typed + '\n'); log.append(dict(prompt=prompt[-600:], typed=typed))
    return typed

def spot_round(rules, spots, skim, priv):
    """Spot checks one at a time; each correction applied by itself and its case shown again (at most one more fix)."""
    od = os.path.join(priv, 'review_CB_spots'); shutil.rmtree(od, ignore_errors=True); os.makedirs(od)
    term, log, cost, fixes = io.StringIO(), [], [0.0], []
    term.write(f"Hive: Now {len(spots)} quick checks on what the build does in real cases. Press Enter if a result is "
               "right, or say what should happen instead.\n")
    for k, s in enumerate(spots, 1):
        typed = ask_owner(term, skim, od, log, f"\nCase {k} of {len(spots)}. {s['say']}\n  Right? (Enter = yes, or say what "
                                                "should happen) > ", cost)
        say(f'CB spot #{k}: {typed[:80]!r}')
        if not typed:
            continue
        fix = dict(shown=s['say'], said=typed, function=s.get('function'), rounds=1)
        rules = apply_one(rules, s.get('function'), s['say'], typed)
        now = recheck(rules, s.get('function'), s['say'])
        fix['now'] = now
        if now:   # shown again, worked out from the corrected rules (Gate 57: corrections were lost turning cases into rules)
            again = ask_owner(term, skim, od, log, f"\n  With your correction: {now}\n  Right now? (Enter = yes, or say what "
                                                   "should happen) > ", cost)
            fix['confirmed'] = not again
            if again:
                fix['said_again'] = again; fix['rounds'] = 2
                rules = apply_one(rules, s.get('function'), now, again)
        fixes.append(fix)
    return rules, fixes, dict(replies=len(log), cost=round(cost[0], 3), log=log, transcript=term.getvalue())

def after(run, oracle_path, base_repo):
    name = os.path.basename(run); priv = os.path.join(ROOT, 'private', name)
    o = intent.load_oracle(oracle_path); spec = wt.spec_lines(o, intent.Gen(o).CATS)
    pre_rec = json.load(open(os.path.join(run, 'pre.json'))); R = pre_rec['R']; cost = dict(pre_rec['cost_usd'])
    r56.P = P
    D, cost['describer'] = r56.describe('describer_brief.md', os.path.join(priv, 'describer'), base_repo, spec)
    sd = os.path.join(priv, 'spotter'); shutil.rmtree(sd, ignore_errors=True); os.makedirs(sd); shutil.copytree(base_repo, os.path.join(sd, 'repo'))
    _, cost['spotter'] = wt.agent(wt.AGENT, sd, brief('spotter_brief.md').replace('{BASE}', os.path.join(sd, 'repo'))
                                  .replace('{OUT}', sd).replace('{SPEC}', spec), os.path.join(sd, 'spotter.log'))
    spots = [s for s in json.load(open(os.path.join(sd, 'spots.json'))) if isinstance(s, dict) and s.get('say')]
    assert spots, 'spotter wrote no spot checks'
    say(f'D: {len(D)} rules; {len(spots)} spot checks over {len({s.get("function") for s in spots})} functions')
    skim = brief('owner_skim.md').replace('{POLICY}', '\n'.join(f'- {r}' for r in R))
    out = {}
    t0 = time.time(); SL, rec = r55.terminal_review(D, skim, priv, 'SL'); rec['minutes'] = round((time.time() - t0) / 60, 1)
    rec['rules'] = SL; out['SL'] = rec; cost['owner_SL'] = rec['cost']
    say(f'SL: {len(SL)} rules after review, {rec["replies"]} replies, {rec["minutes"]} min')
    # CB: SL's list review, then the spot checks of every function the list left as it was
    t0 = time.time(); L2, rec_l = SL, rec
    touched = {s.get('function') for s in spots
               if any(a != b for a, b in zip([D[n - 1] for n in about(D, s.get('function'))],
                                             [L2[n - 1] for n in about(D, s.get('function'))]))}
    shown = [s for s in spots if s.get('function') not in touched]
    CB, fixes, rec_s = spot_round(L2, shown, skim, priv)
    out['CB'] = dict(rules=CB, list=rec_l, spots=rec_s, fixes=fixes, shown=shown, skipped_functions=sorted(touched),
                     minutes=round((time.time() - t0) / 60, 1), replies=rec_l['replies'] + rec_s['replies'])
    cost['owner_CB_spots'] = rec_s['cost']
    say(f'CB: list {rec_l["replies"]} replies; {len(shown)} spot checks ({len(touched)} functions changed by the list '
        f'skipped), {len(fixes)} corrected, {sum(1 for f in fixes if f.get("confirmed"))} confirmed on re-show')
    jd = os.path.join(priv, 'judge'); shutil.rmtree(jd, ignore_errors=True); os.makedirs(jd)
    shutil.copy(oracle_path, os.path.join(jd, 'oracle.py'))
    json.dump(dict(D=D, SL=SL, CB=CB, R=R), open(os.path.join(jd, 'sheets.json'), 'w'), indent=1)
    say('judge labelling every declared decision...')
    _, cost['judge'] = wt.agent(wt.AGENT, jd, brief('judge_brief.md').replace('{DIR}', jd), os.path.join(jd, 'judge.log'))
    labels = json.load(open(os.path.join(jd, 'labels.json')))['labels']
    with open(os.path.join(run, 'ask_texts.md'), 'a') as f:
        f.write(r55.section('SL', SL) + r55.section('CB', CB))
    json.dump(dict(R=R, D=D, reviews=out, cost_usd=cost, labels=labels), open(os.path.join(run, 'sheet.json'), 'w'), indent=1)
    say('ask texts for SL and CB written')

if __name__ == '__main__':
    {'pre': lambda: pre(sys.argv[2], sys.argv[3]), 'after': lambda: after(sys.argv[2], sys.argv[3], sys.argv[4])}[sys.argv[1]]()
