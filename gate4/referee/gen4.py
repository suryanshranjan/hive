"""Tests for Gate 4's 20 business functions. Visible: 2 happy-path tests per function. Hidden: 25 per function,
70% of calls drawn from edge cases. Expected values come from oracle.py (the private intent).
usage: gen4.py visible|hidden <out_dir> <seed>"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oracle

def L(v):
    if v is None: return 'NULL'
    if isinstance(v, str): return "'" + v.replace("'", "''") + "'"
    return repr(v)

H, E = {}, {}
H['discount'] = lambda r: r.choice([(100, 'gold'), (40, 'silver'), (200, 'bronze'), (60, 'gold'), (80, 'silver')])
E['discount'] = lambda r: r.choice([(500, 'gold'), (300, 'silver'), (1000, 'silver'), (100, 'GOLD'), (100, ' gold '), (100, 'platinum'), (-5, 'gold'), (None, 'gold'), (100, None), (0, 'gold')])
H['shipping'] = lambda r: r.choice([(1, 'local'), (3, 'national'), (2, 'intl'), (4, 'local'), (1, 'national')])
E['shipping'] = lambda r: r.choice([(0.5, 'local'), (1.2, 'local'), (0, 'intl'), (-2, 'local'), (31, 'local'), (30, 'local'), (2, 'mars'), (2, 'LOCAL'), (None, 'local'), (5, None)])
H['abbrev'] = lambda r: r.choice([('hello world', 5), ('hi', 5), ('abcdefgh', 4), ('swarm', 10), ('database', 6)])
E['abbrev'] = lambda r: r.choice([('hello', 5), ('hello', 2), ('hello', 1), ('hello', 0), ('', 3), (None, 3), ('hello', None), ('héllo wörld', 4), (12345, 3)])
H['weekday'] = lambda r: (r.choice(['2024-03-04', '2024-03-05', '2024-03-06', '2024-03-07', '2024-03-08']),)
E['weekday'] = lambda r: (r.choice(['2024-03-09', '2024-03-10', 'nope', None, '2024-02-29', '2024-03-09 10:00', '2023-02-29', '2024-03-17']),)
H['age'] = lambda r: r.choice([('1990-06-15', '2024-06-15'), ('1990-06-15', '2024-06-14'), ('2000-01-01', '2024-07-01'), ('1985-03-10', '2024-01-01')])
E['age'] = lambda r: r.choice([('2020-05-05', '2020-05-05'), ('2025-01-01', '2024-01-01'), ('2000-02-29', '2023-02-28'), ('2000-02-29', '2023-03-01'), ('1800-01-01', '2024-01-01'), (None, '2024-01-01'), ('1990-13-01', '2024-01-01'), ('1874-06-01', '2024-06-01'), ('1875-06-02', '2024-06-01')])
H['phone_fmt'] = lambda r: (r.choice(['5551234567', '555-123-4567', '(555) 987 6543', '212.555.0199']),)
E['phone_fmt'] = lambda r: (r.choice(['15551234567', '25551234567', '555123456', '', 'abc', None, 5551234567, '+1 555 123 4567', '555-1234']),)
H['band'] = lambda r: (r.choice([5, 30, 80, 2, 45, 99]),)
E['band'] = lambda r: (r.choice([10, 50, 50.01, -1, 0, None, 9.999, -0.5]),)
H['roman'] = lambda r: (r.choice([4, 9, 14, 2024, 40, 90, 1994]),)
E['roman'] = lambda r: (r.choice([0, 3999, 4000, -1, 2.5, 2.4, None, 0.4]),)
H['ordinal'] = lambda r: (r.choice([1, 2, 3, 4, 21, 22, 5]),)
E['ordinal'] = lambda r: (r.choice([11, 12, 13, 111, 112, 0, -1, 101, 2.5, None]),)
H['split_part'] = lambda r: r.choice([('a,b,c', ',', 2), ('2024-03-15', '-', 1), ('x|y', '|', 2), ('one two', ' ', 1)])
E['split_part'] = lambda r: r.choice([('a,b,c', ',', 0), ('a,b,c', ',', -1), ('a,b,c', ',', 5), ('a,b,c', '', 1), (None, ',', 1), ('a,,c', ',', 2), ('abc', ',', 1), ('a,b,c', ',', -4)])
H['median3'] = lambda r: r.choice([(1, 5, 3), (10, 20, 30), (7, 2, 4), (9, 1, 5)])
E['median3'] = lambda r: r.choice([(1, None, 5), (None, None, 7), (None, None, None), (2, 2, 9), (1.5, 2.5, 2), (-3, None, -8), (5, 5, 5)])
H['stars'] = lambda r: (r.choice([3, 4, 5, 1, 2]),)
E['stars'] = lambda r: (r.choice([3.5, 3.25, 3.24, 6, -1, 0, None, 4.75, 0.3]),)
H['elapsed'] = lambda r: (r.choice([3661, 125, 7200, 4000]),)
E['elapsed'] = lambda r: (r.choice([59, 60, 0, 86400, -61, 59.9, None, 90061, -5]),)
H['grade_point'] = lambda r: (r.choice(['A', 'B', 'C', 'B+', 'D']),)
E['grade_point'] = lambda r: (r.choice(['A+', 'a-', ' B+ ', 'E', 'P', None, 'Z', 'C-', 'D-', '']),)
H['credit_band'] = lambda r: (r.choice([600, 700, 820, 450, 760]),)
E['credit_band'] = lambda r: (r.choice([579, 580, 669.9, 850, 851, 299, None, 739.5, 300, 799.99]),)
H['color_hex'] = lambda r: r.choice([(255, 0, 0), (0, 128, 255), (16, 32, 48), (0, 255, 0)])
E['color_hex'] = lambda r: r.choice([(300, -5, 128), (12.5, 0, 0), (None, 0, 0), (0, 0, 0), (255, 255, 255), (1.4, 2.6, 0)])
H['vowels'] = lambda r: (r.choice(['hello', 'banana', 'education', 'swarm', 'queue']),)
E['vowels'] = lambda r: (r.choice(['sky', 'yes', 'happy day', '', None, 'AEIOU', 'éa', 'rhythm', 'Y', 'boy, toy!']),)
H['next_bizday'] = lambda r: (r.choice(['2024-03-04', '2024-03-05', '2024-03-06', '2024-03-07']),)
E['next_bizday'] = lambda r: (r.choice(['2024-03-08', '2024-03-09', '2024-12-24', '2023-12-29', '2024-12-25', 'bad', None, '2027-12-24']),)
H['loyalty_pts'] = lambda r: r.choice([(100, 0), (50, 1), (20, 1), (75, 0)])
E['loyalty_pts'] = lambda r: r.choice([(100, 5), (99.9, 2), (600, 5), (0.5, 0), (100, None), (-5, 1), (None, 3), (10, 2), (7, 2)])
AGG = 'mode_val'
CATS = sorted(H) + [AGG]

def call(cat, args):
    return f'{cat.upper()}(' + ', '.join(L(a) for a in args) + ')'

def make(cat, rng, edge_share):
    if cat == AGG:
        if edge_share == 0:
            vals = [rng.choice([1, 2, 3])] * 3 + [rng.randint(4, 9) for _ in range(2)]
        else:
            vals = rng.choice([[3, 3, 1, 1], [None, None], [7], [None, 2, 2, None, 5], [1.5, 2.5, 1.5, 2.5, 0.5], [], [4, 4, 4, 1, 1, 1, 9]])
        setup = ['CREATE TABLE m (id INTEGER, v REAL)']
        if vals:
            setup.append('INSERT INTO m VALUES ' + ', '.join(f'({i}, {L(v)})' for i, v in enumerate(vals, 1)))
        return setup, 'SELECT MODE_VAL(v) FROM m'
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
