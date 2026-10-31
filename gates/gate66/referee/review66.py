#!/usr/bin/env python3
"""Gate 66 steps: Hive against a Claude Code agent, with the same owner.

usage: review66.py pre   <run dir> <oracle.py>              the owner's policy in prose (R); ask texts; the owner on call
       review66.py after <run dir> <oracle.py> <N0's repo>  Hive's hand-over of N0's build, by the skimming owner
Arms:
  CC  one Claude Code builder (stage 1) who may ask the owner in plain words at any time (ask_owner.py; the owner is a
      headless Claude holding R, answering in a sentence or two, prompts/owner_qa.md)
  CQ  the same, told to ask him about every business decision the spec leaves open before building it
  N0  Hive's first build: 3 builders, no owner
  HV  Hive's hand-over of N0 (as shipped after Gate 63): the code sheet D as a rule list, then spot checks of every
      function (untouched first), each correction applied alone and re-shown, by the same owner persona as Gates 55-65's
      skimmer; then 3 fresh builders from the corrected sheet (stage 2)
The judge labels D, SL, HV and R."""
import json, os, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
for g in ('gate55', 'gate56', 'gate57', 'gate58', 'gate60', 'gate66'):
    sys.path.insert(0, os.path.join(ROOT, 'gates', g, 'referee'))
import review55 as r55, review56 as r56, review58 as r58, review60 as r60
from review55 import wt, intent, say

HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(ROOT, 'gates', 'gate66', 'prompts')
brief = lambda n: open(os.path.join(P, n)).read()
PORTS = {'CC': 7661, 'CQ': 7662}

def ports(run):
    """Each run its own ports, so a later run never reaches an earlier run's owner."""
    k = 10 * (ord(os.path.basename(run)[-1]) - ord('a'))
    return {a: p + k for a, p in PORTS.items()}

def ask_text(arm, port):
    tool = f'python3 {os.path.join(HERE, "ask_owner.py")} {port} "<your question>"'
    t = (f"The product owner is available on his phone, though busy: ask him with `{tool}`. Ask in plain business words, "
         "one decision per question; he answers in a sentence or two. (`tools/ask.py` is not used on this project.)")
    if arm == 'CQ':
        t += (" **Before you build each function, ask him about every business decision its one-line spec leaves open**: "
              "cut-offs and boundaries, rounding, minimums and caps, what happens with blank, missing, negative or oddly "
              "formatted input. Build to his answers.")
    return t

def pre(run, oracle_path):
    r55.P = P; r55.pre(run, oracle_path)
    with open(os.path.join(run, 'ask_texts.md'), 'a') as f:
        for arm, port in ports(run).items():
            f.write(f'\n## {arm}\n{ask_text(arm, port)}\n')
    for arm, port in ports(run).items():   # the owner on call, for the whole run (stopped by the driver afterwards)
        subprocess.Popen([sys.executable, os.path.join(HERE, 'owner_server.py'), '--port', str(port), '--policy',
                          os.path.join(run, 'pre.json'), '--log', os.path.join(run, f'owner_{arm}.jsonl')],
                         stdout=subprocess.DEVNULL, stderr=open(os.path.join(run, f'owner_{arm}.err'), 'w'), start_new_session=True)
    time.sleep(2)
    say('owner on call for CC and CQ')

def after(run, oracle_path, base_repo):
    name = os.path.basename(run); priv = os.path.join(ROOT, 'private', name)
    o = intent.load_oracle(oracle_path); spec = wt.spec_lines(o, intent.Gen(o).CATS)
    pre_rec = json.load(open(os.path.join(run, 'pre.json'))); R = pre_rec['R']; cost = dict(pre_rec['cost_usd'])
    r56.P = P; r58.P = P
    D, cost['describer'] = r56.describe('describer_brief.md', os.path.join(priv, 'describer'), base_repo, spec)
    sd = os.path.join(priv, 'spotter'); shutil.rmtree(sd, ignore_errors=True); os.makedirs(sd); shutil.copytree(base_repo, os.path.join(sd, 'repo'))
    _, cost['spotter'] = wt.agent(wt.AGENT, sd, brief('spotter_brief.md').replace('{BASE}', os.path.join(sd, 'repo'))
                                  .replace('{OUT}', sd).replace('{SPEC}', spec), os.path.join(sd, 'spotter.log'))
    spots = [s for s in json.load(open(os.path.join(sd, 'spots.json'))) if isinstance(s, dict) and s.get('say')]
    assert spots, 'spotter wrote no spot checks'
    skim = brief('owner_skim.md').replace('{POLICY}', '\n'.join(f'- {r}' for r in R))
    t0 = time.time(); SL, rec = r55.terminal_review(D, skim, priv, 'SL'); rec['minutes'] = round((time.time() - t0) / 60, 1)
    touched = {s.get('function') for s in spots if any(D[n - 1] != SL[n - 1] for n in r58.about(D, s.get('function')) if n <= len(SL))}
    shown = [s for s in spots if s.get('function') not in touched] + [s for s in spots if s.get('function') in touched]
    t1 = time.time()
    HV, fixes, rec_s = r60.review_round(SL, shown, skim, priv, 'HV', f'Now {len(shown)} quick checks on what the build does in real cases.')
    say(f'D {len(D)} rules; SL {rec["replies"]} replies; HV {len(shown)} cases, {len(fixes)} corrected')
    jd = os.path.join(priv, 'judge'); shutil.rmtree(jd, ignore_errors=True); os.makedirs(jd)
    shutil.copy(oracle_path, os.path.join(jd, 'oracle.py'))
    json.dump(dict(D=D, SL=SL, HV=HV, R=R), open(os.path.join(jd, 'sheets.json'), 'w'), indent=1)
    _, cost['judge'] = wt.agent(wt.AGENT, jd, brief('judge_brief.md').replace('{DIR}', jd), os.path.join(jd, 'judge.log'))
    labels = json.load(open(os.path.join(jd, 'labels.json')))['labels']
    with open(os.path.join(run, 'ask_texts.md'), 'a') as f:
        f.write(r55.section('HV', HV))
    cost['owner_SL'] = rec['cost']; cost['owner_HV_spots'] = rec_s['cost']
    json.dump(dict(R=R, D=D, SL=SL, HV=HV, spots=spots, shown=shown, fixes=fixes, list_review=rec, spot_review=rec_s,
                   minutes=dict(list=rec['minutes'], spots=round((time.time() - t1) / 60, 1)), cost_usd=cost, labels=labels),
              open(os.path.join(run, 'sheet.json'), 'w'), indent=1)
    say('ask text for HV written')

if __name__ == '__main__':
    {'pre': lambda: pre(sys.argv[2], sys.argv[3]), 'after': lambda: after(sys.argv[2], sys.argv[3], sys.argv[4])}[sys.argv[1]]()
