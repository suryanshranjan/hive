import sqlite3, math

SPEC = {
    'late_fee': 'late_fee(balance_cents, days_late): Late fee in cents charged on an overdue invoice balance.',
    'initials': "initials(full_name): Uppercase initials of a person's full name, for avatars and mailing labels.",
    'ship_cost': 'ship_cost(weight_kg, zone): Shipping price in dollars for a parcel of the given weight to a delivery zone (A, B or C).',
    'avg_rating': 'avg_rating(score): Average customer review score for a product, shown on the storefront.',
}


def _num(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    try:
        return float(str(x).strip())
    except Exception:
        return None


def late_fee(balance, days):
    b, d = _num(balance), _num(days)
    if b is None or d is None:
        return None
    if b <= 0 or d <= 0:
        return 0
    fee = int(b * 2 // 100)
    return min(fee, 5000)


_PARTICLES = {'de', 'van', 'von', 'da', 'del', 'der'}


def initials(name):
    if name is None:
        return None
    out = ''
    for tok in str(name).split():
        if tok in _PARTICLES:
            continue
        out += tok[0].upper()
    return out


_MULT = {'A': 1.0, 'B': 1.25, 'C': 1.5}


def ship_cost(weight, zone):
    w = _num(weight)
    if w is None or zone is None:
        return None
    if w > 25:
        return None
    m = _MULT.get(str(zone).strip().upper(), 1.5)
    kg = max(0, math.ceil(w))
    return round((4 + 1.5 * kg) * m, 2)


SCALARS = {'late_fee': (late_fee, 2), 'initials': (initials, 1), 'ship_cost': (ship_cost, 2)}


class AvgRating:
    def __init__(self):
        self.vals = []

    def step(self, value):
        if isinstance(value, (int, float)) and 1 <= value <= 5:
            self.vals.append(float(value))

    def finalize(self):
        if len(self.vals) < 3:
            return None
        avg = sum(self.vals) / len(self.vals)
        return math.floor(avg * 2 + 0.5) / 2


AGGREGATE = ('avg_rating', AvgRating)

TYPICAL = {
    'late_fee': [(10000, 10), (20000, 3), (5000, 45), (30000, 1), (1000, 90)],
    'initials': [('john smith',), ('Mary Ann Lee',), ('alice cooper',), ('Grace Brewster Hopper',)],
    'ship_cost': [(1, 'A'), (2.5, 'C'), (4, 'B'), (7.2, 'B'), (10, 'C')],
}

EDGE = {
    'late_fee': [(10000, 0), (10000, -3), (None, 5), (260000, 30), (-1000, 10),
                 (250000, 10), (0, 10), (10000, None), (300000, 7)],
    'initials': [('Ludwig van Beethoven',), ('Ana de la Cruz',), ('',), ('   ',), (None,),
                 ('Jean-Luc Picard',), ('Ada',), ('  anna   maria  ',), ('Van Morrison',)],
    'ship_cost': [(25, 'A'), (26, 'A'), (30.5, 'B'), (3, 'Z'), (3, None), (None, 'A'),
                  (3, 'b'), (0, 'A'), (3, ''), (25.01, 'C')],
}

AGG_TYPICAL = [[4, 5, 3], [5, 5, 4, 4], [2, 3, 4, 3], [3, 4, 4, 3]]

AGG_EDGE = [
    [5, 5, None, 4],
    [1, 1, 0, 6],
    [3, 3, 3, 7, 3],
    [],
    [1, 2, 'x', 5],
    [0, 0, 0],
    [2.25, 3, 4.5],
    [5, 5, 5, 5, 5],
]

DECISIONS = {
    'late_fee': ['fee capped at 5000 cents', 'non-positive balance (credit) gives 0'],
    'initials': ['lowercase name particles (de, van, von, da, del, der) skipped'],
    'ship_cost': ['over 25 kg returns NULL', 'unknown zone priced as zone C'],
    'avg_rating': ['scores outside 1..5 ignored', 'fewer than 3 valid scores gives NULL',
                   'result rounded to nearest 0.5'],
}

DECISION_EXAMPLES = {
    'late_fee': [(400000, 10), (-5000, 10)],
    'initials': [('Vincent van Gogh',)],
    'ship_cost': [(40, 'C'), (5, 'Q')],
    'avg_rating': [[4, 5, 9, 3, 4], [5, 5], [4, 4, 5]],
}


def connect():
    c = sqlite3.connect(':memory:', isolation_level=None)
    for n, (f, k) in SCALARS.items():
        c.create_function(n, k, f, deterministic=True)
    c.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return c


if __name__ == '__main__':
    def run():
        c = connect()
        res = []
        for n in SCALARS:
            for t in TYPICAL[n] + EDGE[n] + DECISION_EXAMPLES[n]:
                q = 'SELECT %s(%s)' % (n, ','.join('?' * len(t)))
                r = c.execute(q, t).fetchone()[0]
                assert r is None or isinstance(r, (int, float, str)), (n, t, r)
                res.append(r)
        an = AGGREGATE[0]
        for L in AGG_TYPICAL + AGG_EDGE + DECISION_EXAMPLES[an]:
            c.execute('DROP TABLE IF EXISTS m')
            c.execute('CREATE TABLE m (id INTEGER, v)')
            for i, v in enumerate(L):
                c.execute('INSERT INTO m VALUES (?,?)', (i, v))
            r = c.execute('SELECT %s(v) FROM m' % an).fetchone()[0]
            assert r is None or isinstance(r, (int, float, str)), (L, r)
            res.append(r)
        return res
    a = run(); b = run()
    assert a == b
    allx = [str(x) for k in TYPICAL for x in TYPICAL[k]] + [str(x) for k in EDGE for x in EDGE[k]]
    for k, v in DECISION_EXAMPLES.items():
        for x in v:
            assert str(x) not in allx and x not in AGG_TYPICAL + AGG_EDGE
    for k in SCALARS: assert 4 <= len(TYPICAL[k]) and 6 <= len(EDGE[k]) <= 10
    assert all(len(DECISIONS[k]) == len(DECISION_EXAMPLES[k]) for k in DECISIONS)
    print('OK', len(a))
