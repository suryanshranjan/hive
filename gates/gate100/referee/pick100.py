"""Gate 100: a harder sample. Django issues (versions 3.0-4.2, not in Gate 86's sample) where Ambig-SWE's Claude Sonnet 3.5
resolved the full issue but not its summary, so the summary loses what that model needed. Shuffled with seed 100; each
validated as SWE-bench does (swe86.py); the first 10 valid kept in private/g86/valid100.json.
usage: python3 gates/gate100/referee/pick100.py"""
import csv, json, os, random, subprocess, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'gate86', 'referee'))
import swe86
pub = {s: {r['instance_id']: r for r in csv.DictReader(open(os.path.join(swe86.PRIV, f'{s}.csv')))} for s in ('fully-specified', 'underspecified')}
used = set(json.load(open(os.path.join(swe86.PRIV, 'valid.json'))))
c = [i for i in swe86.instances() if i['repo'] == 'django/django' and str(i['version']) in ('3', '3.0', '3.1', '3.2', '4', '4.0', '4.1', '4.2')
     and i['instance_id'] not in used and pub['fully-specified'].get(i['instance_id'], {}).get('claude_sonnet3.5') == '1'
     and pub['underspecified'].get(i['instance_id'], {}).get('claude_sonnet3.5') != '1']
random.Random(100).shuffle(c)
out = []
for inst in c:
    if len(out) >= 10: break
    d = tempfile.mkdtemp(prefix='g100v-', dir='/home/claude/swe'); w = swe86.worktree(inst, os.path.join(d, 'w'))
    try:
        ok_t = swe86.apply(w, inst['test_patch']); st0, _ = swe86.run_tests(w, inst); before = swe86.resolved(st0, inst, [])
        ok_g = swe86.apply(w, inst['patch']); st1, log = swe86.run_tests(w, inst)
        p2p = sorted(t for t, v in st1.items() if v == 'PASSED' and st0.get(t) == 'PASSED'); after = swe86.resolved(st1, inst, p2p)
        good = ok_t and ok_g and not before[0] and after[0]
        print(f"{inst['instance_id']} v{inst['version']}: before {before[1]}/{before[2]}, gold {after[1]}/{after[2]} -> {'valid' if good else 'INVALID'}", flush=True)
        if good:
            out.append(inst['instance_id'])
            json.dump(dict(f2p=swe86._list(inst['FAIL_TO_PASS']), p2p=p2p), open(os.path.join(swe86.PRIV, f"tests_{inst['instance_id']}.json"), 'w'))
    finally:
        subprocess.run(['git', '-C', swe86.DJANGO, 'worktree', 'remove', '--force', w], capture_output=True)
        subprocess.run(['rm', '-rf', d])
json.dump(out, open(os.path.join(swe86.PRIV, 'valid100.json'), 'w'), indent=1); print(out)
