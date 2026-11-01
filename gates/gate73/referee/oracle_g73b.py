import math
import re
import sqlite3
import datetime
from fractions import Fraction


def _num(x):
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return x if math.isfinite(x) else None
    if isinstance(x, str):
        try:
            v = float(x.strip())
        except ValueError:
            return None
        return v if math.isfinite(v) else None
    return None


def _ceil_frac(fr):
    return int(math.ceil(fr))


# 1. late_fee -- 4 decisions
def late_fee(balance, days):
    b, d = _num(balance), _num(days)
    if b is None or d is None:
        return None
    if b <= 0 or d <= 10:
        return 0
    fee = _ceil_frac(Fraction(b) * 2 / 100)
    fee = max(fee, 500)
    fee = min(fee, 5000)
    return fee


# 2. ship_cost -- 4 decisions
def ship_cost(weight_g, zone):
    w, z = _num(weight_g), _num(zone)
    if w is None or z is None:
        return None
    if w <= 0:
        return 0
    kg = _ceil_frac(Fraction(w) / 1000)
    base = 500 + 200 * kg
    zi = int(z) if z == int(z) else 3
    mult = {1: 2, 2: 3, 3: 4}.get(zi, 4)
    cost = base * mult // 2
    if w > 30000:
        cost += 2500
    return cost


# 3. mask_account -- 3 decisions
def mask_account(acct):
    if acct is None:
        return None
    s = re.sub(r'[^A-Za-z0-9]', '', str(acct))
    n = len(s)
    if n <= 4:
        return '*' * n
    return '*' * (n - 4) + s[-4:].upper()


# 4. grade_letter -- 3 decisions
def grade_letter(score):
    x = _num(score)
    if x is None:
        return None
    if x < 0 or x > 100:
        return None
    r = int(math.floor(x + 0.5))
    if r >= 97:
        return 'A+'
    if r >= 90:
        return 'A'
    if r >= 80:
        return 'B'
    if r >= 70:
        return 'C'
    if r >= 60:
        return 'D'
    return 'F'


# 5. fiscal_quarter -- 3 decisions
def fiscal_quarter(d):
    if d is None:
        return None
    s = str(d)[:10].replace('/', '-')
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', s)
    if not m:
        return 'FY??'
    try:
        dt = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return 'FY??'
    if dt.month >= 4:
        fy, q = dt.year + 1, (dt.month - 4) // 3 + 1
    else:
        fy, q = dt.year, (dt.month + 8) // 3 + 1
    return 'FY%02dQ%d' % (fy % 100, q)


# 6. loyalty_tier -- 2 decisions
def loyalty_tier(points, years):
    p = _num(points)
    if p is None:
        return None
    y = _num(years)
    if y is None:
        y = 0
    idx = 0 if p < 1000 else 1 if p < 5000 else 2 if p < 20000 else 3
    up = max(0, int(math.floor(y))) // 3
    idx = min(3, idx + up)
    return ['BRONZE', 'SILVER', 'GOLD', 'PLATINUM'][idx]


# 7. pad_code -- 2 decisions
def pad_code(code, width):
    if code is None:
        return None
    w = _num(width)
    if w is None:
        return None
    w = int(math.floor(w))
    if w <= 0:
        return ''
    if isinstance(code, float) and code == int(code):
        code = int(code)
    digits = re.sub(r'\D', '', str(code))
    if len(digits) <= w:
        return digits.zfill(w)
    return digits[-w:]


# 8. biz_days_add -- 2 decisions
def _is_bd(d):
    return d.weekday() < 5 and (d.month, d.day) not in ((12, 25), (1, 1))


def biz_days_add(start, n):
    if start is None:
        return None
    s = str(start)
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', s)
    k = _num(n)
    if not m or k is None or abs(k) > 100000:
        return None
    try:
        d = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        k = int(k)
        if k == 0:
            while not _is_bd(d):
                d += datetime.timedelta(days=1)
            return d.isoformat()
        step = datetime.timedelta(days=1 if k > 0 else -1)
        left = abs(k)
        while left:
            d += step
            if _is_bd(d):
                left -= 1
        return d.isoformat()
    except (ValueError, OverflowError):
        return None


# 9. tip_split -- 1 decision
def tip_split(total_cents, people):
    t, p = _num(total_cents), _num(people)
    if t is None or p is None or p <= 0:
        return None
    return _ceil_frac(Fraction(t) * 118 / (100 * Fraction(p)))


# 10. aggregate -- 1 decision
class MidOrderValue:
    def __init__(self):
        self.vals = []

    def step(self, value):
        if isinstance(value, (int, float)) and not isinstance(value, bool) \
                and math.isfinite(value):
            self.vals.append(value)

    def finalize(self):
        if not self.vals:
            return None
        v = sorted(self.vals)
        return v[(len(v) - 1) // 2]


SPEC = {
    'late_fee': 'late_fee(balance_cents, days_late): Late fee in cents charged on an overdue invoice, given its unpaid balance in cents and how many days it is overdue.',
    'ship_cost': 'ship_cost(weight_g, zone): Shipping charge in cents for a parcel, from its weight in grams and destination zone number.',
    'mask_account': 'mask_account(account): Masks a customer account number for display on statements, hiding everything except the end.',
    'grade_letter': 'grade_letter(score): Converts a numeric exam score from 0 to 100 into a letter grade.',
    'fiscal_quarter': 'fiscal_quarter(date): Fiscal-year and quarter label for a calendar date given as YYYY-MM-DD.',
    'loyalty_tier': 'loyalty_tier(points, years): Customer loyalty tier name from the points balance and years of membership.',
    'pad_code': 'pad_code(code, width): Formats a numeric code as a fixed-width, zero-padded string for legacy systems.',
    'biz_days_add': 'biz_days_add(start_date, n): Date reached by adding n business days to a YYYY-MM-DD date.',
    'tip_split': 'tip_split(total_cents, people): Amount in cents each person pays when a bill including the tip is split evenly.',
    'mid_order_value': 'mid_order_value(amount): Middle order value of a group of orders, ignoring missing amounts.',
}

SCALARS = {
    'late_fee': (late_fee, 2),
    'ship_cost': (ship_cost, 2),
    'mask_account': (mask_account, 1),
    'grade_letter': (grade_letter, 1),
    'fiscal_quarter': (fiscal_quarter, 1),
    'loyalty_tier': (loyalty_tier, 2),
    'pad_code': (pad_code, 2),
    'biz_days_add': (biz_days_add, 2),
    'tip_split': (tip_split, 2),
}

AGGREGATE = ('mid_order_value', MidOrderValue)

TYPICAL = {
    'late_fee': [(50000, 15), (100000, 30), (75000, 45), (120000, 60), (30000, 20)],
    'ship_cost': [(1000, 1), (2000, 2), (3000, 3), (5000, 1), (4000, 2)],
    'mask_account': [('1234567890123456',), ('9876543210',), ('00112233',), ('555566667777',), (4455667788,)],
    'grade_letter': [(95,), (85,), (75,), (65,), (30,), (92,)],
    'fiscal_quarter': [('2026-04-15',), ('2026-08-01',), ('2026-11-30',), ('2027-02-10',), ('2026-01-20',)],
    'loyalty_tier': [(500, 0), (2500, 1), (8000, 2), (30000, 0), (200, 2)],
    'pad_code': [('42', 5), (7, 3), ('1234', 6), (905, 4)],
    'biz_days_add': [('2026-11-02', 1), ('2026-11-02', 5), ('2026-11-04', 3), ('2026-11-06', 1), ('2026-11-10', -2)],
    'tip_split': [(10000, 2), (5000, 1), (20000, 4), (8500, 5), (30000, 3)],
}

EDGE = {
    'late_fee': [(50000, 10), (50000, 11), (25001, 30), (10000, 30), (500000, 30), (None, 30), (-500, 30), (50000, None)],
    'ship_cost': [(0, 1), (-5, 2), (1, 1), (1001, 1), (30000, 2), (30001, 2), (2500, 5), (2500, None)],
    'mask_account': [('1234-5678-9012-3456',), ('1234 5678',), ('abcd1234efgh',), ('1234',), ('12',), ('---',), (None,), (1234567890,)],
    'grade_letter': [(89.5,), (89.4,), (96.5,), (96.4,), (100,), (100.4,), (-1,), (0,), (None,), ('abc',)],
    'fiscal_quarter': [('2026-04-01',), ('2026-03-31',), ('2026-02-30',), ('2026-13-01',), ('2026-04-15T08:30:00',), ('2026-04-15 08:30',), ('2026/07/04',), ('hello',), (None,), (20260415,)],
    'loyalty_tier': [(999, 0), (1000, 0), (5000, 0), (20000, 0), (2500, 3), (30000, 9), (1000, None), (None, 5), (500, 5.9), (-10, 0)],
    'pad_code': [('12345678', 5), ('AB-12', 5), ('', 4), ('42', 0), (42.0, 4), (42.5, 6), ('9', -2), (None, 3), ('7', None), ('123456', 6)],
    'biz_days_add': [('2026-12-24', 1), ('2026-12-31', 1), ('2026-11-07', 0), ('2026-11-09', 0), ('2026-11-07', 1), ('2026-12-25', 0), ('2026-11-10', -5), ('2026-02-30', 1), ('2026-11-02', None)],
    'tip_split': [(10001, 2), (1, 3), (0, 2), (5000, 0), (5000, -1), (None, 2), (5000, None), (12345, 7)],
}

AGG_TYPICAL = [[1, 2, 3], [5, 1, 9, 7, 3], [10, 20, 20, 30], [4, None, 8, 6]]
AGG_EDGE = [[1, 2, 3, 4], [], [None, None], [5], [3, None, 1, None, 2],
            ['a', 4, '7', 2], [1.5, 2.5, 0.5, 3.5], [10, 10, 20, 30, 40, 50]]

DECISIONS = {
    'late_fee': ['grace period of 10 days', 'fee rounded up to whole cent', 'fee capped at 5000', 'minimum fee 500'],
    'ship_cost': ['billed per started kg', 'unknown zone priced as zone 3', 'overweight surcharge above 30kg', 'non-positive weight costs 0'],
    'mask_account': ['separators stripped first', 'length<=4 fully masked', 'visible tail uppercased'],
    'grade_letter': ['score rounded half up before cutoffs', 'out-of-range score is NULL', 'A+ from 97'],
    'fiscal_quarter': ['unparseable/invalid date gives FY??', 'time suffix ignored', 'slash separators accepted'],
    'loyalty_tier': ['one tier up per 3 full years', 'NULL years treated as 0'],
    'pad_code': ['too-long code keeps rightmost digits', 'non-digits removed'],
    'biz_days_add': ['Dec 25 and Jan 1 are non-business days', 'n=0 rolls forward to next business day'],
    'tip_split': ['per-person share rounded up'],
    'mid_order_value': ['even count returns lower middle value'],
}

DECISION_EXAMPLES = {
    'late_fee': [(80000, 3), (30001, 40), (900000, 90), (1000, 25)],
    'ship_cost': [(1200, 1), (2000, 9), (35000, 1), (0, 3)],
    'mask_account': [('9876-5432-1098',), ('987',), ('ab12cd34ef',)],
    'grade_letter': [(79.5,), (105,), (98,)],
    'fiscal_quarter': [('2026-06-31',), ('2027-01-05T23:59:59',), ('2026/11/20',)],
    'loyalty_tier': [(1500, 6), (7000, None)],
    'pad_code': [('987654', 4), ('x9-8', 5)],
    'biz_days_add': [('2025-12-31', 1), ('2026-11-08', 0)],
    'tip_split': [(7777, 3)],
    'mid_order_value': [[10, 40, 20, 30]],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, n) in SCALARS.items():
        con.create_function(name, n, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con
