"""Gate 115 (PREDICTIONS.md): what lives only in the founder's head. For each goal, arm and repeat:
plan (hive/plan.py, real Claude in a copy of the mock site) -> his answers to the plan's questions (a simulated founder
from a private brief) -> plan again with his answers, exactly as hive/assistant.py pursue does on the phone. A blind
judge, given only the goal, one rubric line and the final plan, says whether the plan accounts for the hidden fact.

usage: python gates/gate115/flight115.py [--only G1,G2] [--repeats 2]
Needs private/g115/ (make_company.py, key.json; git-ignored, published after scoring). Results: gates/gate115/results/."""
import argparse, concurrent.futures as cf, json, os, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
PRIV = os.path.join(ROOT, 'private', 'g115')
sys.path.insert(0, ROOT); sys.path.insert(0, PRIV)
OUT = os.path.join(HERE, 'results'); os.makedirs(OUT, exist_ok=True)
os.environ.pop('HIVE_EXPLAIN_CMD', None)

def claude_json(prompt):
    for _ in range(3):
        r = subprocess.run([shutil.which('claude') or 'claude', '-p', '--output-format', 'json', '--tools', ''], input=prompt, capture_output=True,
                           text=True, encoding='utf-8', errors='replace', timeout=300, cwd=tempfile.gettempdir())
        try:
            out = json.loads(r.stdout); t = out['result']
            return json.loads(t[t.index('{'):t.rindex('}') + 1], strict=False), float(out.get('total_cost_usd') or 0)
        except Exception:
            time.sleep(5)
    return {}, 0.0

def founder(brief, questions):
    q = '\n'.join(f'{k}. {x}' for k, x in enumerate(questions, 1))
    got, c = claude_json(f"You are this business owner:\n{brief}\n\nYour assistant asks you on your phone, before planning:\n{q}\n\n"
                         "Answer all of them in one short phone message, in your own words. Reply with JSON only: "
                         '{"say": "..."}')
    return str(got.get('say') or 'Nothing to add.'), c

JUDGE = """A business owner gave his assistant a goal, and the assistant made a plan of changes to his website.
Goal: "{goal}"
Something true about his business: {fact}
The test: {rubric}

The plan:
{plan}

Does the plan pass the test? Judge only from the plan's text. Reply with JSON only: {{"passes": true or false, "why": "one sentence"}}"""

SURFACED = """Something true about a business: {fact}
The owner wrote: "{said}"
Did the owner say this fact (or its substance)? Reply with JSON only: {{"said_it": true or false}}"""

def show(p):
    return '\n'.join(f"- {s['title']}: {s['why']} BUILD: {s['build']}" for s in (p or {}).get('steps', [])) or '(no plan)'

def one(gid, g, arm, rep, brief, make_company):
    from hive import plan
    os.environ['HIVE_PLAN_ASK'] = arm   # read by plan.prompt at call time (one process per run keeps arms apart)
    work = tempfile.mkdtemp(prefix=f'g115-{gid}-{arm}-{rep}-'); repo = os.path.join(work, 'tutornest')
    make_company.make(repo)
    t0, cost = time.time(), 0.0
    p = plan.make(repo, g['goal']); cost += (p or {}).get('cost', 0)
    asked = list((p or {}).get('missing') or []); said, final = '', p
    if asked:
        said, c = founder(brief, asked); cost += c
        if not said.strip().lower().startswith(('nothing', 'no.')):
            p2 = plan.make(repo, g['goal'], notes=[f"Asked: {' / '.join(asked)} He said: {said}"]); cost += (p2 or {}).get('cost', 0)
            final = p2 or p
    row = {'goal': gid, 'arm': arm, 'rep': rep, 'asked': asked, 'said': said, 'first': show(p), 'final': show(final),
           'minutes': round((time.time() - t0) / 60, 1)}
    if g.get('fact') != 'none':
        j, c1 = claude_json(JUDGE.format(goal=g['goal'], fact=g['fact'], rubric=g['accounts_for'], plan=row['final']))
        s, c2 = claude_json(SURFACED.format(fact=g['fact'], said=said)) if said else ({'said_it': False}, 0)
        row.update(passes=bool(j.get('passes')), judge_why=j.get('why', ''), surfaced=bool(s.get('said_it'))); cost += c1 + c2
    row['usd'] = round(cost, 3)
    shutil.rmtree(work, ignore_errors=True)
    return row

def run_one(args):   # in a child process: HIVE_PLAN_ASK must not leak between parallel runs
    gid, arm, rep = args
    r = subprocess.run([sys.executable, __file__, '--child', f'{gid}:{arm}:{rep}'], capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=3600)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return {'goal': gid, 'arm': arm, 'rep': rep, 'error': (r.stderr or r.stdout)[-600:]}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--only'); ap.add_argument('--repeats', type=int, default=2)
    ap.add_argument('--child'); ap.add_argument('--parallel', type=int, default=2)
    a = ap.parse_args()
    key = json.load(open(os.path.join(PRIV, 'key.json'), encoding='utf-8'))
    goals = dict(key['goals']); goals.update(key.get('control', {}))
    if a.child:
        import make_company
        gid, arm, rep = a.child.split(':')
        print(json.dumps(one(gid, goals[gid], arm, int(rep), key['brief'], make_company), ensure_ascii=False)); return
    ids = a.only.split(',') if a.only else list(goals)
    jobs = [(g, arm, rep) for rep in range(1, a.repeats + 1) for g in ids for arm in ('one', 'three')
            if not (g.startswith('C') and rep > 1)]
    path = os.path.join(OUT, 'runs.json')
    rows = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else []
    done = {(r['goal'], r['arm'], r['rep']) for r in rows if 'error' not in r}
    jobs = [j for j in jobs if j not in done]
    print(f'{len(jobs)} runs to do', flush=True)
    with cf.ThreadPoolExecutor(a.parallel) as ex:
        for row in ex.map(run_one, jobs):
            rows = [r for r in rows if (r['goal'], r['arm'], r['rep']) != (row['goal'], row['arm'], row['rep'])] + [row]
            json.dump(rows, open(path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
            print(json.dumps({k: row.get(k) for k in ('goal', 'arm', 'rep', 'passes', 'surfaced', 'asked', 'usd', 'error')},
                             ensure_ascii=False)[:600], flush=True)

if __name__ == '__main__':
    main()
