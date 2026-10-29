#!/usr/bin/env python3
"""Gate 49: train Laya (the open copy of Jev) on the owner's style, then read the messages again.

usage:
  python3 gates/gate49/referee/run49.py rows   <train.jsonl> <rows.jsonl>     # owner messages -> Laya training rows
  python3 gates/gate49/referee/run49.py train  <rows.jsonl> <checkpoint dir>  # fine-tune the multilingual checkpoint
  python3 gates/gate49/referee/run49.py read   <checkpoint dir> <set.jsonl> <out.json>

The question and its 9 options are Gate 48's v1 (Jarvis's own definitions); the state is the conversation plus the
newest message, as in Gate 48. Reading uses 2 threads, as Jarvis would on a laptop."""
import json, os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'gates', 'gate48', 'referee'))
from run48 import INTENTS, recent   # Gate 48's registered question

Q = {'intent': {'type': 'choice', 'instructions': 'A business owner is texting his software assistant, Hive, often with '
                'typos or in Hindi-English. What does he mean by his newest message?', 'criteria': INTENTS}}

def state(it):
    return f"The conversation so far:\n{recent(it['history'])}\n\nHis newest message: {it['text']}"

def main():
    cmd = sys.argv[1]
    if cmd == 'rows':
        items = [json.loads(l) for l in open(sys.argv[2], encoding='utf-8') if l.strip()]
        with open(sys.argv[3], 'w', encoding='utf-8') as f:
            for it in items:
                f.write(json.dumps({'state': state(it), 'questions': Q, 'expected': {'intent': it['intent']}},
                                   ensure_ascii=False) + '\n')
        print(len(items), 'rows')
    elif cmd == 'train':
        from laya.train import TrainConfig, finetune, resolve_checkpoint_dir
        t = time.time()
        cfg = TrainConfig(epochs=4, shuffle_options=('choice',), micro_batch=4, grad_accum=16)   # same effective batch, half the memory
        summary = finetune(sys.argv[2], resolve_checkpoint_dir('multilingual'), sys.argv[3], cfg, device='cpu')
        print('trained in', int(time.time() - t), 's;', {k: v for k, v in (summary or {}).items() if not isinstance(v, (list, dict))})
    elif cmd == 'read':
        import laya
        agent = laya.load(sys.argv[2])
        items = [json.loads(l) for l in open(sys.argv[3], encoding='utf-8') if l.strip()]
        agent.system_one('warm up', Q)
        rows = []
        for it in items:
            t = time.time()
            r = agent.system_one(state(it), Q)['answers']['intent']
            rows.append(dict(id=it['id'], said=r['choice'], conf=r.get('confidence'), top=r.get('answer_confidence'),
                             seconds=round(time.time() - t, 3)))
        json.dump(dict(arm='laya-tuned', rows=rows), open(sys.argv[4], 'w'), indent=1)
        ok = sum(r['said'] == it['intent'] for r, it in zip(rows, items))
        print(f'{ok}/{len(items)} right')

if __name__ == '__main__':
    main()
