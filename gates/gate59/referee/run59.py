#!/usr/bin/env python3
"""Gate 59: the fast reader retrained with the builder commands (13 meanings: Gate 48's 9 plus team, set_team,
stop_builder, instruct), on a new held-out exam written by a separate agent.

usage:
  python3 gates/gate59/referee/run59.py split  <train59.jsonl>                 -> train.jsonl + practice.jsonl (60 held back)
  python3 gates/gate59/referee/run59.py rows   <train.jsonl> <rows.jsonl>      owner messages -> Laya training rows
  python3 gates/gate59/referee/run59.py train  <rows.jsonl> <checkpoint dir>
  python3 gates/gate59/referee/run59.py read   <checkpoint dir> <set.jsonl> <out.json>     (2 threads, as on a laptop)
  python3 gates/gate59/referee/run59.py claude <set.jsonl> <out.json>          Hive's reader today (assistant.CLASSIFY)
The question's 13 options are Jarvis's own definitions (hive/assistant.py INTENTS_V2)."""
import json, os, random, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
G = os.path.join(ROOT, 'gates', 'gate59')

def recent(history):
    return '\n'.join(f"{'Owner' if w == 'owner' else 'Hive'}: {t}" for w, t in history) or '(nothing yet)'

def state(it):
    return f"The conversation so far:\n{recent(it['history'])}\n\nHis newest message: {it['text']}"

def question():
    from hive.assistant import INTENTS_V2
    return {'intent': {'type': 'choice', 'instructions': 'A business owner is texting his software assistant, Hive, '
                       'often with typos or in Hindi-English. What does he mean by his newest message?',
                       'criteria': INTENTS_V2}}

def load(p):
    return [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]

def main():
    cmd = sys.argv[1]
    if cmd == 'split':   # 60 held back, stratified by meaning, for fitting the hand-off threshold (never trained on)
        rows = load(sys.argv[2]); rng = random.Random(59); rng.shuffle(rows)
        by = {}
        for r in rows:
            by.setdefault(r['intent'], []).append(r)
        practice = []
        for intent, rs in sorted(by.items()):
            practice += rs[:max(2, round(60 * len(rs) / len(rows)))]
        practice = practice[:60]; keep = [r for r in rows if r not in practice]
        for name, part in (('train.jsonl', keep), ('practice.jsonl', practice)):
            with open(os.path.join(G, name), 'w', encoding='utf-8') as f:
                for k, r in enumerate(part, 1):
                    f.write(json.dumps(dict(r, id=k), ensure_ascii=False) + '\n')
        print(len(keep), 'train,', len(practice), 'practice')
    elif cmd == 'rows':
        q = question()
        with open(sys.argv[3], 'w', encoding='utf-8') as f:
            for it in load(sys.argv[2]):
                f.write(json.dumps({'state': state(it), 'questions': q, 'expected': {'intent': it['intent']}},
                                   ensure_ascii=False) + '\n')
    elif cmd == 'train':
        from laya.train import TrainConfig, finetune, resolve_checkpoint_dir
        t = time.time()
        cfg = TrainConfig(epochs=4, shuffle_options=('choice',), micro_batch=4, grad_accum=16)   # Gate 49's settings
        summary = finetune(sys.argv[2], resolve_checkpoint_dir('multilingual'), sys.argv[3], cfg, device='cpu')
        print('trained in', int(time.time() - t), 's;', {k: v for k, v in (summary or {}).items() if not isinstance(v, (list, dict))})
    elif cmd == 'read':
        import laya
        agent = laya.load(sys.argv[2]); q = question(); items = load(sys.argv[3])
        agent.system_one('warm up', q)
        rows = []
        for it in items:
            t = time.time()
            r = agent.system_one(state(it), q)['answers']['intent']
            rows.append(dict(id=it['id'], said=r['choice'], conf=r.get('confidence'), seconds=round(time.time() - t, 3)))
        json.dump(dict(arm='laya-tuned', rows=rows), open(sys.argv[4], 'w'), indent=1)
        print(sum(r['said'] == it['intent'] for r, it in zip(rows, items)), '/', len(items))
    elif cmd == 'claude':
        from hive import assistant, explain
        rows = []
        for it in load(sys.argv[2]):
            t = time.time()
            got = explain.ask_json(assistant.CLASSIFY.format(history=recent(it['history']), text=it['text'])) or {}
            rows.append(dict(id=it['id'], said=got.get('intent', ''), seconds=round(time.time() - t, 3)))
        json.dump(dict(arm='claude', rows=rows), open(sys.argv[3], 'w'), indent=1)

if __name__ == '__main__':
    main()
