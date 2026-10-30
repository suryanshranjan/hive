#!/usr/bin/env python3
"""Gate 61: the flight log. Do the outcomes an owner confirmed, kept as tests, survive the next build?

usage: run61.py   (from the repo root; writes runs/g61/ and private/g61/)

1. Build 1: Gate 55's CC build (its owner reviewed every rule carefully; 100% of Gate 55's hidden suite), probed on a new
   hidden suite (seed 61200000).
2. The flight log: Gate 58's spotter (with setup for the aggregate, prompts/spotter_brief.md) writes concrete cases from
   build 1. The cases whose outcome is the policy's (the referee's stand-in for a careful owner confirming them) become
   tests in tests/visible/ (ids <function>_fNN), where the landing guard keeps them passing.
3. Build 2, the week after: clean up the ten functions into one module without changing what they do, and add
   invoice_total (prompts/prompt_refactor.md). Six teams of 2 builders: N1-N3 without the log, T1-T3 with it.
4. Scores: each team's hidden pass on the old functions, calls build 1 had right that build 2 breaks, invoice_total on
   60 calls, and whether the clean-up was done. analyze.py applies the registered rules."""
import json, os, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'lab')); sys.path.insert(0, os.path.join(ROOT, 'gates', 'gate41', 'referee'))
import intent, run_gate
import wind_tunnel as wt

NAME = 'g61'; HIDDEN = 61200000
RUN = os.path.join(ROOT, 'runs', NAME); PRIV = os.path.join(ROOT, 'private', NAME)
P = os.path.join(ROOT, 'gates', 'gate61', 'prompts')
ORACLE = os.path.join(ROOT, 'gates', 'gate55', 'referee', 'oracle.py')
BUILD1 = os.path.join(ROOT, 'runs', 'g55', 'upCC.git')
TEAMS = ['N1', 'T1', 'T2', 'N2', 'N3', 'T3']   # alternating, so neither arm always starts first
say = run_gate.say

def sh(*a, cwd=None):
    return subprocess.run(list(a), cwd=cwd, check=True, capture_output=True, text=True).stdout

def invoice(o, u, q, d):
    bp = o.bulk_price(u, q)
    if bp is None:
        return None
    lf = o.late_fee(bp, d)
    return None if lf is None else bp + lf

def invoice_calls(o):
    days = [a[1] for a in o.TYPICAL['late_fee']] + [a[1] for a in o.EDGE['late_fee']]
    bulk = o.TYPICAL['bulk_price'] + o.EDGE['bulk_price']
    out = [(u, q, d) for k, d in enumerate(days) for i, (u, q) in enumerate(bulk) if (i + k) % 3 == 0]
    return out[:60]

def run_on(engine, setup, q, timeout=10):
    code = ('import json, sys; sys.path.insert(0, sys.argv[1]); import minisql\n'
            'c = minisql.connect(); [c.execute(s) for s in json.loads(sys.argv[2])]\n'
            'print(json.dumps([list(r) for r in c.execute(sys.argv[3])], default=str))')
    try:
        p = subprocess.run([sys.executable, '-c', code, engine, json.dumps(setup), q], capture_output=True, text=True,
                           timeout=timeout, cwd='/')
        return json.loads(p.stdout) if p.returncode == 0 else None
    except Exception:
        return None

def oracle_on(o, setup, q):
    try:
        return intent.oracle_rows(o, setup, q)
    except Exception:
        return None

def same_rows(a, b):
    return a is not None and b is not None and [[intent.norm(v) for v in r] for r in a] == [[intent.norm(v) for v in r] for r in b]

def probe(o, engine, out):
    sh(sys.executable, os.path.join(ROOT, 'lab', 'intent.py'), 'probe', ORACLE, engine, out, str(HIDDEN), cwd='/')
    return json.load(open(out))

def main():
    run_gate.prereg_check('gates/gate61/prompts/PREDICTIONS.md')
    o = intent.load_oracle(ORACLE)
    shutil.rmtree(RUN, ignore_errors=True); os.makedirs(RUN); os.makedirs(PRIV, exist_ok=True)
    b1 = os.path.join(RUN, 'build1'); sh('git', 'clone', '-q', BUILD1, b1)
    P1 = probe(o, b1, os.path.join(RUN, 'probe_build1.json'))
    say(f"build 1: {sum(r['ok'] for r in P1)} of {len(P1)} hidden calls right")
    # 2. the flight log
    sd = os.path.join(PRIV, 'spotter'); shutil.rmtree(sd, ignore_errors=True); os.makedirs(sd)
    shutil.copytree(b1, os.path.join(sd, 'repo'), ignore=shutil.ignore_patterns('.git'))
    spec = wt.spec_lines(o, intent.Gen(o).CATS)
    _, c = wt.agent(wt.AGENT, sd, open(os.path.join(P, 'spotter_brief.md')).read().replace('{BASE}', os.path.join(sd, 'repo'))
                    .replace('{OUT}', sd).replace('{SPEC}', spec), os.path.join(sd, 'spotter.log'))
    spots = [s for s in json.load(open(os.path.join(sd, 'spots.json'))) if isinstance(s, dict) and s.get('call')]
    log, kept, dropped = [], {}, []
    for s in spots:
        fn = str(s.get('function', '')); setup = s.get('setup') or []; q = s['call']
        got, exp = run_on(b1, setup, q), oracle_on(o, setup, q)
        if fn in intent.Gen(o).CATS and same_rows(got, exp) and got:
            kept[fn] = kept.get(fn, 0) + 1
            log.append(dict(id=f'{fn}_f{kept[fn]:02d}', category=fn, setup=setup, query=q, expected=exp, ordered=True))
        else:
            dropped.append(dict(spot=s, got=got, policy=exp))
    say(f'flight log: {len(log)} confirmed outcomes over {len(kept)} functions ({len(dropped)} cases dropped); spotter ${c:.2f}')
    # 3. the two starting repositories
    cases = invoice_calls(o)
    vis = [dict(id=f'invoice_total_{k:03d}', category='invoice_total', setup=[],
                query='SELECT ' + ', '.join(f'INVOICE_TOTAL({u}, {q}, {d})' for u, q, d in cases[3 * k:3 * k + 3]),
                expected=[[invoice(o, u, q, d) for u, q, d in cases[3 * k:3 * k + 3]]], ordered=True) for k in range(2)]
    week = ('\n## This week\n\n1. **Clean-up.** Move the ten business functions from `minisql/biz_w1.py`, `minisql/bizfuncs_w2.py` '
            'and `minisql/bizfuncs_w3.py` into one module, `minisql/business.py`, with shared helpers for reading numbers and '
            'text and for rounding money; delete the three old files. Do not change what any function does: the owner '
            'checked them last week.\n2. **New:** `invoice_total(unit_cents, qty, days_late)`: what the customer owes for an '
            'order paid late, which is the order\'s bulk price plus the late fee on that price. Examples: `tests/visible/'
            'invoice_total_*.json`.\n')
    seeds = {}
    for arm in ('N', 'T'):
        sdir = os.path.join(RUN, f'seed_{arm}'); sh('git', 'clone', '-q', BUILD1, sdir)
        sh('git', 'rm', '-q', '-r', '--ignore-unmatch', 'current_tasks', cwd=sdir)
        os.makedirs(os.path.join(sdir, 'current_tasks'), exist_ok=True); open(os.path.join(sdir, 'current_tasks', '.keep'), 'w').close()
        for t in vis + (log if arm == 'T' else []):
            json.dump(t, open(os.path.join(sdir, 'tests', 'visible', t['id'] + '.json'), 'w'))
        readme = open(os.path.join(sdir, 'README.md')).read()
        extra = week + ('\nThe outcomes the owner confirmed last week are kept as tests too (`tests/visible/<function>_fNN.json`).\n'
                        if arm == 'T' else '')
        readme = readme.replace('\n## Protocol', extra + '\n## Protocol', 1)
        open(os.path.join(sdir, 'README.md'), 'w').write(readme)
        sh('git', 'add', '-A', cwd=sdir)
        sh('git', '-c', 'user.name=hive', '-c', 'user.email=hive@local', 'commit', '-q', '-m', 'This week: clean-up and invoice_total'
           + (' (with last week\'s confirmed outcomes as tests)' if arm == 'T' else ''), cwd=sdir)
        r = subprocess.run([sys.executable, 'run_tests.py', 'tests/visible', '--summary'], cwd=sdir, capture_output=True, text=True)
        say(f'seed {arm}: ' + (r.stdout.strip().splitlines() or ['?'])[-1])
        seeds[arm] = sdir
    asks = os.path.join(RUN, 'ask_texts.md')
    open(asks, 'w').write(''.join(f'## {t}\n{wt.NO_OWNER}\n\n' for t in TEAMS))
    for arm in ('N', 'T'):
        cmd = [sys.executable, os.path.join(ROOT, 'lab', 'make_swarm.py'), '--run', NAME, '--seed', seeds[arm],
               '--prompt', os.path.join(P, 'prompt_refactor.md'), '--ask-texts', asks]
        for t in TEAMS:
            if t[0] == arm: cmd += ['--arm', f'{t}:2:none']
        print(sh(*cmd), end='')
    say('launching 12 builders (6 at a time)...')
    t0 = time.time()
    launch = [sys.executable, os.path.join(ROOT, 'lab', 'launch.py'), '--run', NAME, '--max-parallel', '6']
    for t in TEAMS: launch += ['--arm', t]
    subprocess.run(launch, cwd=ROOT, check=True)
    say(f'builds done in {(time.time() - t0) / 60:.1f} min; scoring...')
    # 4. scores
    res = dict(build1=dict(right=sum(r['ok'] for r in P1), calls=len(P1)), flight_log=dict(tests=len(log), per_function=kept,
               dropped=len(dropped)), teams={})
    for t in TEAMS:
        fin = os.path.join(RUN, f'final_{t}'); shutil.rmtree(fin, ignore_errors=True); sh('git', 'clone', '-q', os.path.join(RUN, f'up{t}.git'), fin)
        Pt = probe(o, fin, os.path.join(RUN, f'probe_{t}.json'))
        assert [r['q'] for r in Pt] == [r['q'] for r in P1], 'the probes must line up call by call'
        broke = [b['q'] for a, b in zip(P1, Pt) if a['ok'] and not b['ok']]
        inv = sum(same_rows(run_on(fin, [], f'SELECT INVOICE_TOTAL({u}, {q}, {d})'), [[invoice(o, u, q, d)]]) for u, q, d in cases)
        mods = os.listdir(os.path.join(fin, 'minisql'))
        res['teams'][t] = dict(arm=t[0], right=sum(r['ok'] for r in Pt), calls=len(Pt), broke=len(broke), broke_calls=broke[:40],
                               build1_right=sum(r['ok'] for r in P1), invoice_right=inv, invoice_calls=len(cases),
                               cleanup=('business.py' in mods) and not any(m in mods for m in ('biz_w1.py', 'bizfuncs_w2.py', 'bizfuncs_w3.py')),
                               commits=int(sh('git', 'rev-list', '--count', 'HEAD', cwd=fin).strip()))
        say(f"{t}: {res['teams'][t]['right']}/{len(Pt)} hidden right, broke {len(broke)}, invoice {inv}/{len(cases)}, "
            f"clean-up {'done' if res['teams'][t]['cleanup'] else 'not done'}")
    json.dump(res, open(os.path.join(RUN, 'results.json'), 'w'), indent=1)
    json.dump(dict(log=log, dropped=dropped), open(os.path.join(RUN, 'flight_log.json'), 'w'), indent=1, default=str)
    say('done: python3 gates/gate61/referee/analyze.py runs/g61/results.json')

if __name__ == '__main__':
    main()
