#!/usr/bin/env python3
"""Gate 52: a flight test of the product. `hive start` end to end on a small shop project, as shipped, with a synthetic
owner answering every terminal prompt from a private refund policy (private/g52/policy.md). The delivered branch is
scored on hidden acceptance tests written from that policy before the run (private/g52/test_refunds_hidden.py), both as
built (when the code sheet is written) and after the hand-over.
usage: python3 gates/gate52/referee/flight.py [--skip-prereg-check]"""
import argparse, contextlib, io, json, os, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RUN = os.path.join(ROOT, 'runs', 'g52'); PRIV = os.path.join(ROOT, 'private', 'g52')
GOAL = ("Add refunds to the shop: a function `refund(order, days_since_delivery, reason)` in `shop/refunds.py` that works "
        "out what the customer gets back. It returns `{'amount': <whole rupees>, 'method': 'card' or 'store_credit'}`. "
        "`reason` is the customer's reason, for example 'changed mind' or 'damaged'.")
OWNER = ['claude', '-p', '--output-format', 'json']
BRIEF = os.path.join(ROOT, 'gates', 'gate52', 'prompts', 'owner_brief.md')   # Gate 54 points this elsewhere
HIDDEN = 'test_refunds_hidden.py'

def sh(*a, cwd=None):
    return subprocess.run(list(a), cwd=cwd, capture_output=True, text=True)

def hidden_score(code_dir):
    r = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', os.path.join(PRIV, HIDDEN)],
                       cwd=code_dir, capture_output=True, text=True, env=dict(os.environ, PYTHONPATH=code_dir))
    last = (r.stdout.strip().splitlines() or [''])[-1]
    import re
    p = int((re.search(r'(\d+) passed', last) or [0, 0])[1]); f = int((re.search(r'(\d+) failed', last) or [0, 0])[1])
    e = int((re.search(r'(\d+) error', last) or [0, 0])[1])
    return dict(passed=p, failed=f, errors=e, line=last)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--skip-prereg-check', action='store_true'); a = ap.parse_args()
    sys.path.insert(0, os.path.join(ROOT, 'lab'))
    if not a.skip_prereg_check:
        import run_gate; run_gate.prereg_check('gates/gate52/prompts/PREDICTIONS.md')
    shutil.rmtree(RUN, ignore_errors=True); os.makedirs(RUN)
    repo = os.path.join(RUN, 'tinyshop'); shutil.copytree(os.path.join(ROOT, 'gates', 'gate52', 'demo'), repo)
    for c in (['init', '-q', '-b', 'main'], ['add', '-A'], ['-c', 'user.name=owner', '-c', 'user.email=o@shop', 'commit', '-qm', 'Tiny Shop']):
        sh('git', *c, cwd=repo)
    home = os.path.expanduser('~')   # this machine's Claude login stays where it is; Hive's own state starts empty
    if os.path.exists(os.path.join(home, '.hive')):
        sys.exit('~/.hive exists: move it aside so the flight starts like a first-time owner')
    sys.path.insert(0, ROOT)
    from hive import start, codesheet
    policy = open(os.path.join(PRIV, 'policy.md')).read()
    brief = open(BRIEF).read().replace('{POLICY}', policy)
    term, log, cost = io.StringIO(), [], [0.0]
    real_stdout = sys.stdout
    class Tee(io.TextIOBase):
        def write(self, s):
            term.write(s); real_stdout.write(s); real_stdout.flush(); return len(s)
    def ask(prompt, default=''):
        print(prompt)
        p = subprocess.run(OWNER, input=brief.replace('{SCREEN}', term.getvalue()[-12000:]), capture_output=True, text=True, timeout=600)
        try:
            d = json.loads(p.stdout); reply = (d.get('result') or '').strip(); cost[0] += float(d.get('total_cost_usd') or 0)
        except Exception:
            reply = ''
        typed = '' if reply.strip('`').upper() in ('ENTER', '(ENTER)', '') else reply
        print(f'  > {typed}')
        log.append(dict(prompt=prompt[-2000:], typed=typed))
        json.dump(log, open(os.path.join(RUN, 'owner_log.json'), 'w'), indent=1)
        return typed or default
    start._ask = ask
    class OwnerKeyboard:   # Gate 54: builders' live questions and any other prompt that reads the keyboard directly
        def readline(self):
            p = subprocess.run(OWNER, input=brief.replace('{SCREEN}', term.getvalue()[-12000:]), capture_output=True,
                               text=True, timeout=600)
            try:
                d = json.loads(p.stdout); reply = (d.get('result') or '').strip(); cost[0] += float(d.get('total_cost_usd') or 0)
            except Exception:
                reply = ''
            typed = '' if reply.strip('`').upper() in ('ENTER', '(ENTER)', '') else ' '.join(reply.split())
            print(f'  > {typed}')
            log.append(dict(prompt=term.getvalue()[-1500:], typed=typed, keyboard=True))
            json.dump(log, open(os.path.join(RUN, 'owner_log.json'), 'w'), indent=1)
            return typed + '\n'
        def isatty(self):
            return False
    sys.stdin = OwnerKeyboard()
    before = {}
    real_describe = codesheet.describe
    def describe(code_dir, goal, timeout=1800):   # the build as delivered, scored before the hand-over changes it
        before.update(hidden_score(code_dir)); return real_describe(code_dir, goal, timeout)
    codesheet.describe = describe
    t0 = time.time(); err = None
    with contextlib.redirect_stdout(Tee()):
        try:
            rc = start.start(repo, None, GOAL, 20)
        except BaseException as e:   # a crash is a finding
            import traceback; err = traceback.format_exc(); rc = None
    minutes = (time.time() - t0) / 60
    branches = [b.strip(' *') for b in sh('git', 'branch', '--list', 'hive/*', cwd=repo).stdout.splitlines()]
    after = {}
    if branches:
        wt = os.path.join(RUN, 'delivered'); sh('git', 'worktree', 'add', '-q', wt, branches[-1], cwd=repo)
        after = hidden_score(wt)
        sh(sys.executable, '-m', 'pytest', '-q', cwd=wt)
    runs = os.path.join(home, '.hive', 'runs'); spent = 0.0
    for st in __import__('glob').glob(os.path.join(runs, '*', 'state.json')):
        try: spent += float(json.load(open(st)).get('cost') or 0)
        except Exception: pass
    out = dict(rc=rc, error=err, minutes=round(minutes, 1), branches=branches, before=before, after=after,
               owner_replies=len(log), owner_cost=round(cost[0], 2), build_cost=round(spent, 2))
    json.dump(out, open(os.path.join(RUN, 'flight.json'), 'w'), indent=1)
    shutil.move(os.path.join(home, '.hive'), os.path.join(RUN, 'hive_state'))   # Hive's state from the flight, kept
    open(os.path.join(RUN, 'terminal.txt'), 'w').write(term.getvalue())
    print(json.dumps(out, indent=1), file=real_stdout)

if __name__ == '__main__':
    main()
