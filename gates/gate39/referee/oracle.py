import math
import re
import sqlite3
from datetime import date, timedelta
from fractions import Fraction


def _num(x):
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        v = x
    elif isinstance(x, str):
        s = x.strip()
        if '_' in s:
            return None
        try:
            v = int(s)
        except ValueError:
            try:
                v = float(s)
            except ValueError:
                return None
    else:
        return None
    if isinstance(v, float) and not math.isfinite(v):
        return None
    return v


# ---------------------------------------------------------------- scalars

def late_fee(amount_cents, days_late):
    a, d = _num(amount_cents), _num(days_late)
    if a is None or d is None:
        return None
    if d <= 5 or a <= 0:
        return 0
    months = math.ceil(Fraction(d) / 30)
    fee = math.ceil(Fraction(a) * 2 * months / 100)
    return min(max(fee, 250), 5000)


_ZONES = {'A': 500, 'B': 800, 'C': 1200}


def ship_cost(weight_g, zone):
    w = _num(weight_g)
    if w is None or zone is None:
        return None
    base = _ZONES.get(str(zone).upper(), 1200)
    extra = max(0, math.ceil((Fraction(w) - 500) / 500)) * 100
    cost = base + extra
    if w > 20000:
        cost += 2500
    return cost


def loyalty_tier(points):
    p = _num(points)
    if p is None:
        return None
    if p < 0:
        return 'void'
    if p >= 20000:
        return 'platinum'
    if p >= 5000:
        return 'gold'
    if p >= 1000:
        return 'silver'
    return 'bronze'


_ISO = re.compile(r'\d{4}-\d{2}-\d{2}')


def _parse_iso(s):
    if not isinstance(s, str) or not _ISO.fullmatch(s):
        return None
    try:
        return date(int(s[:4]), int(s[5:7]), int(s[8:10]))
    except ValueError:
        return None


def fiscal_quarter(d):
    if d is None:
        return None
    if isinstance(d, int) and not isinstance(d, bool):
        s = str(d)
        if len(s) != 8:
            return 'n/a'
        try:
            dt = date(int(s[:4]), int(s[4:6]), int(s[6:8]))
        except ValueError:
            return 'n/a'
    else:
        dt = _parse_iso(d)
        if dt is None:
            return 'n/a'
    if dt.year < 2000:
        return 'legacy'
    fy = dt.year + 1 if dt.month >= 4 else dt.year
    q = ((dt.month - 4) % 12) // 3 + 1
    return 'FY%02d-Q%d' % (fy % 100, q)


_HOLIDAYS = {(1, 1), (12, 25), (12, 26)}


def _is_biz(d):
    return d.weekday() < 5 and (d.month, d.day) not in _HOLIDAYS


def biz_days_add(start_date, n):
    if start_date is None:
        return None
    k = _num(n)
    if k is None:
        return None
    dt = _parse_iso(start_date)
    if dt is None:
        return ''
    k = int(k)
    if abs(k) > 3650:
        return ''
    try:
        if k == 0:
            while not _is_biz(dt):
                dt += timedelta(days=1)
            return dt.isoformat()
        step = 1 if k > 0 else -1
        left = abs(k)
        while left:
            dt += timedelta(days=step)
            if _is_biz(dt):
                left -= 1
        return dt.isoformat()
    except OverflowError:
        return ''


_OCR = {'O': '0', 'o': '0', 'I': '1', 'l': '1'}
_LETTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'


def normalize_sku(raw):
    if raw is None:
        return None
    s = str(raw).strip()
    if len(s) < 2 or s[0] not in _LETTERS or s[1] not in _LETTERS:
        return 'XX-0000'
    digits = ''
    for ch in s[2:]:
        if ch in '- ':
            continue
        ch = _OCR.get(ch, ch)
        if ch in '0123456789':
            digits += ch
        else:
            return 'XX-0000'
    if not digits:
        return 'XX-0000'
    return '%s-%s' % (s[:2].upper(), digits[-4:].zfill(4))


def mask_card(card):
    if card is None:
        return None
    s = str(card).replace(' ', '').replace('-', '')
    if not (12 <= len(s) <= 19) or any(c not in '0123456789' for c in s):
        return 'INVALID'
    return '*' * (len(s) - 4) + s[-4:]


def nps_class(score):
    s = _num(score)
    if s is None:
        return None
    r = math.floor(Fraction(s) + Fraction(1, 2))
    if r < 0 or r > 10:
        return 'invalid'
    if r <= 6:
        return 'detractor'
    if r <= 8:
        return 'passive'
    return 'promoter'


def split_bill(total_cents, people):
    t, p = _num(total_cents), _num(people)
    if t is None or p is None:
        return None
    p = int(p)
    if p < 1:
        return None
    return math.ceil(Fraction(t) / p)


# -------------------------------------------------------------- aggregate

class MidValue:
    def __init__(self):
        self.vals = []

    def step(self, value):
        v = _num(value)
        if v is not None:
            self.vals.append(v)

    def finalize(self):
        if not self.vals:
            return None
        v = sorted(self.vals)
        n = len(v)
        return v[n // 2] if n % 2 else v[n // 2 - 1]


# ------------------------------------------------------------------ module

SPEC = {
    'late_fee': 'late_fee(amount_cents, days_late): late fee in cents charged on an overdue invoice.',
    'ship_cost': 'ship_cost(weight_g, zone): shipping charge in cents for a parcel of a given weight sent to a delivery zone.',
    'loyalty_tier': "loyalty_tier(points): membership tier name for a customer's point balance.",
    'fiscal_quarter': 'fiscal_quarter(day): fiscal year and quarter label for a calendar date.',
    'biz_days_add': 'biz_days_add(start_date, n): the date n business days after (or before) a start date.',
    'normalize_sku': 'normalize_sku(raw): converts a product code typed in by staff to the catalog format.',
    'mask_card': 'mask_card(card): masks a payment card number for display on receipts.',
    'nps_class': 'nps_class(score): classifies a 0-10 survey score as detractor, passive or promoter.',
    'split_bill': 'split_bill(total_cents, people): the amount in cents each person pays when a bill is divided evenly.',
    'mid_value': "mid_value(value): the median of a group's numeric values.",
}

SCALARS = {
    'late_fee': (late_fee, 2),
    'ship_cost': (ship_cost, 2),
    'loyalty_tier': (loyalty_tier, 1),
    'fiscal_quarter': (fiscal_quarter, 1),
    'biz_days_add': (biz_days_add, 2),
    'normalize_sku': (normalize_sku, 1),
    'mask_card': (mask_card, 1),
    'nps_class': (nps_class, 1),
    'split_bill': (split_bill, 2),
}

AGGREGATE = ('mid_value', MidValue)

TYPICAL = {
    'late_fee': [(20000, 10), (50000, 45), (100000, 20), (30000, 70), (150000, 30)],
    'ship_cost': [(400, 'A'), (1000, 'B'), (1500, 'C'), (2500, 'A'), (3000, 'B')],
    'loyalty_tier': [(100,), (2500,), (8000,), (50000,)],
    'fiscal_quarter': [('2024-05-10',), ('2024-08-01',), ('2024-11-20',), ('2025-02-14',), ('2025-04-02',)],
    'biz_days_add': [('2024-03-04', 3), ('2024-03-08', 1), ('2024-03-06', 10), ('2024-03-15', -2)],
    'normalize_sku': [('ab1234',), ('cd-77',), ('XY 5',), ('mn-0420',), (' pq-310 ',)],
    'mask_card': [('4111111111111111',), ('5500000000000004',), ('6011000990139424',), ('3530111333300000',)],
    'nps_class': [(3,), (7,), (8,), (9,), (10,), (0,), (6,)],
    'split_bill': [(10000, 4), (9000, 3), (500, 5), (12000, 2), (7777, 1)],
}

EDGE = {
    'late_fee': [(20000, 5), (20000, 6), (500, 10), (1000000, 10), (15001, 10),
                 (0, 10), (-500, 10), (20000, 31), (None, 10), (20000, 'abc')],
    'ship_cost': [(501, 'A'), (0, 'B'), (1000, 'b'), (1000, 'X'), (1000, ' B'),
                  (20000, 'A'), (20001, 'A'), (35000, 'c'), (None, 'A'), (1000, None)],
    'loyalty_tier': [(0,), (999,), (1000,), (4999,), (5000,), (-1,),
                     ('12000',), ('abc',), (None,), (19999.9,)],
    'fiscal_quarter': [('2024-02-30',), ('garbage',), ('1999-12-31',), ('2000-01-01',),
                       ('2024-03-31',), ('2024-04-01',), (20250101,), (None,),
                       ('2024-05-10 13:45:00',), ('2024/05/10',)],
    'biz_days_add': [('2024-12-20', 5), ('2024-12-31', 1), ('2024-03-10', 0), ('2024-03-12', 0),
                     ('2024-03-09', -1), ('bad', 1), ('2024-02-30', 1), (None, 1),
                     ('2023-12-22', 1), ('2025-01-02', -1)],
    'normalize_sku': [('ab-12345',), ('xy-1O5',), ('12-345',), ('ab',), (None,),
                      ('abc123',), ('cd-l0l',), ('ef-00012',), ('gh 7 7',), ('',)],
    'mask_card': [('4111 1111 1111 1111',), ('1234',), ('12345678901234567890',),
                  ('4111-1111-1111-111a',), ('',), (None,), (4111111111111111,),
                  ('123456789012',), ('1234567890123456789',)],
    'nps_class': [(6.5,), (8.6,), (0,), (-1,), (10.5,), (10,), (6,), (None,), ('9',), (-0.4,)],
    'split_bill': [(100, 3), (1, 2), (0, 5), (100, 0), (100, -2), (None, 2),
                   (100, 2.7), (99999, 7), (-100, 3), (10, 'x')],
}

AGG_TYPICAL = [[3, 1, 2], [10, 50, 20, 40, 30], [5, 5, 5], [1.5, 2.5, 0.5]]
AGG_EDGE = [[1, 2, 3, 4], [None, None], [], [4, None, 8], [2.5, 1.5],
            [10, 20, 30, 40, 50, 60], [3, 'x', 1]]

DECISIONS = {
    'late_fee': ['grace period of 5 days', 'minimum fee 250', 'maximum fee 5000', 'fractional cents round up'],
    'ship_cost': ['partial 500g step rounds up', 'zone letter case-insensitive (no trim)',
                  'unknown zone priced as zone C', 'heavy surcharge above 20000g'],
    'loyalty_tier': ['tier thresholds inclusive', 'negative points -> void'],
    'fiscal_quarter': ['invalid date -> n/a', 'before 2000 -> legacy', 'integer YYYYMMDD accepted'],
    'biz_days_add': ['holidays Jan 1, Dec 25, Dec 26 skipped', 'n=0 rolls forward to business day',
                     'invalid date -> empty string'],
    'normalize_sku': ['numeric part keeps last 4 digits', 'unparseable -> XX-0000', 'O/o->0, I/l->1 in numeric part'],
    'mask_card': ['spaces and dashes stripped', 'must be 12-19 digits else INVALID'],
    'nps_class': ['fractional scores round half up', 'out of 0-10 after rounding -> invalid'],
    'split_bill': ['remainder rounds share up'],
    'mid_value': ['even count -> lower middle value'],
}

DECISION_EXAMPLES = {
    'late_fee': [(30000, 4), (800, 20), (900000, 40), (15003, 12)],
    'ship_cost': [(620, 'A'), (1500, 'c'), (1000, 'Z9'), (25000, 'A')],
    'loyalty_tier': [(20000,), (-0.5,)],
    'fiscal_quarter': [('2024-13-45',), ('1998-06-01',), (20240915,)],
    'biz_days_add': [('2024-12-24', 1), ('2024-03-16', 0), ('2024-02-31', 2)],
    'normalize_sku': [('ab-1234567',), ('99-AB',), ('ij-4O2',)],
    'mask_card': [('3782 8224 6310 005',), ('12345678901',)],
    'nps_class': [(8.5,), (11,)],
    'split_bill': [(1000, 3)],
    'mid_value': [[8, 2, 6, 4]],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, n) in SCALARS.items():
        con.create_function(name, n, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con
