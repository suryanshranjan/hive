#!/usr/bin/env python3
"""Gate 75 (from Gate 74's driver; time to accuracy on an engineering-heavy job, 4 business functions): Gate 74: Gate 72's mixed job and busy owner (60 s an answer, queued, a 90-s ask), one builder (A1) against Hive's
7 split by kind of work (S7B): 6 engine builders who never touch the business functions (prompts/prompt_engine.md), and
1 business builder who owns all 10 and asks the owner systematically, function by function (prompts/prompt_business.md).
Each arm alone on the machine.

usage: python3 gates/gate74/referee/run74.py <a|b> [--skip-prereg-check]
  run a: A1 then S7B; run b: S7B then A1. Seeds 74100/74200000 (a), 74300/74400000 (b); a fresh rule-giver per run.
Scores: minutes from the arm's start to the first landing after which every visible test passes (and to 95%), the engine's
hidden suite (Gate 50's, private/g43/hidden2), the business functions' hidden pass (intent probe), questions asked."""
import argparse, json, os, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
for g in ('gate55', 'gate46'):
    sys.path.insert(0, os.path.join(ROOT, 'gates', g, 'referee'))
sys.path.insert(0, os.path.join(ROOT, 'lab'))
import review55 as r55, run46, run_gate
from review55 import wt, intent

P = os.path.join(ROOT, 'gates', 'gate75', 'prompts'); HERE = os.path.dirname(os.path.abspath(__file__)); say = run_gate.say
SEEDS = {'a': (75100, 75200000), 'b': (75300, 75400000)}; PORTS = {'a': {'A1': 7791, 'S7B': 7792}, 'b': {'A1': 7801, 'S7B': 7802}}
ORDER = {'a': ['A1', 'S7B'], 'b': ['S7B', 'A1']}; SIZE = {'A1': 1, 'S7B': 7}; PACE = 60

def sh(*a, cwd=None):
    return run46.sh(*a, cwd=cwd)

def ask_text(arm, port):
    tool = f'python3 {os.path.join(HERE, "ask_owner.py")} {port}'
    t = (f"He is available on his phone, though busy: ask him with `{tool} \"<your question>\"`, in plain business words, one "
         "decision per question; he answers in a sentence or two, at a person's pace. **Before you build each business function, "
         "ask him about every decision its one-line spec leaves open** (cut-offs and boundaries, rounding, minimums and caps, "
         "what happens with blank, missing, negative or oddly formatted input), and build to his answers. (`tools/ask.py` is "
         "not used on this project.) Ask systematically: for each function, (1) the rule itself (the formula, tiers, labels, "
         "format), (2) rounding and the exact form of the result, (3) boundaries and cut-offs, and (4) what happens with "
         "blank, missing, negative, zero or oddly formatted input. He answers one question at a time; if he has not answered within 90 seconds, the tool says "
         f"so and your question stays with him: work on another part meanwhile, and read `{tool} --answers` before you build "
         "the part it decides.")
    return t

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('run', choices=['a', 'b']); ap.add_argument('--skip-prereg-check', action='store_true')
    a = ap.parse_args()
    if not a.skip_prereg_check: run_gate.prereg_check('gates/gate75/prompts/PREDICTIONS.md')
    name = f'g75{a.run}'; RUN = os.path.join(ROOT, 'runs', name); PRIV = os.path.join(ROOT, 'private', name); run46.RUN = RUN
    shutil.rmtree(RUN, ignore_errors=True); os.makedirs(os.path.join(RUN, 'out')); os.makedirs(os.path.join(RUN, 'logs')); os.makedirs(PRIV, exist_ok=True)
    oracle = os.path.join(PRIV, 'oracle.py')
    if not os.path.exists(oracle):
        say('rule-giver writing the business policy...')
        with open(os.path.join(PRIV, 'rulegiver.json'), 'w') as out:
            subprocess.run(wt.AGENT, cwd=PRIV, input=open(os.path.join(P, 'rulegiver_brief.md')).read().replace('{DIR}', PRIV),
                           stdout=out, stderr=subprocess.STDOUT, text=True)
    o, names = run_gate.check_rules(oracle)
    r55.P = P; r55.pre(RUN, oracle)   # the owner's policy in prose (R) -> pre.json
    vseed, hseed = SEEDS[a.run]
    seed = os.path.join(RUN, 'seed'); sh('git', 'clone', '-q', os.path.join(ROOT, 'gates', 'gate46', 'seed_deep.bundle'), seed)
    sh('git', 'remote', 'remove', 'origin', cwd=seed)
    intent.cmd_tests(oracle, 'visible', os.path.join(seed, 'tests', 'visible'), vseed)
    g = intent.Gen(o)
    rows = [f"| `{o.SPEC[n].split(':', 1)[0].strip()}` | {o.SPEC[n].split(':', 1)[1].strip()}" + (' (an aggregate)' if n == g.AGG else '') + ' |'
            for n in g.CATS]
    rp = os.path.join(seed, 'README.md'); s = open(rp).read().replace('## Protocol', '## Business functions\n\nThe product team also '
         'wants these 4 functions in the engine (each has 2 example tests; category = function name). Their exact behaviour is the '
         'company\'s policy: the product owner decides it, and SQLite cannot tell you.\n\n| Function | Spec from the product team |\n'
         '| --- | --- |\n' + '\n'.join(rows) + '\n\n## Protocol', 1)
    open(rp, 'w').write(s)
    sh('git', 'add', '-A', cwd=seed); sh('git', '-c', 'user.name=referee', '-c', 'user.email=referee@local', 'commit', '-q', '-m', 'Business functions: spec and examples', cwd=seed)
    tot = subprocess.run([sys.executable, 'run_tests.py', 'tests/visible', '--summary'], cwd=seed, capture_output=True, text=True).stdout.strip().splitlines()[-1:]
    say(f'seed: {tot}')
    asks = os.path.join(RUN, 'ask_texts.md'); open(asks, 'w').write(''.join(f'## {arm}\n{ask_text(arm, PORTS[a.run][arm])}\n\n' for arm in SIZE))
    servers = [subprocess.Popen([sys.executable, os.path.join(HERE, 'owner_server.py'), '--port', str(PORTS[a.run][arm]), '--policy',
                                 os.path.join(RUN, 'pre.json'), '--log', os.path.join(RUN, f'owner_{arm}.jsonl'), '--min-seconds', str(PACE)],
                                stdout=subprocess.DEVNULL, stderr=open(os.path.join(RUN, f'owner_{arm}.err'), 'w')) for arm in SIZE]
    time.sleep(2)
    meta = {}
    try:
        for arm in ORDER[a.run]:
            if arm == 'A1':
                print(sh(sys.executable, os.path.join(ROOT, 'lab', 'make_swarm.py'), '--run', name, '--seed', seed, '--prompt',
                         os.path.join(P, 'prompt_mixed.md'), '--ask-texts', asks, '--arm', f'{arm}:{SIZE[arm]}'), end='')
            else:   # 6 engine builders and, as w7, the business builder
                biz = f'{arm}-w{SIZE[arm]}'
                tpl = os.path.join(RUN, 'prompt_engine_filled.md')
                open(tpl, 'w').write(open(os.path.join(P, 'prompt_engine.md')).read().replace('{BIZ}', biz))
                print(sh(sys.executable, os.path.join(ROOT, 'lab', 'make_swarm.py'), '--run', name, '--seed', seed, '--prompt', tpl,
                         '--arm', f'{arm}:{SIZE[arm]}'), end='')
                work = os.path.join(RUN, 'work', biz)
                open(os.path.join(RUN, f'p_{biz}.md'), 'w').write(open(os.path.join(P, 'prompt_business.md')).read()
                    .replace('{ME}', biz).replace('{N}', str(SIZE[arm])).replace('{WORK}', work)
                    .replace('{LOG}', os.path.join(RUN, 'logs', f'{biz}.log')).replace('{ASK}', ask_text(arm, PORTS[a.run][arm])))
            t0 = time.time(); say(f'launching {arm} alone ({SIZE[arm]} builder(s))')
            subprocess.run([sys.executable, os.path.join(ROOT, 'lab', 'launch.py'), '--run', name, '--arm', arm], cwd=ROOT, check=True)
            meta[arm] = dict(team_start=int(t0), team_end=int(time.time()))
            json.dump(meta, open(os.path.join(RUN, 'meta.json'), 'w'), indent=1)
    finally:
        for p in servers: p.terminate()
    hidden = os.path.join(ROOT, 'private', 'g43', 'hidden2'); out = {}
    for arm in ORDER[a.run]:
        final = os.path.join(RUN, f'final_{arm}'); sh('git', 'clone', '-q', os.path.join(RUN, f'up{arm}.git'), final)
        res = {}
        for suite, d in (('visible', os.path.join(final, 'tests', 'visible')), ('hidden', hidden)):
            j = os.path.join(RUN, f'{suite}_{arm}.json')
            subprocess.run([sys.executable, 'run_tests.py', d, '--json', j], cwd=final, capture_output=True, timeout=3600)
            res[suite] = json.load(open(j)) if os.path.exists(j) else {}
        pr = os.path.join(RUN, f'probe_{arm}.json')
        subprocess.run([sys.executable, os.path.join(ROOT, 'lab', 'intent.py'), 'probe', oracle, final, pr, str(hseed)], cwd='/', capture_output=True)
        say(f'{arm}: visible {sum(res["visible"].values())}/{len(res["visible"])}, engine hidden {sum(res["hidden"].values())}/{len(res["hidden"])}; replaying')
        out[arm] = dict(meta[arm], builders=SIZE[arm], visible=res['visible'], hidden=res['hidden'], progress=run46.replay(arm, final))
    json.dump(out, open(os.path.join(RUN, 'teams.json'), 'w'))
    say(f'done: python3 gates/gate75/referee/analyze.py runs/g75a runs/g75b')

if __name__ == '__main__':
    main()
