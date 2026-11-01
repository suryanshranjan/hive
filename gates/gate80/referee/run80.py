#!/usr/bin/env python3
"""Gate 80: areas named from the goal's parts when none are configured, against free-text claims.
The job: Gate 78's (sqlglot 30.27.0 with 12 functions emptied, named in the goal; runs/g78_seed has no areas).
Arms, each 4 builders through the product, no owner, 30 minutes:
  F  as shipped: no areas configured, so any claim name is accepted
  A  hive.swarm.prepare(derive_areas=True): a model names the goal's independent parts (hive.law.part_names), and they
     become the areas builders must claim
usage: python3 gates/gate80/referee/run80.py <F|A> <k> [--skip-prereg-check]
Scores as Gate 78's, plus duplicated work: for each emptied function, the builders whose own commits (landed or not, from
the clones' reflogs; dup.py) rebuilt it."""
import argparse, json, os, shutil, subprocess, sys, tempfile, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'lab')); sys.path.insert(0, os.path.join(ROOT, 'gates', 'gate78', 'referee'))
import run78, dup
WORKERS, MINUTES = 4, 30

def changers(final, functions):
    out = {}
    for f in functions:
        path, name = f.split('::')
        r = subprocess.run(['git', 'log', '--format=%an', f'-L:^def {name}\\b:{path}', 'main'], cwd=final, capture_output=True, text=True)
        names = {l.strip() for l in r.stdout.splitlines() if l.strip() and l.strip().startswith('w') and l.strip()[1:].isdigit()}
        out[f] = sorted(names)
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('arm', choices=['F', 'A']); ap.add_argument('k')
    ap.add_argument('--skip-prereg-check', action='store_true'); a = ap.parse_args()
    if not a.skip_prereg_check:
        import run_gate; run_gate.prereg_check('gates/gate80/prompts/PREDICTIONS.md')
    from hive import swarm
    H = json.load(open(os.path.join(run78.PRIV, 'hidden.json'))); hidden = set(H['hidden'])
    run = os.path.join(ROOT, 'runs', f'g80_{a.arm}{a.k}'); shutil.rmtree(run, ignore_errors=True)
    t0 = time.time()
    swarm.prepare(run78.SEED, run, WORKERS, run78.goal(H['functions']), MINUTES, None, 0, False, code_map=False,
                  derive_areas=(a.arm == 'A'))
    prep = time.time() - t0
    t1 = time.time(); swarm.launch(run); t2 = time.time()
    final = os.path.join(run, 'final'); subprocess.run(['git', 'clone', '-q', os.path.join(run, 'up.git'), final], check=True)
    hp, other = run78.hidden_score(final, hidden)
    cfg = json.load(open(os.path.join(final, '.hive', 'config.json')))
    rows = list(__import__('csv').DictReader(open(os.path.join(run, 'agents.csv'))))
    ch = changers(final, H['functions'])
    per, dups, covered = dup.duplicated(run, [r['worker'] for r in rows], H['functions'])
    locks = subprocess.run(['git', 'log', '--format=%s', 'main'], cwd=final, capture_output=True, text=True).stdout.splitlines()
    out = dict(arm=a.arm, k=a.k, workers=WORKERS, prep_seconds=round(prep, 1), wall_minutes=round((t2 - t1) / 60, 1),
               hidden_passed=hp, hidden_total=len(hidden), other_failures=other, areas=cfg.get('area_parts') or cfg.get('areas'),
               changers=ch, rebuilt_by=per, duplicated=dups, covered=covered, locks=[l for l in locks if l.startswith('Lock:')],
               cost=round(sum(float(r['cost_usd'] or 0) for r in rows), 2), tokens=sum(int(r['tokens'] or 0) for r in rows),
               builders=rows, tools={r['worker']: run78.tool_use(os.path.join(run, 'work', r['worker'])) for r in rows})
    json.dump(out, open(os.path.join(run, 'result.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ('builders', 'tools', 'changers')}, indent=1))

if __name__ == '__main__':
    main()
