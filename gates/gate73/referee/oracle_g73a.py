import math
import re
import sqlite3
import datetime
from fractions import Fraction


def _num(x):
    if isinstance(x, bool):
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
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def _safe(fn):
    def w(*args):
        if any(a is None for a in args):
            return None
        try:
            return fn(*args)
        except Exception:
            return None
    return w


_DATE_RE = re.compile(r'\d{4}-\d{2}-\d{2}')


def _parse_date(s):
    if not isinstance(s, str):
        return None
    s = s.strip()
    if not _DATE_RE.fullmatch(s):
        return None
    try:
        return datetime.date(int(s[:4]), int(s[5:7]), int(s[8:10]))
    except ValueError:
        return None


# ---- late_fee ----
def late_fee(amount_cents, days_late):
    a = _num(amount_cents)
    d = _num(days_late)
    if a is None or d is None:
        return None
    if a <= 0 or d <= 5:
        return 0
    periods = math.ceil(d / 30)
    fee = Fraction(a) * 2 * periods / 100
    fee = min(fee, Fraction(a) / 4)
    fee = math.floor(fee + Fraction(1, 2))
    if fee > 0:
        fee = max(fee, 500)
    return int(fee)


# ---- mask_card ----
def mask_card(text):
    s = str(text)
    digits = [c for c in s if c in '0123456789']
    n = len(digits)
    if n <= 4:
        return '*' * n
    return '*' * min(n - 4, 12) + ''.join(digits[-4:])


# ---- biz_days_after ----
def biz_days_after(date_text, n):
    d = _parse_date(date_text)
    k = _num(n)
    if d is None or k is None:
        return None
    k = int(k)
    if k < 0:
        k = 0
    if k > 260:
        k = 260
    one = datetime.timedelta(days=1)
    while k > 0:
        d = d + one
        if d.weekday() >= 5:
            continue
        if (d.month, d.day) in ((12, 25), (1, 1)):
            continue
        k -= 1
    return d.isoformat()


# ---- star_label ----
def star_label(avg, votes):
    a = _num(avg)
    v = _num(votes)
    if a is None or v is None:
        return None
    if v < 5:
        return 'unrated'
    a = max(0.0, min(5.0, float(a)))
    r = math.floor(a * 2 + 0.5) / 2
    return '%.1f stars' % r


# ---- slugify ----
def slugify(text):
    s = str(text).lower().replace('&', ' and ')
    out = []
    for c in s:
        if ord(c) < 128:
            out.append(c if c.isalnum() else '-')
        # non-ASCII characters are dropped
    slug = re.sub(r'-+', '-', ''.join(out)).strip('-')
    slug = slug[:40].rstrip('-')
    return slug if slug else 'untitled'


# ---- ship_cost ----
_RATES = {1: 300, 2: 450, 3: 700}


def ship_cost(weight_g, zone):
    w = _num(weight_g)
    z = _num(zone)
    if w is None or z is None:
        return None
    if w <= 0:
        return 0
    blocks = math.ceil(w / 500)
    zi = int(z) if z == int(z) else None
    rate = _RATES.get(zi, 700)
    cost = blocks * rate
    if w > 20000:
        cost += 1500
    return int(cost)


# ---- pct_change ----
def pct_change(old, new):
    o = _num(old)
    n = _num(new)
    if o is None or n is None:
        return None
    if o <= 0:
        return 0.0
    return round((n - o) / o * 100, 1) or 0.0


# ---- quarter_label ----
def quarter_label(date_text):
    d = _parse_date(date_text)
    if d is None:
        return 'n/a'
    fy = d.year + 1 if d.month >= 4 else d.year
    q = ((d.month - 4) % 12) // 3 + 1
    return 'FY%02d-Q%d' % (fy % 100, q)


# ---- short_code ----
_ALPHA = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'


def short_code(n):
    v = _num(n)
    if v is None or v != int(v):
        return '----'
    v = int(v)
    if v < 0 or v >= 32 ** 4:
        return '----'
    out = ''
    for _ in range(4):
        out = _ALPHA[v % 32] + out
        v //= 32
    return out


# ---- aggregate: tidy_mean ----
class TidyMean:
    def __init__(self):
        self.total = 0.0
        self.count = 0

    def step(self, value):
        if value is None or isinstance(value, (str, bytes)):
            return
        self.total += value
        self.count += 1

    def finalize(self):
        if self.count == 0:
            return 0.0
        return float(self.total / self.count)


SPEC = {
    'late_fee': 'late_fee(amount_cents, days_late): Late-payment fee in cents charged on an overdue invoice.',
    'mask_card': 'mask_card(card_number): Masks a payment card number for display on receipts and support screens.',
    'biz_days_after': 'biz_days_after(start_date, n): Due date (ISO text) that falls n business days after a start date.',
    'star_label': 'star_label(avg_score, num_votes): Customer-facing star rating label for a product listing.',
    'slugify': 'slugify(title): Turns a page or product title into a URL-friendly slug.',
    'ship_cost': 'ship_cost(weight_g, zone): Shipping charge in cents for a parcel of a given weight to a delivery zone.',
    'pct_change': 'pct_change(old_value, new_value): Percentage change between two period figures, for KPI reports.',
    'quarter_label': 'quarter_label(date_text): Fiscal quarter label for a calendar date, used in finance reports.',
    'short_code': 'short_code(n): Compact human-friendly voucher code for a numeric id.',
    'tidy_mean': 'tidy_mean(value): Average of the numeric values in a group, for dashboards.',
}

SCALARS = {
    'late_fee': (late_fee, 2),
    'mask_card': (mask_card, 1),
    'biz_days_after': (biz_days_after, 2),
    'star_label': (star_label, 2),
    'slugify': (slugify, 1),
    'ship_cost': (ship_cost, 2),
    'pct_change': (pct_change, 2),
    'quarter_label': (quarter_label, 1),
    'short_code': (short_code, 1),
}

AGGREGATE = ('tidy_mean', TidyMean)

TYPICAL = {
    'late_fee': [(50000, 10), (50000, 40), (80000, 65), (120000, 31), (60000, 12)],
    'mask_card': [('4111111111111111',), ('378282246310005',), ('5500000000000004',), ('6011000000000004',)],
    'biz_days_after': [('2025-03-03', 1), ('2025-03-07', 1), ('2025-03-03', 10), ('2025-06-02', 5)],
    'star_label': [(4.3, 50), (3.9, 10), (2.2, 8), (4.8, 100), (1.0, 20)],
    'slugify': [('Hello World',), ('Spring Sale 2025!',), ('  New   Arrivals ',), ('Q3_Report (final)',)],
    'ship_cost': [(400, 1), (1200, 2), (2500, 3), (500, 1), (7000, 2)],
    'pct_change': [(100, 110), (50, 40), (80, 100), (200, 200), (3, 4)],
    'quarter_label': [('2025-05-10',), ('2025-08-01',), ('2025-11-30',), ('2026-02-14',), ('2026-04-15',)],
    'short_code': [(0,), (10,), (163,), (17408,), (32768,)],
}

EDGE = {
    'late_fee': [(50000, 5), (50000, 6), (10000, 10), (50000, 400), (50025, 10),
                 (-100, 30), (50000, -3), ('abc', 10), (None, 10)],
    'mask_card': [('4111-1111-1111-1111',), ('1234',), ('12345',), ('',),
                  ('1234567890123456789012',), ('abcd',), (4111111111111111,), ('12 3456',)],
    'biz_days_after': [('2025-03-08', 0), ('2025-03-08', 1), ('2025-03-05', -1),
                       ('2025-03-03', 300), ('2025-12-24', 1), ('2024-12-31', 1),
                       ('2025-02-30', 3), ('abc', 2), (None, 2)],
    'star_label': [(4.5, 4), (4.5, 5), (6.2, 50), (-1, 50), (4.25, 30), (3.75, 30),
                   (None, 5), (4.0, 'x')],
    'slugify': [('Rock & Roll',), ('Zoë Müller',), ('abcdefghi ' * 6,), ('***',), ('',),
                ('---a---',), (123,), ('Tom&Jerry',)],
    'ship_cost': [(20000, 1), (20001, 1), (1000, 9), (1000, 0), (0, 2), (-5, 2),
                  (None, 2), (1000, '2'), (1000, 2.5)],
    'pct_change': [(0, 50), (0, 0), (-10, 5), (100, 'x'), (100, None), (1, 1000000),
                   (100, -50), (100, 99.99)],
    'quarter_label': [('2025-03-31',), ('2025-04-01',), ('2025-12-31',), ('2025-13-01',),
                      ('hello',), ('',), ('2024-02-29',), ('2025-02-29',)],
    'short_code': [(31,), (18,), (1048575,), (1048576,), (-1,), ('abc',), (12.5,),
                   ('77',), (None,)],
}

AGG_TYPICAL = [[1, 2, 3], [10, 20, 30, 40], [2.5, 3.5], [100, None, 200]]
AGG_EDGE = [[], [None, None, None], [1, 'x', 3], ['12', 'x'], [2.5, None, 3.5], [7],
            [-4, 4, 10]]

DECISIONS = {
    'late_fee': ['no fee within 5 days grace', 'fee capped at 25% of amount',
                 'minimum fee of 500 cents when a fee applies', 'cents rounded half up'],
    'mask_card': ['non-digit characters dropped before masking',
                  '4 or fewer digits fully masked',
                  'at most 12 mask characters shown'],
    'biz_days_after': ['negative n treated as 0',
                       'Dec 25 and Jan 1 are not business days',
                       'n capped at 260'],
    'star_label': ['fewer than 5 votes gives unrated',
                   'score clamped to 0..5',
                   'quarter-star ties round up to higher half'],
    'slugify': ['ampersand becomes and', 'non-ASCII characters dropped not transliterated',
                'slug truncated to 40 chars without trailing hyphen',
                'empty slug becomes untitled'],
    'ship_cost': ['parcels over 20000 g get 1500 surcharge',
                  'unknown zone charged at zone 3 rate'],
    'pct_change': ['non-positive old value returns 0.0'],
    'quarter_label': ['invalid date gives n/a'],
    'short_code': ['Crockford alphabet skipping I L O U',
                   'out of range or non-integer gives ----'],
    'tidy_mean': ['text values ignored even if numeric-looking',
                  'no numeric values gives 0.0'],
}

DECISION_EXAMPLES = {
    'late_fee': [(50000, 3), (50000, 500), (20000, 20), (70025, 10)],
    'mask_card': [('4111 a 1111 b 1111 c 1111',), ('999',), ('12345678901234567890',)],
    'biz_days_after': [('2025-03-05', -2), ('2025-12-30', 2), ('2025-01-06', 500)],
    'star_label': [(3.0, 0), (9, 10), (2.25, 40)],
    'slugify': [('Salt & Pepper',), ('Jalapeño Poppers',), ('x' * 39 + ' yz',), ('@#$',)],
    'ship_cost': [(25000, 2), (3000, 7)],
    'pct_change': [(0, 8)],
    'quarter_label': [('1999-00-10',)],
    'short_code': [(27,), (2000000,)],
    'tidy_mean': [['5', '7', 3], [None, 'zz', None, 'q']],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, nargs) in SCALARS.items():
        con.create_function(name, nargs, _safe(fn), deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con
