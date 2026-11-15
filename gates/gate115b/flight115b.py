"""Gate 115b (PREDICTIONS.md): Gate 115 again, without its two flaws. A strict simulated founder answers only exactly
what each question asks. A second company (CrumbHouse, cakes) has facts of kinds the prompt does not name. A third arm,
`fit`, asks only where his answer would change a step. Same flow and blind judge as Gate 115 (gates/gate115/flight115.py).
usage: python gates/gate115b/flight115b.py [--only T:G1,...] [--parallel 2]
Companies: T = TutorNest (private/g115), C = CrumbHouse (private/g115b). Results: gates/gate115b/results/runs.json."""
import argparse, concurrent.futures as cf, importlib.util, json, os, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'gates', 'gate115'))
import flight115 as F   # claude_json, JUDGE, SURFACED, show
OUT = os.path.join(HERE, 'results'); os.makedirs(OUT, exist_ok=True)
COMPANIES = {'T': os.path.join(ROOT, 'private', 'g115'), 'C': os.path.join(ROOT, 'private', 'g115b')}
ARMS = ('one', 'three', 'fit')
STRICT = ("\n\nHow you answer: you are a busy, guarded owner. Answer only exactly what each question asks, in a few words. "
          "Never bring up any other fact, even one you think is useful, unless the question is specifically about it. "
          "A general question ('anything else?', 'anything I should know?') gets: 'Nothing comes to mind.'")

def founder(brief, questions):
    q = '\n'.join(f'{k}. {x}' for k, x in enumerate(questions, 1))
    got, c = F.claude_json(f"You are this business owner:\n{brief}{STRICT}\n\nYour assistant asks you on your phone, before "
                           f"planning:\n{q}\n\nAnswer in one short phone message. Reply with JSON only: " + '{"say": "..."}')
    return str(got.get('say') or 'Nothing comes to mind.'), c

def company(cid):
    spec = importlib.util.spec_from_file_location(f'co_{cid}', os.path.join(COMPANIES[cid], 'make_company.py'))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    key = json.load(open(os.path.join(COMPANIES[cid], 'key.json'), encoding='utf-8'))
    goals = dict(key['goals']); goals.update(key.get('control', {}))
    return mod, key['brief'].replace(' You answer what you are asked; you do not volunteer things nobody asked about, but if a '
                                     'question touches one of the facts below, you say it plainly.', ''), goals

def one(cid, gid, arm):
    from hive import plan
    os.environ['HIVE_PLAN_ASK'] = arm
    mod, brief, goals = company(cid); g = goals[gid]
    work = tempfile.mkdtemp(prefix=f'g115b-{cid}{gid}-{arm}-'); repo = os.path.join(work, 'site'); mod.make(repo)
    t0, cost = time.time(), 0.0
    p = plan.make(repo, g['goal']); cost += (p or {}).get('cost', 0)
    asked = list((p or {}).get('missing') or []); said, final = '', p
    if asked:
        said, c = founder(brief, asked); cost += c
        if not said.strip().lower().startswith(('nothing', 'no.')):
            p2 = plan.make(repo, g['goal'], notes=[f"Asked: {' / '.join(asked)} He said: {said}"]); cost += (p2 or {}).get('cost', 0)
            final = p2 or p
    row = {'company': cid, 'goal': gid, 'arm': arm, 'asked': asked, 'said': said, 'first': F.show(p), 'final': F.show(final),
           'steps': len((final or {}).get('steps', [])), 'minutes': round((time.time() - t0) / 60, 1)}
    if g.get('fact') != 'none':
        j, c1 = F.claude_json(F.JUDGE.format(goal=g['goal'], fact=g['fact'], rubric=g['accounts_for'], plan=row['final']))
        s, c2 = F.claude_json(F.SURFACED.format(fact=g['fact'], said=said)) if said else ({'said_it': False}, 0)
        row.update(passes=bool(j.get('passes')), judge_why=j.get('why', ''), surfaced=bool(s.get('said_it'))); cost += c1 + c2
    row['usd'] = round(cost, 3)
    shutil.rmtree(work, ignore_errors=True)
    return row

def run_one(job):
    cid, gid, arm = job
    r = subprocess.run([sys.executable, __file__, '--child', f'{cid}:{gid}:{arm}'], capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=3600)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return {'company': cid, 'goal': gid, 'arm': arm, 'error': (r.stderr or r.stdout)[-600:]}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--only'); ap.add_argument('--child'); ap.add_argument('--parallel', type=int, default=2)
    a = ap.parse_args()
    if a.child:
        cid, gid, arm = a.child.split(':'); print(json.dumps(one(cid, gid, arm), ensure_ascii=False)); return
    jobs = [(cid, gid, arm) for cid in COMPANIES for gid in company(cid)[2] for arm in ARMS]
    if a.only:
        want = set(a.only.split(',')); jobs = [j for j in jobs if f'{j[0]}:{j[1]}' in want]
    path = os.path.join(OUT, 'runs.json')
    rows = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else []
    done = {(r['company'], r['goal'], r['arm']) for r in rows if 'error' not in r}
    jobs = [j for j in jobs if j not in done]
    print(f'{len(jobs)} runs to do', flush=True)
    with cf.ThreadPoolExecutor(a.parallel) as ex:
        for row in ex.map(run_one, jobs):
            k = (row['company'], row['goal'], row['arm'])
            rows = [r for r in rows if (r['company'], r['goal'], r['arm']) != k] + [row]
            json.dump(rows, open(path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
            print(json.dumps({x: row.get(x) for x in ('company', 'goal', 'arm', 'passes', 'surfaced', 'asked', 'usd', 'error')},
                             ensure_ascii=False)[:500], flush=True)

if __name__ == '__main__':
    main()
