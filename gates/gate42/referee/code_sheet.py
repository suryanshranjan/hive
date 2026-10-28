#!/usr/bin/env python3
"""Gate 42 steps: a rule sheet complete by construction.

usage: code_sheet.py pre   <run dir> <oracle.py>              (run_gate.py "pre_launch")
       code_sheet.py after <run dir> <oracle.py> <N0's repo>  (run_gate.py "after_baseline", once N0 has built)

pre:   the owner's complete sheet (R, as Gates 39-41) and one interview as shipped (H, Gate 41's harness), and the
       ask texts for N0, H and R.
after: a describer agent reads N0's built code (never the oracle) and writes every behaviour as a plain rule (D).
       The synthetic owner, in a fresh terminal, sees D through Hive's own confirm_sheet: he marks the wrong rules,
       says each one right (amended, not replaced), and adds what is missing (C). The judge labels D, C, H and R for
       every declared decision before any stage-2 build exists. The C section is appended to the ask texts."""
import contextlib, io, json, os, re, shutil, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'lab'))
sys.path.insert(0, os.path.join(ROOT, 'gates', 'gate41', 'referee'))
import intent
import wind_tunnel as wt   # Gate 41's harness: agent(), spec_lines(), run_interview() (owner sees his whole terminal)
from hive import interview

PROMPTS = os.path.join(ROOT, 'gates', 'gate42', 'prompts')
say = wt.say

def setup(run, oracle_path):
    name = os.path.basename(run); priv = os.path.join(ROOT, 'private', name)
    o = intent.load_oracle(oracle_path); spec = wt.spec_lines(o, intent.Gen(o).CATS)
    brief = open(os.path.join(PROMPTS, 'owner_brief.md')).read().replace('{SPEC}', spec)
    return priv, spec, brief

def section(arm, rules):   # "## The owner's rules" would start a new section in make_swarm.py's parser
    return f'\n## {arm}\n{wt.NO_OWNER}' + interview.instructions(rules).replace('\n## ', '\n### ')

def pre(run, oracle_path):
    priv, spec, brief = setup(run, oracle_path); cost = {}
    d = os.path.join(priv, 'documenter'); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    shutil.copy(oracle_path, os.path.join(d, 'oracle.py'))
    say("documenter writing the owner's complete rule sheet...")
    _, cost['documenter'] = wt.agent(wt.AGENT, d, open(os.path.join(PROMPTS, 'documenter_brief.md')).read()
                                     .replace('{DIR}', d).replace('{SPEC}', spec), os.path.join(d, 'documenter.log'))
    R = [r.strip() for r in json.load(open(os.path.join(d, 'rules.json'))) if isinstance(r, str) and r.strip()]
    assert R, 'documenter wrote no rules'
    say(f'R: {len(R)} rules (${cost["documenter"]:.2f})')
    goal = ("Add these business functions to our SQL engine (each is called from SQL, like the built-in functions; "
            "the last is an aggregate over one column):\n\n" + spec + '\n')
    say('interview starting (hive.interview as shipped, terminal mode)...')
    iv = wt.run_interview('H', False, goal, brief, oracle_path, priv)
    cost['owner_interview'] = iv['owner_cost']
    base = open(os.path.join(ROOT, 'lab', 'experiments', 'g42_ask_texts.md')).read().rstrip() + '\n'
    open(os.path.join(run, 'ask_texts.md'), 'w').write(base + section('H', iv['rules']) + section('R', R))
    json.dump(dict(R=R, interview=iv, cost_usd=cost), open(os.path.join(run, 'pre.json'), 'w'), indent=1)
    say('ask texts for N0, H and R written')

def after(run, oracle_path, base_repo):
    priv, spec, brief = setup(run, oracle_path)
    pre_rec = json.load(open(os.path.join(run, 'pre.json'))); cost = dict(pre_rec['cost_usd'])
    # 1. the describer: N0's code, never the oracle
    dd = os.path.join(priv, 'describer'); shutil.rmtree(dd, ignore_errors=True); os.makedirs(dd)
    repo = os.path.join(dd, 'repo'); shutil.copytree(base_repo, repo)
    say("describer writing what N0's code does, as rules...")
    _, cost['describer'] = wt.agent(wt.AGENT, dd, open(os.path.join(PROMPTS, 'describer_brief.md')).read()
                                    .replace('{BASE}', repo).replace('{OUT}', dd).replace('{SPEC}', spec),
                                    os.path.join(dd, 'describer.log'))
    D = [r.strip() for r in json.load(open(os.path.join(dd, 'rules.json'))) if isinstance(r, str) and r.strip()]
    assert D, 'describer wrote no rules'
    say(f'D: {len(D)} rules from the code (${cost["describer"]:.2f})')
    # 2. the owner reviews D in a fresh terminal, through Hive's own confirm_sheet
    od = os.path.join(priv, 'owner_review'); shutil.rmtree(od, ignore_errors=True); os.makedirs(od)
    shutil.copy(oracle_path, os.path.join(od, 'oracle.py'))
    term, log, oc = io.StringIO(), [], [0.0]
    def ask(prompt):
        term.write(prompt)
        reply, c = wt.agent(wt.OWNER, od, brief.replace('{SCREEN}', term.getvalue()[-20000:]), os.path.join(od, 'owner.log'))
        oc[0] += c
        typed = '' if reply.strip().strip('`').upper() in ('ENTER', '(ENTER)', '') else reply.strip()
        term.write(typed + '\n'); log.append(dict(prompt=prompt, reply=reply, typed=typed))
        say(f'review owner #{len(log)}: {typed[:80]!r}')
        return typed
    t0 = time.time()
    with contextlib.redirect_stdout(term):
        C = interview.confirm_sheet(D, ask=ask, title='What the built code does now, as rules',
                                    note='Each one is what the product will do. Mark any that is not your policy.',
                                    missing=True)
    marked = [int(x) for x in re.findall(r'\d+', log[0]['typed'])] if log else []
    cost['owner_review'] = round(oc[0], 3)
    say(f'C: {len(C)} rules; owner marked {len(marked)} of {len(D)}, {len(log)} replies, '
        f'{(time.time() - t0) / 60:.1f} min, owner ${oc[0]:.2f}')
    # 3. the judge, before any stage-2 build
    jd = os.path.join(priv, 'judge'); shutil.rmtree(jd, ignore_errors=True); os.makedirs(jd)
    shutil.copy(oracle_path, os.path.join(jd, 'oracle.py'))
    json.dump(dict(D=D, C=C, H=pre_rec['interview']['rules'], R=pre_rec['R']), open(os.path.join(jd, 'sheets.json'), 'w'), indent=1)
    say('judge labelling every declared decision...')
    _, cost['judge'] = wt.agent(wt.AGENT, jd, open(os.path.join(PROMPTS, 'judge_brief.md')).read().replace('{DIR}', jd),
                                os.path.join(jd, 'judge.log'))
    labels = json.load(open(os.path.join(jd, 'labels.json')))['labels']
    say(f'judge: {len(labels)} labels (${cost["judge"]:.2f})')
    with open(os.path.join(run, 'ask_texts.md'), 'a') as f:
        f.write(section('C', C))
    json.dump(dict(R=pre_rec['R'], interview=pre_rec['interview'], D=D, C=C, marked=marked, review=log,
                   review_terminal=term.getvalue(), cost_usd=cost, labels=labels),
              open(os.path.join(run, 'wind_tunnel.json'), 'w'), indent=1)
    say('C section appended to the ask texts')

if __name__ == '__main__':
    {'pre': lambda: pre(sys.argv[2], sys.argv[3]),
     'after': lambda: after(sys.argv[2], sys.argv[3], sys.argv[4])}[sys.argv[1]]()
