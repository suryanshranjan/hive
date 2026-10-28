#!/usr/bin/env python3
"""Gate 39 pre-launch step: Hive's real interview, answered by a synthetic owner who holds the exact rules.

usage: wind_tunnel.py <run dir> <oracle.py>      (run_gate.py calls it through the config's "pre_launch")

1. Documenter: the owner writes his complete policy as a rule sheet (arm R).
2. Interview: hive.interview.interview() exactly as `hive start` runs it in a terminal (decisions from the goal,
   situations, readings, the rule sheet with disagreements and corrections). Every prompt goes to a synthetic owner:
   a headless Claude Code process that sees the screen and may run python3 on the oracle (arm H).
3. Judge: labels every declared decision as asked or not, and how each sheet states it (before any build result exists).
4. Writes <run>/ask_texts.md: N0 and T from lab/experiments/g39_ask_texts.md; H and R carry the rules in exactly the
   words Hive gives builders (interview.instructions).
Private outputs go to private/<name>/ (git-ignored) and <run>/ (git-ignored)."""
import contextlib, io, json, os, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'lab'))
import intent
from hive import interview

PROMPTS = os.path.join(ROOT, 'gates', 'gate39', 'prompts')
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

def main():
    run, oracle_path = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    name = os.path.basename(run); priv = os.path.join(ROOT, 'private', name)
    o = intent.load_oracle(oracle_path); names = intent.Gen(o).CATS; spec = spec_lines(o, names)
    cost = {}

    # 1. the owner's complete rule sheet (arm R)
    d = os.path.join(priv, 'documenter'); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    shutil.copy(oracle_path, os.path.join(d, 'oracle.py'))
    say('documenter writing the owner\'s complete rule sheet...')
    _, cost['documenter'] = agent(AGENT, d, open(os.path.join(PROMPTS, 'documenter_brief.md')).read()
                                  .replace('{DIR}', d).replace('{SPEC}', spec), os.path.join(d, 'documenter.log'))
    R = [r.strip() for r in json.load(open(os.path.join(d, 'rules.json'))) if isinstance(r, str) and r.strip()]
    assert R, 'documenter wrote no rules'
    say(f'R: {len(R)} rules (${cost["documenter"]:.2f})')

    # 2. Hive's interview with a synthetic owner (arm H)
    od = os.path.join(priv, 'owner'); shutil.rmtree(od, ignore_errors=True); os.makedirs(od)
    shutil.copy(oracle_path, os.path.join(od, 'oracle.py'))
    brief = open(os.path.join(PROMPTS, 'owner_brief.md')).read().replace('{SPEC}', spec)
    goal = ("Add these business functions to our SQL engine (each is called from SQL, like the built-in functions; "
            "the last is an aggregate over one column):\n\n" + spec + '\n')
    screen, log, owner_cost = io.StringIO(), [], [0.0]
    def ask(prompt):
        shown = screen.getvalue()[-6000:] + prompt; screen.seek(0); screen.truncate()
        reply, c = agent(OWNER, od, brief.replace('{SCREEN}', shown), os.path.join(od, 'owner.log'))
        owner_cost[0] += c
        typed = '' if reply.strip().strip('`').upper() in ('ENTER', '(ENTER)', '') else reply.strip()
        log.append(dict(screen=shown, reply=reply, typed=typed))
        say(f'owner answered #{len(log)}: {typed[:90]!r}')
        json.dump(log, open(os.path.join(priv, 'interview_transcript.json'), 'w'), indent=1)
        return typed
    say('interview starting (hive.interview, terminal mode)...')
    t0 = time.time()
    with contextlib.redirect_stdout(screen):
        H = interview.interview(goal, None, [], ask=ask, save=os.path.join(priv, 'interview'))
    minutes = (time.time() - t0) / 60
    assert H, 'the interview produced no rules'
    qs = json.load(open(os.path.join(priv, 'interview.questions.json')))['qs']
    ans = interview.telegram._load(os.path.join(priv, 'interview.answers.json'))
    say(f'H: {len(H)} rules from {len(qs)} questions, {len(log)} owner replies, {minutes:.1f} min, owner ${owner_cost[0]:.2f}')
    cost['owner'] = owner_cost[0]

    # 3. the judge, before any build result exists
    jd = os.path.join(priv, 'judge'); shutil.rmtree(jd, ignore_errors=True); os.makedirs(jd)
    shutil.copy(oracle_path, os.path.join(jd, 'oracle.py'))
    json.dump(dict(questions=qs, owner_replies=[dict(screen=x['screen'][-1500:], reply=x['typed']) for x in log]),
              open(os.path.join(jd, 'interview.json'), 'w'), indent=1)
    json.dump(dict(H=H, R=R), open(os.path.join(jd, 'sheets.json'), 'w'), indent=1)
    say('judge labelling every declared decision...')
    _, cost['judge'] = agent(AGENT, jd, open(os.path.join(PROMPTS, 'judge_brief.md')).read().replace('{DIR}', jd),
                             os.path.join(jd, 'judge.log'))
    labels = json.load(open(os.path.join(jd, 'labels.json')))['labels']
    say(f'judge: {len(labels)} labels (${cost["judge"]:.2f})')

    # 4. ask texts: the rules in exactly the words Hive gives builders
    base = open(os.path.join(ROOT, 'lab', 'experiments', 'g39_ask_texts.md')).read().rstrip() + '\n'
    def section(arm, rules):   # "## The owner's rules" would start a new section in make_swarm.py's parser
        return f'\n## {arm}\n{NO_OWNER}' + interview.instructions(rules).replace('\n## ', '\n### ')
    open(os.path.join(run, 'ask_texts.md'), 'w').write(base + section('H', H) + section('R', R))
    json.dump(dict(H=H, R=R, questions=qs, answers=ans, interview_minutes=round(minutes, 1), owner_replies=len(log),
                   cost_usd=cost, labels=labels), open(os.path.join(run, 'wind_tunnel.json'), 'w'), indent=1)
    say(f'ask texts written: {os.path.join(run, "ask_texts.md")}')

if __name__ == '__main__':
    main()
