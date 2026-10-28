#!/usr/bin/env python3
"""Run a whole intent experiment from one config file: rules -> tests -> product owners -> swarms -> scores.

usage: run_gate.py lab/experiments/<card>.json [--oracle FILE] [--skip-prereg-check] [--max-parallel N] [--replay]

Stages (each prints what it did):
  1. Preregistration check: the config's "predictions" file must already be committed and pushed to origin/main.
  2. Rules: a fresh independent rule-giver (headless Claude Code, given only the neutral brief) writes
     private/<name>/oracle.py. Pass --oracle to reuse an existing oracle instead (for tests only).
  3. Mechanical check of the rules (they run, types are right, repeated runs agree). Never edit them.
  4. Tests and starting repo (lab/new_intent_gate.py); hidden suite goes to private/<name>/hidden.
  5. Random allowance per function, if the config has one (seeded, fixed in the config before the rules exist).
  6. Product-owner servers for every arm that can ask; swarms (lab/make_swarm.py); workers (lab/launch.py).
     With a "stratified" block, the baseline arm runs and is scored first; functions are then paired by its edge
     errors, a seeded coin picks the 'hi' function of each pair, and each stratified arm's plan sets hi/lo questions.
  7. Scoring: every arm's final engine, call by call; 95% intervals bootstrapped over functions; paired differences
     against the baseline arm; gain by allowance level. Writes runs/<name>/summary.json and summary.md.
Afterwards (by the session, not this script): write gates/gate<k>/RESULTS.md from summary.md, update BRAIN.md and
lab/QUEUE.md, and push. Private rules stay out of the repo until the run is scored."""
import argparse, collections, json, os, random, re, shutil, signal, socket, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lab'))
import intent

def sh(*args, cwd=ROOT, check=True):
    r = subprocess.run(list(args), cwd=cwd, capture_output=True, text=True)
    if check and r.returncode: sys.exit(f'failed: {" ".join(args)}\n{r.stdout}\n{r.stderr}')
    return r.stdout

def say(msg): print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)

def prereg_check(path):
    sh('git', 'fetch', '-q', 'origin', check=False)
    if not sh('git', 'ls-tree', 'origin/main', '--', path, check=False).strip():
        sys.exit(f'preregistration: {path} is not on origin/main. Commit and push the predictions before launching.')
    if sh('git', 'diff', 'origin/main', '--', path, check=False).strip():
        sys.exit(f'preregistration: {path} differs from origin/main. Push the final predictions first.')
    say(f'predictions registered on origin/main: {path}')

def get_rules(cfg, name, oracle_arg):
    d = os.path.join(ROOT, 'private', name); os.makedirs(d, exist_ok=True)
    dest = os.path.join(d, 'oracle.py')
    if oracle_arg:
        shutil.copy(oracle_arg, dest); say(f'reusing oracle {oracle_arg} (test mode)'); return dest
    brief = open(os.path.join(ROOT, cfg['rulegiver_brief'])).read().replace('{DIR}', d)
    cmd = os.environ.get('HIVE_WORKER_CMD', 'claude -p --output-format json --permission-mode acceptEdits --allowedTools Bash Read Edit Write Glob Grep').split()
    say('rule-giver writing private rules (headless Claude Code)...')
    with open(os.path.join(d, 'rulegiver.json'), 'w') as out:
        pr = subprocess.run(cmd, cwd=d, input=brief, stdout=out, stderr=subprocess.STDOUT, text=True)
    if pr.returncode or not os.path.exists(dest): sys.exit(f'rule-giver failed; see {d}/rulegiver.json')
    return dest

def check_rules(path):
    o = intent.load_oracle(path)
    names = list(o.SCALARS) + ([o.AGGREGATE[0]] if getattr(o, 'AGGREGATE', None) else [])
    assert set(o.SPEC) == set(names), 'SPEC does not match the functions'
    runs = []
    for _ in range(2):
        out = []
        for f, (fn, k) in o.SCALARS.items():
            for args in o.TYPICAL[f] + o.EDGE[f]:
                assert len(args) == k and all(a is None or type(a) in (int, float, str) for a in args), (f, args)
                out.append(o.connect().execute(f'SELECT {f}(' + ', '.join(intent.L(a) for a in args) + ')').fetchone()[0])
        if getattr(o, 'AGGREGATE', None):
            for vals in o.AGG_TYPICAL + o.AGG_EDGE:
                c = o.connect(); c.execute('CREATE TABLE m (id INTEGER, v)')
                for i, v in enumerate(vals): c.execute('INSERT INTO m VALUES (?, ?)', (i, v))
                out.append(c.execute(f'SELECT {o.AGGREGATE[0]}(v) FROM m').fetchone()[0])
        runs.append(out)
    assert runs[0] == runs[1], 'rules are not deterministic'
    assert all(v is None or type(v) in (int, float, str) for v in runs[0]), 'bad output type'
    say(f'rules checked: {len(names)} functions, {len(runs[0])} calls, deterministic')
    return o, sorted(names)

def wait_port(port):
    for _ in range(50):
        with socket.socket() as s:
            if s.connect_ex(('127.0.0.1', port)) == 0: return
        time.sleep(0.2)
    sys.exit(f'product-owner server on port {port} did not start')

def boot(vals, rng, n=4000):
    b = sorted(sum(rng.choice(vals) for _ in vals) / len(vals) for _ in range(n)); return b[int(.025 * n)], b[int(.975 * n) - 1]

def probe(cfg, oracle_path, run, arm):
    final = os.path.join(run, f'final_{arm}'); shutil.rmtree(final, ignore_errors=True)
    sh('git', 'clone', '-q', os.path.join(run, f'up{arm}.git'), final)
    out = os.path.join(run, f'probe_{arm}.json')
    sh(sys.executable, os.path.join(ROOT, 'lab', 'intent.py'), 'probe', oracle_path, final, out, str(cfg['hidden_seed']), cwd='/')
    return json.load(open(out))

def edge_errors(rows):
    err = collections.Counter()
    for r in rows:
        if r['kind'] == 'edge': err[r['cat']] += not r['ok']
    return err

def pair_allowance(st, names, err):
    """Sort functions by the base arm's edge errors, pair neighbours, and flip a seeded coin per pair for which one is 'hi'.
    Every stratified arm gives st['plans'][arm]['hi'] questions to the hi function of each pair and ['lo'] to the other."""
    order = sorted(names, key=lambda f: (err[f], f)); rng = random.Random(st['seed'])
    assert len(order) % 2 == 0, 'stratified pairing needs an even number of functions'
    pairs = []
    for i in range(0, len(order), 2):
        a, b = order[i], order[i + 1]
        pairs.append((a, b) if rng.random() < .5 else (b, a))      # (hi, lo)
    alw = {arm: {f: plan[k] for hi, lo in pairs for f, k in ((hi, 'hi'), (lo, 'lo'))} for arm, plan in st['plans'].items()}
    return pairs, alw

def score(cfg, name, oracle_path, arms, run, allowance):
    say('scoring every arm call by call...')
    o = intent.load_oracle(oracle_path); cats = intent.Gen(o).CATS
    res = {}
    ex_path = os.path.join(run, 'hidden_exclude.json'); exclude = set(json.load(open(ex_path))) if os.path.exists(ex_path) else set()
    for arm in arms:
        rows = probe(cfg, oracle_path, run, arm)
        if exclude:
            rows = [r for r in rows if r['q'] not in exclude]
            json.dump(rows, open(os.path.join(run, f'probe_{arm}.json'), 'w'), default=str)
        tests = collections.defaultdict(lambda: collections.defaultdict(list)); edge = collections.defaultdict(list)
        for r in rows:
            tests[r['cat']][r['test']].append(r['ok'])
            if r['kind'] == 'edge': edge[r['cat']].append(r['ok'])
        res[arm] = dict(tests={c: [all(v) for v in tests[c].values()] for c in cats},
                        edge={c: (sum(edge[c]) / len(edge[c]) if edge[c] else None) for c in cats},
                        right={c: sum(edge[c]) for c in cats}, wrong={c: len(edge[c]) - sum(edge[c]) for c in cats})
    rng = random.Random(7); summary = dict(name=name, arms={}, diffs={}, allowance={})
    for arm in arms:
        T = res[arm]['tests']; n = sum(len(v) for v in T.values()); p = sum(sum(v) for v in T.values()) / n
        lo, hi = boot([sum(T[c]) / len(T[c]) for c in cats], rng)
        summary['arms'][arm] = dict(hidden_pass=round(p, 4), ci95_by_function=[round(lo, 4), round(hi, 4)], tests=n)
    base = cfg.get('baseline')
    for arm in arms:
        if not base or arm == base: continue
        d = [sum(res[arm]['tests'][c]) / len(res[arm]['tests'][c]) - sum(res[base]['tests'][c]) / len(res[base]['tests'][c]) for c in cats]
        lo, hi = boot(d, rng)
        summary['diffs'][f'{arm}-{base}'] = dict(points=round(100 * sum(d) / len(d), 1), ci95=[round(100 * lo, 1), round(100 * hi, 1)])
    for arm, alw in allowance.items():
        g = collections.defaultdict(list)
        for c in cats:
            if res[arm]['edge'][c] is not None and res[base]['edge'][c] is not None:
                g[alw[c]].append(res[arm]['edge'][c] - res[base]['edge'][c])
        summary['allowance'][arm] = {str(k): dict(mean_gain_points=round(100 * sum(v) / len(v), 1),
                                                  ci95=[round(100 * x, 1) for x in boot(v, rng)], functions=len(v)) for k, v in sorted(g.items())}
    st = cfg.get('stratified')
    if st:
        # errors fixed = edge calls right minus the base arm's, per function; ratio of two arms bootstrapped over pairs
        pairs = json.load(open(os.path.join(run, 'pairs.json')))
        fixed = {arm: {c: res[arm]['right'][c] - res[base]['right'][c] for c in cats} for arm in st['plans']}
        summary['stratified'] = dict(pairs=pairs, arms={})
        for arm in st['plans']:
            lv = collections.defaultdict(lambda: [0, 0])
            for c in cats:
                lv[allowance[arm][c]][0] += fixed[arm][c]; lv[allowance[arm][c]][1] += res[base]['wrong'][c]
            summary['stratified']['arms'][arm] = dict(errors_fixed=sum(fixed[arm].values()), base_errors=sum(res[base]['wrong'].values()),
                share_fixed_by_questions={str(q): dict(fixed=f, base_errors=e, share=round(f / e, 3) if e else None) for q, (f, e) in sorted(lv.items())})
        num, den = st['ratio']
        def ratio(ps):
            d = sum(fixed[den][c] for p in ps for c in p); return sum(fixed[num][c] for p in ps for c in p) / d if d else float('inf')
        bs = sorted(ratio([rng.choice(pairs) for _ in pairs]) for _ in range(4000))
        summary['stratified']['ratio'] = dict(arms=f'{num}/{den}', value=round(ratio(pairs), 3), ci95=[round(bs[100], 3), round(bs[3899], 3)])
    json.dump(summary, open(os.path.join(run, 'summary.json'), 'w'), indent=1)
    md = [f'# {name}: summary', '', '| Arm | Hidden pass | 95% CI by function |', '| --- | --- | --- |']
    md += [f"| {a} | {v['hidden_pass']:.1%} | {v['ci95_by_function'][0]:.1%}–{v['ci95_by_function'][1]:.1%} |" for a, v in summary['arms'].items()]
    if summary['diffs']:
        md += ['', '| Paired difference | Points | 95% CI |', '| --- | --- | --- |']
        md += [f"| {k} | {v['points']:+.1f} | {v['ci95'][0]:+.1f} to {v['ci95'][1]:+.1f} |" for k, v in summary['diffs'].items()]
    for arm, levels in summary['allowance'].items():
        md += ['', f'Gain in edge-call accuracy over {base}, by allowance ({arm}):', '', '| Questions allowed | Mean gain | 95% CI | Functions |', '| --- | --- | --- | --- |']
        md += [f"| {k} | {v['mean_gain_points']:+.1f} | {v['ci95'][0]:+.1f} to {v['ci95'][1]:+.1f} | {v['functions']} |" for k, v in levels.items()]
    if st:
        s = summary['stratified']
        md += ['', f'Edge errors fixed over {base} (pairs matched on {base} edge errors):', '',
               '| Arm | Errors fixed | Share fixed at 0 / 1 / 2 / 3 questions |', '| --- | --- | --- |']
        for arm, v in s['arms'].items():
            lv = v['share_fixed_by_questions']
            md.append(f"| {arm} | {v['errors_fixed']} of {v['base_errors']} | " +
                      ' / '.join(f"{lv[q]['share']:.2f}" if q in lv and lv[q]['share'] is not None else '–' for q in '0123') + ' |')
        r = s['ratio']; md += ['', f"Ratio {r['arms']}: **{r['value']:.2f}** (95% CI {r['ci95'][0]:.2f} to {r['ci95'][1]:.2f}, bootstrap over pairs)"]
    open(os.path.join(run, 'summary.md'), 'w').write('\n'.join(md) + '\n')
    print('\n'.join(md))

def tour_kinds(cfg):
    t = cfg.get('tour_arms', {})
    return {a: 'tour' for a in t} if isinstance(t, list) else dict(t)

def build_tour(o, names, run, contrast=False):
    """runs/<name>/seed_tour: the starting repo plus the owner's decision tour as visible tests (one example per declared
    decision, at most 3 calls per test). Tour inputs must not be TYPICAL or EDGE inputs, so no hidden test is copied.
    contrast=True (runs/<name>/seed_tourc) also adds CONTRAST_EXAMPLES: per decision, a nearby input it does not cover."""
    dec = o.DECISIONS
    sets = [('tour', o.DECISION_EXAMPLES)] + ([('contrast', o.CONTRAST_EXAMPLES)] if contrast else [])
    g = intent.Gen(o); out = os.path.join(run, 'seed_tourc' if contrast else 'seed_tour'); shutil.rmtree(out, ignore_errors=True)
    sh('git', 'clone', '-q', os.path.join(run, 'seed'), out); vis = os.path.join(out, 'tests', 'visible'); n = 0
    seen = {f: {tuple(a) for a in o.TYPICAL[f] + o.EDGE[f]} for f in o.SCALARS}
    for label, ex in sets:
        assert set(ex) == set(names), f'{label} examples must list every function'
        for f in names:
            assert len(ex[f]) == len(dec[f]), f'{f}: one {label} example per decision'
            if f == g.AGG:
                for k, vals in enumerate(ex[f]):
                    assert list(vals) not in [list(v) for v in o.AGG_TYPICAL + o.AGG_EDGE], f'{f}: {label} input is a test input'
                    setup = ['CREATE TABLE m (id INTEGER, v)'] + (['INSERT INTO m VALUES ' + ', '.join(f'({i}, {intent.L(v)})' for i, v in enumerate(vals, 1))] if vals else [])
                    q = f'SELECT {f.upper()}(v) FROM m'
                    t = dict(id=f'{f}_{label}_{k}', category=f, setup=setup, query=q, expected=intent.oracle_rows(o, setup, q), ordered=True)
                    json.dump(t, open(os.path.join(vis, t['id'] + '.json'), 'w')); n += 1
                continue
            for args in ex[f]:
                assert tuple(args) not in seen[f], f'{f}: {label} input {args} is a TYPICAL, EDGE or earlier tour input'
            seen[f] |= {tuple(a) for a in ex[f]}
            for k in range(0, len(ex[f]), 3):
                q = 'SELECT ' + ', '.join(g.call(f, a) for a in ex[f][k:k + 3])
                t = dict(id=f'{f}_{label}_{k // 3}', category=f, setup=[], query=q, expected=intent.oracle_rows(o, [], q), ordered=True)
                json.dump(t, open(os.path.join(vis, t['id'] + '.json'), 'w')); n += 1
    sh('git', 'add', '-A', cwd=out)
    sh('git', '-c', 'user.name=hive', '-c', 'user.email=hive@local', 'commit', '-q', '-m',
       "Product owner's decision tour: one worked example per policy decision (tests/visible/*_tour_*.json)"
       + (', each with a contrast example it does not cover (*_contrast_*.json)' if contrast else ''), cwd=out)
    say(f'decision tour built ({"with" if contrast else "without"} contrasts): {sum(len(v) for _, ex in sets for v in ex.values())} examples in {n} visible tests')
    return out

def worker_cmd():
    return os.environ.get('HIVE_WORKER_CMD', 'claude -p --output-format json --permission-mode acceptEdits --allowedTools Bash Read Edit Write Glob Grep').split()

def build_handbook(o, run, base='seed', out_name='seed_hb'):
    """runs/<name>/<out_name>: the <base> starting repo plus the owner's prose handbook (HANDBOOK.md), linked from README."""
    out = os.path.join(run, out_name); shutil.rmtree(out, ignore_errors=True)
    sh('git', 'clone', '-q', os.path.join(run, base), out)
    open(os.path.join(out, 'HANDBOOK.md'), 'w').write(o.HANDBOOK.strip() + '\n')
    rp = os.path.join(out, 'README.md')
    open(rp, 'a').write("\n## Company policy handbook\n\nThe product team's policy handbook for these functions is in `HANDBOOK.md`.\n")
    sh('git', 'add', '-A', cwd=out)
    sh('git', '-c', 'user.name=hive', '-c', 'user.email=hive@local', 'commit', '-q', '-m', "Company policy handbook (HANDBOOK.md)", cwd=out)
    say('handbook seed built'); return out

def build_xtour(cfg, o, names, run, name):
    """An extractor agent sees only the handbook and the one-line spec, and picks inputs (one per decision it finds or
    suspects, at most 50). The owner (oracle) answers them; the answers become a tour in runs/<name>/seed_xtour.
    Inputs equal to a TYPICAL or EDGE input are dropped (logged), so no hidden test is copied."""
    d = os.path.join(ROOT, 'private', name, 'extractor'); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    open(os.path.join(d, 'handbook.md'), 'w').write(o.HANDBOOK.strip() + '\n')
    open(os.path.join(d, 'spec.md'), 'w').write('\n'.join(
        f'- `{o.SPEC[f].split(":", 1)[0].strip()}`: {o.SPEC[f].split(":", 1)[1].strip()}'
        + (' (an aggregate over one column)' if f == o.AGGREGATE[0] else '') for f in names) + '\n')
    brief = open(os.path.join(ROOT, cfg['extractor_brief'])).read().replace('{DIR}', d)
    say('extractor reading the handbook (headless Claude Code)...')
    with open(os.path.join(d, 'extractor.json'), 'w') as out:
        subprocess.run(worker_cmd(), cwd=d, input=brief, stdout=out, stderr=subprocess.STDOUT, text=True)
    path = os.path.join(d, 'tour_inputs.json')
    if not os.path.exists(path): sys.exit(f'extractor wrote no tour_inputs.json; see {d}/extractor.json')
    raw = json.load(open(path)); g = intent.Gen(o); picked, dropped, overlap = {}, [], []
    fair = cfg.get('copy_rule') == 'exclude_from_hidden'   # keep picks that equal hidden inputs; drop those calls from scoring
    total = 0
    for f in names:
        for args in raw.get(f, []):
            if total >= 50: break
            vals = list(args) if isinstance(args, list) else [args]
            if f == g.AGG:
                if vals in [list(v) for v in o.AGG_TYPICAL + o.AGG_EDGE]: dropped.append((f, vals)); continue
            else:
                if len(vals) != o.SCALARS[f][1] or any(v is not None and type(v) not in (int, float, str) for v in vals): dropped.append((f, vals)); continue
                if tuple(vals) in {tuple(a) for a in o.TYPICAL[f] + o.EDGE[f]}:
                    if not fair: dropped.append((f, vals)); continue
                    overlap.append('SELECT ' + g.call(f, vals))
            picked.setdefault(f, []).append(vals if f == g.AGG else tuple(vals)); total += 1
    json.dump(dict(picked={f: [list(a) for a in v] for f, v in picked.items()}, dropped=dropped, overlap=overlap), open(os.path.join(run, 'xtour_inputs.json'), 'w'), indent=1)
    if fair: json.dump(sorted(set(overlap)), open(os.path.join(run, 'hidden_exclude.json'), 'w'), indent=1)
    out = os.path.join(run, 'seed_xtour'); shutil.rmtree(out, ignore_errors=True)
    sh('git', 'clone', '-q', os.path.join(run, 'seed'), out); vis = os.path.join(out, 'tests', 'visible'); n = 0
    for f, ex in picked.items():
        if f == g.AGG:
            for k, vals in enumerate(ex):
                setup = ['CREATE TABLE m (id INTEGER, v)'] + (['INSERT INTO m VALUES ' + ', '.join(f'({i}, {intent.L(v)})' for i, v in enumerate(vals, 1))] if vals else [])
                q = f'SELECT {f.upper()}(v) FROM m'
                try: exp = intent.oracle_rows(o, setup, q)
                except Exception: continue
                json.dump(dict(id=f'{f}_tour_{k}', category=f, setup=setup, query=q, expected=exp, ordered=True), open(os.path.join(vis, f'{f}_tour_{k}.json'), 'w')); n += 1
            continue
        ok = []
        for a in ex:
            try: intent.oracle_rows(o, [], 'SELECT ' + g.call(f, a)); ok.append(a)
            except Exception: dropped.append((f, list(a)))
        for k in range(0, len(ok), 3):
            q = 'SELECT ' + ', '.join(g.call(f, a) for a in ok[k:k + 3])
            json.dump(dict(id=f'{f}_tour_{k // 3}', category=f, setup=[], query=q, expected=intent.oracle_rows(o, [], q), ordered=True), open(os.path.join(vis, f'{f}_tour_{k // 3}.json'), 'w')); n += 1
    sh('git', 'add', '-A', cwd=out)
    sh('git', '-c', 'user.name=hive', '-c', 'user.email=hive@local', 'commit', '-q', '-m',
       "Product owner's worked examples (tests/visible/*_tour_*.json), answered at inputs picked from the handbook", cwd=out)
    say(f'extracted tour built: {total} inputs picked, {len(dropped)} dropped, {len(overlap)} equal hidden inputs'
        + (' (kept; those calls are removed from scoring for every team)' if fair else '') + f', {n} visible tests')
    return out

def run_arms(cfg, name, run, oracle_path, specs, max_parallel):
    """Product-owner servers, swarms and workers for the given arms only; waits until every worker exits.
    Arms listed in cfg['tour_arms'] start from runs/<name>/seed_tour instead of runs/<name>/seed."""
    servers = []
    for spec in specs:
        p = spec.split(':'); arm = p[0]
        if len(p) > 2 and p[2] in ('budget', 'quota'):
            port = int(p[3]); args = [sys.executable, os.path.join(ROOT, 'lab', 'ask_server.py'), '--oracle', oracle_path, '--port', str(port),
                                      '--log', os.path.join(run, f'asks_{arm}.log')]
            args += ['--budget', p[4]] if p[2] == 'budget' else ['--allowance', os.path.join(run, f'allowance_{arm}.json')]
            servers.append(subprocess.Popen(args, cwd='/', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)); wait_port(port)
    try:
        kinds = tour_kinds(cfg); where = {'tour': 'seed_tour', 'contrast': 'seed_tourc', 'handbook': 'seed_hb', 'xtour': 'seed_xtour',
                                          'xtour+handbook': 'seed_xtour_hb', 'tour+handbook': 'seed_tour_hb'}
        for seed_dir in ('seed', 'seed_tour', 'seed_tourc', 'seed_hb', 'seed_xtour', 'seed_xtour_hb', 'seed_tour_hb'):
            group = [s for s in specs if where.get(kinds.get(s.split(':')[0]), 'seed') == seed_dir]
            if not group: continue
            cmd = [sys.executable, os.path.join(ROOT, 'lab', 'make_swarm.py'), '--run', name, '--seed', os.path.join(run, seed_dir),
                   '--prompt', os.path.join(ROOT, cfg['prompt']), '--ask-texts', os.path.join(ROOT, cfg['ask_texts']),
                   '--example-file', os.path.join(run, 'example.txt')]
            for spec in group:
                p = spec.split(':'); cmd += ['--arm', spec if not (len(p) > 2 and p[2] == 'quota') else ':'.join(p[:4])]
            print(sh(*cmd), end='')
        say('launching workers...')
        launch = [sys.executable, os.path.join(ROOT, 'lab', 'launch.py'), '--run', name]
        for spec in specs: launch += ['--arm', spec.split(':')[0]]
        if max_parallel: launch += ['--max-parallel', str(max_parallel)]
        subprocess.run(launch, cwd=ROOT, check=True)
    finally:
        for s in servers: s.send_signal(signal.SIGTERM)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('config'); ap.add_argument('--oracle'); ap.add_argument('--skip-prereg-check', action='store_true')
    ap.add_argument('--max-parallel', type=int, default=0); ap.add_argument('--replay', action='store_true')
    a = ap.parse_args()
    cfg = json.load(open(a.config)); name = cfg['name']; run = os.path.join(ROOT, 'runs', name)
    if not a.skip_prereg_check: prereg_check(cfg['predictions'])
    oracle_path = get_rules(cfg, name, a.oracle)
    o, names = check_rules(oracle_path)
    if cfg.get('require_decisions'):
        dec = getattr(o, 'DECISIONS', None)
        assert isinstance(dec, dict) and set(dec) == set(names), 'DECISIONS must list every function'
        counts = collections.Counter(len(v) for v in dec.values())
        assert all(1 <= len(v) <= 4 for v in dec.values()), 'each function needs 1 to 4 decisions'
        say('declared decisions per function: ' + ', '.join(f'{k}:{counts[k]}' for k in sorted(counts)))
    sh(sys.executable, os.path.join(ROOT, 'lab', 'new_intent_gate.py'), '--name', name, '--oracle', oracle_path,
       '--visible-seed', str(cfg['visible_seed']), '--hidden-seed', str(cfg['hidden_seed']), cwd='/')
    say('starting repo and hidden suite built')
    if cfg.get('guard'):   # install another tools/land.py (e.g. Gate 23's cached guard) in the starting repo; tour repos clone it
        seed = os.path.join(run, 'seed'); shutil.copy(os.path.join(ROOT, cfg['guard']), os.path.join(seed, 'tools', 'land.py'))
        sh('git', '-c', 'user.name=hive', '-c', 'user.email=hive@local', 'commit', '-q', '-am', f'tools/land.py from {cfg["guard"]}', cwd=seed)
        say(f'guard installed: {cfg["guard"]}')
    kinds = set(tour_kinds(cfg).values())
    for kind in sorted(kinds):
        if kind in ('tour', 'contrast') or (kind == 'tour+handbook' and 'tour' not in kinds): build_tour(o, names, run, contrast=(kind == 'contrast'))
        elif kind == 'handbook': build_handbook(o, run)
    if kinds & {'xtour', 'xtour+handbook'}: build_xtour(cfg, o, names, run, name)
    if 'xtour+handbook' in kinds: build_handbook(o, run, base='seed_xtour', out_name='seed_xtour_hb')
    if 'tour+handbook' in kinds: build_handbook(o, run, base='seed_tour', out_name='seed_tour_hb')
    for cmd in cfg.get('pre_launch', []):   # gate-specific steps after the seeds exist and before any builder starts
        say(f'pre-launch: {cmd}')         # (Gate 39: Hive's interview with a synthetic owner writes the ask texts)
        r = subprocess.run(cmd.format(root=ROOT, run=run, name=name, oracle=oracle_path), shell=True, cwd=ROOT)
        if r.returncode: sys.exit(f'pre-launch step failed: {cmd}')
    allowance = {}
    for arm, spec in cfg.get('allowance', {}).items():
        order = sorted(names); random.Random(spec['seed']).shuffle(order); alw = {}
        for level, count in spec['counts'].items():
            for _ in range(count): alw[order.pop(0)] = int(level)
        assert not order, 'allowance counts must cover every function'
        json.dump(alw, open(os.path.join(run, f'allowance_{arm}.json'), 'w'), indent=1); allowance[arm] = alw
        say(f'allowance for {arm}: ' + ', '.join(f'{k}:{sum(1 for v in alw.values() if v == int(k))}' for k in spec['counts']))
    st = cfg.get('stratified')
    if st:
        # stage 1: the base arm alone, scored, so allowances can be matched on what it got wrong
        base_specs = [s for s in cfg['arms'] if s.split(':')[0] == cfg['baseline']]
        say(f'stage 1: {cfg["baseline"]} alone')
        run_arms(cfg, name, run, oracle_path, base_specs, a.max_parallel)
        err = edge_errors(probe(cfg, oracle_path, run, cfg['baseline']))
        pairs, alw = pair_allowance(st, names, err)
        json.dump([list(p) for p in pairs], open(os.path.join(run, 'pairs.json'), 'w'), indent=1)
        for arm, al in alw.items():
            json.dump(al, open(os.path.join(run, f'allowance_{arm}.json'), 'w'), indent=1); allowance[arm] = al
            say(f'allowance for {arm} (stratified, {len(pairs)} pairs): ' + ', '.join(f'{q}:{sum(1 for v in al.values() if v == q)}' for q in sorted(set(al.values()))))
        say(f'stage 2: ' + ', '.join(s.split(':')[0] for s in cfg['arms'] if s not in base_specs))
        run_arms(cfg, name, run, oracle_path, [s for s in cfg['arms'] if s not in base_specs], a.max_parallel)
    elif cfg.get('after_baseline'):
        # stage 1: the base arm alone; then gate-specific steps that read its code (Gate 42: a rule sheet written from
        # the built code, corrected by the owner); then every other arm
        base_specs = [s for s in cfg['arms'] if s.split(':')[0] == cfg['baseline']]
        say(f'stage 1: {cfg["baseline"]} alone')
        run_arms(cfg, name, run, oracle_path, base_specs, a.max_parallel)
        final = os.path.join(run, f'final_{cfg["baseline"]}'); shutil.rmtree(final, ignore_errors=True)
        sh('git', 'clone', '-q', os.path.join(run, f'up{cfg["baseline"]}.git'), final)
        for cmd in cfg['after_baseline']:
            say(f'after {cfg["baseline"]}: {cmd}')
            r = subprocess.run(cmd.format(root=ROOT, run=run, name=name, oracle=oracle_path, base=final), shell=True, cwd=ROOT)
            if r.returncode: sys.exit(f'after-baseline step failed: {cmd}')
        say('stage 2: ' + ', '.join(s.split(':')[0] for s in cfg['arms'] if s not in base_specs))
        run_arms(cfg, name, run, oracle_path, [s for s in cfg['arms'] if s not in base_specs], a.max_parallel)
    else:
        run_arms(cfg, name, run, oracle_path, cfg['arms'], a.max_parallel)
    score(cfg, name, oracle_path, [s.split(':')[0] for s in cfg['arms']], run, allowance)
    if a.replay:
        for spec in cfg['arms']:
            arm = spec.split(':')[0]
            sh(sys.executable, os.path.join(ROOT, 'gates', 'gate2', 'referee', 'evaluate.py'), os.path.join(run, f'up{arm}.git'),
               os.path.join(ROOT, 'private', name, 'hidden'), os.path.join(run, f'eval_{arm}.json'), cwd='/')
        say('per-commit replays written')
    say(f'done. Next: write the gate RESULTS.md from runs/{name}/summary.md, update BRAIN.md and lab/QUEUE.md, push.')

if __name__ == '__main__':
    main()
