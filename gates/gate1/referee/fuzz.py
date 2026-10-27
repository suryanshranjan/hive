"""Compositional SQL fuzzer: queries that mix features the way real users do (joins + grouping +
CASE + subqueries + functions), checked against SQLite. Same JSON format as gen.py.
usage: fuzz.py <out_dir> <first_seed> <count>"""
import json, os, random, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen import tables


def scalar(rng, cols, depth=0):
    r = rng.random()
    if depth >= 2 or r < 0.3:
        return rng.choice(cols)
    if r < 0.4:
        return rng.choice([str(rng.randint(-3, 9)), "'k'", 'NULL', '2.5'])
    if r < 0.6:
        return f'({scalar(rng, cols, depth+1)} {rng.choice(["+", "-", "*", "/", "%"])} {scalar(rng, cols, depth+1)})'
    if r < 0.7:
        return f'CASE WHEN {pred(rng, cols, depth+1)} THEN {scalar(rng, cols, depth+1)} ELSE {scalar(rng, cols, depth+1)} END'
    if r < 0.8:
        return f'COALESCE({scalar(rng, cols, depth+1)}, {scalar(rng, cols, depth+1)})'
    if r < 0.9:
        return f'{rng.choice(["ABS", "LENGTH", "UPPER", "LOWER"])}({scalar(rng, cols, depth+1)})'
    return f'-{scalar(rng, cols, depth+1)}'


def pred(rng, cols, depth=0):
    r = rng.random()
    if depth < 2 and r < 0.25:
        return f'({pred(rng, cols, depth+1)} {rng.choice(["AND", "OR"])} {pred(rng, cols, depth+1)})'
    if depth < 2 and r < 0.32:
        return f'NOT {pred(rng, cols, depth+1)}'
    if r < 0.42:
        return f'{rng.choice(cols)} IS {rng.choice(["", "NOT "])}NULL'
    if r < 0.5:
        return f'{scalar(rng, cols, depth+1)} BETWEEN {rng.randint(-3, 3)} AND {rng.randint(2, 9)}'
    if r < 0.58:
        return f'{rng.choice(cols)} {rng.choice(["", "NOT "])}IN ({", ".join(str(rng.randint(-2, 9)) for _ in range(rng.randint(1, 4)))})'
    if r < 0.64:
        return f"t.s LIKE '{rng.choice(['%a%', 'b%', '%E%', '_r%', 'apple'])}'"
    if r < 0.7:
        return f't.id {rng.choice(["", "NOT "])}IN (SELECT u.t_id FROM u WHERE u.v > {rng.randint(-2, 6)})'
    return f'{scalar(rng, cols, depth+1)} {rng.choice(["=", "<>", "<", "<=", ">", ">="])} {scalar(rng, cols, depth+1)}'


def query(rng):
    join = rng.random() < 0.45
    tcols = ['t.id', 't.a', 't.b', 't.x']
    cols = tcols + (['u.v', 'u.id'] if join else [])
    frm = 't'
    if join:
        frm = f't {rng.choice(["JOIN", "LEFT JOIN", "INNER JOIN"])} u ON {rng.choice(["t.id = u.t_id", "u.t_id = t.id", "t.b = u.v"])}'
    where = f' WHERE {pred(rng, cols)}' if rng.random() < 0.7 else ''
    if rng.random() < 0.4:
        g = rng.choice(['t.b', 't.a % 3', 't.s'] + (['u.name'] if join else []))
        aggs = [rng.choice(['COUNT(*)', f'SUM({rng.choice(cols)})', f'MIN({scalar(rng, cols, 1)})', f'MAX({rng.choice(cols)})',
                            f'AVG({rng.choice(cols)})', f'COUNT(DISTINCT {rng.choice(cols)})', f'TOTAL({rng.choice(cols)})',
                            f'SUM(CASE WHEN {pred(rng, cols, 1)} THEN 1 ELSE 0 END)']) for _ in range(rng.randint(1, 3))]
        hv = f' HAVING {rng.choice(["COUNT(*) > 1", "SUM(t.id) > 4", "MIN(t.id) < 5", "COUNT(*) >= 1"])}' if rng.random() < 0.4 else ''
        return f'SELECT {g}, {", ".join(aggs)} FROM {frm}{where} GROUP BY {g}{hv}', False
    items = [scalar(rng, cols) for _ in range(rng.randint(1, 3))]
    dist = 'DISTINCT ' if rng.random() < 0.15 else ''
    if not join and not dist and rng.random() < 0.4:
        ob = f' ORDER BY {rng.choice(["t.a", "t.b", "t.x", "t.s"])} {rng.choice(["ASC", "DESC"])}, t.id'
        lim = f' LIMIT {rng.randint(1, 5)}' + (f' OFFSET {rng.randint(1, 3)}' if rng.random() < 0.3 else '') if rng.random() < 0.5 else ''
        return f'SELECT {dist}t.id, {", ".join(items)} FROM {frm}{where}{ob}{lim}', True
    return f'SELECT {dist}{", ".join(items)} FROM {frm}{where}', False


if __name__ == '__main__':
    out, first, count = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    os.makedirs(out, exist_ok=True)
    made, seed = 0, first
    while made < count:
        rng = random.Random(seed); seed += 1
        setup = tables(rng)
        q, ordered = query(rng)
        con = sqlite3.connect(':memory:')
        try:
            for s in setup: con.execute(s)
            rows = [list(r) for r in con.execute(q).fetchall()]
        except sqlite3.Error:
            continue
        t = dict(id=f'fuzz_{made:04d}', category='fuzz', setup=setup, query=q, expected=rows, ordered=ordered)
        json.dump(t, open(os.path.join(out, t['id'] + '.json'), 'w'))
        made += 1
    print(made, 'fuzz tests in', out, 'from', seed - first, 'seeds')
