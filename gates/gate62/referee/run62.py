#!/usr/bin/env python3
"""Gate 62: does a second build from a different model disagree where the first build is wrong? (mechanical, no owner)

usage: run62.py <g60 run name: g60a | g60b> <oracle.py>      (from the repo root)

For one of Gate 60's runs: three more builds of the same spec from its starting repo, 3 builders each, no owner:
  So  Sonnet again (the default builder model; Gate 60's N0 and B were Sonnet): the same-model replicate
  Op  Opus
  Ha  Haiku
Each runs Gate 60's 300 prober calls (gates/gate60/referee/wings.py). analyze.py compares each with Gate 60's N0 on the
calls where N0's result differs from the policy (the oracle is used only for scoring)."""
import json, os, shutil, subprocess, sys, threading

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'lab')); sys.path.insert(0, os.path.join(ROOT, 'gates', 'gate41', 'referee'))
import intent, run_gate
import wind_tunnel as wt
say = run_gate.say
BASE = 'claude -p --output-format json --permission-mode acceptEdits --allowedTools Bash Read Edit Write Glob Grep'
WINGS = {'So': 'sonnet', 'Op': 'opus', 'Ha': 'haiku'}

def main(src, oracle):
    run_gate.prereg_check('gates/gate62/prompts/PREDICTIONS.md')
    score_only = os.environ.get('G62_SCORE_ONLY') == '1'   # rescoring finished builds after a referee fault (disclosed)
    name = 'g62' + src[-1]; run = os.path.join(ROOT, 'runs', name)
    if not score_only:
        shutil.rmtree(run, ignore_errors=True); os.makedirs(run)
    o = intent.load_oracle(oracle); agg = intent.Gen(o).AGG or ''
    asks = os.path.join(run, 'ask_texts.md')
    os.path.exists(asks) and score_only or open(asks, 'w').write(''.join(f'## {w}\n{wt.NO_OWNER} Work from the spec and the examples.\n\n' for w in WINGS))
    cmd = [sys.executable, os.path.join(ROOT, 'lab', 'make_swarm.py'), '--run', name, '--seed', os.path.join(ROOT, 'runs', src, 'seed'),
           '--prompt', os.path.join(ROOT, 'gates', 'gate60', 'prompts', 'prompt_builder.md'), '--ask-texts', asks,
           '--example-file', os.path.join(ROOT, 'runs', src, 'example.txt')]
    for w in WINGS: cmd += ['--arm', f'{w}:3:none']
    if not score_only:
        subprocess.run(cmd, check=True, cwd=ROOT)
    def go(w):
        env = dict(os.environ, HIVE_WORKER_CMD=f'{BASE} --model {WINGS[w]}')
        subprocess.run([sys.executable, os.path.join(ROOT, 'lab', 'launch.py'), '--run', name, '--arm', w], env=env, cwd=ROOT)
    say(f'{name}: building So, Op, Ha (3 builders each) from runs/{src}/seed...')
    ts = [threading.Thread(target=go, args=(w,)) for w in WINGS]
    if not score_only:
        [t.start() for t in ts]; [t.join() for t in ts]
    calls = os.path.join(ROOT, 'private', src, 'wings', 'calls.json')
    res = {}
    for w in list(WINGS) + ['N0', 'B']:
        fin = os.path.join(run, f'final_{w}')
        if w in WINGS:
            shutil.rmtree(fin, ignore_errors=True); subprocess.run(['git', 'clone', '-q', os.path.join(run, f'up{w}.git'), fin], check=True)
        else:
            fin = os.path.join(ROOT, 'runs', src, f'final_{w}')
        out = os.path.join(run, f'out_{w}.json')
        subprocess.run([sys.executable, os.path.join(ROOT, 'gates', 'gate60', 'referee', 'wings.py'), 'run', fin, calls, agg, out],
                       check=True, cwd='/')
        pr = os.path.join(run, f'probe_{w}.json')
        subprocess.run([sys.executable, os.path.join(ROOT, 'lab', 'intent.py'), 'probe', oracle, fin, pr,
                        str(json.load(open(os.path.join(ROOT, 'lab', 'experiments', f'{src}_wings.json')))['hidden_seed'])],
                       check=True, cwd='/', capture_output=True)
        P = json.load(open(pr))
        res[w] = dict(hidden_calls_right=sum(r['ok'] for r in P), hidden_calls=len(P))
    subprocess.run([sys.executable, os.path.join(ROOT, 'gates', 'gate60', 'referee', 'wings.py'), 'run', os.path.abspath(oracle), calls,
                    agg, os.path.join(run, 'out_policy.json')], check=True, cwd='/')
    json.dump(dict(src=src, wings=res, calls=json.load(open(calls))), open(os.path.join(run, 'results.json'), 'w'), indent=1)
    say(f'{name} done: ' + ', '.join(f"{w} {v['hidden_calls_right']}/{v['hidden_calls']}" for w, v in res.items()))

if __name__ == '__main__':
    main(sys.argv[1], os.path.abspath(sys.argv[2]))   # the probes run from '/'
