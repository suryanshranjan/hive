#!/usr/bin/env python3
"""Gate 69: does Hive need less of the owner the more he uses it, when builders ask? Gate 67's business (15 functions,
three features, 5 house conventions), built feature after feature on one codebase by 3 builders who ask the owner about
every open decision before building (Gate 68's SQ), each arm with its own owner on call (Gate 68's server).
No hand-over: the build's hidden pass is scored directly.

usage: python3 gates/gate69/referee/run69.py [--skip-prereg-check]

Feature 1 runs once (shared). From feature 2 on:
  F  fresh: the builders see only this feature's answers (Hive as shipped: hive answers is per build)
  M  every earlier answer is kept and given to later builds as the owner's standing answers (they read them before asking)
  C  M, plus house rules distilled from all earlier answers (prompts/house_brief.md), applied to new functions"""
import argparse, json, os, shutil, subprocess, sys, threading, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'gates', 'gate67', 'referee')); sys.path.insert(0, os.path.join(ROOT, 'lab'))
import run67 as g
import run_gate
from review55 import intent
from hive import explain

g.NAME = 'g69'; g.RUN = os.path.join(ROOT, 'runs', 'g69'); g.PRIV = os.path.join(ROOT, 'private', 'g69')
g.VSEED = {1: 69101, 2: 69102, 3: 69103}; g.HSEED = {1: 69200000, 2: 69300000, 3: 69400000}
P = os.path.join(ROOT, 'gates', 'gate69', 'prompts'); HERE = os.path.dirname(os.path.abspath(__file__))
SRV = os.path.join(ROOT, 'gates', 'gate68', 'referee'); PORTS = {'S': 7700, 'F': 7701, 'M': 7702, 'C': 7703}
say = g.say

def ask_text(arm, port, earlier, house):
    tool = f'python3 {os.path.join(SRV, "ask_owner.py")} {port}'
    t = (f"The product owner is available on his phone, though busy: ask him with `{tool} \"<your question>\"`. Ask in plain "
         "business words, one decision per question; he answers in a sentence or two. (`tools/ask.py` is not used on this "
         "project.) **Before you build each function, ask him about every business decision its one-line spec leaves open**: "
         "cut-offs and boundaries, rounding, minimums and caps, what happens with blank, missing, negative or oddly formatted "
         "input. Build to his answers. Your teammates ask him too: first read every answer he has given so far with "
         f"`{tool} --answers`, and do not ask again what he has already answered.")
    if earlier:
        t += ("\n\n## The owner's answers from earlier weeks\nHe gave these while the earlier functions were built. Read them before "
              "asking: do not ask him again what they already settle.\n\n" + '\n'.join(f"- Q: {x['question']}\n  A: {x['answer']}" for x in earlier) + '\n')
    if house:
        t += ("\n\n## The owner's house rules\nLearned from his earlier answers: how his business does things everywhere. Apply them to "
              "the new functions too, wherever they fit; ask him only where they do not settle a decision.\n\n" + '\n'.join(f'- {h}' for h in house) + '\n')
    return t

def server(arm):
    log = os.path.join(g.RUN, f'owner_{arm}.jsonl')
    subprocess.Popen([sys.executable, os.path.join(SRV, 'owner_server.py'), '--port', str(PORTS[arm]), '--policy', os.path.join(g.RUN, 'pre.json'),
                      '--log', log], stdout=subprocess.DEVNULL, stderr=open(log + '.err', 'w'), start_new_session=True)
    time.sleep(2)
    return log

def house_rules(answers):
    got = explain.ask_json(open(os.path.join(P, 'house_brief.md')).read().replace('{RULINGS}', '\n'.join(f"- Q: {x['question']} A: {x['answer']}" for x in answers)))
    return [h.strip() for h in (got or {}).get('house', []) if isinstance(h, str) and h.strip()] if isinstance(got, dict) else []

def feature(k, arm, seed, earlier, house, log):
    tag = f'{k}{arm}'; t0 = time.time(); n0 = sum(1 for _ in open(log)) if os.path.exists(log) else 0
    fin = g.build(f'Q{tag}', seed, ask_text(arm, PORTS[arm], earlier, house))
    L = [json.loads(x) for x in open(log)][n0:] if os.path.exists(log) else []
    of = os.path.join(g.PRIV, f'oracle_f{k}.py'); probe = os.path.join(g.RUN, f'probe_{tag}.json')
    g.sh(sys.executable, os.path.join(ROOT, 'lab', 'intent.py'), 'probe', of, fin, probe, str(g.HSEED[k]))
    tests = {}
    for r in json.load(open(probe)): tests.setdefault(r['test'], []).append(r['ok'])
    rec = dict(feature=k, arm=arm, questions=L, earlier_in=len(earlier), house_in=house, hidden_tests=sum(all(v) for v in tests.values()),
               hidden_total=len(tests), minutes=round((time.time() - t0) / 60, 1))
    json.dump(rec, open(os.path.join(g.RUN, f'feature_{tag}.json'), 'w'), indent=1)
    say(f'{tag}: {len(L)} questions, hidden {rec["hidden_tests"]}/{rec["hidden_total"]}, {rec["minutes"]} min')
    return rec, fin

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--skip-prereg-check', action='store_true'); a = ap.parse_args()
    if not a.skip_prereg_check: run_gate.prereg_check('gates/gate69/prompts/PREDICTIONS.md')
    shutil.rmtree(g.RUN, ignore_errors=True); os.makedirs(g.RUN); os.makedirs(g.PRIV, exist_ok=True)
    shutil.copy(os.path.join(ROOT, 'gates', 'gate67', 'referee', 'oracle_g67.py'), os.path.join(g.PRIV, 'oracle.py'))
    for k in (1, 2, 3):
        open(os.path.join(g.PRIV, f'oracle_f{k}.py'), 'w').write(g.WRAP.format(f=f'f{k}'))
    shutil.copy(os.path.join(ROOT, 'gates', 'gate67', 'results', 'pre.json'), os.path.join(g.RUN, 'pre.json'))   # the owner's policy prose (R)
    g.P = os.path.join(ROOT, 'gates', 'gate67', 'prompts')   # the builder prompt
    g.sh(sys.executable, os.path.join(ROOT, 'lab', 'new_intent_gate.py'), '--name', g.NAME, '--oracle', os.path.join(g.PRIV, 'oracle_f1.py'),
         '--visible-seed', str(g.VSEED[1]), '--hidden-seed', str(g.HSEED[1]))
    logs = {arm: server(arm) for arm in PORTS}
    rec1, fin1 = feature(1, 'S', os.path.join(g.RUN, 'seed'), [], [], logs['S'])
    answers1 = rec1['questions']
    house1 = house_rules(answers1)
    say(f'after feature 1: {len(answers1)} answers; house rules: {house1}')
    def chain(arm):
        earlier = list(answers1) if arm in ('M', 'C') else []; house = list(house1) if arm == 'C' else []; fin = fin1
        for k in (2, 3):
            seed = g.next_seed(k, fin, arm)
            rec, fin = feature(k, arm, seed, earlier, house, logs[arm])
            if arm in ('M', 'C'):
                earlier = earlier + rec['questions']
            if arm == 'C':
                house = house_rules(earlier)
    ts = [threading.Thread(target=chain, args=(arm,)) for arm in ('F', 'M', 'C')]
    [t.start() for t in ts]; [t.join() for t in ts]
    say('done: python3 gates/gate69/referee/analyze.py runs/g69')

if __name__ == '__main__':
    main()
