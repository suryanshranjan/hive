#!/usr/bin/env python3
"""Launch a run's workers as separate headless Claude Code processes, wait for all, record time and tokens.

usage: launch.py --run g8 [--arm D30 --arm NQ] [--max-parallel 6] [--dry-run]

--max-parallel caps how many workers run at once (others wait); use it on small machines and cloud sessions.

Each worker runs `$HIVE_WORKER_CMD` inside its own clone, with its rendered prompt on stdin.
Default HIVE_WORKER_CMD:
  claude -p --output-format json --permission-mode acceptEdits --allowedTools Bash Read Edit Write Glob Grep
Workers run shell commands, so run the whole lab inside a container or a throwaway VM.
Results: runs/<run>/out/<worker>.json (the CLI's JSON result) and runs/<run>/agents.csv (start, end, exit code, tokens)."""
import argparse, csv, glob, json, os, shlex, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT = 'claude -p --output-format json --permission-mode acceptEdits --allowedTools Bash Read Edit Write Glob Grep'

def usage(path):
    try:
        d = json.load(open(path))
    except Exception:
        return '', ''
    u = d.get('usage') or {}
    t = sum(int(u.get(k) or 0) for k in ('input_tokens', 'output_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens'))
    return (t or ''), d.get('total_cost_usd', '')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', required=True); ap.add_argument('--arm', action='append'); ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--max-parallel', type=int, default=0)
    a = ap.parse_args()
    run = os.path.join(ROOT, 'runs', a.run); os.makedirs(os.path.join(run, 'out'), exist_ok=True)
    prompts = sorted(glob.glob(os.path.join(run, 'p_*.md')))
    if a.arm: prompts = [p for p in prompts if os.path.basename(p)[2:].split('-w')[0] in a.arm]
    if not prompts: sys.exit('no prompts found; run lab/make_swarm.py first')
    cmd = shlex.split(os.environ.get('HIVE_WORKER_CMD', DEFAULT))
    procs, queue = [], []
    for p in prompts:
        me = os.path.basename(p)[2:-3]; work = os.path.join(run, 'work', me); text = open(p).read()
        if a.dry_run:
            print('would run in', work, ':', ' '.join(cmd), f'< prompt ({len(text)} chars on stdin)'); continue
        queue.append((me, work, text))
    if a.dry_run: return
    def start(me, work, text):
        out = open(os.path.join(run, 'out', f'{me}.json'), 'w')
        pr = subprocess.Popen(cmd, cwd=work, stdin=subprocess.PIPE, stdout=out, stderr=subprocess.STDOUT, text=True)
        try:
            pr.stdin.write(text); pr.stdin.close()
        except BrokenPipeError:
            pass
        print('launched', me, flush=True)
        return (me, time.time(), pr, out)
    cap = a.max_parallel or len(queue)
    while queue and len(procs) < cap: procs.append(start(*queue.pop(0)))
    rows, live = [], procs
    while live:
        for item in list(live):
            me, t0, pr, out = item
            code = pr.poll()
            if code is None: continue
            live.remove(item); out.close(); t1 = time.time()
            if queue: live.append(start(*queue.pop(0)))
            tok, cost = usage(os.path.join(run, 'out', f'{me}.json'))
            rows.append(dict(worker=me, start=int(t0), end=int(t1), minutes=round((t1 - t0) / 60, 1), exit=code, tokens=tok, cost_usd=cost))
            print(f'{me} finished: exit {code}, {rows[-1]["minutes"]} min, tokens {tok}, cost {cost}', flush=True)
        time.sleep(2)
    path = os.path.join(run, 'agents.csv'); new = not os.path.exists(path)
    with open(path, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); new and w.writeheader(); w.writerows(rows)
    print('wrote', path)

if __name__ == '__main__':
    main()
