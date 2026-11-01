"""G76 registered analysis (committed with the predictions, before the flights):
    python3 gates/gate76/referee/analyze.py runs/g76_live runs/g76_overnight
F1 live: no crash, one branch delivered          F2 live: the split engaged (the last builder's prompt has the business
role; the others' have "build the rest") and every question the owner was asked came from that builder
F3 live: >= 24 of 27 hidden after               F4 live: <= 45 owner prompts
F5 overnight: no crash; >= 5 questions recorded overnight; the morning fix ran and the branch moved
F6 overnight: >= 22 of 27 hidden after the morning"""
import glob, json, os, sys
live, night = sys.argv[1], sys.argv[2]
def flight(d): return json.load(open(os.path.join(d, 'flight.json')))
L, N = flight(live), flight(night)
def builds(d):
    return sorted(glob.glob(os.path.join(d, 'hive_state', 'runs', '*', 'build')))
def roles(b):
    ps = sorted(glob.glob(os.path.join(b, 'prompts', '*.md'))); last = ps[-1] if ps else None
    biz = bool(last) and 'Your role: the business builder' in open(last).read()
    rest = all('Your role: build the rest' in open(p).read() for p in ps[:-1]) if len(ps) > 1 else False
    askers = {json.load(open(q)).get('worker') for q in glob.glob(os.path.join(b, 'owner', 'questions', '*.json'))}
    return dict(builders=len(ps), business_role=biz, rest_role=rest, askers=sorted(a for a in askers if a), last=os.path.basename(last or '')[:-3])
bl = builds(live); rl = roles(bl[-1]) if bl else {}
bn = builds(night); qn = len(glob.glob(os.path.join(bn[-1], 'owner', 'questions', '*.json'))) if bn else 0
fixed = os.path.isdir(os.path.join(os.path.dirname(bn[-1]), 'fix')) if bn else False
tot = lambda r: (r or {}).get('passed', 0) + (r or {}).get('failed', 0) + (r or {}).get('errors', 0)
print(f"live: rc {L['rc']}, error {bool(L['error'])}, {L['minutes']} min, branches {L['branches']}, before {L['before'].get('line')}, after {L['after'].get('line')}, "
      f"owner prompts {L['owner_replies']}, builders' cost ${L['build_cost']}; roles {rl}")
print(f"overnight: rc {N['rc']}, error {bool(N['error'])}, {N['minutes']} min, branches {N['branches']}, night {N.get('night', {}).get('line')}, after morning "
      f"{N['after'].get('line')}, owner prompts {N['owner_replies']}, questions recorded {qn}, fix round {fixed}")
res = [('F1', 'live: no crash, one branch', L['rc'] == 0 and not L['error'] and len(L['branches']) == 1),
       ('F2', f"live: split engaged and only {rl.get('last')} asked: {rl}", rl.get('business_role') and rl.get('rest_role') and rl.get('askers') in ([], [rl.get('last')])),
       ('F3', f"live: ≥ 24 of 27 after: {L['after'].get('passed')}", (L['after'].get('passed') or 0) >= 24),
       ('F4', f"live: ≤ 45 owner prompts: {L['owner_replies']}", L['owner_replies'] <= 45),
       ('F5', f"overnight: no crash, ≥ 5 recorded ({qn}), fix ran ({fixed})", N['rc'] == 0 and not N['error'] and qn >= 5 and fixed),
       ('F6', f"overnight: ≥ 22 of 27 after the morning: {N['after'].get('passed')}", (N['after'].get('passed') or 0) >= 22)]
print('\npredictions')
for tag, text, held in res:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
