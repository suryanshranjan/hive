#!/usr/bin/env python3
"""Gate 48: a fast local reader for Jarvis. Reads every message in gates/gate48/set.jsonl and records what each arm
thinks the owner means (one of Jarvis's 9 intents), with its confidence and the time it took.

usage: python3 gates/gate48/referee/run48.py <arm> <out.json> [--set dev.jsonl] [--variant v1|v2|v3]
  claude    Hive's own reader today: assistant.CLASSIFY through explain.ask_json (Claude Code). Needs Claude logged in.
  laya-ml   Laya's multilingual checkpoint, on CPU (pip install laya).   laya-en: Laya's English checkpoint.
The conversation before a message is given to every arm the way Jarvis gives it (Owner:/Hive: lines).
Variants (designed on the separate practice set dev.jsonl after v1 read only 43% of the registered set; v1 is the
registered arm): v2 splits "anything else" into concrete meanings, since these models rarely pick a catch-all (it was
picked 3 times for 29 such messages); v3 is v2 plus a stricter stop and the bare message when there is no conversation;
v4 asks v3's options as one yes/no question each and takes the likeliest (pass --variant v4 with laya-ml or laya-en)."""
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

REPLY = {   # v2: concrete kinds of "anything else", each mapped back to Jarvis's 'reply'
    'thanks': 'he thanks or praises Hive, or says the work is good',
    'complaint': 'he complains, is frustrated, or says something is slow, wrong or broken, without asking for a build',
    'product_question': 'he asks how his product works, or what it does in some case',
    'hive_question': 'he asks about Hive itself: what it can do, what it is, its cost, which models it uses, what it decided',
    'decline': 'he says no or not now to what Hive just proposed, or tells Hive not to do something',
    'acknowledge': 'a bare acknowledgement with no request: ok, hmm, theek hai, acha, lol',
}

def options(variant):
    if variant == 'v1':
        return INTENTS
    o = {k: v for k, v in INTENTS.items() if k != 'reply'}
    if variant in ('v3', 'v4'):
        o['stop_build'] = ('he explicitly tells Hive to stop, cancel, abort or kill the build that is running right now '
                           '(not a complaint, and not "stop doing" something else)')
    o.update(REPLY)
    return o

def recent(history):
    return '\n'.join(f"{'Owner' if w == 'owner' else 'Hive'}: {t}" for w, t in history) or '(nothing yet)'

def main():
    arm, out = sys.argv[1], sys.argv[2]
    flag = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    variant, path = flag('--variant', 'v1'), flag('--set', SET)
    items = [json.loads(l) for l in open(path, encoding='utf-8') if l.strip()]
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
                        'criteria': options(variant)}}
        if variant == 'v4':
            q = {k: {'type': 'noul', 'instructions': f'Does he mean this: {v}?'} for k, v in options(variant).items()}
        agent.system_one('warm up', q)   # the first call pays one-off setup; Jarvis keeps the model loaded
        for it in items:
            state = f"The conversation so far:\n{recent(it['history'])}\n\nHis newest message: {it['text']}"
            if variant in ('v3', 'v4') and not it['history']:
                state = f"His message: {it['text']}"
            t = time.time()
            ans = agent.system_one(state, q)['answers']
            if variant == 'v4':   # the likeliest yes; its probability is the confidence
                k = max(ans, key=lambda k: ans[k]['noul'])
                r = {'choice': k, 'confidence': ans[k]['noul'], 'answer_confidence': ans[k]['noul']}
            else:
                r = ans['intent']
            said = 'reply' if r['choice'] in REPLY else r['choice']
            rows.append(dict(id=it['id'], said=said, raw=r['choice'], conf=r.get('confidence'), top=r.get('answer_confidence'),
                             seconds=round(time.time() - t, 3)))
            print(it['id'], said, r.get('confidence'), rows[-1]['seconds'], flush=True)
    json.dump(dict(arm=arm, variant=variant, set=os.path.basename(path), rows=rows), open(out, 'w'), indent=1)

if __name__ == '__main__':
    main()
