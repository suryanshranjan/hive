#!/usr/bin/env python3
"""Gate 64: dynamic effort. A strong planner over cheap builders, and cheap builders that call in stronger ones only
when they get stuck, against today's all-Sonnet team, on Gate 46's deep project (a 221-line skeleton to 1,340 tests).

usage: python3 gates/gate64/referee/run64.py [--skip-prereg-check]

Five teams, each alone on the machine, in the order H, OHE, S, HE, OH. Every wave's builders have a 30-minute cap.
  S    4 Sonnet builders, flat (today's Hive)
  H    4 Haiku builders, flat
  OH   an Opus lead writes and keeps BRAIN.md (Gate 46's lead) over 4 Haiku builders who follow it
  HE   H, then escalation: if any visible test still fails when the Haiku builders stop, 2 Sonnet builders take over
       what is left; if any still fails after them, 1 Opus builder
  OHE  OH, then the same escalation (the lead keeps running while the escalation builders work)
Before an escalation wave, locks left behind are cleared. Afterwards every landing on each team's main is replayed on the
visible suite and the final main is scored on the hidden suite (private/g43/hidden2). Writes runs/g64/teams.json."""
import argparse, glob, json, os, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'lab')); sys.path.insert(0, os.path.join(ROOT, 'gates', 'gate46', 'referee'))
import run46
G = os.path.join(ROOT, 'gates', 'gate64'); RUN = os.path.join(ROOT, 'runs', 'g64'); run46.RUN = RUN
BASE = 'claude -p --output-format json --permission-mode acceptEdits --allowedTools Bash Read Edit Write Glob Grep'
MODEL = lambda m: f'{BASE} --model {m}'
ORDER = ['H', 'OHE', 'S', 'HE', 'OH']
N = 4
say, sh = run46.say, run46.sh

def make(arm, n, prompt, seed):
    print(sh(sys.executable, os.path.join(ROOT, 'lab', 'make_swarm.py'), '--run', 'g64', '--seed', seed,
             '--prompt', os.path.join(G, 'prompts', prompt), '--arm', f'{arm}:{n}'), end='')

def launch(arm, model):
    subprocess.run([sys.executable, os.path.join(ROOT, 'lab', 'launch.py'), '--run', 'g64', '--arm', arm], cwd=ROOT, check=True,
                   env=dict(os.environ, HIVE_WORKER_CMD=MODEL(model)))

def visible_now(team):
    """(passing, total) on the team's main right now, after clearing locks left behind (committed as hive)."""
    d = os.path.join(RUN, f'check_{team}'); shutil.rmtree(d, ignore_errors=True)
    sh('git', 'clone', '-q', os.path.join(RUN, f'up{team}.git'), d)
    locks = [f for f in glob.glob(os.path.join(d, 'current_tasks', '*.txt'))]
    if locks:
        sh('git', 'rm', '-q', *[os.path.relpath(f, d) for f in locks], cwd=d)
        sh('git', '-c', 'user.name=hive', '-c', 'user.email=hive@local', 'commit', '-q', '-m', 'hive: clear locks left behind', cwd=d)
        sh('git', 'push', '-q', 'origin', 'HEAD:main', cwd=d)
    j = os.path.join(RUN, f'check_{team}.json')
    subprocess.run([sys.executable, 'run_tests.py', 'tests/visible', '--json', j], cwd=d, capture_output=True, timeout=900)
    v = json.load(open(j)); shutil.rmtree(d, ignore_errors=True)
    return sum(v.values()), len(v), len(locks)

def escalate(team):
    """Stronger builders, only while something still fails: 2 Sonnet, then 1 Opus. They clone the team's main."""
    waves = []
    for k, (model, n) in enumerate((('sonnet', 2), ('opus', 1)), 1):
        ok, tot, locks = visible_now(team)
        say(f'{team}: {ok}/{tot} visible pass' + (f' ({locks} locks cleared)' if locks else ''))
        if ok >= tot:
            break
        arm = f'{team}x{k}'
        up = os.path.join(RUN, f'up{team}.git'); template = open(os.path.join(G, 'prompts', 'prompt_flat.md')).read()
        for w in range(1, n + 1):
            me = f'{arm}-w{w}'; work = os.path.join(RUN, 'work', me)
            shutil.rmtree(work, ignore_errors=True); sh('git', 'clone', '-q', up, work)
            sh('git', 'config', 'user.name', me, cwd=work); sh('git', 'config', 'user.email', f'{me.lower()}@hive.local', cwd=work)
            open(os.path.join(RUN, f'p_{me}.md'), 'w').write(template.replace('{ME}', me).replace('{N}', str(n)).replace('{WORK}', work)
                                                            .replace('{LOG}', os.path.join(RUN, 'logs', f'{me}.log')))
        say(f'{team}: escalating to {n} {model} builder(s) ({tot - ok} visible tests still fail)')
        t0 = time.time(); launch(arm, model)
        waves.append(dict(model=model, builders=n, start=int(t0), end=int(time.time()), failing_before=tot - ok))
    ok, tot, _ = visible_now(team)
    return waves, ok

def lead_team(team, seed, then_escalate):
    make(team, N, 'prompt_worker_h.md', seed)
    up = os.path.join(RUN, f'up{team}.git'); work = os.path.join(RUN, 'work', f'{team}-lead')
    sh('git', 'clone', '-q', up, work); sh('git', 'config', 'user.name', f'{team}-lead', cwd=work)
    sh('git', 'config', 'user.email', f'{team.lower()}-lead@hive.local', cwd=work)
    text = open(os.path.join(G, 'prompts', 'prompt_lead.md')).read().replace('{NW}', str(N)).replace('{WORK}', work)
    out = open(os.path.join(RUN, 'out', f'{team}-lead.json'), 'w'); t0 = time.time()
    lead = subprocess.Popen(MODEL('opus').split(), cwd=work, stdin=subprocess.PIPE, stdout=out, stderr=subprocess.STDOUT, text=True)
    lead.stdin.write(text); lead.stdin.close()
    say(f'{team}: Opus lead started; waiting for the plan on main')
    plan_at = None
    while time.time() - t0 < 900 and lead.poll() is None:
        if 'BRAIN' in sh('git', '--git-dir', up, 'log', '--format=%s', 'main', check=False):
            plan_at = time.time(); break
        time.sleep(5)
    say(f'{team}: plan on main after {(plan_at or time.time()) - t0:.0f} s; launching {N} Haiku builders')
    launch(team, 'haiku')
    waves, final_ok = escalate(team) if then_escalate else ([], None)
    try:
        lead.wait(timeout=360)
    except subprocess.TimeoutExpired:
        lead.kill(); say(f'{team}: lead still running 6 min after the builders stopped; stopped it (its cost is lost)')
    out.close()
    try:
        cost = float(json.load(open(os.path.join(RUN, 'out', f'{team}-lead.json'))).get('total_cost_usd') or 0)
    except Exception:
        cost = None
    return dict(team_start=int(t0), plan_seconds=round((plan_at or time.time()) - t0), lead_cost=cost, waves=waves)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--skip-prereg-check', action='store_true'); a = ap.parse_args()
    if not a.skip_prereg_check:
        import run_gate; run_gate.prereg_check('gates/gate64/prompts/PREDICTIONS.md')
    shutil.rmtree(RUN, ignore_errors=True); os.makedirs(os.path.join(RUN, 'out')); os.makedirs(os.path.join(RUN, 'logs'))
    hidden = os.path.join(ROOT, 'private', 'g43', 'hidden2')
    seed = os.path.join(RUN, 'seed'); sh('git', 'clone', '-q', os.path.join(ROOT, 'gates', 'gate46', 'seed_deep.bundle'), seed)
    sh('git', 'remote', 'remove', 'origin', cwd=seed)
    meta = {}
    for team in ORDER:
        if team.startswith('O'):
            meta[team] = lead_team(team, seed, team.endswith('E'))
        else:
            make(team, N, 'prompt_flat.md', seed); t0 = time.time()
            say(f'launching {team} alone ({N} {"Sonnet" if team == "S" else "Haiku"} builders)')
            launch(team, 'sonnet' if team == 'S' else 'haiku')
            waves = escalate(team)[0] if team.endswith('E') else []
            meta[team] = dict(team_start=int(t0), waves=waves)
        meta[team]['team_end'] = int(time.time())
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
        out[team] = dict(meta[team], visible=res['visible'], hidden=res['hidden'], progress=run46.replay(team, final))
    json.dump(out, open(os.path.join(RUN, 'teams.json'), 'w'))
    say('done: python3 gates/gate64/referee/analyze.py runs/g64')

if __name__ == '__main__':
    main()
