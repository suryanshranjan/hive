import math
import re
import sqlite3
from datetime import date, timedelta
from fractions import Fraction


def _num(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    if isinstance(x, float) and not math.isfinite(x):
        return None
    return x


def _frac(x):
    return Fraction(repr(x)) if isinstance(x, float) else Fraction(x)


# ---------------------------------------------------------------- scalars
def late_fee(balance, days_late):
    b, d = _num(balance), _num(days_late)
    if b is None or d is None:
        return None
    if b <= 0 or d <= 3:
        return 0.0
    weeks = math.ceil(d / 7)
    fee = b * 0.01 * weeks
    fee = max(fee, 5.0)
    fee = min(fee, b * 0.2)
    return round(fee, 2)


_TIME = re.compile(r'^\s*(\d{1,2}):(\d{2})\s*$')


def meeting_end(start_time, minutes):
    m = _num(minutes)
    if not isinstance(start_time, str) or m is None:
        return None
    t = _TIME.match(start_time)
    if not t:
        return None
    h, mi = int(t.group(1)), int(t.group(2))
    if h > 23 or mi > 59:
        return None
    m = math.ceil(m)
    if m <= 0:
        m = 15
    m = min(m, 480)
    m = -(-m // 15) * 15
    total = h * 60 + mi + m
    day, rem = divmod(total, 1440)
    out = '%02d:%02d' % (rem // 60, rem % 60)
    return out + ('+1' if day >= 1 else '')


def ship_cost(weight_kg, zone):
    w, z = _num(weight_kg), _num(zone)
    if w is None or z is None or w <= 0:
        return None
    kg = math.ceil(w)
    mult = {1: 1.0, 2: 1.5}.get(z, 2.0) if z in (1, 2, 3) else 2.0
    cost = (4.0 + 1.5 * kg) * mult
    if w > 20:
        cost += 25.0
    return round(cost, 2)


def _parse_date(s):
    if not isinstance(s, str):
        return None
    if len(s) < 10 or not re.match(r'^\d{4}-\d{2}-\d{2}$', s[:10]):
        return None
    if len(s) > 10 and s[10] not in ' T':
        return None
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def _bd(a, b):
    n = (b - a).days
    full, rem = divmod(n, 7)
    cnt = full * 5
    for i in range(rem):
        if (a + timedelta(days=full * 7 + i)).weekday() < 5:
            cnt += 1
    for y in range(a.year, b.year + 1):
        for md in ((12, 25), (1, 1)):
            try:
                h = date(y, md[0], md[1])
            except ValueError:
                continue
            if a <= h < b and h.weekday() < 5:
                cnt -= 1
    return cnt


def business_days(start_date, end_date):
    a, b = _parse_date(start_date), _parse_date(end_date)
    if a is None or b is None:
        return None
    if a <= b:
        return _bd(a, b)
    return -_bd(b, a)


def promo_code(code):
    if code is None:
        return None
    if isinstance(code, float) and not math.isfinite(code):
        return None
    s = str(code).strip().replace(' ', '').replace('-', '').upper()
    s = s[:12]
    return s


def mask_card(card_number):
    if card_number is None or isinstance(card_number, bool):
        return None
    if isinstance(card_number, float):
        return None
    d = re.sub(r'\D', '', str(card_number))
    if len(d) < 12:
        return 'INVALID'
    return '*' * (len(d) - 4) + d[-4:]


def split_bill(total, people):
    t, p = _num(total), _num(people)
    if t is None or p is None or t < 0 or p <= 0 or p != int(p):
        return None
    cents = math.ceil(_frac(t) * 100 / int(p))
    return cents / 100


def rating_stars(score, max_score):
    s, m = _num(score), _num(max_score)
    if s is None or m is None or m <= 0 or s < 0 or s > m:
        return None
    x = _frac(s) * 5 / _frac(m)
    return math.floor(x * 2 + Fraction(1, 2)) / 2


def age_band(age):
    a = _num(age)
    if a is None:
        return None
    a = math.floor(a)
    if a < 18:
        return 'minor'
    return '%ds' % (a // 10 * 10)


# -------------------------------------------------------------- aggregate
class AvgRating:
    def __init__(self):
        self.vals = []

    def step(self, value):
        v = _num(value)
        if v is None or v < 1 or v > 5:
            return
        self.vals.append(_frac(v))

    def finalize(self):
        if len(self.vals) < 3:
            return None
        avg = sum(self.vals) / len(self.vals)
        return math.floor(avg * 10 + Fraction(1, 2)) / 10


SPEC = {
    'late_fee': 'late_fee(balance, days_late): Late-payment fee in dollars charged on an overdue invoice balance, growing the longer it stays overdue.',
    'meeting_end': 'meeting_end(start_time, minutes): End time (HH:MM) of a calendar meeting, given its start time and booked duration in minutes.',
    'ship_cost': 'ship_cost(weight_kg, zone): Shipping charge in dollars for a parcel of the given weight sent to a delivery zone (1 = local, 3 = far).',
    'business_days': 'business_days(start_date, end_date): Number of working days from a start date up to, but not including, an end date.',
    'promo_code': 'promo_code(code): Normalizes a promo code typed by a customer into the canonical form used in the promotions table.',
    'mask_card': 'mask_card(card_number): Masks a payment card number for display on receipts, leaving only the end visible.',
    'split_bill': 'split_bill(total, people): Amount each person pays when a restaurant bill is split evenly.',
    'rating_stars': 'rating_stars(score, max_score): Converts a raw review score into a star rating out of 5 for display.',
    'age_band': 'age_band(age): Demographic label for a customer age, used in marketing reports.',
    'avg_rating': 'avg_rating(rating): Average customer rating (1 to 5 stars) for a product, shown on the product page.',
}

SCALARS = {
    'late_fee': (late_fee, 2),
    'meeting_end': (meeting_end, 2),
    'ship_cost': (ship_cost, 2),
    'business_days': (business_days, 2),
    'promo_code': (promo_code, 1),
    'mask_card': (mask_card, 1),
    'split_bill': (split_bill, 2),
    'rating_stars': (rating_stars, 2),
    'age_band': (age_band, 1),
}
AGGREGATE = ('avg_rating', AvgRating)

TYPICAL = {
    'late_fee': [(1000, 7), (2500, 14), (800, 21), (1500, 28)],
    'meeting_end': [('09:00', 30), ('13:15', 45), ('10:30', 60), ('14:00', 90)],
    'ship_cost': [(1, 1), (2, 2), (5, 3), (10, 1), (4, 2)],
    'business_days': [('2026-03-02', '2026-03-06'), ('2026-03-02', '2026-03-09'),
                      ('2026-03-06', '2026-03-09'), ('2026-02-02', '2026-02-27')],
    'promo_code': [('summer20',), ('  Welcome5 ',), ('save15',), ('VIP',)],
    'mask_card': [('4111111111111111',), ('378282246310005',), ('5500005555555559',), ('4012888888881881',)],
    'split_bill': [(100, 4), (90, 3), (50, 2), (120.5, 5)],
    'rating_stars': [(80, 100), (90, 100), (50, 100), (83, 100), (87, 100), (7, 10)],
    'age_band': [(20,), (34,), (47,), (65,), (82,)],
}

EDGE = {
    'late_fee': [(1000, 3), (1000, 4), (1000, 10), (1000, 200), (100, 7), (10, 7),
                 (-50, 10), (None, 5), (1000, 3.5), (0, 30)],
    'meeting_end': [('09:00', 20), ('09:00', 0), ('09:00', -30), ('09:00', 600),
                    ('23:00', 60), ('25:00', 30), ('9:00', 30), (None, 30), ('09:00', None), ('09:00', 15.5)],
    'ship_cost': [(2.5, 1), (20, 1), (20.5, 1), (5, 7), (5, 0), (0, 1), (-3, 1), (None, 1), (5, None), (50, 2)],
    'business_days': [('2026-12-21', '2026-12-28'), ('2026-12-31', '2027-01-04'),
                      ('2026-03-09', '2026-03-02'), ('2026-03-02 14:30', '2026-03-06 09:00'),
                      ('2026-13-01', '2026-03-02'), (None, '2026-03-02'), ('2026-03-02', '2026-03-02'),
                      ('2026-03-07', '2026-03-08'), ('2026-03-02', 'garbage')],
    'promo_code': [('SUMMER-SALE-20',), ('spring sale 2026 big',), ('   ',), ('---',), ('',), (None,),
                   (123,), ('abcdefghijkl',), ('abcdefghijklm',)],
    'mask_card': [('4111 1111 1111 1111',), ('4111-1111-1111-1111',), ('4111111111',), ('',), ('abcd',),
                  (4111111111111111,), (None,), ('4111 1111 1111 111x',)],
    'split_bill': [(100, 3), (10, 3), (0.01, 2), (0, 4), (100, 0), (-10, 2), (None, 2), (100, 2.5), (1, 1)],
    'rating_stars': [(55, 100), (45, 100), (105, 100), (-1, 100), (0, 100), (100, 100), (50, 0), (None, 100), (3, 'x')],
    'age_band': [(18,), (17.5,), (0,), (-5,), (100,), (150,), (29.99,), (None,), ('abc',)],
}

AGG_TYPICAL = [[5, 4, 3], [5, 5, 4, 4], [1, 2, 3, 4, 5], [4, 4, 5, None], [3, 4, 4]]
AGG_EDGE = [[5, 4, 4, 5], [4, 4, 4, 5], [5, 5], [], [0, 5, 5, 5], ['5', '4', '3', '4'],
            [6, 4, 4, 4], [4.5, 4.5, 3.5]]

DECISIONS = {
    'late_fee': ['grace period: 3 days or fewer overdue costs nothing',
                 'partial weeks count as a full week',
                 'fee capped at 20% of balance (applied last)',
                 'minimum fee of 5.00 once any fee applies'],
    'meeting_end': ['duration rounded up to a multiple of 15 minutes',
                    'zero or negative duration treated as 15 minutes',
                    'duration capped at 480 minutes',
                    'end past midnight gets a +1 suffix'],
    'ship_cost': ['partial kg billed as a full kg',
                  'flat 25.00 surcharge for weight over 20 kg',
                  'unknown zone priced as zone 3'],
    'business_days': ['Dec 25 and Jan 1 are holidays (not counted)',
                      'reversed range gives negative count',
                      'time part of timestamps ignored'],
    'promo_code': [],
    'mask_card': ['non-digit separators stripped before masking',
                  'fewer than 12 digits returns INVALID'],
    'split_bill': ['share rounded up to the next cent'],
    'rating_stars': ['exact quarter-star ties round up',
                     'score outside 0..max returns NULL'],
    'age_band': ['under 18 labelled minor'],
    'avg_rating': ['ratings outside 1-5 or non-numeric ignored',
                   'fewer than 3 valid ratings gives NULL',
                   'ties round half up at one decimal'],
}
DECISIONS['promo_code'] = ['internal spaces and hyphens removed',
                           'truncated to 12 characters']

DECISION_EXAMPLES = {
    'late_fee': [(1000, 2), (1000, 8), (1000, 365), (200, 8)],
    'meeting_end': [('08:00', 50), ('08:00', -5), ('08:00', 1000), ('21:00', 240)],
    'ship_cost': [(1.2, 1), (30, 1), (3, 9)],
    'business_days': [('2025-12-22', '2025-12-29'), ('2026-04-10', '2026-04-06'),
                      ('2026-05-04T08:00:00', '2026-05-08')],
    'promo_code': [('new-user',), ('loyaltymember2026',)],
    'mask_card': [('5500-0055-5555-5559',), ('1234567',)],
    'split_bill': [(20, 3)],
    'rating_stars': [(35, 100), (120, 100)],
    'age_band': [(12,)],
    'avg_rating': [[5, 5, 9, 'x', 4], [3, 4], [3, 3, 3, 4]],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, n) in SCALARS.items():
        con.create_function(name, n, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con
