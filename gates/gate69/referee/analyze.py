"""G69 registered analysis (committed with the predictions, before the run):  python3 gates/gate69/referee/analyze.py runs/g69
Features 2 and 3 pooled, per arm (F fresh, M earlier answers kept, C answers plus house rules): questions the owner was
asked; hidden pass (mean of the two builds).
A1 C asks <= 0.7x F's questions      A2 M asks <= 0.85x F's      A3 hidden C >= F - 2      A4 hidden C >= F + 3
Ship (Hive keeps every answer for later builds and distils house rules from them): A1 and A3.
Kill (nothing compounds): C asks > 0.85x F's."""
import collections, json, os, sys
d = sys.argv[1]; R = {}
for f in os.listdir(d):
    if f.startswith('feature_'):
        r = json.load(open(os.path.join(d, f))); R[(r['feature'], r['arm'])] = r
print('feature arm  questions  hidden   earlier answers in / house rules in')
for (k, a), r in sorted(R.items()):
    print(f"{k}  {a}    {len(r['questions']):4d}     {100 * r['hidden_tests'] / r['hidden_total']:5.1f}%   {r['earlier_in']} / {len(r['house_in'])}")
q = collections.Counter(); h = collections.defaultdict(list)
for (k, a), r in R.items():
    if k in (2, 3): q[a] += len(r['questions']); h[a].append(100 * r['hidden_tests'] / r['hidden_total'])
mh = {a: sum(v) / len(v) for a, v in h.items()}
print('\nfeatures 2-3: ' + '; '.join(f'{a}: {q[a]} questions, hidden {mh[a]:.1f}%' for a in ('F', 'M', 'C') if a in mh))
res = [('A1', f"C asks ≤ 0.7 × F: {q['C']} vs {q['F']}", q['C'] <= .7 * q['F']),
       ('A2', f"M asks ≤ 0.85 × F: {q['M']} vs {q['F']}", q['M'] <= .85 * q['F']),
       ('A3', f"hidden C ≥ F − 2: {mh['C'] - mh['F']:+.1f}", mh['C'] - mh['F'] >= -2),
       ('A4', f"hidden C ≥ F + 3: {mh['C'] - mh['F']:+.1f}", mh['C'] - mh['F'] >= 3)]
print('\npredictions')
for tag, text, held in res:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
print(f"Ship (keep answers, distil house rules): {'FIRED' if res[0][2] and res[2][2] else 'did not fire'}")
print(f"Kill (nothing compounds): {'FIRED' if q['C'] > .85 * q['F'] else 'did not fire'}")
