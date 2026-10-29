#!/usr/bin/env python3
"""Gate 46: a two-level swarm (a lead who keeps a shared BRAIN.md over 6 builders) against a flat silent swarm of 7,
on a deep project: Gate 1's 221-line skeleton engine with the scale project's 1,340 tests (9 pass at the start).

usage: python3 gates/gate46/referee/run46.py [--skip-prereg-check]

Teams run one after another, each alone on the machine, ABBA: F1, H1, H2, F2.
- F (flat): 7 workers, Gate 3's protocol, silent (prompt_flat.md).
- H (lead + brain): the lead starts first and pushes BRAIN.md (levels, interfaces, what is unblocked); when the plan is
  on main, 6 workers start (prompt_worker_h.md): they follow the plan and leave notes in brain/notes/<name>.md. The lead
  keeps BRAIN.md current until the work stops. Headcount is 7 in both arms.
Afterwards every landing on each team's main is replayed on the visible suite (progress over time), and the final main
is scored on the hidden suite (gen2.py seed 5000000, private/g43/hidden2, never committed). Writes runs/g46/teams.json."""
import argparse, json, os, shlex, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'lab'))
G = os.path.join(ROOT, 'gates', 'gate46'); RUN = os.path.join(ROOT, 'runs', 'g46')
ORDER = ['F1', 'H1', 'H2', 'F2']
CMD = shlex.split('claude -p --output-format json --permission-mode acceptEdits --allowedTools Bash Read Edit Write Glob Grep')

def sh(*a, cwd=None, check=True):
    r = subprocess.run(list(a), cwd=cwd, capture_output=True, text=True)
    if check and r.returncode: sys.exit(f'failed: {" ".join(a)}\n{r.stdout}\n{r.stderr}')
    return r.stdout

def say(m): print(f'[{time.strftime("%H:%M:%S")}] {m}', flush=True)

def make(team, workers, prompt, seed):
    print(sh(sys.executable, os.path.join(ROOT, 'lab', 'make_swarm.py'), '--run', 'g46', '--seed', seed,
             '--prompt', os.path.join(G, 'prompts', prompt), '--arm', f'{team}:{workers}'), end='')

def run_h(team):
    up = os.path.join(RUN, f'up{team}.git'); work = os.path.join(RUN, 'work', f'{team}-lead')
    sh('git', 'clone', '-q', up, work); sh('git', 'config', 'user.name', f'{team}-lead', cwd=work)
    sh('git', 'config', 'user.email', f'{team.lower()}-lead@hive.local', cwd=work)
    text = open(os.path.join(G, 'prompts', 'prompt_lead.md')).read().replace('{NW}', '6').replace('{WORK}', work)
    out = open(os.path.join(RUN, 'out', f'{team}-lead.json'), 'w'); t0 = time.time()
    lead = subprocess.Popen(CMD, cwd=work, stdin=subprocess.PIPE, stdout=out, stderr=subprocess.STDOUT, text=True)
    lead.stdin.write(text); lead.stdin.close()
    say(f'{team}: lead started; waiting for the plan on main')
    plan_at = None
    while time.time() - t0 < 900 and lead.poll() is None:
        if 'BRAIN' in sh('git', '--git-dir', up, 'log', '--format=%s', 'main', check=False):
            plan_at = time.time(); break
        time.sleep(5)
    say(f'{team}: plan on main after {(plan_at or time.time()) - t0:.0f} s; launching 6 workers')
    subprocess.run([sys.executable, os.path.join(ROOT, 'lab', 'launch.py'), '--run', 'g46', '--arm', team], cwd=ROOT, check=True)
    try:
        lead.wait(timeout=360)
    except subprocess.TimeoutExpired:
        lead.kill(); say(f'{team}: lead still running 6 min after the workers stopped; stopped it (its cost is lost)')
    out.close(); t1 = time.time()
    try:
        d = json.load(open(os.path.join(RUN, 'out', f'{team}-lead.json'))); cost = float(d.get('total_cost_usd') or 0)
    except Exception:
        cost = None
    return dict(lead_start=int(t0), plan_seconds=round((plan_at or t1) - t0), lead_end=int(t1), lead_cost=cost)

def replay(team, final):
    """Visible pass after every first-parent commit on main (progress over time)."""
    log = sh('git', 'log', '--first-parent', '--reverse', '--format=%H|%ct|%an|%s', 'main', cwd=final).splitlines()
    rows, wt = [], os.path.join(RUN, f'replay_{team}')
    sh('git', 'clone', '-q', os.path.join(RUN, f'up{team}.git'), wt)
    for line in log:
        h, ct, an, subj = line.split('|', 3)
        if subj.startswith('Lock:') or an == 'hive':
            continue
        sh('git', 'checkout', '-q', '-f', h, cwd=wt)
        j = os.path.join(RUN, 'tmp_replay.json')
        subprocess.run([sys.executable, 'run_tests.py', 'tests/visible', '--json', j], cwd=wt, capture_output=True, timeout=900)
        try: n = sum(json.load(open(j)).values())
        except Exception: n = None
        rows.append(dict(hash=h, t=int(ct), who=an, subject=subj[:120], visible=n))
    shutil.rmtree(wt, ignore_errors=True)
    return rows

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--skip-prereg-check', action='store_true'); a = ap.parse_args()
    if not a.skip_prereg_check:
        import run_gate; run_gate.prereg_check('gates/gate46/prompts/PREDICTIONS.md')
    shutil.rmtree(RUN, ignore_errors=True); os.makedirs(os.path.join(RUN, 'out'))
    hidden = os.path.join(ROOT, 'private', 'g43', 'hidden2')
    if not os.path.isdir(hidden):
        sh(sys.executable, os.path.join(ROOT, 'gates', 'gate2', 'referee', 'gen2.py'), hidden, '5000000', '20')
    seed = os.path.join(RUN, 'seed'); sh('git', 'clone', '-q', os.path.join(G, 'seed_deep.bundle'), seed)
    sh('git', 'remote', 'remove', 'origin', cwd=seed)
    meta = {}
    for team in ORDER:
        if team[0] == 'F':
            make(team, 7, 'prompt_flat.md', seed); t0 = time.time()
            say(f'launching {team} alone (7 workers)')
            subprocess.run([sys.executable, os.path.join(ROOT, 'lab', 'launch.py'), '--run', 'g46', '--arm', team], cwd=ROOT, check=True)
            meta[team] = dict(team_start=int(t0))
        else:
            make(team, 6, 'prompt_worker_h.md', seed)
            m = run_h(team); m['team_start'] = m['lead_start']; meta[team] = m
        json.dump(meta, open(os.path.join(RUN, 'meta.json'), 'w'), indent=1)
    out = {}
    for team in ORDER:
        final = os.path.join(RUN, f'final_{team}'); sh('git', 'clone', '-q', os.path.join(RUN, f'up{team}.git'), final)
        res = {}
        for suite, d in (('visible', os.path.join(final, 'tests', 'visible')), ('hidden', hidden)):
            j = os.path.join(RUN, f'{suite}_{team}.json')
            subprocess.run([sys.executable, 'run_tests.py', d, '--json', j], cwd=final, capture_output=True, timeout=3600)
            res[suite] = json.load(open(j)) if os.path.exists(j) else {}
        say(f'{team}: visible {sum(res["visible"].values())}/{len(res["visible"])}, hidden {sum(res["hidden"].values())}/{len(res["hidden"])}; replaying')
        out[team] = dict(meta[team], visible=res['visible'], hidden=res['hidden'], progress=replay(team, final))
    json.dump(out, open(os.path.join(RUN, 'teams.json'), 'w'))
    say('done: python3 gates/gate46/referee/analyze.py runs/g46')

if __name__ == '__main__':
    main()
