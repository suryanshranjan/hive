"""G93 registered analysis (dry-run on Gate 90's flights before registering: C4 flagged live5's split key, as it should) (committed with the predictions, before the flights):
    python3 gates/gate93/referee/analyze.py runs/g93_live1 ... runs/g93_live5
A flight succeeds if it ends without a crash, with one branch, and >= 24 of 27 hidden tests pass.
pass^1: the share of flights that succeed. pass^5: whether all five do (tau-bench's reliability measure, Yao et al. 2024).
C1 pass^1 >= 0.8          C2 pass^5 (all five succeed)
C3 the median flight asks the owner <= 45 prompts (Gate 85: 55; Gate 90: 64)
C4 no delivery breaks an interface the goal states (refund's {amount, method}; the summary's three keys)
Also reported: hidden, prompts, words the owner typed, minutes, Hive's own spend by step (summed over flights)."""
import json, os, sys
from statistics import median
R = []
for d in sys.argv[1:]:
    f = json.load(open(os.path.join(d, 'flight.json'))); f['name'] = os.path.basename(d); R.append(f)
ok = lambda f: f['rc'] == 0 and not f['error'] and len(f['branches']) == 1 and (f['after'].get('passed') or 0) >= 24
by = {}
for f in R:
    print(f"{f['name']}: success {ok(f)}, hidden {f['after'].get('passed')}/27, prompts {f['owner_replies']}, words typed {f.get('owner_typed_words')}, "
          f"{f['minutes']} min, builders ${f['build_cost']}, Hive's own ${f.get('hive_own')} ({(f.get('hive_own') or 0) / max(0.01, f['build_cost']):.1f}x)")
    for k, v in (f.get('hive_own_by') or {}).items(): by[k] = by.get(k, 0) + v
tot = sum(by.values()) or 1
print("\nHive's own spend by step, all flights: " + ', '.join(f"{k} ${v:.2f} ({100*v/tot:.0f}%)" for k, v in sorted(by.items(), key=lambda x: -x[1])))
p1 = sum(ok(f) for f in R) / len(R); p5 = all(ok(f) for f in R)
mp = median(f['owner_replies'] for f in R)
import glob, re
def broken(d):
    t = open(os.path.join(d, 'delivered', 'shop', 'refunds.py')).read() if os.path.exists(os.path.join(d, 'delivered', 'shop', 'refunds.py')) else ''
    return bool(re.search(r"return \{[^}]*'(split|card|store_credit)'\s*:", t))
c4 = not any(broken(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', '..', 'runs', f['name'])) for f in R)
print(f"\npass^1 {p1:.2f}, pass^5 {p5}, median prompts {mp}, median hidden {median(f['after'].get('passed') or 0 for f in R)}")
print('\npredictions')
for tag, text, held in [('C1', f'pass^1 >= 0.8 ({p1:.2f})', p1 >= 0.8), ('C2', f'pass^5 ({p5})', p5),
                        ('C3', f'median prompts <= 45 ({mp})', mp <= 45), ('C4', 'no delivery breaks a stated interface', c4)]:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
