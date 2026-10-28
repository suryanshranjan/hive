#!/usr/bin/env python3
"""Gate 40 pre-launch step: two runs of Hive's real interview, answered by a synthetic owner who holds the exact rules.

usage: wind_tunnel.py <run dir> <oracle.py>      (run_gate.py calls it through the config's "pre_launch")

Same as Gate 39's step, with two changes:
- Two interviews: H, hive.interview.interview() as it now ships (with Gate 39's fixes), and H2, the same with
  inputs=True (the planner also lists what the product shows for unusual input; up to 30 questions).
- The owner sees his whole terminal (everything Hive printed and everything he typed, last 9,000 characters), as a
  person at a terminal would. Gate 39's harness cleared it between prompts, so "Rule 2: what should it be?" reached
  him without the sheet above it.
The planner's decision lists are recorded. The judge labels both interviews and all three sheets before any build."""
import contextlib, io, json, os, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'lab'))
import intent
from hive import interview

PROMPTS = os.path.join(ROOT, 'gates', 'gate40', 'prompts')
AGENT = 'claude -p --output-format json --permission-mode acceptEdits --allowedTools Bash Read Edit Write Glob Grep'.split()
OWNER = 'claude -p --output-format json --allowedTools Bash Read'.split()
NO_OWNER = "There is no product owner to ask on this project: `tools/ask.py` will tell you so."

def say(m): print(f'[{time.strftime("%H:%M:%S")}] wind tunnel: {m}', file=sys.__stdout__, flush=True)

def agent(cmd, cwd, prompt, log):
    p = subprocess.run(cmd, cwd=cwd, input=prompt, capture_output=True, text=True, timeout=1800)
    open(log, 'a').write(p.stdout + p.stderr + '\n')
    try:
        d = json.loads(p.stdout)
        return (d.get('result') or '').strip(), float(d.get('total_cost_usd') or 0)
    except Exception:
        return '', 0.0

def spec_lines(o, names):
    g = intent.Gen(o)
    return '\n'.join(f'- `{o.SPEC[f].split(":", 1)[0].strip()}`: {o.SPEC[f].split(":", 1)[1].strip()}'
                     + (' (an aggregate over one column)' if f == g.AGG else '') for f in names)

def run_interview(arm, inputs, goal, brief, oracle_path, priv):
    """One full interview in terminal mode; every prompt answered by the synthetic owner. Returns its record."""
    od = os.path.join(priv, f'owner_{arm}'); shutil.rmtree(od, ignore_errors=True); os.makedirs(od)
    shutil.copy(oracle_path, os.path.join(od, 'oracle.py'))
    term, log, cost, plans = io.StringIO(), [], [0.0], []
    def ask(prompt):
        term.write(prompt)
        shown = term.getvalue()[-9000:]
        reply, c = agent(OWNER, od, brief.replace('{SCREEN}', shown), os.path.join(od, 'owner.log'))
        cost[0] += c
        typed = '' if reply.strip().strip('`').upper() in ('ENTER', '(ENTER)', '') else reply.strip()
        term.write(typed + '\n')
        log.append(dict(prompt=prompt, reply=reply, typed=typed))
        say(f'{arm} owner #{len(log)}: {typed[:80]!r}')
        json.dump(log, open(os.path.join(priv, f'interview_{arm}_transcript.json'), 'w'), indent=1)
        return typed
    real = interview.decisions
    def recorded(g, inp=False):
        ds = real(g, inp); plans.append(ds); return ds
    interview.decisions = recorded
    save = os.path.join(priv, f'interview_{arm}')
    for ext in ('.questions.json', '.answers.json', '.drafts.json', '.readings.json', '.sheet.json'):
        if os.path.exists(save + ext): os.remove(save + ext)
    t0 = time.time()
    try:
        with contextlib.redirect_stdout(term):
            rules = interview.interview(goal, None, [], ask=ask, save=save, inputs=inputs)
    finally:
        interview.decisions = real
    assert rules, f'interview {arm} produced no rules'
    qs = json.load(open(save + '.questions.json'))['qs']
    rec = dict(rules=rules, questions=qs, planned_decisions=plans[0] if plans else [], owner_replies=len(log),
               owner_cost=round(cost[0], 3), minutes=round((time.time() - t0) / 60, 1),
               terminal=term.getvalue())
    say(f'{arm}: {len(rules)} rules from {len(qs)} questions ({len(rec["planned_decisions"])} planned decisions), '
        f'{len(log)} owner replies, {rec["minutes"]} min, owner ${cost[0]:.2f}')
    return rec

def main():
    run, oracle_path = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    name = os.path.basename(run); priv = os.path.join(ROOT, 'private', name)
    o = intent.load_oracle(oracle_path); names = intent.Gen(o).CATS; spec = spec_lines(o, names)
    cost = {}

    d = os.path.join(priv, 'documenter'); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    shutil.copy(oracle_path, os.path.join(d, 'oracle.py'))
    say("documenter writing the owner's complete rule sheet...")
    _, cost['documenter'] = agent(AGENT, d, open(os.path.join(PROMPTS, 'documenter_brief.md')).read()
                                  .replace('{DIR}', d).replace('{SPEC}', spec), os.path.join(d, 'documenter.log'))
    R = [r.strip() for r in json.load(open(os.path.join(d, 'rules.json'))) if isinstance(r, str) and r.strip()]
    assert R, 'documenter wrote no rules'
    say(f'R: {len(R)} rules (${cost["documenter"]:.2f})')

    brief = open(os.path.join(PROMPTS, 'owner_brief.md')).read().replace('{SPEC}', spec)
    goal = ("Add these business functions to our SQL engine (each is called from SQL, like the built-in functions; "
            "the last is an aggregate over one column):\n\n" + spec + '\n')
    iv = {}
    for arm, inputs in (('H', False), ('H2', True)):
        say(f'interview {arm} starting (hive.interview, terminal mode, inputs={inputs})...')
        iv[arm] = run_interview(arm, inputs, goal, brief, oracle_path, priv)
        cost[f'owner_{arm}'] = iv[arm]['owner_cost']

    jd = os.path.join(priv, 'judge'); shutil.rmtree(jd, ignore_errors=True); os.makedirs(jd)
    shutil.copy(oracle_path, os.path.join(jd, 'oracle.py'))
    for arm in ('H', 'H2'):
        json.dump(dict(questions=iv[arm]['questions'], terminal=iv[arm]['terminal']),
                  open(os.path.join(jd, f'interview_{arm}.json'), 'w'), indent=1)
    json.dump(dict(H=iv['H']['rules'], H2=iv['H2']['rules'], R=R), open(os.path.join(jd, 'sheets.json'), 'w'), indent=1)
    say('judge labelling every declared decision...')
    _, cost['judge'] = agent(AGENT, jd, open(os.path.join(PROMPTS, 'judge_brief.md')).read().replace('{DIR}', jd),
                             os.path.join(jd, 'judge.log'))
    labels = json.load(open(os.path.join(jd, 'labels.json')))['labels']
    say(f'judge: {len(labels)} labels (${cost["judge"]:.2f})')

    base = open(os.path.join(ROOT, 'lab', 'experiments', 'g40_ask_texts.md')).read().rstrip() + '\n'
    def section(arm, rules):   # "## The owner's rules" would start a new section in make_swarm.py's parser
        return f'\n## {arm}\n{NO_OWNER}' + interview.instructions(rules).replace('\n## ', '\n### ')
    open(os.path.join(run, 'ask_texts.md'), 'w').write(
        base + section('H', iv['H']['rules']) + section('H2', iv['H2']['rules']) + section('R', R))
    json.dump(dict(R=R, interviews=iv, cost_usd=cost, labels=labels), open(os.path.join(run, 'wind_tunnel.json'), 'w'),
              indent=1)
    say(f'ask texts written: {os.path.join(run, "ask_texts.md")}')

if __name__ == '__main__':
    main()
