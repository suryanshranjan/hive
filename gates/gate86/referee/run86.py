#!/usr/bin/env python3
"""Gate 86: Hive on a real codebase, by Ambig-SWE's protocol (Vijayvargiya et al., ICLR 2026): SWE-bench Verified Django
issues, given in full or in their underspecified rewrite, with a simulated user who sees the full issue and answers only
from it. Run without Docker (swe86.py: the Django checkout at the base commit, Python 3.9, Django's own runner).
Arms (one issue each run):
  F  one builder, the full issue, no asking                 (the ceiling)
  N  one builder, the underspecified issue, no asking       (Ambig-SWE's "Hidden")
  S  `hive start` as shipped on the underspecified issue, the simulated user at the keyboard (interview, builders' questions,
     review), so Hive's whole flow is what is tested
usage: python3 gates/gate86/referee/run86.py <F|N|S> <instance_id> [--skip-prereg-check]
Visible tests (all arms): the test modules the issue's test patch touches, without that patch (Hive's guard needs a suite;
this names where the tests live, the same for every arm). Hidden: the test patch's FAIL_TO_PASS tests, and the tests that
pass both before and with the gold patch (measured by swe86.py validate)."""
import argparse, contextlib, io, json, os, shutil, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'lab')); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import swe86
OWNER = ['claude', '-p', '--output-format', 'json']
USER = """You are the GitHub user who reported the issue below in Django's tracker. You are not an AI assistant. A developer
(through a tool called Hive, which talks to you in a terminal) is fixing it. Below are the full issue you wrote, the
maintainers' hints, and the files that the fix touches. Reply to the last prompt in the terminal, at the bottom, with exactly
what you would type there, and nothing else.

- Answer questions about the issue concisely, from the information below only. If a question is unrelated, or you are not
  sure, reply "I don't have that information."
- If it offers options and one matches the issue, you may reply with its letter.
- If it shows you rules or a summary of what was built and asks whether it is right, check it against the issue: say what is
  wrong, or reply `ENTER` if it is right. If it asks for numbers of wrong rules, give them, or `ENTER`.
- If it only asks you to press Enter or confirm something harmless, reply `ENTER`.
- If it asks for a description of what to build, reply exactly: "As described in the goal."

Full issue:
{ISSUE}

Hints:
{HINTS}

Files the fix touches: {FILES}

Your terminal:
<<<
{SCREEN}
>>>"""

def goal_text(inst, full):
    body = inst['original_issue'] if full else inst['problem_statement']
    return ("This repository is Django. Fix the issue below, so that Django behaves as the issue intends, and keep every "
            "existing test passing. Add tests for your fix.\n\n# The issue\n\n" + str(body).strip())

def make_repo(inst, where):
    tmp = where + '_wt'
    swe86.worktree(inst, tmp)
    shutil.copytree(tmp, where, ignore=shutil.ignore_patterns('.git'), symlinks=True)
    subprocess.run(['git', '-C', swe86.DJANGO, 'worktree', 'remove', '--force', tmp], capture_output=True)
    mods = swe86.directives(inst['test_patch'])
    os.makedirs(os.path.join(where, '.hive'), exist_ok=True)
    json.dump({'test_cmd': f"{swe86.PY} /home/claude/swe/django_junit.py .hive/junit.xml {' '.join(mods)}", 'branch': 'main',
               'junit': '.hive/junit.xml', 'areas': {}}, open(os.path.join(where, '.hive', 'config.json'), 'w'), indent=1)
    open(os.path.join(where, '.gitignore'), 'a').write('\n.hive/junit.xml\n.hive/guard_cache/\n__pycache__/\n*.pyc\n')
    for c in (['init', '-q', '-b', 'main'], ['add', '-A'], ['-c', 'user.name=owner', '-c', 'user.email=o@x', 'commit', '-qm', 'base']):
        subprocess.run(['git', *c], cwd=where, check=True, capture_output=True)

def score(inst, code_dir, scratch):
    """Apply the issue's test patch to a copy of the delivered code and run the hidden tests."""
    t = json.load(open(os.path.join(swe86.PRIV, f"tests_{inst['instance_id']}.json")))
    if os.path.exists(scratch): shutil.rmtree(scratch)
    shutil.copytree(code_dir, scratch, ignore=shutil.ignore_patterns('.git', '.hive', '__pycache__'), symlinks=True)
    if not swe86.apply(scratch, inst['test_patch']):   # a builder's test file can collide with the patch: apply with --reject
        p = os.path.join(scratch, '.p.diff'); open(p, 'w').write(inst['test_patch'])
        subprocess.run(['git', 'apply', '--reject', '--whitespace=nowarn', p], cwd=scratch, capture_output=True)
    st, _ = swe86.run_tests(scratch, inst)
    ok, f2p_ok, f2p_n, p2p_broken = swe86.resolved(st, inst, t['p2p'])
    return dict(resolved=ok, f2p=f'{f2p_ok}/{f2p_n}', p2p_broken=p2p_broken)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('arm', choices=['F', 'N', 'S']); ap.add_argument('instance')
    ap.add_argument('--skip-prereg-check', action='store_true'); a = ap.parse_args()
    if not a.skip_prereg_check:
        import run_gate; run_gate.prereg_check('gates/gate86/prompts/PREDICTIONS.md')
    inst = next(i for i in swe86.instances() if i['instance_id'] == a.instance)
    RUN = os.path.join(ROOT, 'runs', 'g86', f'{a.arm}_{a.instance}'); shutil.rmtree(RUN, ignore_errors=True); os.makedirs(RUN)
    repo = os.path.join(RUN, 'repo'); make_repo(inst, repo)
    from hive import swarm, start, explain
    t0 = time.time(); out = dict(arm=a.arm, instance=a.instance, version=str(inst['version']))
    if a.arm in ('F', 'N'):
        run = os.path.join(RUN, 'run')
        swarm.prepare(repo, run, 1, goal_text(inst, a.arm == 'F'), 30, None, 0, False)
        swarm.launch(run)
        final = os.path.join(RUN, 'final'); subprocess.run(['git', 'clone', '-q', os.path.join(run, 'up.git'), final], check=True)
        rows = list(__import__('csv').DictReader(open(os.path.join(run, 'agents.csv'))))
        out.update(build_cost=round(sum(float(r['cost_usd'] or 0) for r in rows), 2), owner_prompts=0, hive_own=0.0)
    else:
        home = os.path.expanduser('~')
        if os.path.exists(os.path.join(home, '.hive')):
            sys.exit('~/.hive exists: move it aside first')
        brief = USER.replace('{ISSUE}', str(inst['original_issue'])).replace('{HINTS}', str(inst['hints_text'] or 'None')) \
                    .replace('{FILES}', str(inst['files']))
        term, log, cost = io.StringIO(), [], [0.0]; real = sys.stdout
        class Tee(io.TextIOBase):
            def write(self, s):
                term.write(s); real.write(s); real.flush(); return len(s)
        def reply():
            p = subprocess.run(OWNER, input=brief.replace('{SCREEN}', term.getvalue()[-12000:]), capture_output=True, text=True, timeout=600)
            try:
                d = json.loads(p.stdout); r = (d.get('result') or '').strip(); cost[0] += float(d.get('total_cost_usd') or 0)
            except Exception:
                r = ''
            return '' if r.strip('`').upper() in ('ENTER', '(ENTER)', '') else ' '.join(r.split())
        def ask(prompt, default=''):
            print(prompt); typed = reply(); print(f'  > {typed}')
            log.append(dict(prompt=prompt[-2000:], typed=typed)); json.dump(log, open(os.path.join(RUN, 'owner_log.json'), 'w'), indent=1)
            return typed or default
        start._ask = ask
        class Keyboard:
            def readline(self):
                typed = reply(); print(f'  > {typed}')
                log.append(dict(prompt=term.getvalue()[-1500:], typed=typed, keyboard=True))
                json.dump(log, open(os.path.join(RUN, 'owner_log.json'), 'w'), indent=1); return typed + '\n'
            def isatty(self): return False
        sys.stdin = Keyboard(); err = None
        with contextlib.redirect_stdout(Tee()):
            try:
                start.start(repo, None, goal_text(inst, False), 30)
            except BaseException:
                import traceback; err = traceback.format_exc()
        open(os.path.join(RUN, 'terminal.txt'), 'w').write(term.getvalue())
        br = [b.strip(' *') for b in subprocess.run(['git', 'branch', '--list', 'hive/*'], cwd=repo, capture_output=True, text=True).stdout.splitlines()]
        final = os.path.join(RUN, 'final')
        if br: subprocess.run(['git', 'worktree', 'add', '-q', final, br[-1]], cwd=repo, check=True)
        else: final = repo
        spent = 0.0
        for stf in __import__('glob').glob(os.path.join(home, '.hive', 'runs', '*', 'state.json')):
            try: spent += float(json.load(open(stf)).get('cost') or 0)
            except Exception: pass
        shutil.move(os.path.join(home, '.hive'), os.path.join(RUN, 'hive_state'))
        out.update(build_cost=round(spent, 2), owner_prompts=len(log), user_cost=round(cost[0], 2), hive_own=round(explain.SPENT[0], 2),
                   error=err, branch=bool(br))
    out.update(minutes=round((time.time() - t0) / 60, 1), **score(inst, final, os.path.join(RUN, 'scored')))
    json.dump(out, open(os.path.join(RUN, 'result.json'), 'w'), indent=1); print(json.dumps(out), file=sys.__stdout__)

if __name__ == '__main__':
    main()
