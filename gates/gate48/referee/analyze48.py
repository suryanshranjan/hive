"""G48 registered analysis (committed with the predictions, before any arm runs). From the repo root:
    python3 gates/gate48/referee/analyze48.py runs/g48
Reads claude.json, laya-ml.json, laya-en.json (from run48.py) and gates/gate48/set.jsonl.
Accuracy = share of messages whose intent matches the label. Latency = median seconds per message.
Hybrid (what Jarvis would ship): Laya-ml's answer when its confidence >= t, else Claude's. t is fitted on the dev half
(odd ids): the lowest t on a 0.05 grid at which Laya-ml's accepted dev answers are >= 95% right (with >= 5 accepted).
It is then scored on the test half (even ids) only.
L1: Claude >= 90% accurate.                          L2: Laya-ml >= 80% accurate.
L3: Laya-ml median <= 1.0 s on 2 CPUs.               L4: on the test half the hybrid is within 3 points of Claude and Laya
                                                         answers >= 50% of messages.
L5: Laya-ml is >= 10 points less accurate on Hindi or mixed messages than on English ones.
L6: Laya-ml never says stop_build, cloud_off or cloud_on for a message that means something else.
Ship (Jarvis reads with Laya first, Claude when unsure): L4 holds.
Kill (Claude stays the only reader): on the test half the hybrid loses more than 3 points, or Laya answers < 30%."""
import json, os, statistics, sys

d = sys.argv[1]
S = {it['id']: it for it in (json.loads(l) for l in open('gates/gate48/set.jsonl', encoding='utf-8') if l.strip())}
A = {a: {r['id']: r for r in json.load(open(os.path.join(d, f'{a}.json')))['rows']}
     for a in ('claude', 'laya-ml', 'laya-en') if os.path.exists(os.path.join(d, f'{a}.json'))}
ok = lambda a, i: A[a][i]['said'] == S[i]['intent']
acc = lambda a, ids: 100 * sum(ok(a, i) for i in ids) / max(1, len(ids))
ids = sorted(S); dev = [i for i in ids if i % 2]; test = [i for i in ids if not i % 2]
for a in A:
    print(f'{a:8s} accuracy {acc(a, ids):5.1f}%  median {statistics.median(r["seconds"] for r in A[a].values()):.2f} s  '
          f'en {acc(a, [i for i in ids if S[i]["lang"] == "en"]):5.1f}%  hi/mix '
          f'{acc(a, [i for i in ids if S[i]["lang"] != "en"]):5.1f}%')
L = A['laya-ml']; t_fit = None
for k in range(21):
    t = k / 20; taken = [i for i in dev if (L[i]['conf'] or 0) >= t]
    if len(taken) >= 5 and acc('laya-ml', taken) >= 95:
        t_fit = t; break
print(f'threshold fitted on dev: {t_fit}')
if t_fit is None:
    t_fit = 2.0   # Laya never trusted
hyb = {i: (L[i]['said'] if (L[i]['conf'] or 0) >= t_fit else A['claude'][i]['said']) for i in test}
h_acc = 100 * sum(hyb[i] == S[i]['intent'] for i in test) / len(test)
cover = 100 * sum((L[i]['conf'] or 0) >= t_fit for i in test) / len(test)
c_acc = acc('claude', test)
print(f'test half: Claude {c_acc:.1f}%, hybrid {h_acc:.1f}% with Laya answering {cover:.0f}%')
for i in ids:
    if not ok('laya-ml', i) or not ok('claude', i):
        print(f'  {i:3d} {S[i]["intent"]:10s} claude={A["claude"][i]["said"]:10s} laya={L[i]["said"]:10s} '
              f'conf={L[i]["conf"]}  "{S[i]["text"]}"')
danger = [i for i in ids if L[i]['said'] in ('stop_build', 'cloud_off', 'cloud_on') and L[i]['said'] != S[i]['intent']]
en = acc('laya-ml', [i for i in ids if S[i]['lang'] == 'en']); hi = acc('laya-ml', [i for i in ids if S[i]['lang'] != 'en'])
print('\npredictions')
for tag, text, held in [
        ('L1', f'Claude {acc("claude", ids):.1f}% >= 90%', acc('claude', ids) >= 90),
        ('L2', f'Laya-ml {acc("laya-ml", ids):.1f}% >= 80%', acc('laya-ml', ids) >= 80),
        ('L3', f'Laya-ml median {statistics.median(r["seconds"] for r in L.values()):.2f} s <= 1.0',
         statistics.median(r['seconds'] for r in L.values()) <= 1.0),
        ('L4', f'hybrid {h_acc:.1f}% vs Claude {c_acc:.1f}% (within 3), Laya answers {cover:.0f}% (>= 50%)',
         h_acc >= c_acc - 3 and cover >= 50),
        ('L5', f'Laya-ml en {en:.1f}% vs hi/mix {hi:.1f}% (gap >= 10)', en - hi >= 10),
        ('L6', f'Laya-ml wrong stop/cloud calls: {danger}', not danger)]:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
print(f'Ship (Laya first): {"FIRED" if h_acc >= c_acc - 3 and cover >= 50 else "did not fire"}')
print(f'Kill (Claude only): {"FIRED" if h_acc < c_acc - 3 or cover < 30 else "did not fire"}')
