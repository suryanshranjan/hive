#!/usr/bin/env python3
"""Gate 41 pre-launch step: one run of Hive's real interview (as shipped), answered by a synthetic owner who holds the
exact rules, handed to builders two ways.

usage: wind_tunnel.py <run dir> <oracle.py>      (run_gate.py calls it through the config's "pre_launch")

Same harness as Gate 40 (the owner sees his whole terminal). One interview, as shipped (inputs=False):
- H: interview.instructions(sheet), as `hive start` does.
- K: interview.instructions(sheet, rulings): the same sheet plus his answer to each situation, kept whole (the rules
  list the interview had before it merged them into the sheet, recorded by wrapping interview.rule_sheet).
Questions skipped as "settled" are recorded from the terminal. The judge labels, before any build, for each declared
decision: asked (answered), skipped only, his answer, and hand-overs H, K and R."""
import contextlib, io, json, os, re, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'lab'))
import intent
from hive import interview

PROMPTS = os.path.join(ROOT, 'gates', 'gate41', 'prompts')
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
    term, log, cost, plans, sheet_in, answered, current = io.StringIO(), [], [0.0], [], [], {}, [None]
    def ask(prompt):
        m = re.match(r'\s*(\d+) of \d+\. ', prompt)
        if m: current[0] = int(m.group(1))
        elif 'So, what should happen' not in prompt: current[0] = None   # a reading, the sheet, a correction
        term.write(prompt)
        shown = term.getvalue()[-9000:]
        reply, c = agent(OWNER, od, brief.replace('{SCREEN}', shown), os.path.join(od, 'owner.log'))
        cost[0] += c
        typed = '' if reply.strip().strip('`').upper() in ('ENTER', '(ENTER)', '') else reply.strip()
        term.write(typed + '\n')
        log.append(dict(prompt=prompt, reply=reply, typed=typed))
        if current[0]: answered.setdefault(current[0], []).append(typed)
        say(f'{arm} owner #{len(log)}: {typed[:80]!r}')
        json.dump(log, open(os.path.join(priv, f'interview_{arm}_transcript.json'), 'w'), indent=1)
        return typed
    real, real_sheet = interview.decisions, interview.rule_sheet
    def recorded(g, inp=False):
        ds = real(g, inp); plans.append(ds); return ds
    def recorded_sheet(rules, *a, **k):
        sheet_in.extend(rules); return real_sheet(rules, *a, **k)
    interview.decisions, interview.rule_sheet = recorded, recorded_sheet
    save = os.path.join(priv, f'interview_{arm}')
    for ext in ('.questions.json', '.answers.json', '.drafts.json', '.readings.json', '.sheet.json'):
        if os.path.exists(save + ext): os.remove(save + ext)
    t0 = time.time()
    try:
        with contextlib.redirect_stdout(term):
            rules = interview.interview(goal, None, [], ask=ask, save=save, inputs=inputs)
    finally:
        interview.decisions, interview.rule_sheet = real, real_sheet
    assert rules, f'interview {arm} produced no rules'
    qs = json.load(open(save + '.questions.json'))['qs']
    rec = dict(rules=rules, rulings=list(sheet_in), questions=qs, planned_decisions=plans[0] if plans else [],
               answered={qs[k - 1]['id']: v for k, v in answered.items() if k <= len(qs)},
               skipped=[q['id'] for k, q in enumerate(qs, 1) if k not in answered], owner_replies=len(log),
               owner_cost=round(cost[0], 3), minutes=round((time.time() - t0) / 60, 1),
               terminal=term.getvalue())
    say(f'{arm}: {len(rules)} rules and {len(sheet_in)} rulings from {len(qs)} questions ({len(rec["skipped"])} skipped as '
        f'settled; {len(rec["planned_decisions"])} planned decisions), {len(log)} owner replies, {rec["minutes"]} min, '
        f'owner ${cost[0]:.2f}')
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
    say('interview starting (hive.interview as shipped, terminal mode)...')
    iv = run_interview('H', False, goal, brief, oracle_path, priv)
    cost['owner'] = iv['owner_cost']
    assert iv['rulings'], 'the rule sheet step never ran'
    hand = dict(H=interview.instructions(iv['rules']), K=interview.instructions(iv['rules'], iv['rulings']),
                R=interview.instructions(R))

    jd = os.path.join(priv, 'judge'); shutil.rmtree(jd, ignore_errors=True); os.makedirs(jd)
    shutil.copy(oracle_path, os.path.join(jd, 'oracle.py'))
    byid = {q['id']: q for q in iv['questions']}
    json.dump(dict(answered=[dict(byid[i], replies=v) for i, v in iv['answered'].items()],
                   skipped=[byid[i] for i in iv['skipped']], terminal=iv['terminal']),
              open(os.path.join(jd, 'interview.json'), 'w'), indent=1)
    json.dump(hand, open(os.path.join(jd, 'handovers.json'), 'w'), indent=1)
    say('judge labelling every declared decision...')
    _, cost['judge'] = agent(AGENT, jd, open(os.path.join(PROMPTS, 'judge_brief.md')).read().replace('{DIR}', jd),
                             os.path.join(jd, 'judge.log'))
    labels = json.load(open(os.path.join(jd, 'labels.json')))['labels']
    say(f'judge: {len(labels)} labels (${cost["judge"]:.2f})')

    base = open(os.path.join(ROOT, 'lab', 'experiments', 'g41_ask_texts.md')).read().rstrip() + '\n'
    open(os.path.join(run, 'ask_texts.md'), 'w').write(base + ''.join(
        f'\n## {arm}\n{NO_OWNER}' + hand[arm].replace('\n## ', '\n### ') for arm in ('H', 'K', 'R')))
    json.dump(dict(R=R, interview=iv, handovers=hand, cost_usd=cost, labels=labels),
              open(os.path.join(run, 'wind_tunnel.json'), 'w'), indent=1)
    say(f'ask texts written: {os.path.join(run, "ask_texts.md")}')

if __name__ == '__main__':
    main()
