import math
import re
import sqlite3
import datetime
from fractions import Fraction


def _num(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    if isinstance(x, float) and not math.isfinite(x):
        return None
    return x


def _fr(x):
    return Fraction(x) if isinstance(x, int) else Fraction(repr(x))


def _ceil(fr):
    return -((-fr.numerator) // fr.denominator)


def _floor(fr):
    return fr.numerator // fr.denominator


# ---------------- scalars ----------------
def late_fee(amount, days):
    a, d = _num(amount), _num(days)
    if a is None or d is None:
        return None
    if d <= 3:
        return 0
    raw = _fr(a) * _fr(d) * 5 / 1000
    cap = _fr(a) / 4
    return _ceil(min(raw, cap))


def mask_card(card):
    if card is None:
        return None
    digits = re.sub(r'\D', '', str(card))
    if len(digits) < 12:
        return 'INVALID'
    return digits[:6] + '*' * (len(digits) - 10) + digits[-4:]


_RATE = {1: 100, 2: 180, 3: 260}


def ship_cost(weight, zone):
    w, z = _num(weight), _num(zone)
    if w is None or z is None:
        return None
    if w <= 0:
        return 0
    units = _ceil(_fr(w) / 500)
    zi = int(z) if z == int(z) else None
    rate = _RATE.get(zi, _RATE[3])
    cost = 300 + units * rate
    if w > 20000:
        cost += 2000
    return cost


def letter_grade(score):
    s = _num(score)
    if s is None:
        return None
    if s < 0 or s > 100:
        return 'X'
    r = _floor(_fr(s) + Fraction(1, 2))
    if r >= 90:
        return 'A'
    if r >= 80:
        return 'B'
    if r >= 70:
        return 'C'
    if r >= 60:
        return 'D'
    return 'F'


def _is_bd(d):
    return d.weekday() < 5 and not ((d.month == 12 and d.day == 25) or (d.month == 1 and d.day == 1))


def biz_days_add(start, n):
    if start is None or n is None:
        return None
    k = _num(n)
    if k is None:
        return None
    if not isinstance(start, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', start):
        return 'BAD_DATE'
    try:
        d = datetime.datetime.strptime(start, '%Y-%m-%d').date()
        k = int(k)
        while d.weekday() >= 5:
            d += datetime.timedelta(days=1)
        step = 1 if k >= 0 else -1
        left = abs(k)
        while left > 0:
            d += datetime.timedelta(days=step)
            if _is_bd(d):
                left -= 1
        return d.isoformat()
    except (ValueError, OverflowError):
        return 'BAD_DATE'


def ticket_priority(severity, hours):
    s, h = _num(severity), _num(hours)
    if s is None or h is None:
        return None
    base = int(s) if (s == int(s) and 1 <= s <= 4) else 4
    if h >= 48:
        base = max(1, base - 1)
    return 'P%d' % base


def pct_change(old, new):
    o, n = _num(old), _num(new)
    if o is None or n is None:
        return None
    if o == 0:
        return 999.0
    return float(round((n - o) / o * 100, 1))


def slug(title):
    if title is None:
        return None
    s = ''.join(c for c in str(title).lower() if ord(c) < 128)
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    s = s[:30].rstrip('-')
    return s if s else 'n-a'


_MULT = {'basic': Fraction(1), 'silver': Fraction(3, 2), 'gold': Fraction(2)}


def loyalty_points(spend, tier):
    sp = _num(spend)
    if sp is None:
        return None
    t = tier.strip().lower() if isinstance(tier, str) else 'basic'
    m = _MULT.get(t, Fraction(1))
    eff = min(_fr(sp), Fraction(5000))
    return _floor(eff * m)


class AvgRating:
    def __init__(self):
        self.total = Fraction(0)
        self.count = 0

    def step(self, value):
        v = _num(value)
        if v is None:
            return
        self.total += min(max(_fr(v), Fraction(1)), Fraction(5))
        self.count += 1

    def finalize(self):
        if self.count == 0:
            return None
        return float(round(float(self.total / self.count), 2))


SPEC = {
    'late_fee': 'late_fee(amount_cents, days_late): Late-payment fee in cents charged on an overdue invoice.',
    'mask_card': 'mask_card(card_number): Masks a payment card number for safe display on receipts.',
    'ship_cost': 'ship_cost(weight_g, zone): Shipping charge in cents for a parcel of the given weight sent to a delivery zone (1-3).',
    'letter_grade': 'letter_grade(score): Converts a numeric exam score into a letter grade.',
    'biz_days_add': 'biz_days_add(start_date, n): Adds n business days to an ISO date (YYYY-MM-DD) for delivery and SLA planning.',
    'ticket_priority': 'ticket_priority(severity, hours_open): Support ticket priority label (P1 highest to P4 lowest) from severity and age.',
    'pct_change': 'pct_change(old_value, new_value): Percentage change between two metric values for dashboards.',
    'slug': 'slug(title): URL-friendly slug for a page title.',
    'loyalty_points': 'loyalty_points(spend, tier): Loyalty points earned on a purchase for a member tier.',
    'avg_rating': 'avg_rating(rating): Average customer rating (1-5 stars) across a group of reviews.',
}

SCALARS = {
    'late_fee': (late_fee, 2),
    'mask_card': (mask_card, 1),
    'ship_cost': (ship_cost, 2),
    'letter_grade': (letter_grade, 1),
    'biz_days_add': (biz_days_add, 2),
    'ticket_priority': (ticket_priority, 2),
    'pct_change': (pct_change, 2),
    'slug': (slug, 1),
    'loyalty_points': (loyalty_points, 2),
}
AGGREGATE = ('avg_rating', AvgRating)

TYPICAL = {
    'late_fee': [(100000, 5), (20000, 10), (50000, 20), (80000, 7)],
    'mask_card': [('4111111111111111',), ('5500000000000004',), ('378282246310005',), ('6011111111111117',)],
    'ship_cost': [(500, 1), (1000, 2), (2500, 3), (5000, 1), (10000, 2)],
    'letter_grade': [(95,), (85,), (75,), (65,), (40,), (100,)],
    'biz_days_add': [('2025-03-03', 1), ('2025-03-07', 1), ('2025-03-03', 5), ('2025-03-10', 10), ('2025-03-12', -2)],
    'ticket_priority': [(1, 2), (2, 5), (3, 10), (4, 1), (2, 0)],
    'pct_change': [(100, 150), (200, 150), (80, 100), (50, 50)],
    'slug': [('Hello World',), ('Hello, World!',), ('Q3 Sales Report 2025',), ('Summer_Sale 50% Off',)],
    'loyalty_points': [(120, 'gold'), (80.0, 'silver'), (45, 'basic'), (200, 'gold')],
}

EDGE = {
    'late_fee': [(100000, 3), (100000, 4), (100000, 0), (1001, 10), (1000, 100),
                 (100000, 60), (100000, 50), (None, 5), (100000, None), (100000, -5)],
    'mask_card': [('4111 1111 1111 1111',), ('4111-1111-1111-1111',), ('12345678901',),
                  ('123456789012',), ('',), (None,), ('abcd',), (4111111111111111,)],
    'ship_cost': [(501, 2), (1, 1), (20000, 1), (20001, 2), (1000, 0), (1000, 9),
                  (0, 1), (-5, 2), (None, 1), (1000, None)],
    'letter_grade': [(89.5,), (89.4,), (59.5,), (59.4,), (100.4,), (-1,), (100,), (0,), (None,), (99.6,)],
    'biz_days_add': [('2025-03-08', 0), ('2025-03-08', 1), ('2025-03-09', -1), ('2025-12-24', 1),
                     ('2025-12-31', 1), ('2025-03-03', 0), ('2025-02-30', 1), ('garbage', 2),
                     (None, 1), ('2025-12-26', -1)],
    'ticket_priority': [(3, 48), (3, 47.9), (1, 100), (2, 200), (4, 72), (0, 1), (7, 10),
                        (5, 60), (None, 5), (2, None)],
    'pct_change': [(0, 5), (0, 0), (0, -3), (-100, -50), (3, 4), (1, 1000000), (None, 5), (5, None)],
    'slug': [('Café Münchën',), ('x' * 40,), ('a' * 29 + ' bbbb',), ('!!!',), ('',), ('   ',),
             ('日本語',), (None,), ('  Spaced   Out  ',)],
    'loyalty_points': [(45, 'silver'), (100, 'GOLD'), (100, ' gold '), (100, 'platinum'), (100, None),
                       (6000, 'gold'), (5000, 'basic'), (0, 'gold'), (None, 'gold'), (19.99, 'basic')],
}

AGG_TYPICAL = [[5, 4, 3], [4, 4, 5, 5], [1, 2, 3, 4, 5], [5, None, 3]]
AGG_EDGE = [[7, 3], [0, 5], [-2, 2.5], [None, None], [], [1, 1, 2], [4.25, 4.5]]

DECISIONS = {
    'late_fee': ['3-day grace period (days<=3 costs nothing)', 'fee capped at 25% of amount', 'fee rounded up to whole cents'],
    'mask_card': ['non-digit separators stripped first', 'fewer than 12 digits -> INVALID'],
    'ship_cost': ['weight rounded up to 500g units', 'unknown zone priced as zone 3',
                  'over 20000g adds 2000 surcharge', 'weight <= 0 costs 0'],
    'letter_grade': ['fractional scores rounded half up before banding', 'score outside 0-100 -> X'],
    'biz_days_add': ['weekend start rolls forward to Monday before counting',
                     'Dec 25 and Jan 1 are skipped as holidays', 'invalid date -> BAD_DATE'],
    'ticket_priority': ['48h or more open escalates one level (not above P1)', 'invalid severity treated as P4'],
    'pct_change': ['old value 0 -> 999.0'],
    'slug': ['truncated to 30 chars, trailing hyphen trimmed', 'non-ASCII characters dropped (not transliterated)',
             "empty result -> 'n-a'"],
    'loyalty_points': ['points rounded down', 'unknown or NULL tier earns as basic',
                       'tier case-insensitive and trimmed', 'spend capped at 5000'],
    'avg_rating': ['out-of-range ratings clamped to 1..5'],
}

DECISION_EXAMPLES = {
    'late_fee': [(100000, 2), (2000, 90), (333, 7)],
    'mask_card': [('3782 822463 10005',), ('1234567',)],
    'ship_cost': [(501, 1), (1000, 7), (20001, 1), (-100, 3)],
    'letter_grade': [(79.5,), (150,)],
    'biz_days_add': [('2025-03-15', 2), ('2026-12-24', 1), ('2025-13-01', 3)],
    'ticket_priority': [(2, 50), (9, 3)],
    'pct_change': [(0, 120)],
    'slug': [('The quick brown fox jumps over the lazy dog',), ('Crème brûlée',), ('?!',)],
    'loyalty_points': [(33, 'silver'), (60, 'vip'), (50, 'Silver'), (7000, 'basic')],
    'avg_rating': [[9, 9, 1]],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, n) in SCALARS.items():
        con.create_function(name, n, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con
