import math
import sqlite3
import unicodedata
import datetime


def _num(x):
    if x is None or isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        v = float(x) if isinstance(x, float) else x
    else:
        try:
            v = float(str(x).strip())
        except ValueError:
            return None
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def _date(x):
    if not isinstance(x, str):
        return None
    try:
        return datetime.date.fromisoformat(x.strip())
    except ValueError:
        return None


def _half_up(x):
    return math.floor(x + 0.5)


# ---------- late_fee ----------
def late_fee(amount, days_late):
    a, d = _num(amount), _num(days_late)
    if a is None or d is None:
        return None
    if math.isinf(d):
        d = 10 ** 6 if d > 0 else -1
    if d <= 5:
        return 0
    weeks = math.ceil(d / 7)
    fee = math.floor(a * weeks / 100)
    fee = max(fee, 500)
    cap = math.floor(a / 4)
    return int(min(fee, cap))


# ---------- ship_cost ----------
_ZONES = {'A': (300, 100), 'B': (500, 150), 'C': (800, 200)}


def ship_cost(weight_g, zone):
    w = _num(weight_g)
    if w is None or zone is None:
        return None
    if w <= 0:
        return 0
    base, per = _ZONES.get(str(zone).strip().upper(), _ZONES['C'])
    if math.isinf(w):
        w = 1e12
    cost = base + per * math.ceil(w / 500)
    if w > 20000:
        cost += 1500
    return int(cost)


# ---------- mask_card ----------
def mask_card(text):
    if text is None:
        return None
    s = str(text)
    digits = [c for c in s if c in '0123456789']
    n = len(digits)
    if n == 0:
        return 'INVALID'
    if n < 5:
        keep = 0
    elif n == 15 and digits[0] == '3':
        keep = 5
    else:
        keep = 4
    out = []
    seen = 0
    for c in s:
        if c in '0123456789':
            seen += 1
            out.append(c if seen > n - keep else '*')
        else:
            out.append(c)
    return ''.join(out)


# ---------- grade_letter ----------
def grade_letter(score):
    v = _num(score)
    if v is None:
        return None
    if isinstance(v, float) and math.isinf(v):
        return 'INVALID'
    s = _half_up(v)
    if s < 0 or s > 100:
        return 'INVALID'
    if s == 100:
        return 'A+'
    for cut, g in ((90, 'A'), (80, 'B'), (70, 'C'), (60, 'D')):
        if s >= cut:
            return g
    return 'F'


# ---------- biz_days ----------
def biz_days(start, end):
    a, b = _date(start), _date(end)
    if a is None or b is None:
        return None
    if b <= a:
        return 0
    n = 0
    d = a
    one = datetime.timedelta(days=1)
    while d < b:
        if d.weekday() < 5 and (d.month, d.day) not in ((12, 25), (1, 1)):
            n += 1
        d += one
    return n


# ---------- loyalty_pts ----------
_TIERS = {'basic': 1.0, 'silver': 1.5, 'gold': 2.0}


def loyalty_pts(amount_cents, tier):
    a = _num(amount_cents)
    if a is None:
        return None
    mult = 1.0
    if isinstance(tier, str):
        mult = _TIERS.get(tier.strip().lower(), 1.0)
    if isinstance(a, float) and math.isinf(a):
        return 5000 if a > 0 else None
    pts = math.floor(a * mult / 100)
    return int(min(pts, 5000))


# ---------- slugify ----------
def slugify(text):
    if text is None:
        return None
    s = unicodedata.normalize('NFKD', str(text))
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    out = []
    pend = False
    for c in s:
        if c in 'abcdefghijklmnopqrstuvwxyz0123456789':
            if pend and out:
                out.append('-')
            pend = False
            out.append(c)
        else:
            pend = True
    slug = ''.join(out)
    return slug[:30].strip('-')


# ---------- shift_pay ----------
def shift_pay(hours, rate_cents):
    h, r = _num(hours), _num(rate_cents)
    if h is None or r is None:
        return None
    if isinstance(h, float) and math.isinf(h):
        h = 1e9 if h > 0 else -1e9
    if isinstance(r, float) and math.isinf(r):
        return None
    h = _half_up(h * 4) / 4
    reg = min(h, 40)
    ot = max(0, min(h, 60) - 40)
    dt = max(0, h - 60)
    return int(_half_up(r * (reg + 1.5 * ot + 2 * dt)))


# ---------- age_years ----------
def age_years(birth, as_of):
    a, b = _date(birth), _date(as_of)
    if a is None or b is None:
        return None
    y = b.year - a.year
    if (b.month, b.day) < (a.month, a.day):
        y -= 1
    return y


# ---------- robust_mean (aggregate) ----------
class RobustMean:
    def __init__(self):
        self.vals = []

    def step(self, value):
        if value is None or isinstance(value, (str, bytes)):
            return
        self.vals.append(float(value))

    def finalize(self):
        if len(self.vals) < 3:
            return None
        v = sorted(self.vals)[1:-1]
        return sum(v) / len(v)


SPEC = {
    'late_fee': 'late_fee(amount_cents, days_late): Late-payment fee in cents charged on an overdue invoice.',
    'ship_cost': 'ship_cost(weight_g, zone): Shipping charge in cents for a parcel of the given weight in grams to a delivery zone.',
    'mask_card': 'mask_card(text): Masks a payment card number for display on receipts and logs.',
    'grade_letter': 'grade_letter(score): Converts a numeric course score into a letter grade.',
    'biz_days': 'biz_days(start_date, end_date): Number of working days between two ISO dates (YYYY-MM-DD).',
    'loyalty_pts': 'loyalty_pts(amount_cents, tier): Loyalty points earned on a purchase for a customer tier.',
    'slugify': 'slugify(text): Turns a title into a URL-friendly slug.',
    'shift_pay': 'shift_pay(hours, rate_cents): Gross pay in cents for hours worked in a week at an hourly rate in cents.',
    'age_years': 'age_years(birth_date, as_of_date): Age in whole years on a given date, from ISO dates.',
    'robust_mean': 'robust_mean(value): Aggregate average of a numeric column that is resistant to outliers.',
}

SCALARS = {
    'late_fee': (late_fee, 2),
    'ship_cost': (ship_cost, 2),
    'mask_card': (mask_card, 1),
    'grade_letter': (grade_letter, 1),
    'biz_days': (biz_days, 2),
    'loyalty_pts': (loyalty_pts, 2),
    'slugify': (slugify, 1),
    'shift_pay': (shift_pay, 2),
    'age_years': (age_years, 2),
}

AGGREGATE = ('robust_mean', RobustMean)

TYPICAL = {
    'late_fee': [(100000, 14), (100000, 8), (250000, 30), (80000, 10), (500000, 60)],
    'ship_cost': [(400, 'A'), (1200, 'B'), (2500, 'C'), (5000, 'A'), (900, 'B')],
    'mask_card': [('4111 1111 1111 1111',), ('5500-0000-0000-0004',), ('4111111111111111',), ('6011 0009 9013 9424',)],
    'grade_letter': [(95,), (85,), (72,), (65,), (40,), (90,)],
    'biz_days': [('2024-03-04', '2024-03-11'), ('2024-03-01', '2024-03-04'), ('2024-03-02', '2024-03-04'),
                 ('2024-02-05', '2024-02-20'), ('2024-03-04', '2024-03-04')],
    'loyalty_pts': [(5000, 'basic'), (15000, 'silver'), (20000, 'gold'), (10000, 'basic')],
    'slugify': [('Hello World',), ('Spring Sale 2024!',), ('  New   Arrivals  - Men ',), ('Q3_Report (Final)',)],
    'shift_pay': [(38, 2000), (45, 2000), (8, 1500), (50, 1000), (7.5, 2000)],
    'age_years': [('1990-05-15', '2024-05-14'), ('1990-05-15', '2024-05-15'), ('2001-12-31', '2024-01-01'),
                  ('1985-07-04', '2020-09-09')],
}

EDGE = {
    'late_fee': [(100000, 5), (100000, 6), (20000, 14), (1000, 30), (50555, 30), (1000000, 365),
                 (None, 10), (100000, None), (100000, -3)],
    'ship_cost': [(0, 'A'), (-5, 'B'), (20000, 'A'), (20001, 'A'), (1000, 'b'), (1000, ' B '),
                  (1000, 'Z'), (1000, None), (None, 'A')],
    'mask_card': [('1234',), ('12345',), ('3782 822463 10005',), ('4111-1111-1111-1111',), ('abc',),
                  ('',), (None,), (4111111111111111,), ('3530111333300000',)],
    'grade_letter': [(89.4,), (89.6,), (59.5,), (59.4,), (100,), (100.4,), (100.5,), (-1,), ('abc',), ('88',)],
    'biz_days': [('2024-03-11', '2024-03-04'), ('2024-12-20', '2024-12-30'), ('2023-12-29', '2024-01-03'),
                 ('2024-02-28', '2024-03-01'), ('2024-13-01', '2024-03-01'), (None, '2024-03-01'),
                 ('2024-03-04', 'garbage'), ('2024-12-25', '2024-12-26')],
    'loyalty_pts': [(5000, None), (5000, 'platinum'), (5000, 'GOLD'), (250099, 'silver'), (999, 'basic'),
                    (1000000, 'gold'), (500000, 'basic'), (-2000, 'basic'), (None, 'gold')],
    'slugify': [('Crème Brûlée',), ('!!!',), ('',), (None,), ('word ' * 10,), ('a' * 29 + ' bbb',),
                ('ÀÉÎ',), ('日本語',)],
    'shift_pay': [(40, 1000), (60, 1000), (61, 1000), (60.1, 1000), (7.12, 2000), (7.13, 2000),
                  (None, 1000), (0, 1000), (-5, 1000)],
    'age_years': [('2000-02-29', '2023-02-28'), ('2000-02-29', '2023-03-01'), ('2000-02-29', '2024-02-29'),
                  ('2024-01-01', '2020-01-01'), ('2000-13-01', '2024-01-01'), (None, '2024-01-01'),
                  ('2000-01-01', 'xyz')],
}

AGG_TYPICAL = [[1, 2, 3, 4, 5], [10, 20, 30], [5, 5, 5, 5], [1, 100, 2, 3, 50]]
AGG_EDGE = [[], [1, 2], [None, None, None], [1, 2, 3], [None, 1, 2, 3, 4], ['a', 1, 2, 3],
            [1.5, 2.5, 9.5, 100], [7]]

DECISIONS = {
    'late_fee': ['grace period of 5 days', 'cap at 25% of amount', 'minimum fee of 500 cents',
                 'fractional cents truncated down'],
    'ship_cost': ['unknown zone uses zone C rates', 'zone is case/space-insensitive',
                  'oversize surcharge above 20000 g', 'non-positive weight costs 0'],
    'mask_card': ['fewer than 5 digits fully masked', '15-digit numbers starting with 3 show last 5',
                  'no digits gives INVALID'],
    'grade_letter': ['score rounded half up before grading', 'out of range gives INVALID',
                     '100 gives A+'],
    'biz_days': ['reversed range returns 0', 'Dec 25 and Jan 1 are not working days'],
    'loyalty_pts': ['NULL or unknown tier treated as basic', 'points capped at 5000',
                    'fractional points truncated down'],
    'slugify': ['accents transliterated to ASCII', 'truncated to 30 chars without trailing hyphen'],
    'shift_pay': ['double time beyond 60 hours', 'hours rounded to nearest quarter hour'],
    'age_years': ['Feb 29 birthday counts only from Mar 1 in non-leap years'],
    'robust_mean': ['fewer than 3 numeric values gives NULL'],
}

DECISION_EXAMPLES = {
    'late_fee': [(80000, 3), (10000, 10), (200000, 200), (77777, 12)],
    'ship_cost': [(700, 'Q'), (700, 'c'), (30000, 'B'), (-100, 'C')],
    'mask_card': [('987',), ('371449635398431',), ('n/a',)],
    'grade_letter': [(79.5,), (105,), (100.2,)],
    'biz_days': [('2024-04-10', '2024-04-01'), ('2024-12-23', '2024-12-27')],
    'loyalty_pts': [(5000, 'vip'), (900000, 'gold'), (1999, 'basic')],
    'slugify': [('Jalapeño Poppers',), ('The Quick Brown Fox Jumps Over The Lazy Dog',)],
    'shift_pay': [(70, 1000), (7.1, 2000)],
    'age_years': [('2004-02-29', '2021-02-28')],
    'robust_mean': [[4, 9]],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, n) in SCALARS.items():
        con.create_function(name, n, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con
