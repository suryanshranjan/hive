"""G84 registered analysis (committed with the predictions, before any run):
    python3 gates/gate84/referee/analyze.py runs/g84_fix runs/g84_live1 runs/g84_live2
I1 Gate 83's live build: the check finds the extra keys, the fix round runs, the fixed code has 0 problems, and >= 24 of 27
I3 both flights: no crash, one branch, >= 24 of 27
I4 both flights: the delivered code has 0 problems against the goal's interfaces (the referee re-checks, with its own reading
   of the goal)
I5 both flights: where the review was skipped, the check ran (state.json has 'contract'), and if it found problems its
   fix round ran"""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from hive import contract
F = json.load(open(os.path.join(sys.argv[1], 'result.json')))
i1 = bool(F['problems']) and F['fix_ran'] and not F['problems_after'] and F['after'].get('passed', 0) >= 24
print(f"fix: before {F['before'].get('line')}; problems {F['problems']}; fix ran {F['fix_ran']}; after {F['after'].get('line')}; problems after {F['problems_after']}")
flights = []
for d in sys.argv[2:]:
    f = json.load(open(os.path.join(d, 'flight.json')))
    st = json.load(open(glob.glob(os.path.join(d, 'hive_state', 'runs', '*', 'state.json'))[0]))
    term = open(os.path.join(d, 'terminal.txt')).read()
    skipped = 'while building, and your answers are built in' in term
    left = contract.check(st['goal'], os.path.join(d, 'delivered')) if os.path.isdir(os.path.join(d, 'delivered')) else ['no delivery']
    fixdir = glob.glob(os.path.join(d, 'hive_state', 'runs', '*', 'contract_fix'))
    ran = 'contract' in st
    ok5 = (not skipped) or (ran and (not st['contract'] or bool(fixdir)))
    flights.append((f, left, ok5))
    print(f"{os.path.basename(d)}: rc {f['rc']}, {f['minutes']} min, after {f['after'].get('line')}, owner prompts {f['owner_replies']}, "
          f"review skipped {skipped}, check ran {ran}, found {st.get('contract')}, fix round {bool(fixdir)}, problems left {left}")
i3 = all(f['rc'] == 0 and not f['error'] and len(f['branches']) == 1 and (f['after'].get('passed') or 0) >= 24 for f, _, _ in flights)
i4 = all(not left for _, left, _ in flights); i5 = all(ok for _, _, ok in flights)
print('\npredictions')
for tag, text, ok in [('I1', "Gate 83's build: found, fixed, 0 left, >= 24", i1), ('I3', 'flights: no crash, one branch, >= 24 each', i3),
                      ('I4', 'flights: 0 interface problems delivered', i4), ('I5', 'flights: check ran where the review was skipped; fix ran if needed', i5)]:
    print(f'{tag} {text} -> {"held" if ok else "failed"}')
