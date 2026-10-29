#!/usr/bin/env python3
"""Gate 51: team notes at 12 builders, the size where Hive's law turns them on. Deep project, ABBA: S1, T1, T2, S2.
- S: 12 silent builders (Gate 50's flat prompt).
- T: 12 builders with team notes: tools/notes.py at every sync and before resolving a conflict; tools/land_note.py
  carries one line for the team in the landing commit, as Hive's `hive land --note` does.
The machine's load average is sampled every 10 s while each team runs (is it the CPU or the builders?).
usage: python3 gates/gate51/referee/run51.py [--skip-prereg-check]"""
import argparse, json, os, shutil, subprocess, sys, threading, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'lab')); sys.path.insert(0, os.path.join(ROOT, 'gates', 'gate46', 'referee'))
import run46
G = os.path.join(ROOT, 'gates', 'gate51'); RUN = os.path.join(ROOT, 'runs', 'g51'); run46.RUN = RUN
ORDER = ['S1', 'T1', 'T2', 'S2']; N = 12

def sample(stop, out):
    while not stop.is_set():
        out.append((int(time.time()), float(open('/proc/loadavg').read().split()[0]))); stop.wait(10)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--skip-prereg-check', action='store_true'); a = ap.parse_args()
    if not a.skip_prereg_check:
        import run_gate; run_gate.prereg_check('gates/gate51/prompts/PREDICTIONS.md')
    shutil.rmtree(RUN, ignore_errors=True); os.makedirs(os.path.join(RUN, 'out'))
    hidden = os.path.join(ROOT, 'private', 'g43', 'hidden2')
    seeds = {}
    for kind in ('S', 'T'):
        s = os.path.join(RUN, f'seed_{kind}'); run46.sh('git', 'clone', '-q', os.path.join(ROOT, 'gates', 'gate46', 'seed_deep.bundle'), s)
        run46.sh('git', 'remote', 'remove', 'origin', cwd=s)
        if kind == 'T':
            for f in ('notes.py', 'land_note.py'):
                shutil.copy(os.path.join(G, 'tools', f), os.path.join(s, 'tools', f))
            run46.sh('git', 'add', 'tools', cwd=s)
            run46.sh('git', '-c', 'user.name=hive', '-c', 'user.email=hive@local', 'commit', '-q', '-m', 'tools: team notes', cwd=s)
        seeds[kind] = s
    meta = {}
    for team in ORDER:
        print(run46.sh(sys.executable, os.path.join(ROOT, 'lab', 'make_swarm.py'), '--run', 'g51', '--seed', seeds[team[0]],
                       '--prompt', os.path.join(G, 'prompts', 'prompt_notes.md' if team[0] == 'T' else 'prompt_silent.md'),
                       '--arm', f'{team}:{N}'), end='')
        load, stop = [], threading.Event(); th = threading.Thread(target=sample, args=(stop, load)); th.start()
        t0 = time.time(); run46.say(f'launching {team} alone ({N} builders)')
        subprocess.run([sys.executable, os.path.join(ROOT, 'lab', 'launch.py'), '--run', 'g51', '--arm', team], cwd=ROOT, check=True)
        stop.set(); th.join()
        meta[team] = dict(team_start=int(t0), team_end=int(time.time()), builders=N, load=load)
        json.dump(meta, open(os.path.join(RUN, 'meta.json'), 'w'), indent=1)
    out = {}
    for team in ORDER:
        final = os.path.join(RUN, f'final_{team}'); run46.sh('git', 'clone', '-q', os.path.join(RUN, f'up{team}.git'), final)
        res = {}
        for suite, d in (('visible', os.path.join(final, 'tests', 'visible')), ('hidden', hidden)):
            j = os.path.join(RUN, f'{suite}_{team}.json')
            subprocess.run([sys.executable, 'run_tests.py', d, '--json', j], cwd=final, capture_output=True, timeout=3600)
            res[suite] = json.load(open(j)) if os.path.exists(j) else {}
        notes = run46.sh('git', 'log', 'main', '--format=%B', cwd=final).count('Team-note:')
        run46.say(f'{team}: visible {sum(res["visible"].values())}, hidden {sum(res["hidden"].values())}, notes {notes}; replaying')
        out[team] = dict(meta[team], visible=res['visible'], hidden=res['hidden'], notes=notes, progress=run46.replay(team, final))
    json.dump(out, open(os.path.join(RUN, 'teams.json'), 'w'))
    run46.say('done: python3 gates/gate51/referee/analyze.py runs/g51')

if __name__ == '__main__':
    main()
