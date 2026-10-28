#!/usr/bin/env python3
"""Gate 43: a talking swarm against a silent swarm on the Gate 2/3 scale project (1,340 visible tests, 127 categories).

usage: python3 gates/gate43/referee/run43.py [--workers 6] [--skip-prereg-check]

Four teams of the same size run one after another, each alone on the machine, in the order S1, T1, T2, S2 (ABBA):
- S (silent): Gate 3's scale prompt, unchanged.
- T (talking): the same prompt plus a shared message board (tools/board.py post / read) and a paragraph asking for
  high-level coordination through it. Board files live in runs/g43/board_<team>.txt.
Then each team's final main is scored on the visible suite and on the hidden suite (gen2.py, seed 5000000, 20 per
category, generated into private/g43/hidden2 and never committed). Writes runs/g43/teams.json; analysis in analyze.py."""
import argparse, json, os, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'lab'))
G = os.path.join(ROOT, 'gates', 'gate43')
RUN = os.path.join(ROOT, 'runs', 'g43')
ORDER = ['S1', 'T1', 'T2', 'S2']

def sh(*a, cwd=None):
    r = subprocess.run(list(a), cwd=cwd, capture_output=True, text=True)
    if r.returncode: sys.exit(f'failed: {" ".join(a)}\n{r.stdout}\n{r.stderr}')
    return r.stdout

def say(m): print(f'[{time.strftime("%H:%M:%S")}] {m}', flush=True)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--skip-prereg-check', action='store_true'); a = ap.parse_args()
    if not a.skip_prereg_check:
        import run_gate; run_gate.prereg_check('gates/gate43/prompts/PREDICTIONS.md')
    shutil.rmtree(RUN, ignore_errors=True); os.makedirs(RUN)
    hidden = os.path.join(ROOT, 'private', 'g43', 'hidden2')
    if not os.path.isdir(hidden):
        sh(sys.executable, os.path.join(ROOT, 'gates', 'gate2', 'referee', 'gen2.py'), hidden, '5000000', '20')
    seeds = {}
    for kind in ('S', 'T'):
        s = os.path.join(RUN, f'seed_{kind}'); sh('git', 'clone', '-q', os.path.join(ROOT, 'gates', 'gate3', 'seed_scale.bundle'), s)
        sh('git', 'remote', 'remove', 'origin', cwd=s)
        if kind == 'T':
            shutil.copy(os.path.join(G, 'tools', 'board.py'), os.path.join(s, 'tools', 'board.py'))
            sh('git', 'add', 'tools/board.py', cwd=s)
            sh('git', '-c', 'user.name=hive', '-c', 'user.email=hive@local', 'commit', '-q', '-m',
               'tools/board.py: the team message board', cwd=s)
        seeds[kind] = s
    for team in ORDER:
        kind = team[0]
        print(sh(sys.executable, os.path.join(ROOT, 'lab', 'make_swarm.py'), '--run', 'g43', '--seed', seeds[kind],
                 '--prompt', os.path.join(G, 'prompts', 'prompt_talk.md' if kind == 'T' else 'prompt_silent.md'),
                 '--arm', f'{team}:{a.workers}'), end='')
        if kind == 'T':
            board = os.path.join(RUN, f'board_{team}.txt'); open(board, 'w').close()
            for k in range(1, a.workers + 1):
                sh('git', 'config', 'hive.board', board, cwd=os.path.join(RUN, 'work', f'{team}-w{k}'))
    for team in ORDER:
        say(f'launching {team} alone ({a.workers} workers)')
        subprocess.run([sys.executable, os.path.join(ROOT, 'lab', 'launch.py'), '--run', 'g43', '--arm', team], cwd=ROOT, check=True)
    out = {}
    for team in ORDER:
        final = os.path.join(RUN, f'final_{team}'); sh('git', 'clone', '-q', os.path.join(RUN, f'up{team}.git'), final)
        res = {}
        for suite, d in (('visible', os.path.join(final, 'tests', 'visible')), ('hidden', hidden)):
            j = os.path.join(RUN, f'{suite}_{team}.json')
            subprocess.run([sys.executable, 'run_tests.py', d, '--json', j], cwd=final, capture_output=True, text=True, timeout=3600)
            res[suite] = json.load(open(j)) if os.path.exists(j) else {}
        log = sh('git', 'log', '--first-parent', '--format=%ct|%an|%s', 'main', cwd=final).splitlines()
        out[team] = dict(visible=res['visible'], hidden=res['hidden'],
                         commits=[dict(t=int(l.split('|', 2)[0]), who=l.split('|', 2)[1], subject=l.split('|', 2)[2]) for l in log])
        say(f'{team}: visible {sum(res["visible"].values())}/{len(res["visible"])}, hidden {sum(res["hidden"].values())}/{len(res["hidden"])}')
    json.dump(out, open(os.path.join(RUN, 'teams.json'), 'w'))
    say('done: python3 gates/gate43/referee/analyze.py runs/g43')

if __name__ == '__main__':
    main()
