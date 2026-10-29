import datetime
import math
import re
import sqlite3


def _num(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        v = x
    elif isinstance(x, str):
        try:
            v = float(x.strip())
        except ValueError:
            return None
    else:
        return None
    if isinstance(v, float) and not math.isfinite(v):
        return None
    return v


def _round_half_up(x):
    return int(math.floor(x + 0.5))


def late_fee(amount_cents, days_late):
    a = _num(amount_cents)
    d = _num(days_late)
    if a is None or d is None:
        return None
    if d <= 5:
        return 0
    if a <= 0:
        return 0
    periods = math.ceil(d / 30)
    fee = a * 0.02 * periods
    fee = min(fee, a * 0.25)
    return _round_half_up(fee)


_ZONE_BASE = {'A': 500, 'B': 800, 'C': 1200}


def ship_cost(weight_g, zone):
    w = _num(weight_g)
    if w is None or zone is None:
        return None
    z = str(zone).strip().upper()
    base = _ZONE_BASE.get(z, _ZONE_BASE['C'])
    if w <= 0:
        return None
    if w > 30000:
        return 9999
    extra = math.ceil((w - 500) / 500) if w > 500 else 0
    return base + 100 * extra


def mask_card(number):
    if number is None:
        return None
    if isinstance(number, float) and number == int(number):
        number = int(number)
    s = str(number).replace(' ', '').replace('-', '')
    if any(c not in '0123456789' for c in s):
        return None
    if len(s) < 8:
        return 'INVALID'
    return '*' * (len(s) - 4) + s[-4:]


def age_band(age):
    a = _num(age)
    if a is None or a < 0 or a > 120:
        return 'unknown'
    a = int(a)
    if a <= 17:
        return '0-17'
    if a <= 34:
        return '18-34'
    if a <= 54:
        return '35-54'
    if a <= 64:
        return '55-64'
    return '65+'


def star_rating(avg_score, votes):
    s = _num(avg_score)
    v = _num(votes)
    if s is None or v is None:
        return None
    if v < 5:
        return None
    s = max(0.0, min(5.0, float(s)))
    return math.floor(s * 2 + 0.5) / 2


_DATE_RE = re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}')


def _parse_date(s):
    if not isinstance(s, str) or not _DATE_RE.fullmatch(s):
        return None
    try:
        return datetime.date.fromisoformat(s)
    except ValueError:
        return None


def _is_bday(d):
    if d.weekday() >= 5:
        return False
    if (d.month, d.day) in ((1, 1), (12, 25)):
        return False
    return True


def next_bday(date_text, n):
    if date_text is None:
        return None
    d = _parse_date(date_text)
    k = _num(n)
    if d is None or k is None:
        return None
    k = int(k)
    if k < 0:
        k = 0
    if k > 100000:
        return None
    one = datetime.timedelta(days=1)
    try:
        if k == 0:
            while not _is_bday(d):
                d += one
            return d.isoformat()
        for _ in range(k):
            d += one
            while not _is_bday(d):
                d += one
        return d.isoformat()
    except OverflowError:
        return None


_SKU_RE = re.compile(r'([A-Za-z]{2})-?([0-9]{4})', re.ASCII)


def sku_clean(code):
    if code is None:
        return None
    m = _SKU_RE.fullmatch(str(code))
    if not m:
        return 'BAD'
    return m.group(1).upper() + '-' + m.group(2)


def split_bill(total_cents, people):
    t = _num(total_cents)
    p = _num(people)
    if t is None or p is None:
        return None
    n = int(p)
    if n < 1:
        n = 1
    if isinstance(t, int):
        return -(-t // n)
    return int(math.ceil(t / n))


def fiscal_qtr(date_text):
    if date_text is None:
        return None
    d = _parse_date(date_text)
    if d is None:
        return 'N/A'
    if d.month >= 4:
        fy = d.year + 1
        q = (d.month - 4) // 3 + 1
    else:
        fy = d.year
        q = 4
    return 'FY%d-Q%d' % (fy, q)


class TrimAvg:
    def __init__(self):
        self.vals = []

    def step(self, value):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if isinstance(value, float) and not math.isfinite(value):
                return
            self.vals.append(value)

    def finalize(self):
        if len(self.vals) < 3:
            return None
        v = sorted(self.vals)[1:-1]
        return sum(v) / len(v)


SPEC = {
    'late_fee': 'late_fee(amount_cents, days_late): Late-payment fee in cents charged on an overdue invoice.',
    'ship_cost': 'ship_cost(weight_g, zone): Shipping charge in cents for a parcel of the given weight sent to a delivery zone.',
    'mask_card': 'mask_card(card_number): Masked card number safe to print on customer receipts.',
    'age_band': 'age_band(age): Marketing age-band label for a customer age.',
    'star_rating': 'star_rating(avg_score, votes): Star rating to display on a product page, in half-star steps.',
    'next_bday': 'next_bday(date, n): ISO date that falls n business days after the given ISO date.',
    'sku_clean': 'sku_clean(code): Normalized product SKU code in the catalogue format.',
    'split_bill': 'split_bill(total_cents, people): Amount in cents each person pays when a bill is shared equally.',
    'fiscal_qtr': 'fiscal_qtr(date): Fiscal year and quarter label for an ISO date.',
    'trim_avg': 'trim_avg(score): Robust average of review scores that discounts outliers.',
}

SCALARS = {
    'late_fee': (late_fee, 2),
    'ship_cost': (ship_cost, 2),
    'mask_card': (mask_card, 1),
    'age_band': (age_band, 1),
    'star_rating': (star_rating, 2),
    'next_bday': (next_bday, 2),
    'sku_clean': (sku_clean, 1),
    'split_bill': (split_bill, 2),
    'fiscal_qtr': (fiscal_qtr, 1),
}

AGGREGATE = ('trim_avg', TrimAvg)

TYPICAL = {
    'late_fee': [(10000, 10), (10000, 45), (25000, 70), (4000, 31)],
    'ship_cost': [(400, 'A'), (1000, 'B'), (2600, 'C'), (1500, 'A')],
    'mask_card': [('4111111111111111',), ('378282246310005',),
                  ('5500000000000004',), ('6011111111111117',)],
    'age_band': [(5,), (25,), (40,), (60,), (80,)],
    'star_rating': [(4.3, 50), (3.9, 100), (2.2, 30), (4.8, 12)],
    'next_bday': [('2024-03-04', 1), ('2024-03-08', 1),
                  ('2024-03-04', 5), ('2024-03-06', 3)],
    'sku_clean': [('ab-1234',), ('XY-0042',), ('mk-7788',), ('Qr-0001',)],
    'split_bill': [(9000, 3), (10000, 4), (6000, 2), (12000, 6)],
    'fiscal_qtr': [('2024-05-10',), ('2024-11-02',), ('2025-02-14',),
                   ('2024-07-01',), ('2024-03-20',)],
}

EDGE = {
    'late_fee': [(10000, 5), (10000, 6), (10000, 400), (-5000, 40),
                 (None, 10), (12525, 10), (0, 100), ('abc', 10)],
    'ship_cost': [(0, 'A'), (-5, 'B'), (30000, 'A'), (30001, 'A'),
                  (500, 'a'), (700, ' b '), (800, 'Z'), (800, ''),
                  (None, 'A'), (1000, None)],
    'mask_card': [('4111-1111-1111-1111',), ('4111 1111 1111 1111',),
                  ('1234567',), ('12345678',), ('4111x1111',), ('abcd',),
                  ('',), (4111111111111111,), (None,)],
    'age_band': [(0,), (17,), (17.9,), (18,), (34.99,), (-1,), (121,),
                 ('abc',), (65,), (120,)],
    'star_rating': [(4.5, 4), (4.5, 5), (7.2, 50), (-1, 50), (2.25, 20),
                    (None, 10), (3.0, None), (4.5, 0), ('x', 10)],
    'next_bday': [('2024-03-09', 0), ('2024-03-08', 0), ('2024-12-24', 1),
                  ('2024-12-31', 1), ('2024-03-04', -2), ('2024-02-30', 1),
                  ('bad', 1), (None, 1), ('2024-03-04', None),
                  ('2023-12-29', 1)],
    'sku_clean': [('ab-1234',), ('AB1234',), ('ab123',), ('ABC-1234',),
                  ('12-ABCD',), (' ab-1234',), ('ab-12345',), (None,),
                  ('',), ('Ab-0000',)],
    'split_bill': [(10000, 3), (100, 0), (100, -2), (1, 2), (0, 5),
                   (-1000, 3), (None, 2), (1000, None), (1000, 2.9)],
    'fiscal_qtr': [('2024-04-01',), ('2024-03-31',), ('2025-01-01',),
                   ('2024-12-31',), ('2024-02-30',), ('hello',),
                   ('2024-4-1',), (None,), ('',), ('2024-06-30',)],
}

AGG_TYPICAL = [[1, 5, 5, 5, 9], [2, 4, 6, 8], [10, 20, 30, 40, 50, 1000]]
AGG_EDGE = [[], [5], [1, 2], [1, 2, 3], [None, 1, 2, 3, 4],
            [7, 7, 7], [1.5, 2.5, 9.5, 0.5]]

DECISIONS = {
    'late_fee': ['grace period of 5 days', 'fee capped at 25% of amount',
                 'rounding of fractional cents is half up',
                 'negative amount gives 0 fee'],
    'ship_cost': ['zone is trimmed and case-insensitive',
                  'unknown zone priced as zone C',
                  'weight over 30000 g is flat 9999',
                  'non-positive weight gives NULL'],
    'mask_card': ['spaces and dashes stripped from input and output',
                  'fewer than 8 digits gives INVALID',
                  'other characters give NULL'],
    'age_band': ['fractional age truncated, not rounded',
                 'age below 0 or above 120 gives unknown',
                 'missing or non-numeric age gives unknown'],
    'star_rating': ['fewer than 5 votes gives NULL',
                    'average clamped into 0..5'],
    'next_bday': ['n=0 on a non-business day rolls forward',
                  'Jan 1 and Dec 25 are not business days',
                  'negative n treated as 0'],
    'sku_clean': ['dash may be omitted in input',
                  'invalid code gives the text BAD'],
    'split_bill': ['share rounded up',
                   'fewer than 1 person treated as 1'],
    'fiscal_qtr': ["invalid date text gives 'N/A'"],
    'trim_avg': ['fewer than 3 numeric values gives NULL'],
}

DECISION_EXAMPLES = {
    'late_fee': [(20000, 3), (8000, 500), (10025, 10), (-20000, 90)],
    'ship_cost': [(900, ' a'), (1000, 'north'), (45000, 'B'), (-1, 'C')],
    'mask_card': [('3782 822463 10005',), ('1234-567',), ('41111111111111X1',)],
    'age_band': [(54.9,), (150,), (None,)],
    'star_rating': [(4.0, 3), (6, 30)],
    'next_bday': [('2024-03-10', 0), ('2024-12-20', 3), ('2024-03-06', -1)],
    'sku_clean': [('xy9876',), ('zz-12',)],
    'split_bill': [(7000, 3), (500, 0.5)],
    'fiscal_qtr': [('2023-02-29',)],
    'trim_avg': [[3, 9]],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, nargs) in SCALARS.items():
        con.create_function(name, nargs, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con


def _selfcheck():
    def run():
        out = []
        con = connect()
        for name in SCALARS:
            for args in TYPICAL[name] + EDGE[name] + DECISION_EXAMPLES[name]:
                q = 'SELECT %s(%s)' % (name, ','.join('?' * len(args)))
                r = con.execute(q, args).fetchone()[0]
                assert r is None or isinstance(r, (int, float, str)), (name, args, r)
                out.append((name, args, r))
        an = AGGREGATE[0]
        for vals in AGG_TYPICAL + AGG_EDGE + DECISION_EXAMPLES[an]:
            con.execute('DROP TABLE IF EXISTS m')
            con.execute('CREATE TABLE m (id INTEGER, v)')
            for i, v in enumerate(vals):
                con.execute('INSERT INTO m VALUES (?, ?)', (i, v))
            r = con.execute('SELECT %s(v) FROM m' % an).fetchone()[0]
            assert r is None or isinstance(r, (int, float, str)), (vals, r)
            out.append((an, vals, r))
        return out
    a, b = run(), run()
    assert a == b
    # structure checks
    n = 0
    for name in list(SCALARS) + [AGGREGATE[0]]:
        assert len(DECISIONS[name]) == len(DECISION_EXAMPLES[name])
        n += len(DECISIONS[name])
        pool = (TYPICAL.get(name, []) + EDGE.get(name, [])) if name in SCALARS \
            else AGG_TYPICAL + AGG_EDGE
        for ex in DECISION_EXAMPLES[name]:
            assert ex not in pool, (name, ex)
    assert n == 25, n
    return a


if __name__ == '__main__':
    for row in _selfcheck():
        print(row)
    print('OK')
