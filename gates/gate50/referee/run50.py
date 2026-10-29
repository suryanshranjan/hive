#!/usr/bin/env python3
"""Gate 50: does the swarm beat one agent? A scaling curve on Gate 46's deep project with today's model.

usage: python3 gates/gate50/referee/run50.py [--skip-prereg-check]

Flat silent teams of 1, 2, 4, 7 and 12 builders (Gate 46's flat prompt, cap raised to 90 minutes so one builder can
finish), each alone on the 2-CPU machine, in a fixed shuffled order: N4, N1, N12, N2, N7. Every landing on each team's
main is replayed on the visible suite; the final main is scored on the hidden suite (private/g43/hidden2).
Writes runs/g50/teams.json; analysis in analyze.py."""
import argparse, json, os, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'lab')); sys.path.insert(0, os.path.join(ROOT, 'gates', 'gate46', 'referee'))
import run46
G = os.path.join(ROOT, 'gates', 'gate50'); RUN = os.path.join(ROOT, 'runs', 'g50')
run46.RUN = RUN
ORDER = [('N4', 4), ('N1', 1), ('N12', 12), ('N2', 2), ('N7', 7)]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--skip-prereg-check', action='store_true'); a = ap.parse_args()
    if not a.skip_prereg_check:
        import run_gate; run_gate.prereg_check('gates/gate50/prompts/PREDICTIONS.md')
    shutil.rmtree(RUN, ignore_errors=True); os.makedirs(os.path.join(RUN, 'out'))
    hidden = os.path.join(ROOT, 'private', 'g43', 'hidden2')
    if not os.path.isdir(hidden):
        run46.sh(sys.executable, os.path.join(ROOT, 'gates', 'gate2', 'referee', 'gen2.py'), hidden, '5000000', '20')
    seed = os.path.join(RUN, 'seed'); run46.sh('git', 'clone', '-q', os.path.join(ROOT, 'gates', 'gate46', 'seed_deep.bundle'), seed)
    run46.sh('git', 'remote', 'remove', 'origin', cwd=seed)
    meta = {}
    for team, n in ORDER:
        print(run46.sh(sys.executable, os.path.join(ROOT, 'lab', 'make_swarm.py'), '--run', 'g50', '--seed', seed,
                       '--prompt', os.path.join(G, 'prompts', 'prompt_flat.md'), '--arm', f'{team}:{n}'), end='')
        t0 = time.time(); run46.say(f'launching {team} alone ({n} builders)')
        subprocess.run([sys.executable, os.path.join(ROOT, 'lab', 'launch.py'), '--run', 'g50', '--arm', team], cwd=ROOT, check=True)
        meta[team] = dict(team_start=int(t0), builders=n, team_end=int(time.time()))
        json.dump(meta, open(os.path.join(RUN, 'meta.json'), 'w'), indent=1)
    out = {}
    for team, n in ORDER:
        final = os.path.join(RUN, f'final_{team}'); run46.sh('git', 'clone', '-q', os.path.join(RUN, f'up{team}.git'), final)
        res = {}
        for suite, d in (('visible', os.path.join(final, 'tests', 'visible')), ('hidden', hidden)):
            j = os.path.join(RUN, f'{suite}_{team}.json')
            subprocess.run([sys.executable, 'run_tests.py', d, '--json', j], cwd=final, capture_output=True, timeout=3600)
            res[suite] = json.load(open(j)) if os.path.exists(j) else {}
        run46.say(f'{team}: visible {sum(res["visible"].values())}/{len(res["visible"])}, hidden {sum(res["hidden"].values())}/{len(res["hidden"])}; replaying')
        out[team] = dict(meta[team], visible=res['visible'], hidden=res['hidden'], progress=run46.replay(team, final))
    json.dump(out, open(os.path.join(RUN, 'teams.json'), 'w'))
    run46.say('done: python3 gates/gate50/referee/analyze.py runs/g50')

if __name__ == '__main__':
    main()
