"""Post hoc (not registered): Gate 49's shipped reader (9 meanings) on Gate 59's independent exam, items with those 9."""
import json, sys, time
sys.path.insert(0, '/g59')
import laya
from hive.assistant import INTENTS_V1
NINE = set(INTENTS_V1)
items = [json.loads(l) for l in open('/g59/gates/gate59/exam.jsonl', encoding='utf-8') if l.strip()]
items = [i for i in items if i['intent'] in NINE]
recent = lambda h: '\n'.join(f"{'Owner' if w == 'owner' else 'Hive'}: {t}" for w, t in h) or '(nothing yet)'
q = {'intent': {'type': 'choice', 'instructions': 'A business owner is texting his software assistant, Hive, often with '
                'typos or in Hindi-English. What does he mean by his newest message?', 'criteria': INTENTS_V1}}
agent = laya.load('/g49/ckpt'); agent.system_one('warm up', q)
rows = []
for it in items:
    r = agent.system_one(f"The conversation so far:\n{recent(it['history'])}\n\nHis newest message: {it['text']}", q)['answers']['intent']
    rows.append(dict(id=it['id'], said=r['choice'], conf=r.get('confidence'), want=it['intent'], lang=it['lang']))
ok = sum(r['said'] == r['want'] for r in rows)
acc_at = [r for r in rows if (r['conf'] or 0) >= 0.5]
print(f'Gate 49 reader on {len(rows)} independent exam items (its 9 meanings): {ok}/{len(rows)} = {100 * ok / len(rows):.1f}%')
print(f'at its shipped threshold 0.5: answers {len(acc_at)} ({100 * len(acc_at) / len(rows):.0f}%), right {sum(r["said"] == r["want"] for r in acc_at)}')
print('accepted and wrong:', [(r['id'], r['want'], r['said']) for r in acc_at if r['said'] != r['want']])
json.dump(rows, open('/g59/g49_on_exam59.json', 'w'), indent=1)
