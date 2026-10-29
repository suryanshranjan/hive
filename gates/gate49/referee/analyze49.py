"""G49 registered analysis (committed with the predictions, before training). From the repo root:
    python3 gates/gate49/referee/analyze49.py <exam answers.json> <practice answers.json>
Exam: gates/gate48/set.jsonl (120); practice: gates/gate48/dev.jsonl (48); Claude's exam answers: Gate 48's
results/claude.json. Threshold: lowest t on a 0.05 grid where the trained model's practice answers with confidence >= t
are >= 95% right (>= 5 accepted); hybrid on the exam: trained answer at >= t, else Claude's."""
import json, statistics, sys

load = lambda p: {json.loads(l)['id']: json.loads(l) for l in open(p, encoding='utf-8') if l.strip()}
S, D = load('gates/gate48/set.jsonl'), load('gates/gate48/dev.jsonl')
E = {r['id']: r for r in json.load(open(sys.argv[1]))['rows']}
P = {r['id']: r for r in json.load(open(sys.argv[2]))['rows']}
C = {r['id']: r for r in json.load(open('gates/gate48/results/claude.json'))['rows']}
acc = lambda ids, src=E, ref=S: 100 * sum(src[i]['said'] == ref[i]['intent'] for i in ids) / max(1, len(ids))
ids = sorted(S); en = [i for i in ids if S[i]['lang'] == 'en']; hi = [i for i in ids if S[i]['lang'] != 'en']
t_fit = None
for k in range(21):
    t = k / 20; taken = [i for i in P if (P[i]['conf'] or 0) >= t]
    if len(taken) >= 5 and acc(taken, P, D) >= 95:
        t_fit = t; break
thr = t_fit if t_fit is not None else 2.0
hyb = {i: E[i]['said'] if (E[i]['conf'] or 0) >= thr else C[i]['said'] for i in ids}
h_acc = 100 * sum(hyb[i] == S[i]['intent'] for i in ids) / len(ids)
cover = 100 * sum((E[i]['conf'] or 0) >= thr for i in ids) / len(ids)
c_acc = acc(ids, C)
med = statistics.median(r['seconds'] for r in E.values())
danger = [i for i in ids if E[i]['said'] in ('stop_build', 'cloud_on', 'cloud_off') and E[i]['said'] != S[i]['intent']]
print(f'trained: exam {acc(ids):.1f}% (en {acc(en):.1f}%, hi/mix {acc(hi):.1f}%), practice {acc(sorted(P), P, D):.1f}%, '
      f'median {med:.2f} s')
print(f'threshold fitted on practice: {t_fit}; hybrid {h_acc:.1f}% vs Claude {c_acc:.1f}%, trained model answering {cover:.0f}%')
for i in ids:
    if E[i]['said'] != S[i]['intent']:
        print(f'  {i:3d} {S[i]["intent"]:10s} trained={E[i]["said"]:10s} conf={E[i]["conf"]}  "{S[i]["text"]}"')
import re
grams = lambda t: (lambda w: {tuple(w[i:i + 3]) for i in range(len(w) - 2)})(re.sub(r'[^\w\s]', ' ', t.lower()).split())
trained = set().union(*(grams(json.loads(l)['text']) for l in open('gates/gate49/train.jsonl', encoding='utf-8') if l.strip()))
clean = [i for i in ids if not grams(S[i]['text']) & trained]   # the disclosed leak: exam items with no shared phrase
print(f'exam messages sharing no 3-word sequence with training: {len(clean)}; trained model on them: {acc(clean):.1f}%')
print('\npredictions')
for tag, text, held in [
        ('T1', f'{acc(ids):.1f}% >= 75%', acc(ids) >= 75), ('T2', f'{acc(ids):.1f}% >= 85%', acc(ids) >= 85),
        ('T3', f'hi/mix {acc(hi):.1f}% >= 65%', acc(hi) >= 65), ('T4', f'median {med:.2f} s <= 1.0', med <= 1.0),
        ('T5', f'wrong stop/cloud calls {len(danger)} <= 3: {danger}', len(danger) <= 3),
        ('T6', f'hybrid {h_acc:.1f}% within 3 of Claude {c_acc:.1f}%, answering {cover:.0f}% >= 50%',
         h_acc >= c_acc - 3 and cover >= 50)]:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
print(f'Ship: {"FIRED" if h_acc >= c_acc - 3 and cover >= 50 else "did not fire"}')
print(f'Kill: {"FIRED" if cover < 30 or h_acc < c_acc - 3 else "did not fire"}')
