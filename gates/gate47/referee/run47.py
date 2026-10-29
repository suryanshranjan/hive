#!/usr/bin/env python3
"""Gate 47: Claude and Codex in one swarm. Do builders on two different coding agents coordinate through Hive's
protocol (claims, the guard) as well as builders on one? And Codex as the lead of Gate 46's two-level swarm.

usage: python3 gates/gate47/referee/run47.py [--skip-prereg-check] [--only M1,C]

Project: Gate 46's deep project (gates/gate46/seed_deep.bundle: Gate 1's 221-line skeleton engine, 1,340 visible
tests, 9 pass at the start). Prompts are Gate 46's, unchanged. Teams run one after another, each alone on the machine:
- M1, M2: 4 flat workers, mixed: w1, w3 on Claude Code, w2, w4 on Codex (Hive's presets).
- C: 4 flat workers on Claude Code.   X: 4 flat workers on Codex.
- LX: a Codex lead keeps BRAIN.md over 6 Claude workers.   LC: the same with a Claude lead (Gate 46's H, on this machine).
Order: M1, C, X, LX, LC, M2. Afterwards every landing on each team's main is replayed on the visible suite (progress over
time, and which agent's commit broke main, if any), and the final main is scored on the hidden suite (gen2.py seed
5000000, generated privately under private/, never committed). Writes runs/g47/teams.json."""
import argparse, json, os, shlex, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'lab')); sys.path.insert(0, ROOT)
from hive.swarm import AGENTS, _usage
G = os.path.join(ROOT, 'gates', 'gate47'); RUN = os.path.join(ROOT, 'runs', 'g47')
SEED = os.path.join(ROOT, 'gates', 'gate46', 'seed_deep.bundle')
ORDER = ['M1', 'C', 'X', 'LX', 'LC', 'M2']
TEAMS = {'M1': ('flat', 4, 'claude,codex', None), 'M2': ('flat', 4, 'claude,codex', None),   # kind, workers, mix, lead
         'C': ('flat', 4, 'claude', None), 'X': ('flat', 4, 'codex', None),
         'LX': ('lead', 6, 'claude', 'codex'), 'LC': ('lead', 6, 'claude', 'claude')}

def sh(*a, cwd=None, check=True):
    r = subprocess.run(list(a), cwd=cwd, capture_output=True, text=True)
    if check and r.returncode: sys.exit(f'failed: {" ".join(a)}\n{r.stdout}\n{r.stderr}')
    return r.stdout

def say(m): print(f'[{time.strftime("%H:%M:%S")}] {m}', flush=True)

def make(team, workers, prompt, seed):
    print(sh(sys.executable, os.path.join(ROOT, 'lab', 'make_swarm.py'), '--run', 'g47', '--seed', seed,
             '--prompt', os.path.join(G, 'prompts', prompt), '--arm', f'{team}:{workers}'), end='')

def launch(team, mix):
    subprocess.run([sys.executable, os.path.join(ROOT, 'lab', 'launch.py'), '--run', 'g47', '--arm', team, '--mix', mix],
                   cwd=ROOT, check=True)

def run_lead(team, mix, lead_agent):
    up = os.path.join(RUN, f'up{team}.git'); work = os.path.join(RUN, 'work', f'{team}-lead')
    sh('git', 'clone', '-q', up, work); sh('git', 'config', 'user.name', f'{team}-lead', cwd=work)
    sh('git', 'config', 'user.email', f'{team.lower()}-lead@hive.local', cwd=work)
    text = open(os.path.join(G, 'prompts', 'prompt_lead.md')).read().replace('{NW}', '6').replace('{WORK}', work)
    path = os.path.join(RUN, 'out', f'{team}-lead.json'); out = open(path, 'w'); t0 = time.time()
    lead = subprocess.Popen(shlex.split(AGENTS[lead_agent][0]), cwd=work, stdin=subprocess.PIPE, stdout=out,
                            stderr=subprocess.STDOUT, text=True)
    lead.stdin.write(text); lead.stdin.close()
    say(f'{team}: {lead_agent} lead started; waiting for the plan on main')
    plan_at = None
    while time.time() - t0 < 900 and lead.poll() is None:
        if 'BRAIN' in sh('git', '--git-dir', up, 'log', '--format=%s', 'main', check=False):
            plan_at = time.time(); break
        time.sleep(5)
    say(f'{team}: plan on main after {(plan_at or time.time()) - t0:.0f} s; launching 6 workers')
    launch(team, mix)
    try:
        lead.wait(timeout=360)
    except subprocess.TimeoutExpired:
        lead.kill(); say(f'{team}: lead still running 6 min after the workers stopped; stopped it')
    out.close(); tok, cost, _ = _usage(path)
    return dict(lead_agent=lead_agent, lead_start=int(t0), plan_seconds=round((plan_at or time.time()) - t0),
                lead_end=int(time.time()), lead_cost=float(cost) if cost not in ('', None) else None, lead_tokens=tok)

def replay(team, final):
    """Visible pass after every first-parent commit on main (progress over time, and whose commit broke main)."""
    log = sh('git', 'log', '--first-parent', '--reverse', '--format=%H|%ct|%an|%s', 'main', cwd=final).splitlines()
    rows, wt = [], os.path.join(RUN, f'replay_{team}')
    sh('git', 'clone', '-q', os.path.join(RUN, f'up{team}.git'), wt)
    for line in log:
        h, ct, an, subj = line.split('|', 3)
        if subj.startswith('Lock:') or an == 'hive':
            continue
        sh('git', 'checkout', '-q', '-f', h, cwd=wt)
        j = os.path.join(RUN, 'tmp_replay.json')
        if os.path.exists(j): os.remove(j)
        subprocess.run([sys.executable, 'run_tests.py', 'tests/visible', '--json', j], cwd=wt, capture_output=True, timeout=900)
        try: n = sum(json.load(open(j)).values())
        except Exception: n = None
        rows.append(dict(hash=h, t=int(ct), who=an, subject=subj[:120], visible=n))
    shutil.rmtree(wt, ignore_errors=True)
    return rows

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--skip-prereg-check', action='store_true'); ap.add_argument('--only')
    a = ap.parse_args()
    if not a.skip_prereg_check:
        import run_gate; run_gate.prereg_check('gates/gate47/prompts/PREDICTIONS.md')
    order = a.only.split(',') if a.only else ORDER
    shutil.rmtree(RUN, ignore_errors=True); os.makedirs(os.path.join(RUN, 'out'))
    hidden = os.path.join(ROOT, 'private', 'g43', 'hidden2')
    if not os.path.isdir(hidden):
        sh(sys.executable, os.path.join(ROOT, 'gates', 'gate2', 'referee', 'gen2.py'), hidden, '5000000', '20')
    seed = os.path.join(RUN, 'seed'); sh('git', 'clone', '-q', SEED, seed)
    sh('git', 'remote', 'remove', 'origin', cwd=seed)
    meta = {}
    for team in order:
        kind, n, mix, lead_agent = TEAMS[team]
        if kind == 'flat':
            make(team, n, 'prompt_flat.md', seed); t0 = time.time()
            say(f'launching {team} alone ({n} workers: {mix})')
            launch(team, mix); meta[team] = dict(team_start=int(t0), mix=mix)
        else:
            make(team, n, 'prompt_worker_h.md', seed)
            m = run_lead(team, mix, lead_agent); m.update(team_start=m['lead_start'], mix=mix); meta[team] = m
        json.dump(meta, open(os.path.join(RUN, 'meta.json'), 'w'), indent=1)
        say(f'{team} done')
    out = {}
    for team in order:
        final = os.path.join(RUN, f'final_{team}'); sh('git', 'clone', '-q', os.path.join(RUN, f'up{team}.git'), final)
        res = {}
        for suite, d in (('visible', os.path.join(final, 'tests', 'visible')), ('hidden', hidden)):
            j = os.path.join(RUN, f'{suite}_{team}.json')
            subprocess.run([sys.executable, 'run_tests.py', d, '--json', j], cwd=final, capture_output=True, timeout=3600)
            res[suite] = json.load(open(j)) if os.path.exists(j) else {}
        say(f'{team}: visible {sum(res["visible"].values())}/{len(res["visible"])}, '
            f'hidden {sum(res["hidden"].values())}/{len(res["hidden"])}; replaying')
        out[team] = dict(meta[team], visible=res['visible'], hidden=res['hidden'], progress=replay(team, final))
        json.dump(out, open(os.path.join(RUN, 'teams.json'), 'w'))
    say('done: python3 gates/gate47/referee/analyze.py runs/g47')

if __name__ == '__main__':
    main()
