#!/usr/bin/env python3
"""Gate 101: silent owner drift (Gate 92 with a day-2 goal that does not say his rules changed). Day 1: a live flight with the owner's day-1 policy; he merges the branch. Day 2: his rules have changed
(policy_day2.md: refund window 7 days, minimum refund 100 rupees, a point per 50 rupees); he asks Hive to update the shop.
Arm M keeps Hive's memory of his day-1 rulings (~/.hive/rules); arm F starts without it (only his fast/cheap choice).
usage: python3 flight92.py day1 | flight92.py day2 <M|F> <k>
 Gate 76 (Gate 52's driver, Gate 54's three-part goal and private policy): a flight test of hive start as shipped
after Gates 66-75, live (the owner at the keyboard) or overnight (then `hive morning` at the keyboard).
usage: python3 gates/gate90/referee/flight85.py live <k> [--skip-prereg-check]
Gate 52: a flight test of the product. `hive start` end to end on a small shop project, as shipped, with a synthetic
owner answering every terminal prompt from a private refund policy (private/g52/policy.md). The delivered branch is
scored on hidden acceptance tests written from that policy before the run (private/g52/test_refunds_hidden.py), both as
built (when the code sheet is written) and after the hand-over.
usage: python3 gates/gate52/referee/flight.py [--skip-prereg-check]"""
import os as _os
_os.environ['HIVE_EXPLAIN_CMD'] = 'claude -p --output-format json'   # Gate 85's reader (Gate 91 tests Haiku)
import argparse, glob, contextlib, io, json, os, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RUN = None; PRIV = os.path.join(ROOT, 'private', 'g54')
GOAL = ("Add three things to the shop. (1) Refunds: `refund(order, days_since_delivery, reason)` in `shop/refunds.py`, "
        "returning `{'amount': <whole rupees>, 'method': 'card' or 'store_credit'}`; `reason` is the customer's "
        "reason, for example 'changed mind' or 'damaged'. (2) Loyalty points: `points_earned(order)` in "
        "`shop/loyalty.py`, the points a customer earns for an order. (3) A daily sales summary for me: "
        "`sales_summary(orders)` in `shop/report.py`, returning `{'orders': ..., 'revenue': ..., 'average': ...}` "
        "in whole rupees.")
OWNER = ['claude', '-p', '--output-format', 'json']
BRIEF = os.path.join(ROOT, 'gates', 'gate101', 'prompts', 'owner_brief.md')
GOAL2 = ("Customers keep asking about refunds and points on discounted orders. Go over refunds and loyalty points and make sure they handle every case the way my shop works.")
P92 = os.path.join(ROOT, 'private', 'g92')
HIDDEN = 'test_hidden.py'

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
    global RUN, PRIV, HIDDEN
    ap = argparse.ArgumentParser(); ap.add_argument('mode', choices=['day1', 'day2']); ap.add_argument('arm', nargs='?', default='')
    ap.add_argument('k', nargs='?', default=''); ap.add_argument('--skip-prereg-check', action='store_true'); a = ap.parse_args()
    sys.path.insert(0, os.path.join(ROOT, 'lab'))
    if not a.skip_prereg_check:
        import run_gate; run_gate.prereg_check('gates/gate101/prompts/PREDICTIONS.md')
    home = os.path.expanduser('~'); D1 = os.path.join(ROOT, 'runs', 'g101_day1')
    if os.path.exists(os.path.join(home, '.hive')):
        sys.exit('~/.hive exists: move it aside first')
    if a.mode == 'day1':
        RUN = D1; shutil.rmtree(RUN, ignore_errors=True); os.makedirs(RUN)
        repo = os.path.join(RUN, 'tinyshop'); shutil.copytree(os.path.join(ROOT, 'gates', 'gate52', 'demo'), repo)
        for c in (['init', '-q', '-b', 'main'], ['add', '-A'], ['-c', 'user.name=owner', '-c', 'user.email=o@shop', 'commit', '-qm', 'Tiny Shop']):
            sh('git', *c, cwd=repo)
        policy_file, goal = os.path.join(PRIV, 'policy.md'), GOAL
    else:
        RUN = os.path.join(ROOT, 'runs', f'g101_day2_{a.arm}{a.k}'); shutil.rmtree(RUN, ignore_errors=True); os.makedirs(RUN)
        repo = os.path.join(RUN, 'tinyshop'); shutil.copytree(os.path.join(D1, 'tinyshop_merged'), repo, symlinks=True)
        snap = os.path.join(D1, 'hive_after_day1')
        os.makedirs(os.path.join(home, '.hive'))
        if a.arm == 'M':
            for x in os.listdir(snap):
                if x != 'runs': (shutil.copytree if os.path.isdir(os.path.join(snap, x)) else shutil.copy)(os.path.join(snap, x), os.path.join(home, '.hive', x))
        elif os.path.exists(os.path.join(snap, 'pace')):
            shutil.copy(os.path.join(snap, 'pace'), os.path.join(home, '.hive', 'pace'))
        policy_file, goal = os.path.join(P92, 'policy_day2_silent.md'), GOAL2
        PRIV, HIDDEN = P92, 'test_day2.py'
    sys.path.insert(0, ROOT)
    from hive import start, codesheet
    policy = open(policy_file).read()
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
    before = {}; night = {}
    def hidden_score_branch(repo):
        br = [b.strip(' *') for b in sh('git', 'branch', '--list', 'hive/*', cwd=repo).stdout.splitlines()]
        if not br: return {}
        wt = os.path.join(RUN, 'night'); sh('git', 'worktree', 'add', '-q', wt, br[-1], cwd=repo)
        res = hidden_score(wt); sh('git', 'worktree', 'remove', '--force', wt, cwd=repo); return res
    real_describe = codesheet.describe
    def describe(code_dir, goal, timeout=1800):   # the build as delivered, scored before the hand-over changes it
        before.update(hidden_score(code_dir)); return real_describe(code_dir, goal, timeout)
    codesheet.describe = describe
    t0 = time.time(); err = None
    with contextlib.redirect_stdout(Tee()):
        try:
            rc = start.start(repo, None, goal, 20)
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
    out = dict(mode=a.mode, arm=a.arm, k=a.k, rc=rc, error=err, minutes=round(minutes, 1), branches=branches, before=before, night=night, after=after,
               owner_replies=len(log), owner_cost=round(cost[0], 2), build_cost=round(spent, 2),
               hive_own=round(__import__('hive.explain', fromlist=['x']).SPENT[0], 2), hive_own_by=__import__('hive.explain', fromlist=['x']).SPENT_BY,
               owner_typed_words=sum(len((r.get('typed') or '').split()) for r in log))
    json.dump(out, open(os.path.join(RUN, 'flight.json'), 'w'), indent=1)
    if a.mode == 'day1':   # he merges the branch; Hive's memory after day 1 is kept for day 2's arm M
        merged = os.path.join(RUN, 'tinyshop_merged'); shutil.copytree(repo, merged, symlinks=True)
        if branches:
            sh('git', '-c', 'user.name=owner', '-c', 'user.email=o@shop', 'merge', '-q', '--no-edit', branches[-1], cwd=merged)
        sh('git', 'worktree', 'prune', cwd=merged)
        shutil.copytree(os.path.join(home, '.hive'), os.path.join(RUN, 'hive_after_day1'), symlinks=True)
        out['rulings_kept'] = len(json.load(open(glob.glob(os.path.join(home, '.hive', 'rules', '*.json'))[0]))) if glob.glob(os.path.join(home, '.hive', 'rules', '[0-9a-f]*.json')) else 0
    shutil.move(os.path.join(home, '.hive'), os.path.join(RUN, 'hive_state'))   # Hive's state from the flight, kept
    open(os.path.join(RUN, 'terminal.txt'), 'w').write(term.getvalue())
    print(json.dumps(out, indent=1), file=real_stdout)

if __name__ == '__main__':
    main()
