#!/usr/bin/env python3
"""Gate 79: a map of the codebase where finding the code is the work. sqlglot 30.27.0 with 12 planted bugs (pick79.py,
seed 79), given to the builders only as 11 users' bug reports (seed79.py), with areas bug01..bug11.
Arms, each 4 builders through the product (hive.swarm.prepare + launch), no owner, 30 minutes:
  H   Hive as shipped
  HG  plus the map in every clone, guided as graphify guides Claude Code: its rule (CLAUDE.local.md) and its hook, which
      reminds the builder of the map before each search or file read (hive/codemap.py, map_guide=True)
usage: python3 gates/gate79/referee/run79.py <H|HG> <k> [--skip-prereg-check]
Scoring as Gate 78's (run78.py): hidden suite (the 25 removed test methods) at the end and at every landing, cost, tool
calls per builder from the transcripts, leak check."""
import argparse, json, os, shutil, subprocess, sys, tempfile, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'lab')); sys.path.insert(0, os.path.join(ROOT, 'gates', 'gate78', 'referee'))
import run78
PRIV = os.path.join(ROOT, 'private', 'g79'); SEED = os.path.join(ROOT, 'runs', 'g79_seed')
WORKERS, MINUTES = 4, 30

def hidden_score(code_dir, hidden):
    run78.PRIV = os.path.join(PRIV, '_orig_link')   # run78 reads <PRIV>/orig/tests
    return run78.hidden_score(code_dir, hidden)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('arm', choices=['H', 'HG']); ap.add_argument('k')
    ap.add_argument('--skip-prereg-check', action='store_true'); a = ap.parse_args()
    if not a.skip_prereg_check:
        import run_gate; run_gate.prereg_check('gates/gate79/prompts/PREDICTIONS.md')
    link = os.path.join(PRIV, '_orig_link'); os.makedirs(link, exist_ok=True)
    if not os.path.exists(os.path.join(link, 'orig')): os.symlink(os.path.join(PRIV, 'src'), os.path.join(link, 'orig'))
    from hive import swarm
    os.environ['HIVE_GRAPHIFY'] = run78.GRAPHIFY
    H = json.load(open(os.path.join(PRIV, 'hidden.json'))); hidden = set(H['hidden'])
    run = os.path.join(ROOT, 'runs', f'g79_{a.arm}{a.k}'); shutil.rmtree(run, ignore_errors=True)
    t0 = time.time()
    swarm.prepare(SEED, run, WORKERS, open(os.path.join(PRIV, 'goal.md')).read(), MINUTES, None, 0, False,
                  code_map=(a.arm == 'HG'), map_guide=(a.arm == 'HG'))
    prep = time.time() - t0
    t1 = time.time(); swarm.launch(run); t2 = time.time()
    final = os.path.join(run, 'final'); subprocess.run(['git', 'clone', '-q', os.path.join(run, 'up.git'), final], check=True)
    hp, other = hidden_score(final, hidden)
    log = subprocess.run(['git', 'log', '--first-parent', '--format=%H %ct %s', 'main'], cwd=final, capture_output=True, text=True).stdout.split('\n')
    land = []
    for line in reversed([l for l in log if l.strip()][:-1]):
        h, ts, subj = line.split(' ', 2)
        if subj.startswith('Lock:'): continue
        wt = tempfile.mkdtemp(prefix='g79land-')
        subprocess.run(['git', 'worktree', 'add', '-q', '--detach', wt, h], cwd=final, capture_output=True)
        p, o = hidden_score(wt, hidden)
        subprocess.run(['git', 'worktree', 'remove', '--force', wt], cwd=final, capture_output=True)
        land.append(dict(commit=h[:8], minute=round((int(ts) - t1) / 60, 1), subject=subj[:100], hidden=p, other_fail=o))
        print(f"  landing {h[:8]} at {land[-1]['minute']} min: hidden {p}/{len(hidden)}", flush=True)
    rows = list(__import__('csv').DictReader(open(os.path.join(run, 'agents.csv'))))
    tools = {r['worker']: run78.tool_use(os.path.join(run, 'work', r['worker'])) for r in rows}
    out = dict(arm=a.arm, k=a.k, workers=WORKERS, prep_seconds=round(prep, 1), wall_minutes=round((t2 - t1) / 60, 1),
               hidden_passed=hp, hidden_total=len(hidden), other_failures=other, landings=land,
               cost=round(sum(float(r['cost_usd'] or 0) for r in rows), 2), tokens=sum(int(r['tokens'] or 0) for r in rows),
               builders=rows, tools=tools, map=os.path.exists(os.path.join(run, 'map', 'graphify-out', 'GRAPH_REPORT.md')))
    json.dump(out, open(os.path.join(run, 'result.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ('landings', 'builders', 'tools')}, indent=1))

if __name__ == '__main__':
    main()
