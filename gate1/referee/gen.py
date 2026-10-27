"""Test generator for minisql. SQLite is the referee: every expected result comes from sqlite3.
Each test = random tables + one query from one feature category. Same generator, disjoint seeds
for the visible suite (in the repo) and the hidden suite (never in the repo).
usage: gen.py <out_dir> <first_seed> <per_category>"""
import json, os, random, sqlite3, sys

CATS = ['basic', 'arith', 'where', 'nulls', 'order_limit', 'aggregates', 'group_by', 'distinct',
        'join', 'left_join', 'strings', 'case', 'update_delete', 'subquery']

def tables(rng):
    n = rng.randint(3, 9)
    t_rows = []
    for i in range(1, n + 1):
        a = rng.choice([None] + list(range(-5, 15)))
        b = rng.choice([None] + list(range(0, 8)))
        s = rng.choice([None, 'apple', 'Banana', 'cherry', 'date', 'Elder', 'fig', 'grape', 'kiwi', 'apple'])
        x = rng.choice([None, 0.5, 1.25, 2.0, 3.5, -1.5, 10.0])
        t_rows.append((i, a, b, s, x))
    m = rng.randint(2, 8)
    u_rows = []
    for j in range(1, m + 1):
        u_rows.append((j, rng.choice([None] + list(range(1, n + 3))), rng.randint(-3, 9),
                       rng.choice(['red', 'green', 'blue', None, 'Red'])))
    setup = ['CREATE TABLE t (id INTEGER, a INTEGER, b INTEGER, s TEXT, x REAL)',
             'CREATE TABLE u (id INTEGER, t_id INTEGER, v INTEGER, name TEXT)']
    def lit(v):
        if v is None: return 'NULL'
        if isinstance(v, str): return "'" + v + "'"
        return repr(v)
    setup.append('INSERT INTO t VALUES ' + ', '.join('(' + ', '.join(lit(v) for v in r) + ')' for r in t_rows))
    setup.append('INSERT INTO u VALUES ' + ', '.join('(' + ', '.join(lit(v) for v in r) + ')' for r in u_rows))
    return setup

def num_expr(rng, cols=('a', 'b', 'id'), depth=0):
    r = rng.random()
    if depth > 1 or r < 0.35: return rng.choice(cols)
    if r < 0.5: return str(rng.randint(-4, 9))
    op = rng.choice(['+', '-', '*', '/', '%'])
    return f'({num_expr(rng, cols, depth+1)} {op} {num_expr(rng, cols, depth+1)})'

def cond(rng, cols=('a', 'b', 'id'), depth=0):
    r = rng.random()
    if depth < 1 and r < 0.3:
        return f'({cond(rng, cols, depth+1)} {rng.choice(["AND", "OR"])} {cond(rng, cols, depth+1)})'
    if depth < 1 and r < 0.38:
        return f'NOT ({cond(rng, cols, depth+1)})'
    if r < 0.48:
        return f'{rng.choice(cols)} BETWEEN {rng.randint(-3, 3)} AND {rng.randint(3, 10)}'
    if r < 0.56:
        return f'{rng.choice(cols)} IN ({", ".join(str(rng.randint(-2, 9)) for _ in range(3))})'
    return f'{rng.choice(cols)} {rng.choice(["=", "<>", "!=", "<", "<=", ">", ">="])} {rng.randint(-2, 9)}'

def query(cat, rng):
    if cat == 'basic':
        cols = rng.sample(['id', 'a', 'b', 's', 'x'], rng.randint(1, 4))
        return rng.choice([f'SELECT {", ".join(cols)} FROM t', 'SELECT * FROM t', f'SELECT {cols[0]} AS c1, id FROM t',
                           f'SELECT t.{cols[0]} FROM t', 'SELECT 1, 2 + 3, \'hi\'', f'SELECT {cols[0]} FROM t AS q'])
    if cat == 'arith':
        return f'SELECT id, {num_expr(rng)}, -{rng.choice(["a", "b"])}, x * {rng.choice([2, 0.5, 3])} FROM t'
    if cat == 'where':
        return f'SELECT id, a, b FROM t WHERE {cond(rng)}'
    if cat == 'nulls':
        return rng.choice([f'SELECT id FROM t WHERE {rng.choice(["a", "b", "s", "x"])} IS NULL',
                           f'SELECT id FROM t WHERE {rng.choice(["a", "b", "s", "x"])} IS NOT NULL',
                           f'SELECT id, COALESCE(a, b, {rng.randint(0, 9)}), a + b, a = NULL FROM t',
                           f'SELECT id, IFNULL(s, \'none\'), NULLIF(b, {rng.randint(0, 7)}) FROM t',
                           f'SELECT id FROM t WHERE a > {rng.randint(-2, 5)} OR b IS NULL'])
    if cat == 'order_limit':
        keys = rng.sample(['a', 'b', 's', 'x'], rng.randint(1, 2))
        ob = ', '.join(f'{k} {rng.choice(["", "ASC", "DESC"])}'.strip() for k in keys) + ', id'
        lim = rng.choice(['', f' LIMIT {rng.randint(1, 5)}', f' LIMIT {rng.randint(1, 4)} OFFSET {rng.randint(1, 3)}'])
        return f'SELECT id, {", ".join(keys)} FROM t ORDER BY {ob}{lim}'
    if cat == 'aggregates':
        aggs = rng.sample(['COUNT(*)', 'COUNT(a)', 'SUM(a)', 'MIN(b)', 'MAX(s)', 'AVG(a)', 'SUM(x)', 'MAX(a) - MIN(a)', 'COUNT(s)', 'TOTAL(b)'], rng.randint(1, 4))
        w = rng.choice(['', f' WHERE {cond(rng)}'])
        return f'SELECT {", ".join(aggs)} FROM t{w}'
    if cat == 'group_by':
        g = rng.choice(['b', 's', 'a % 3'])
        aggs = rng.sample(['COUNT(*)', 'SUM(a)', 'MIN(id)', 'MAX(x)', 'AVG(id)', 'COUNT(a)'], rng.randint(1, 3))
        hv = rng.choice(['', f' HAVING COUNT(*) > {rng.randint(0, 2)}', f' HAVING SUM(id) >= {rng.randint(1, 10)}'])
        return f'SELECT {g}, {", ".join(aggs)} FROM t GROUP BY {g}{hv}'
    if cat == 'distinct':
        return rng.choice(['SELECT DISTINCT b FROM t', 'SELECT DISTINCT s FROM t', 'SELECT DISTINCT a % 2, b FROM t',
                           'SELECT COUNT(DISTINCT b) FROM t', 'SELECT DISTINCT name FROM u'])
    if cat == 'join':
        w = rng.choice(['', f' WHERE u.v > {rng.randint(-2, 5)}', f' AND t.a IS NOT NULL'])
        return rng.choice([f'SELECT t.id, u.id, u.v FROM t JOIN u ON t.id = u.t_id{w if w.startswith(" AND") else ""}',
                           f'SELECT t.id, u.name FROM t INNER JOIN u ON u.t_id = t.id{w if w.startswith(" WHERE") else ""}',
                           'SELECT a.id, b.id FROM t a, u b WHERE a.id = b.t_id',
                           'SELECT t.s, COUNT(*) FROM t JOIN u ON t.id = u.t_id GROUP BY t.s'])
    if cat == 'left_join':
        return rng.choice(['SELECT t.id, u.v FROM t LEFT JOIN u ON t.id = u.t_id',
                           'SELECT t.id, u.name FROM t LEFT OUTER JOIN u ON u.t_id = t.id WHERE u.id IS NULL',
                           f'SELECT t.id, COUNT(u.id) FROM t LEFT JOIN u ON t.id = u.t_id GROUP BY t.id',
                           f'SELECT t.id, u.v FROM t LEFT JOIN u ON t.id = u.t_id AND u.v > {rng.randint(0, 5)}'])
    if cat == 'strings':
        return rng.choice(["SELECT id, s || '-' || id FROM t", f"SELECT id FROM t WHERE s LIKE '{rng.choice(['a%', '%e', '%an%', 'A%', '_i%'])}'",
                           'SELECT id, UPPER(s), LOWER(s), LENGTH(s) FROM t', "SELECT id, SUBSTR(s, 2, 3) FROM t",
                           "SELECT id FROM t WHERE s = 'apple'", "SELECT id, s FROM t WHERE s < 'd'"])
    if cat == 'case':
        return rng.choice([f'SELECT id, CASE WHEN a > {rng.randint(0, 6)} THEN \'big\' WHEN a IS NULL THEN \'none\' ELSE \'small\' END FROM t',
                           f'SELECT id, CASE b WHEN 1 THEN \'one\' WHEN 2 THEN \'two\' END FROM t',
                           'SELECT SUM(CASE WHEN a > 0 THEN 1 ELSE 0 END) FROM t'])
    if cat == 'update_delete':
        return rng.choice([f'UPDATE t SET a = a + {rng.randint(1, 5)} WHERE {cond(rng)}; SELECT id, a FROM t',
                           f'DELETE FROM t WHERE {cond(rng)}; SELECT id FROM t',
                           f'UPDATE t SET s = \'z\', b = NULL WHERE id > {rng.randint(1, 5)}; SELECT id, s, b FROM t',
                           f'DELETE FROM u WHERE v < {rng.randint(0, 5)}; SELECT COUNT(*) FROM u'])
    if cat == 'subquery':
        return rng.choice(['SELECT id FROM t WHERE id IN (SELECT t_id FROM u)',
                           'SELECT id FROM t WHERE id NOT IN (SELECT t_id FROM u WHERE t_id IS NOT NULL)',
                           'SELECT id, (SELECT COUNT(*) FROM u WHERE u.t_id = t.id) FROM t',
                           'SELECT id FROM t WHERE a > (SELECT AVG(a) FROM t)',
                           'SELECT MAX(c) FROM (SELECT b, COUNT(*) AS c FROM t GROUP BY b)'])
    raise ValueError(cat)

def make(cat, seed):
    rng = random.Random(seed)
    setup = tables(rng)
    q = query(cat, rng)
    stmts = [x.strip() for x in q.split(';') if x.strip()]
    setup = setup + stmts[:-1]; q = stmts[-1]
    con = sqlite3.connect(':memory:')
    try:
        for s in setup: con.execute(s)
        rows = [list(r) for r in con.execute(q).fetchall()]
    except sqlite3.Error:
        return None
    ordered = 'ORDER BY' in q.upper() and 'FROM (' not in q
    return dict(category=cat, setup=setup, query=q, expected=rows, ordered=ordered)

if __name__ == '__main__':
    out, first, per = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    os.makedirs(out, exist_ok=True)
    n = 0
    for ci, cat in enumerate(CATS):
        made = 0; seed = first + ci * 100000
        while made < per:
            t = make(cat, seed); seed += 1
            if t is None: continue
            t['id'] = f'{cat}_{made:03d}'
            json.dump(t, open(os.path.join(out, t['id'] + '.json'), 'w'))
            made += 1; n += 1
    print(n, 'tests in', out)
