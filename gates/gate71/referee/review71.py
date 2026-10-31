#!/usr/bin/env python3
"""Gate 71 steps: a 20-function job, the owner on call at a person's pace (60 s an answer). One builder against 7 Hive
builders, both told to ask first, run one after the other (A1 then S7 in g71a; S7 then A1 in g71b).

usage: review71.py pre   <run dir> <oracle.py>      the owner's policy in prose (R); ask texts; one owner on call per arm
       review71.py after <run dir> <oracle.py> <repo>  nothing: the second arm simply runs after the first"""
import json, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
for g in ('gate55', 'gate71'):
    sys.path.insert(0, os.path.join(ROOT, 'gates', g, 'referee'))
import review55 as r55
from review55 import say
HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(ROOT, 'gates', 'gate71', 'prompts')
PORTS = {'A1': 7711, 'S7': 7712}; PACE = 60

def ports(run):
    k = 10 * (ord(os.path.basename(run)[-1]) - ord('a'))
    return {a: p + k for a, p in PORTS.items()}

def ask_text(arm, port):
    tool = f'python3 {os.path.join(HERE, "ask_owner.py")} {port}'
    t = (f"The product owner is available on his phone, though busy: ask him with `{tool} \"<your question>\"`. Ask in plain "
         "business words, one decision per question; he answers in a sentence or two, at a person's pace. (`tools/ask.py` is not "
         "used on this project.) **Before you build each function, ask him about every business decision its one-line spec "
         "leaves open**: cut-offs and boundaries, rounding, minimums and caps, what happens with blank, missing, negative or "
         "oddly formatted input. Build to his answers.")
    if arm == 'S7':
        t += (f" Your teammates ask him too: first read every answer he has given so far with `{tool} --answers`, and do not "
              "ask again what he has already answered.")
    return t

def pre(run, oracle_path):
    r55.P = P; r55.pre(run, oracle_path)
    with open(os.path.join(run, 'ask_texts.md'), 'a') as f:
        for arm, port in ports(run).items():
            f.write(f'\n## {arm}\n{ask_text(arm, port)}\n')
    for arm, port in ports(run).items():
        subprocess.Popen([sys.executable, os.path.join(HERE, 'owner_server.py'), '--port', str(port), '--policy', os.path.join(run, 'pre.json'),
                          '--log', os.path.join(run, f'owner_{arm}.jsonl'), '--min-seconds', str(PACE)],
                         stdout=subprocess.DEVNULL, stderr=open(os.path.join(run, f'owner_{arm}.err'), 'w'), start_new_session=True)
    time.sleep(2); say(f'owner on call for A1 and S7, {PACE} s an answer')

if __name__ == '__main__':
    if sys.argv[1] == 'pre':
        pre(sys.argv[2], sys.argv[3])
