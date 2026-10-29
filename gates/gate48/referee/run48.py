#!/usr/bin/env python3
"""Gate 48: a fast local reader for Jarvis. Reads every message in gates/gate48/set.jsonl and records what each arm
thinks the owner means (one of Jarvis's 9 intents), with its confidence and the time it took.

usage: python3 gates/gate48/referee/run48.py <arm> <out.json>
  claude    Hive's own reader today: assistant.CLASSIFY through explain.ask_json (Claude Code). Needs Claude logged in.
  laya-ml   Laya's multilingual checkpoint, on CPU (pip install laya).   laya-en: Laya's English checkpoint.
The conversation before a message is given to every arm the way Jarvis gives it (Owner:/Hive: lines)."""
import json, os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SET = os.path.join(ROOT, 'gates', 'gate48', 'set.jsonl')
# Jarvis's own definitions (hive/assistant.py CLASSIFY), one per option
INTENTS = {
    'build': 'he wants something built, added, fixed or made in the product, including agreeing to or correcting a build '
             'Hive just proposed',
    'stop_build': 'he wants the build that is running stopped or cancelled',
    'change': 'he has changed his mind about an earlier rule',
    'rule': 'he states, plainly and on purpose, a rule for how the product should behave from now on',
    'status': 'he asks how things are going',
    'greeting': 'a hello, with no request yet',
    'cloud_on': 'move Hive to the cloud, to keep working while his computer is off',
    'cloud_off': 'shut the cloud machine down',
    'reply': 'anything else: a question, a complaint, thanks, frustration, small talk, or declining what Hive proposed',
}

def recent(history):
    return '\n'.join(f"{'Owner' if w == 'owner' else 'Hive'}: {t}" for w, t in history) or '(nothing yet)'

def main():
    arm, out = sys.argv[1], sys.argv[2]
    items = [json.loads(l) for l in open(SET, encoding='utf-8') if l.strip()]
    rows = []
    if arm == 'claude':
        sys.path.insert(0, ROOT)
        from hive import assistant, explain
        for it in items:
            t = time.time()
            got = explain.ask_json(assistant.CLASSIFY.format(history=recent(it['history']), text=it['text'])) or {}
            rows.append(dict(id=it['id'], said=got.get('intent', ''), conf=None, seconds=round(time.time() - t, 3)))
            print(it['id'], rows[-1]['said'], rows[-1]['seconds'], flush=True)
    else:
        import laya
        agent = laya.load('ml' if arm == 'laya-ml' else 'convaiinnovations/laya')
        q = {'intent': {'type': 'choice', 'instructions': 'A business owner is texting his software assistant, Hive, '
                        'often with typos or in Hindi-English. What does he mean by his newest message?',
                        'criteria': INTENTS}}
        agent.system_one('warm up', q)   # the first call pays one-off setup; Jarvis keeps the model loaded
        for it in items:
            state = f"The conversation so far:\n{recent(it['history'])}\n\nHis newest message: {it['text']}"
            t = time.time()
            r = agent.system_one(state, q)['answers']['intent']
            rows.append(dict(id=it['id'], said=r['choice'], conf=r.get('confidence'), top=r.get('answer_confidence'),
                             seconds=round(time.time() - t, 3)))
            print(it['id'], r['choice'], r.get('confidence'), rows[-1]['seconds'], flush=True)
    json.dump(dict(arm=arm, rows=rows), open(out, 'w'), indent=1)

if __name__ == '__main__':
    main()
