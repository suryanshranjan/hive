#!/usr/bin/env python3
"""Gate 84, part A: the interface check and its fix round, run by the product (hive.start._keep_contract) on Gate 83's
live build, whose refund() came back with extra keys. A copy of that build's state is used (runs/g84_fix/home); Gate 83's
own run is not touched. Scores the hidden suite (private/g54) before and after, and re-checks the fixed code.
usage: python3 gates/gate84/referee/fix84.py [--skip-prereg-check]"""
import argparse, glob, json, os, shutil, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'lab')); sys.path.insert(0, os.path.join(ROOT, 'gates', 'gate84', 'referee'))
ap = argparse.ArgumentParser(); ap.add_argument('--skip-prereg-check', action='store_true'); a = ap.parse_args()
if not a.skip_prereg_check:
    import run_gate; run_gate.prereg_check('gates/gate84/prompts/PREDICTIONS.md')
import flight84
from hive import start, contract
RUN = os.path.join(ROOT, 'runs', 'g84_fix'); shutil.rmtree(RUN, ignore_errors=True); os.makedirs(RUN)
src = glob.glob(os.path.join(ROOT, 'runs', 'g83_live', 'hive_state', 'runs', '*'))[0]
home = os.path.join(RUN, 'home'); shutil.copytree(src, home, symlinks=True)
repo = os.path.join(RUN, 'tinyshop'); shutil.copytree(os.path.join(ROOT, 'runs', 'g83_live', 'tinyshop'), repo, symlinks=True)
st = json.load(open(os.path.join(home, 'state.json')))
st.update(home=home, final=os.path.join(home, 'build'), repo=repo)
def score(label):
    d = os.path.join(RUN, label); subprocess.run(['git', 'clone', '-q', '--branch', st['b'], os.path.join(st['final'], 'up.git'), d], check=True)
    return d, flight84.hidden_score(d)
d0, before = score('before')
fixed = start._keep_contract(st)
d1, after = score('after')
again = contract.check(st['goal'], d1)
out = dict(before=before, problems=st.get('contract'), fix_ran=fixed, after=after, problems_after=again, cost=st['cost'])
json.dump(out, open(os.path.join(RUN, 'result.json'), 'w'), indent=1); print(json.dumps(out, indent=1))
