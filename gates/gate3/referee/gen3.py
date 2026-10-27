"""Tests for the 20 business functions. Visible: 2 happy-path tests per function. Hidden: 25 per function
drawn from happy and edge cases. Expected values come from oracle.py (the private intent).
usage: gen3.py visible|hidden <out_dir> <seed>"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oracle

def L(v):
    if v is None: return 'NULL'
    if isinstance(v, str): return "'" + v.replace("'", "''") + "'"
    return repr(v)

def D(rng, lo=2023, hi=2025):
    return f'{rng.randint(lo, hi)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}'

def days_after(d, n):
    import datetime
    return (datetime.date.fromisoformat(d) + datetime.timedelta(days=n)).isoformat()

H, E = {}, {}  # happy and edge argument makers
H['clamp'] = lambda r: (r.randint(1, 20), 5, 15)
E['clamp'] = lambda r: r.choice([(None, 1, 5), (7, 10, 2), (3, None, 5), (30, 1, None), (2.5, 1, 2), (-4, -2, 8), (5, 5, 5), (12, None, None)])
H['bucket'] = lambda r: (r.randint(0, 99), r.choice([5, 10]))
E['bucket'] = lambda r: r.choice([(-7, 5), (13, 0), (13, -5), (None, 5), (7.5, 2), (9, 2.5), (13, None), (0, 3)])
H['mask'] = lambda r: (r.choice(['secret', 'password', 'card1234', 'hello']),)
E['mask'] = lambda r: (r.choice(['', 'a', 'ab', 'abc', None, 12345, 'x y z']),)
H['slug'] = lambda r: (r.choice(['Hello World', 'Big Data Summit', 'my first post']),)
E['slug'] = lambda r: (r.choice(['!!!', '', '--a--', 'C++ & Rust', 'Ünïcode Text', None, '  spaced  out  ', 'ALL_CAPS_99']),)
H['titlecase'] = lambda r: (r.choice(['hello world', 'big blue sky', 'good morning']),)
E['titlecase'] = lambda r: (r.choice(['the lord of the rings', 'war and peace', 'mIxEd cAsE', 'double  space', '', None, 'of mice', 'x']),)
H['fiscal_q'] = lambda r: (f'{r.randint(2023, 2025)}-{r.randint(5, 12):02d}-{r.randint(1, 28):02d}',)
E['fiscal_q'] = lambda r: (r.choice(['2024-01-15', '2024-03-31', '2024-04-01', '2023-12-31', 'not a date', None, '2025-02-28 10:00:00', '2024-06-30']),)
H['biz_days'] = lambda r: (lambda d: (d, days_after(d, r.randint(1, 4))))('2024-03-04')
E['biz_days'] = lambda r: (lambda d: r.choice([(d, d), (days_after(d, 9), d), ('2024-03-09', '2024-03-11'), (d, days_after(d, 30)), (None, d), (d, 'bad')]))(D(r))
H['round_half_even'] = lambda r: r.choice([(1.26, 1), (2.4,), (7.71, 1), (3.14159, 2)])
E['round_half_even'] = lambda r: r.choice([(2.5,), (3.5,), (-2.5,), (0.125, 2), (0.135, 2), (None,), (1.25, 1), (2.675, 2), (5, None)])
H['pct'] = lambda r: r.choice([(1, 4), (3, 8), (2, 5), (7, 10)])
E['pct'] = lambda r: r.choice([(1, 0), (-1, 4), (None, 3), (1, 3), (2, 3), (0, 9), (5, 2)])
H['initials'] = lambda r: (r.choice(['john smith', 'ada lovelace', 'alan mathison turing']),)
E['initials'] = lambda r: (r.choice(['mary-jane watson', '   ', '123 abc', None, 'x', 'jean-luc  picard', '', 'élodie durand']),)
H['score'] = lambda r: (r.choice([3, 5, 25, 50, 80]),)
E['score'] = lambda r: (r.choice([-3, 0, 10, 100, 1000, None, 9.5, 99, 250]),)
H['grade'] = lambda r: (r.choice([95, 85, 72, 64, 30]),)
E['grade'] = lambda r: (r.choice([100, 120, 90, 60, 59.9, None, -5, 89.99]),)
H['safe_div'] = lambda r: r.choice([(10, 4), (9, 3), (1, 8)])
E['safe_div'] = lambda r: r.choice([(5, 0), (5, 0, -1), (None, 2), (5, None, 3), (0, 5), (5, 0, None), (-6, 4)])
H['tax'] = lambda r: (r.choice([100, 50, 200]), r.choice(['IN', 'US', 'EU']))
E['tax'] = lambda r: r.choice([(5, 'UK'), (15, 'uk'), (100, 'XX'), (-10, 'IN'), (None, 'EU'), (100, None), (9.99, 'UK'), (10, 'UK'), (100, 'in')])
H['checksum'] = lambda r: (r.choice(['abc', 'hello', 'order-42']),)
E['checksum'] = lambda r: (r.choice(['', 'a', None, 'zzzzzzzzzzzz', 'A', 'b', 123]),)
H['nth_word'] = lambda r: ('the quick brown fox', r.randint(1, 4))
E['nth_word'] = lambda r: r.choice([('a b c', 0), ('a b c', -1), ('a b c', 10), (None, 1), ('one', None), ('  spaced   words ', 2), ('a b c', -3)])
H['collapse'] = lambda r: (r.choice(['aabbcc', 'bookkeeper', 'hello']),)
E['collapse'] = lambda r: (r.choice(['aAAb', '', None, 'Mississippi', 'AaAa', '  x  ', '112233']),)
H['ago'] = lambda r: ('2024-05-01', days_after('2024-05-01', r.randint(2, 5)))
E['ago'] = lambda r: (lambda n: ('2024-05-01', days_after('2024-05-01', n)))(r.choice([0, 1, 7, 8, 14, 30, 45, 61, 365, 800, -3]))
H['luhn_ok'] = lambda r: (r.choice(['79927398713', '79927398710', '4539148803436467']),)
E['luhn_ok'] = lambda r: (r.choice(['4539 1488 0343 6467', '12a4', '0', '', None, '4539-1488-0343-6467', '00', '18']),)
CATS = sorted(H) + ['wavg']

def call(cat, args):
    return f'{cat.upper()}(' + ', '.join(L(a) for a in args) + ')'

def make(cat, rng, edge_share):
    if cat == 'wavg':
        if edge_share == 0:
            rows = [(i, rng.randint(1, 9), rng.randint(1, 5)) for i in range(1, 5)]
        else:
            rows = [(i, rng.choice([None, 1, 4, 7.5, -2]), rng.choice([None, 0, 1, 3, -1])) for i in range(1, rng.randint(2, 6))]
        setup = ['CREATE TABLE w (id INTEGER, v REAL, wt REAL)', 'INSERT INTO w VALUES ' + ', '.join('(' + ', '.join(L(x) for x in r) + ')' for r in rows)]
        return setup, 'SELECT WAVG(v, wt) FROM w'
    calls = []
    for _ in range(3):
        args = (E[cat] if rng.random() < edge_share else H[cat])(rng)
        calls.append(call(cat, args))
    return [], 'SELECT ' + ', '.join(calls)

if __name__ == '__main__':
    kind, out, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
    per, edge = (2, 0.0) if kind == 'visible' else (25, 0.7)
    os.makedirs(out, exist_ok=True)
    n = 0
    for ci, cat in enumerate(CATS):
        rng = random.Random(seed + ci * 1000)
        for k in range(per):
            setup, q = make(cat, rng, edge)
            con = oracle.connect()
            for s in setup: con.execute(s)
            rows = [list(r) for r in con.execute(q).fetchall()]
            t = dict(id=f'{cat}_{k:03d}', category=cat, setup=setup, query=q, expected=rows, ordered=True)
            json.dump(t, open(os.path.join(out, t['id'] + '.json'), 'w')); n += 1
    print(n, kind, 'tests in', out)
