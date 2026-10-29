#!/usr/bin/env python3
"""Gate 44 steps (Gate 42's code sheet, without its interview, documenter or judge).

usage: sheet44.py pre   <run dir> <oracle.py>              writes the ask texts for N0 and NT
       sheet44.py after <run dir> <oracle.py> <N0's repo>  describer on N0's code (never the oracle) -> D; the synthetic
                                                           owner reviews D through hive.interview.confirm_sheet -> C;
                                                           C goes to arms C and CT in exactly the same words."""
import contextlib, io, json, os, re, shutil, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'lab'))
sys.path.insert(0, os.path.join(ROOT, 'gates', 'gate41', 'referee'))
import intent
import wind_tunnel as wt
from hive import interview

P = os.path.join(ROOT, 'gates', 'gate44', 'prompts')
say = wt.say
NO_RULES = "There is no product owner to ask on this project: `tools/ask.py` will tell you so. Work from the spec and the examples."

def section(arm, rules):
    return f'\n## {arm}\n{wt.NO_OWNER}' + interview.instructions(rules).replace('\n## ', '\n### ')

def pre(run, oracle_path):
    open(os.path.join(run, 'ask_texts.md'), 'w').write(
        "# Gate 44 ask texts (written by gates/gate44/referee/sheet44.py)\n" +
        ''.join(f'\n## {a}\n{NO_RULES}\n' for a in ('N0', 'NT')))
    say('ask texts for N0 and NT written')

def after(run, oracle_path, base_repo):
    name = os.path.basename(run); priv = os.path.join(ROOT, 'private', name)
    o = intent.load_oracle(oracle_path); spec = wt.spec_lines(o, intent.Gen(o).CATS); cost = {}
    dd = os.path.join(priv, 'describer'); shutil.rmtree(dd, ignore_errors=True); os.makedirs(dd)
    repo = os.path.join(dd, 'repo'); shutil.copytree(base_repo, repo)
    say("describer writing what N0's code does, as rules...")
    _, cost['describer'] = wt.agent(wt.AGENT, dd, open(os.path.join(P, 'describer_brief.md')).read()
                                    .replace('{BASE}', repo).replace('{OUT}', dd).replace('{SPEC}', spec),
                                    os.path.join(dd, 'describer.log'))
    D = [r.strip() for r in json.load(open(os.path.join(dd, 'rules.json'))) if isinstance(r, str) and r.strip()]
    assert D, 'describer wrote no rules'
    say(f'D: {len(D)} rules from the code (${cost["describer"]:.2f})')
    od = os.path.join(priv, 'owner_review'); shutil.rmtree(od, ignore_errors=True); os.makedirs(od)
    shutil.copy(oracle_path, os.path.join(od, 'oracle.py'))
    brief = open(os.path.join(P, 'owner_brief.md')).read().replace('{SPEC}', spec)
    term, log, oc = io.StringIO(), [], [0.0]
    def ask(prompt):
        term.write(prompt)
        reply, c = wt.agent(wt.OWNER, od, brief.replace('{SCREEN}', term.getvalue()[-20000:]), os.path.join(od, 'owner.log'))
        oc[0] += c
        typed = '' if reply.strip().strip('`').upper() in ('ENTER', '(ENTER)', '') else reply.strip()
        term.write(typed + '\n'); log.append(dict(prompt=prompt, reply=reply, typed=typed))
        say(f'review owner #{len(log)}: {typed[:80]!r}')
        return typed
    with contextlib.redirect_stdout(term):
        C = interview.confirm_sheet(D, ask=ask, title='What the built code does now, as rules',
                                    note='Each one is what the product will do. Mark any that is not your policy.',
                                    missing=True)
    marked = [int(x) for x in re.findall(r'\d+', log[0]['typed'])] if log else []
    cost['owner_review'] = round(oc[0], 3)
    say(f'C: {len(C)} rules; owner marked {len(marked)} of {len(D)}, {len(log)} replies, owner ${oc[0]:.2f}')
    with open(os.path.join(run, 'ask_texts.md'), 'a') as f:
        f.write(section('C', C) + section('CT', C))
    json.dump(dict(D=D, C=C, marked=marked, review=log, review_terminal=term.getvalue(), cost_usd=cost),
              open(os.path.join(run, 'sheet.json'), 'w'), indent=1)

if __name__ == '__main__':
    {'pre': lambda: pre(sys.argv[2], sys.argv[3]), 'after': lambda: after(sys.argv[2], sys.argv[3], sys.argv[4])}[sys.argv[1]]()
