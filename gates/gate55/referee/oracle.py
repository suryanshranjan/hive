import math
import re
import sqlite3
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from datetime import date

DIGITS = '0123456789'


def _num(v):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return v


def _text(v):
    return None if v is None else str(v)


# ---- 1. late_fee -----------------------------------------------------------
def late_fee(amount, days):
    a, d = _num(amount), _num(days)
    if a is None or d is None:
        return None
    if a <= 0 or d <= 5:
        return 0
    periods = math.ceil(Fraction(d) / 30)
    fee = math.ceil(Fraction(a) * 2 * periods / 100)
    fee = max(fee, 500)
    cap = math.floor(Fraction(a) / 5)
    return int(min(fee, cap))


# ---- 2. make_slug ----------------------------------------------------------
_STOP = {'the', 'a', 'an', 'of'}


def make_slug(title, maxlen):
    t, n = _text(title), _num(maxlen)
    if t is None or n is None:
        return None
    t = t.replace('&', ' and ').lower()
    words = [w for w in re.findall(r'[a-z0-9]+', t) if w not in _STOP]
    s = '-'.join(words)
    n = max(0, int(n))
    if len(s) > n:
        cut = s[:n]
        if s[n] != '-' and '-' in cut:
            cut = cut[:cut.rfind('-')]
        s = cut.strip('-')
    return s or 'untitled'


# ---- 3. loyalty_tier -------------------------------------------------------
def loyalty_tier(points):
    p = _num(points)
    if p is None:
        return None
    if p < 0:
        return 'suspended'
    if p < 1000:
        return 'bronze'
    if p < 5000:
        return 'silver'
    if p < 20000:
        return 'gold'
    return 'platinum'


# ---- 4. fiscal_label -------------------------------------------------------
_DATE_RE = re.compile(r'^(\d{4})-(\d{2})-(\d{2})(?:[T ]\d{2}:\d{2}(?::\d{2})?)?$')


def fiscal_label(d):
    s = _text(d)
    if s is None:
        return None
    m = _DATE_RE.match(s.strip())
    if not m:
        return 'INVALID'
    y, mo, dy = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        date(y, mo, dy)
    except ValueError:
        return 'INVALID'
    fy = y + 1 if mo >= 4 else y
    if mo == 3 and dy >= 27:
        return 'FY%d-CLOSE' % fy
    q = ((mo - 4) % 12) // 3 + 1
    return 'FY%d-Q%d' % (fy, q)


# ---- 5. bulk_price ---------------------------------------------------------
def bulk_price(unit, qty):
    u, q = _num(unit), _num(qty)
    if u is None or q is None:
        return None
    if u <= 0 or q <= 0:
        return 0
    pct = 15 if q >= 100 else 10 if q >= 50 else 5 if q >= 10 else 0
    tot = Fraction(u) * Fraction(q) * (100 - pct) / 100
    total = math.floor(tot / 5 + Fraction(1, 2)) * 5
    return int(max(total, 500))


# ---- 6. isbn_check ---------------------------------------------------------
def isbn_check(code):
    t = _text(code)
    if t is None:
        return None
    digits = [int(c) for c in t if c in DIGITS][:9]
    r = sum((i + 1) * x for i, x in enumerate(digits)) % 11
    return 'X' if r == 10 else str(r)


# ---- 7. meeting_end --------------------------------------------------------
def meeting_end(start, minutes):
    s, m = _text(start), _num(minutes)
    if s is None or m is None:
        return None
    mt = re.match(r'^(\d{2}):(\d{2})$', s.strip())
    if not mt or int(mt.group(1)) > 23 or int(mt.group(2)) > 59:
        return None
    blocks = max(0, math.ceil(Fraction(m) / 15))
    end = int(mt.group(1)) * 60 + int(mt.group(2)) + blocks * 15
    end = min(end, 23 * 60 + 59)
    return '%02d:%02d' % (end // 60, end % 60)


# ---- 8. pct_change ---------------------------------------------------------
def pct_change(old, new):
    o, n = _num(old), _num(new)
    if o is None or n is None:
        return None
    if o == 0:
        return 0.0
    return round((n - o) / o * 100, 1) + 0.0


# ---- 9. phone_fmt ----------------------------------------------------------
def phone_fmt(raw):
    t = _text(raw)
    if t is None:
        return None
    d = [c for c in t if c in DIGITS]
    if len(d) != 10:
        return t
    return '(%s) %s-%s' % (''.join(d[:3]), ''.join(d[3:6]), ''.join(d[6:]))


# ---- 10. avg_rating (aggregate) -------------------------------------------
class AvgRating:
    def __init__(self):
        self.vals = []

    def step(self, value):
        if _num(value) is not None and 1 <= value <= 5:
            self.vals.append(Decimal(str(value)))

    def finalize(self):
        if not self.vals:
            return None
        s = sorted(self.vals)
        if len(s) >= 5:
            s = s[1:-1]
        avg = sum(s) / len(s)
        return float(avg.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))


SPEC = {
    'late_fee': 'late_fee(amount_cents, days_late): late-payment fee, in cents, charged on an overdue invoice.',
    'make_slug': 'make_slug(title, maxlen): URL-friendly slug for a page or product title, at most maxlen characters long.',
    'loyalty_tier': 'loyalty_tier(points): customer loyalty tier name for a points balance.',
    'fiscal_label': 'fiscal_label(date_text): fiscal-year and quarter label for an ISO date (YYYY-MM-DD).',
    'bulk_price': 'bulk_price(unit_cents, qty): order total in cents for qty units at a unit price, with volume discounts.',
    'isbn_check': 'isbn_check(code): check digit for a 9-digit catalogue code, ISBN-10 style.',
    'meeting_end': 'meeting_end(start, minutes): end time (HH:MM, 24-hour) of a room booking that begins at start and lasts the given minutes.',
    'pct_change': 'pct_change(old, new): percentage change from old to new, rounded to 1 decimal.',
    'phone_fmt': 'phone_fmt(raw): formats a North American phone number as (AAA) EEE-NNNN.',
    'avg_rating': 'avg_rating(rating): average customer rating on the 1-to-5 scale over a group of rows.',
}

SCALARS = {
    'late_fee': (late_fee, 2),
    'make_slug': (make_slug, 2),
    'loyalty_tier': (loyalty_tier, 1),
    'fiscal_label': (fiscal_label, 1),
    'bulk_price': (bulk_price, 2),
    'isbn_check': (isbn_check, 1),
    'meeting_end': (meeting_end, 2),
    'pct_change': (pct_change, 2),
    'phone_fmt': (phone_fmt, 1),
}

AGGREGATE = ('avg_rating', AvgRating)

TYPICAL = {
    'late_fee': [(50000, 10), (50000, 40), (120000, 31), (80000, 90), (200000, 7)],
    'make_slug': [('Summer Sale 2024', 40), ('Hello, World!', 30), ('Q3  Results -- Draft', 50), ('Best Pizza in Town', 60)],
    'loyalty_tier': [(100,), (800,), (1500,), (3200,), (7500,), (15000,)],
    'fiscal_label': [('2024-05-10',), ('2024-08-01',), ('2024-11-15',), ('2025-02-14',), ('2025-04-02',)],
    'bulk_price': [(1000, 5), (1000, 12), (2000, 60), (1500, 100)],
    'isbn_check': [('030640615',), ('013110362',), ('052152079',), ('201896834',)],
    'meeting_end': [('09:00', 30), ('13:15', 45), ('08:30', 90), ('10:00', 60)],
    'pct_change': [(100, 110), (200, 150), (80, 100), (3, 4)],
    'phone_fmt': [('5551234567',), ('555-123-4567',), ('(555) 123 4567',), ('555.987.6543',)],
}

EDGE = {
    'late_fee': [(50000, 5), (50000, 6), (50000, 31), (20000, 12), (50000, 365), (50010, 10),
                 (1000, 100), (0, 10), (None, 10), (50000, None)],
    'make_slug': [('A', 10), ('The Quick Brown Fox', 12), ('Fish & Chips', 100), ("Tom & Jerry's Big Adventure", 15),
                  ('abcdefghijkl', 5), ('one two', 3), ('   ', 10), (None, 10), ('Hello', None)],
    'loyalty_tier': [(0,), (999,), (1000,), (4999.5,), (5000,), (19999,), (20000,), (-1,), (None,), ('abc',)],
    'fiscal_label': [('2025-03-26',), ('2025-03-27',), ('2025-03-31',), ('2024-02-29',), ('2023-02-29',),
                     ('not a date',), ('2024-05-10 14:00',), (None,), ('2024-04-01',), ('',)],
    'bulk_price': [(199, 1), (1000, 10), (333, 10), (99, 10), (1000, 49), (1000, 50), (0, 5),
                   (1000, 0), (None, 3), (1000, None)],
    'isbn_check': [('',), ('abc',), ('12345',), ('0-306-40615-2',), ('ISBN 0 306 40615',), ('9780306406157',),
                   ('000000010',), (None,), (306406152,)],
    'meeting_end': [('09:00', 1), ('09:00', 0), ('23:45', 15), ('22:00', 90), ('25:00', 30), ('abc', 30),
                    (None, 30), ('09:00', None), ('09:00', -30), ('09:07', 14.5)],
    'pct_change': [(0, 5), (0, 0), (-50, -25), (None, 1), (1, None), (100, 100), (1, 3), (7, 8), (-5, -5)],
    'phone_fmt': [('+1 555 123 4567',), ('555-123-4567 ext 89',), ('',), (None,), ('(555)123.4567',),
                  ('abcdefghij',), (5551234567,), ('1-555-123-4567',), ('12345',)],
}

AGG_TYPICAL = [[4, 5, 3], [5, 5, 4, 4], [2, 3, 4], [5]]

AGG_EDGE = [[1, 2, 2], [0, 5, 5], [6, 3], [1, 5, 3, 4, 2], [None, None], [], [1, 1, 1, 5, 5, 5],
            [4.5, 'x', 3]]

DECISIONS = {
    'late_fee': ['grace period of days_late', 'minimum fee', 'cap as share of amount', 'fee rounded up to whole cent'],
    'make_slug': ['stopwords dropped', 'ampersand becomes and', 'truncation at word boundary', 'empty slug becomes untitled'],
    'loyalty_tier': ['negative points suspended', 'top tier above 20000'],
    'fiscal_label': ['year-end close label for Mar 27-31', 'time suffix tolerated', 'invalid date gives INVALID'],
    'bulk_price': ['total rounded to nearest 5 cents', 'minimum order total of 500'],
    'isbn_check': ['remainder 10 gives X', 'non-digits ignored', 'only first 9 digits used'],
    'meeting_end': ['duration rounded up to 15 minutes', 'end capped at 23:59'],
    'pct_change': ['old of zero gives 0.0'],
    'phone_fmt': ['not exactly 10 digits returned unchanged'],
    'avg_rating': ['out-of-range or non-numeric ratings ignored', 'one high and one low dropped when 5+ ratings',
                   'rounded to 1 decimal half up'],
}

DECISION_EXAMPLES = {
    'late_fee': [(50000, 3), (10000, 10), (50000, 400), (50001, 10)],
    'make_slug': [('The Art of War', 50), ('Salt & Pepper', 50), ('Quarterly Revenue Report', 20), ('!!!', 30)],
    'loyalty_tier': [(-50,), (75000,)],
    'fiscal_label': [('2025-03-30',), ('2024-06-15T08:30:00',), ('2024-13-45',)],
    'bulk_price': [(1001, 12), (100, 3)],
    'isbn_check': [('123456789',), ('0-306-40615',), ('0306406159999',)],
    'meeting_end': [('10:00', 20), ('23:00', 120)],
    'pct_change': [(0, 17.5)],
    'phone_fmt': [('555-1234',)],
    'avg_rating': [[9, -1, 4, 2], [1, 5, 4, 4, 4], [4, 4, 5]],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, n) in SCALARS.items():
        con.create_function(name, n, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con
