"""G67 registered analysis (committed with the predictions, before the run):  python3 gates/gate67/referee/analyze.py runs/g67
For features 2 and 3 (pooled), per arm (F fresh, M Hive's standing rulings, C rulings plus house rules):
conv_D = convention decisions the first build's code gets right (judge's D labels, decisions labelled 'convention: ...');
conv_FINAL / own_FINAL = right in what the second build is given; hidden = mean hidden pass of the second builds;
owner load = rules shown in the list, cases shown, his replies, and corrections.
C1  conv_D(C) >= conv_D(F) + 4        C2  conv_D(M) >= conv_D(F) + 2
C3  hidden(C) >= hidden(F) + 5        C4  owner corrections (fixes + list replies that change a rule) C <= 0.7 x F
Ship (Hive distils house rules from each hand-over and gives them to later builds): C1 and C3.
Kill: conv_D(C) <= conv_D(F) and hidden(C) <= hidden(F) (nothing compounds)."""
import collections, json, os, sys
d = sys.argv[1]
recs = {}
for f in os.listdir(d):
    if f.startswith('feature_') and f.endswith('.json'):
        r = json.load(open(os.path.join(d, f))); recs[(r['feature'], r['arm'])] = r
def counts(r):
    is_conv = lambda x: str(r['decisions'].get(x['function'], [''] * 9)[int(x['decision'])] if int(x['decision']) < len(
        r['decisions'].get(x['function'], [])) else '').startswith('convention')   # from the policy's own labels
    conv = [x for x in r['labels'] if is_conv(x)]
    own = [x for x in r['labels'] if not is_conv(x)]
    return dict(conv_n=len(conv), conv_D=sum(x['D'] == 'right' for x in conv), conv_FINAL=sum(x['FINAL'] == 'right' for x in conv),
                own_n=len(own), own_D=sum(x['D'] == 'right' for x in own), own_FINAL=sum(x['FINAL'] == 'right' for x in own),
                hidden=100 * r['hidden_tests'] / r['hidden_total'], rules_shown=len(r['shown']), repeats=len(r['repeats']),
                cases=len(r['shown_cases']), replies=r['list_review']['replies'] + r['spot_review']['replies'],
                fixes=len(r['fixes']), changed=len(r['changed']), house=len(r['house_in']), rulings=len(r['rulings_in']))
print('feature arm  conv D/FINAL (of n)  own D/FINAL (of n)  hidden   rules shown (repeats left out)  cases  replies  fixes  changed  rulings/house in')
for (k, a), r in sorted(recs.items()):
    c = counts(r)
    print(f"{k}  {a}    {c['conv_D']:2d} / {c['conv_FINAL']:2d} ({c['conv_n']})        {c['own_D']:2d} / {c['own_FINAL']:2d} ({c['own_n']})      "
          f"{c['hidden']:5.1f}%   {c['rules_shown']:3d} ({c['repeats']})                       {c['cases']:3d}    {c['replies']:3d}    {c['fixes']:3d}    "
          f"{c['changed']:3d}     {c['rulings']}/{c['house']}")
P = collections.defaultdict(collections.Counter); H = collections.defaultdict(list)
for (k, a), r in recs.items():
    if k in (2, 3):
        c = counts(r)
        for key in ('conv_n', 'conv_D', 'conv_FINAL', 'own_n', 'own_D', 'own_FINAL', 'rules_shown', 'cases', 'replies', 'fixes', 'changed'):
            P[a][key] += c[key]
        H[a].append(c['hidden'])
h = {a: sum(v) / len(v) for a, v in H.items() if v}
print('\nfeatures 2-3 pooled:')
for a in ('F', 'M', 'C'):
    if a in P:
        p = P[a]
        print(f"{a}: conventions right first build {p['conv_D']}/{p['conv_n']}, given to second build {p['conv_FINAL']}/{p['conv_n']}; own decisions "
              f"{p['own_D']}/{p['own_n']} -> {p['own_FINAL']}/{p['own_n']}; hidden {h.get(a, float('nan')):.1f}%; owner: {p['rules_shown']} rules, "
              f"{p['cases']} cases, {p['replies']} replies, {p['fixes']} corrected cases, {p['changed']} rules changed")
if all(a in P for a in 'FMC'):
    corr = {a: P[a]['changed'] for a in 'FMC'}
    res = [('C1', f"conv_D C ≥ F + 4: {P['C']['conv_D']} vs {P['F']['conv_D']}", P['C']['conv_D'] >= P['F']['conv_D'] + 4),
           ('C2', f"conv_D M ≥ F + 2: {P['M']['conv_D']} vs {P['F']['conv_D']}", P['M']['conv_D'] >= P['F']['conv_D'] + 2),
           ('C3', f"hidden C ≥ F + 5: {h['C'] - h['F']:+.1f}", h['C'] - h['F'] >= 5),
           ('C4', f"owner corrections C ≤ 0.7 × F: {corr['C']} vs {corr['F']}", corr['C'] <= .7 * corr['F'])]
    print('\npredictions')
    for tag, text, held in res:
        print(f'{tag} {text} -> {"held" if held else "failed"}')
    print(f"Ship (house rules): {'FIRED' if res[0][2] and res[2][2] else 'did not fire'}")
    print(f"Kill (nothing compounds): {'FIRED' if P['C']['conv_D'] <= P['F']['conv_D'] and h['C'] <= h['F'] else 'did not fire'}")
