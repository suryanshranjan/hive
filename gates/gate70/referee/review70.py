#!/usr/bin/env python3
"""Gate 70 steps: the owner is away overnight. Hive's overnight hand-over against questions saved for the morning.

usage: review70.py pre   <run dir> <oracle.py>              the owner's policy in prose (R); ask texts for N0 and QN
       review70.py after <run dir> <oracle.py> <N0's repo>  morning: he answers QN's recorded questions; Hive's hand-over of N0
Arms:
  N0  overnight build, no owner, no questions (3 builders): Hive's overnight build as shipped
  QN  overnight build (3 builders) told to record a question for every business decision the spec leaves open
      (queue_question.py), build their best guess, and keep going; in the morning the owner answers every recorded question
      (prompts/owner_qa.md, one at a time)
  HV  Hive's morning hand-over of N0 (code sheet as a list, spot checks of every function, skimming owner), then 3 fresh
      builders from the corrected sheet
  QA  3 fresh builders given his morning answers to QN's questions
The judge labels D, SL, HV, QA (as a sheet) and R."""
import json, os, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
for g in ('gate55', 'gate56', 'gate57', 'gate58', 'gate60', 'gate70'):
    sys.path.insert(0, os.path.join(ROOT, 'gates', g, 'referee'))
import review55 as r55, review56 as r56, review58 as r58, review60 as r60
from review55 import wt, intent, say

HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(ROOT, 'gates', 'gate70', 'prompts')
brief = lambda n: open(os.path.join(P, n)).read()
CMD = ['claude', '-p', '--output-format', 'json']

def pre(run, oracle_path):
    r55.P = P; r55.pre(run, oracle_path)
    q = os.path.join(run, 'queue_QN.jsonl'); open(q, 'w').close()
    tool = f'python3 {os.path.join(HERE, "queue_question.py")} {q} "<your question>"'
    with open(os.path.join(run, 'ask_texts.md'), 'a') as f:
        f.write(f"\n## QN\nThe product owner is away until the morning. For every business decision a function's one-line spec "
                "leaves open (cut-offs and boundaries, rounding, minimums and caps, what happens with blank, missing, negative or "
                f"oddly formatted input), record one question for him with `{tool}`, in plain business words, one decision per "
                "question; he will answer them all in the morning. Then build your best guess and keep going. Do not record a "
                "question a teammate has already recorded (`cat " + q + "`). (`tools/ask.py` is not used on this project.)\n")

def morning(run, R):
    """He answers every recorded question, one at a time, as Gate 66's owner on call."""
    b = brief('owner_qa.md').replace('{POLICY}', '\n'.join(f'- {r}' for r in R)); out, cost = [], 0.0
    for line in open(os.path.join(run, 'queue_QN.jsonl')):
        q = json.loads(line)
        p = subprocess.run(CMD, input=b.replace('{QUESTION}', q['question']), capture_output=True, text=True, timeout=300, cwd='/tmp')
        try:
            d = json.loads(p.stdout); ans, c = (d.get('result') or '').strip(), float(d.get('total_cost_usd') or 0)
        except Exception:
            ans, c = '', 0.0
        out.append(dict(q, answer=ans or 'Use your judgement on that one.')); cost += c
    return out, cost

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
    QA, cost['owner_morning'] = morning(run, R)
    say(f'morning: he answered {len(QA)} recorded questions')
    skim = brief('owner_skim.md').replace('{POLICY}', '\n'.join(f'- {r}' for r in R))
    t0 = time.time(); SL, rec = r55.terminal_review(D, skim, priv, 'SL'); rec['minutes'] = round((time.time() - t0) / 60, 1)
    touched = {s.get('function') for s in spots if any(D[n - 1] != SL[n - 1] for n in r58.about(D, s.get('function')) if n <= len(SL))}
    shown = [s for s in spots if s.get('function') not in touched] + [s for s in spots if s.get('function') in touched]
    t1 = time.time()
    HV, fixes, rec_s = r60.review_round(SL, shown, skim, priv, 'HV', f'Now {len(shown)} quick checks on what the build does in real cases.')
    say(f'D {len(D)} rules; SL {rec["replies"]} replies; HV {len(shown)} cases, {len(fixes)} corrected')
    jd = os.path.join(priv, 'judge'); shutil.rmtree(jd, ignore_errors=True); os.makedirs(jd)
    shutil.copy(oracle_path, os.path.join(jd, 'oracle.py'))
    json.dump(dict(D=D, SL=SL, HV=HV, QA=[f"Q: {x['question']} A: {x['answer']}" for x in QA], R=R), open(os.path.join(jd, 'sheets.json'), 'w'), indent=1)
    _, cost['judge'] = wt.agent(wt.AGENT, jd, brief('judge_brief.md').replace('{DIR}', jd), os.path.join(jd, 'judge.log'))
    labels = json.load(open(os.path.join(jd, 'labels.json')))['labels']
    with open(os.path.join(run, 'ask_texts.md'), 'a') as f:
        f.write(r55.section('HV', HV))
        f.write(f'\n## QA\n{wt.NO_OWNER}\n\n### The owner\'s answers\nThe team recorded these questions overnight and the owner answered them this '
                'morning. Build to his answers.\n\n'
                + '\n'.join(f"- Q: {x['question']}\n  A: {x['answer']}" for x in QA) + '\n')
    cost['owner_SL'] = rec['cost']; cost['owner_HV_spots'] = rec_s['cost']
    json.dump(dict(R=R, D=D, SL=SL, HV=HV, QA=QA, spots=spots, shown=shown, fixes=fixes, list_review=rec, spot_review=rec_s,
                   minutes=dict(list=rec['minutes'], spots=round((time.time() - t1) / 60, 1)), cost_usd=cost, labels=labels),
              open(os.path.join(run, 'sheet.json'), 'w'), indent=1)
    say('ask text for HV written')

if __name__ == '__main__':
    {'pre': lambda: pre(sys.argv[2], sys.argv[3]), 'after': lambda: after(sys.argv[2], sys.argv[3], sys.argv[4])}[sys.argv[1]]()
