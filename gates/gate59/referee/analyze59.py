"""G59 registered analysis (committed with the predictions, before training). From the repo root:
    python3 gates/gate59/referee/analyze59.py <exam answers.json> <practice answers.json> <claude exam answers.json>
Exam: gates/gate59/exam.jsonl (130, written by a separate agent that read no repo file); practice: gates/gate59/practice.jsonl
(60 held back from training). Threshold: the lowest t on a 0.05 grid where the trained model's practice answers with
confidence >= t are >= 95% right (>= 5 accepted). Hybrid on the exam: trained answer at >= t, else Claude's."""
import json, statistics, sys

load = lambda p: {json.loads(l)['id']: json.loads(l) for l in open(p, encoding='utf-8') if l.strip()}
S, D = load('gates/gate59/exam.jsonl'), load('gates/gate59/practice.jsonl')
E = {r['id']: r for r in json.load(open(sys.argv[1]))['rows']}
P = {r['id']: r for r in json.load(open(sys.argv[2]))['rows']}
C = {r['id']: r for r in json.load(open(sys.argv[3]))['rows']}
acc = lambda ids, src=E, ref=S: 100 * sum(src[i]['said'] == ref[i]['intent'] for i in ids) / max(1, len(ids))
ids = sorted(S)
NEW = ('team', 'set_team', 'stop_builder', 'instruct')
new = [i for i in ids if S[i]['intent'] in NEW]
hi = [i for i in ids if S[i]['lang'] != 'en']
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
# a wrong action the reader would take alone: a stop (whole or one builder) or a cloud move it was confident about
risky = [i for i in ids if (E[i]['conf'] or 0) >= thr and E[i]['said'] != S[i]['intent']
         and E[i]['said'] in ('stop_build', 'stop_builder', 'cloud_on', 'cloud_off')]
print(f'trained: exam {acc(ids):.1f}% (builder commands {acc(new):.1f}%, hi/mix {acc(hi):.1f}%), median {med:.2f} s')
print(f'Claude: exam {c_acc:.1f}% (builder commands {acc(new, C):.1f}%)')
print(f'threshold fitted on practice: {t_fit}; hybrid {h_acc:.1f}% vs Claude {c_acc:.1f}%, trained model answering {cover:.0f}%')
for i in ids:
    if E[i]['said'] != S[i]['intent']:
        print(f'  {i:3d} {S[i]["intent"]:12s} trained={E[i]["said"]:12s} claude={C[i]["said"]:12s} conf={E[i]["conf"]}  "{S[i]["text"]}"')
print('\npredictions')
for tag, text, held in [
        ('B1', f'trained >= 75% on the exam: {acc(ids):.1f}%', acc(ids) >= 75),
        ('B2', f'trained >= 70% on the builder commands: {acc(new):.1f}%', acc(new) >= 70),
        ('B3', f'Claude >= 88% on the exam: {c_acc:.1f}%', c_acc >= 88),
        ('B4', f'median <= 1.0 s: {med:.2f}', med <= 1.0),
        ('B5', f'no confident wrong stop or cloud call: {risky}', not risky),
        ('B6', f'hybrid {h_acc:.1f}% within 3 of Claude {c_acc:.1f}%, answering {cover:.0f}% >= 50%', h_acc >= c_acc - 3 and cover >= 50)]:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
print(f'Ship: {"FIRED" if h_acc >= c_acc - 3 and cover >= 50 else "did not fire"}')
print(f'Kill: {"FIRED" if cover < 30 or h_acc < c_acc - 3 else "did not fire"}')
