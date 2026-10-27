"""Run minisql against a directory of JSON tests.

usage:
  python3 run_tests.py tests/visible                    # whole suite, summary by category
  python3 run_tests.py tests/visible --category where   # one category
  python3 run_tests.py tests/visible --sample 0.3       # random 30% sample (seeded by time unless --seed)
  python3 run_tests.py tests/visible --list-failing     # print failing test ids
  python3 run_tests.py tests/visible --show where_004   # show one test: setup, query, expected, got
  python3 run_tests.py tests/visible --json out.json    # machine-readable results

A test passes when minisql returns the same rows as SQLite did. Numbers compare by value
(3 == 3.0, rounded to 6 places); NULL is None; row order matters only if the query has ORDER BY.
"""
import argparse, glob, json, os, random, signal, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def norm(v):
    if isinstance(v, bool):
        v = int(v)
    if isinstance(v, (int, float)):
        return ('n', round(float(v), 6))
    if v is None:
        return ('0',)
    return ('s', str(v))


def norm_rows(rows, ordered):
    out = [tuple(norm(v) for v in r) for r in rows]
    return out if ordered else sorted(out)


class Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise Timeout()


def run_one(t):
    import minisql
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(3)
    try:
        con = minisql.connect()
        for s in t['setup']:
            con.execute(s)
        got = [list(r) for r in con.execute(t['query'])]
        ok = norm_rows(got, t['ordered']) == norm_rows(t['expected'], t['ordered'])
        return ok, got, None
    except Timeout:
        return False, None, 'timeout'
    except BaseException as e:  # engine bugs must not stop the run
        return False, None, f'{type(e).__name__}: {e}'
    finally:
        signal.alarm(0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('suite')
    ap.add_argument('--category')
    ap.add_argument('--sample', type=float)
    ap.add_argument('--seed', type=int)
    ap.add_argument('--list-failing', action='store_true')
    ap.add_argument('--show')
    ap.add_argument('--json')
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(a.suite, '*.json')))
    tests = [json.load(open(f)) for f in files]
    if a.show:
        t = next(t for t in tests if t['id'] == a.show)
        ok, got, err = run_one(t)
        print('\n'.join(t['setup'])); print('QUERY:', t['query'])
        print('EXPECTED:', t['expected']); print('GOT:', got if err is None else err); print('PASS' if ok else 'FAIL')
        return
    if a.category:
        tests = [t for t in tests if t['category'] == a.category]
    if a.sample:
        rng = random.Random(a.seed if a.seed is not None else time.time_ns())
        tests = [t for t in tests if rng.random() < a.sample]
    res = {}
    for t in tests:
        ok, got, err = run_one(t)
        res[t['id']] = ok
    bycat = {}
    for t in tests:
        c = bycat.setdefault(t['category'], [0, 0]); c[1] += 1; c[0] += res[t['id']]
    if a.json:
        json.dump(res, open(a.json, 'w'))
    if a.list_failing:
        print('\n'.join(k for k, v in res.items() if not v))
        return
    for c in sorted(bycat):
        p, n = bycat[c]
        print(f'{c:14s} {p:3d}/{n:<3d}')
    print(f'TOTAL          {sum(res.values())}/{len(res)}')


if __name__ == '__main__':
    main()
