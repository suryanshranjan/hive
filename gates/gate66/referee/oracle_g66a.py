import math
import re
import sqlite3
from datetime import date, timedelta
from fractions import Fraction


def _num(x):
    if x is None or isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
            return None
        return x
    try:
        v = float(str(x).strip())
    except ValueError:
        return None
    if math.isnan(v) or math.isinf(v):
        return None
    return int(v) if v == int(v) and re.fullmatch(r'\s*[+-]?\d+\s*', str(x)) else v


def _frac(x):
    return Fraction(x) if isinstance(x, int) else Fraction(repr(x))


# 1. mask_card
def mask_card(text):
    if text is None:
        return None
    digits = ''.join(c for c in str(text) if c in '0123456789')
    if len(digits) <= 4:
        return digits
    return '*' * (len(digits) - 4) + digits[-4:]


# 2. rating_band
def rating_band(avg):
    v = _num(avg)
    if v is None:
        return None
    if v > 4.5:
        return 'A'
    if v > 3.5:
        return 'B'
    if v > 2.5:
        return 'C'
    return 'D'


# 3. discount_price
def discount_price(price_cents, pct):
    p = _num(price_cents)
    d = _num(pct)
    if p is None or d is None:
        return None
    d = min(_frac(d), Fraction(50))
    val = _frac(p) * (Fraction(100) - d) / 100
    return int(math.ceil(val))


# 4. biz_days
_ISO = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def _parse(s):
    if not isinstance(s, str) or not _ISO.match(s.strip()):
        return None
    try:
        return date.fromisoformat(s.strip())
    except ValueError:
        return None


def biz_days(start, end):
    a, b = _parse(start), _parse(end)
    if a is None or b is None:
        return None
    if b <= a:
        return 0
    n = (b - a).days
    full, rem = divmod(n, 7)
    count = full * 5
    d = a + timedelta(days=full * 7)
    for _ in range(rem):
        if d.weekday() < 5:
            count += 1
        d += timedelta(days=1)
    for y in range(a.year, b.year + 1):
        for m, dd in ((1, 1), (12, 25)):
            h = date(y, m, dd)
            if a <= h < b and h.weekday() < 5:
                count -= 1
    return count


# 5. slugify
def slugify(text):
    if text is None:
        return None
    s = ''.join(c for c in str(text).lower() if ord(c) < 128)
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    s = s[:40].rstrip('-')
    return s


# 6. ship_cost
def ship_cost(weight_g, zone):
    w = _num(weight_g)
    z = _num(zone)
    if w is None or z is None:
        return None
    if w > 30000:
        return None
    if w <= 0:
        return 0
    z = int(z)
    if z < 1 or z > 4:
        z = 4
    base = 400 + 150 * (z - 1)
    extra = max(0, math.ceil((w - 500) / 500)) * 100
    return base + extra


# 7. check_digit
def check_digit(code):
    if code is None:
        return None
    digits = [int(c) for c in str(code) if c in '0123456789'][-12:]
    if not digits:
        return 0
    total = 0
    for i, dg in enumerate(reversed(digits)):
        total += dg * (3 if i % 2 == 0 else 1)
    return (10 - total % 10) % 10


# 8. loyalty_points
_MULT = {'basic': 1, 'gold': 2, 'platinum': 3}


def loyalty_points(spend_cents, tier):
    s = _num(spend_cents)
    if s is None:
        return None
    mult = _MULT.get(tier, 1) if isinstance(tier, str) else 1
    dollars = int(s // 100)
    return min(dollars * mult, 5000)


# 9. format_money
_SYM = {'USD': '$', 'EUR': '€', 'GBP': '£'}


def format_money(cents, currency):
    c = _num(cents)
    if c is None or currency is None:
        return None
    c = int(round(c))
    code = str(currency).strip().upper()
    prefix = _SYM.get(code, code + ' ')
    if c == 0:
        return '-'
    a = abs(c)
    if a >= 100_000_000:
        t = a * 10 // 100_000_000
        body = '%s%d.%dM' % (prefix, t // 10, t % 10)
    else:
        body = '%s%s.%02d' % (prefix, format(a // 100, ','), a % 100)
    return '(' + body + ')' if c < 0 else body


# 10. order_avg (aggregate)
class OrderAvg:
    def __init__(self):
        self.vals = []

    def step(self, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return
        if value <= 0:
            return
        self.vals.append(min(value, 1_000_000))

    def finalize(self):
        if len(self.vals) < 3:
            return None
        mean = sum((_frac(v) for v in self.vals), Fraction(0)) / len(self.vals)
        return int(math.floor(mean + Fraction(1, 2)))


SPEC = {
    'mask_card': 'mask_card(card_number): Masks a payment card number for display on receipts and support screens.',
    'rating_band': 'rating_band(avg_score): Converts an average customer review score (0-5) into a letter band for dashboards.',
    'discount_price': 'discount_price(price_cents, pct_off): Price in cents after applying a percentage promotional discount.',
    'biz_days': 'biz_days(start_date, end_date): Number of working days between two ISO dates, for delivery and SLA estimates.',
    'slugify': 'slugify(title): Turns a product or article title into a URL-friendly slug.',
    'ship_cost': 'ship_cost(weight_g, zone): Shipping charge in cents for a parcel of the given weight to a delivery zone.',
    'check_digit': 'check_digit(code): Computes the numeric check digit to append to a product code.',
    'loyalty_points': 'loyalty_points(spend_cents, tier): Loyalty points earned by a customer for a purchase, given their membership tier.',
    'format_money': 'format_money(cents, currency): Formats an amount in minor units as a display string for invoices and reports.',
    'order_avg': 'order_avg(order_value): Average order value in cents across a group of orders, for sales reporting.',
}

SCALARS = {
    'mask_card': (mask_card, 1),
    'rating_band': (rating_band, 1),
    'discount_price': (discount_price, 2),
    'biz_days': (biz_days, 2),
    'slugify': (slugify, 1),
    'ship_cost': (ship_cost, 2),
    'check_digit': (check_digit, 1),
    'loyalty_points': (loyalty_points, 2),
    'format_money': (format_money, 2),
}

AGGREGATE = ('order_avg', OrderAvg)

TYPICAL = {
    'mask_card': [('4111111111111111',), ('378282246310005',), ('5500000000000004',), ('6011111111111117',)],
    'rating_band': [(4.8,), (4.0,), (3.0,), (1.2,), (2.9,)],
    'discount_price': [(10000, 10), (2000, 25), (999, 0), (5000, 20), (8000, 12.5)],
    'biz_days': [('2024-03-04', '2024-03-08'), ('2024-03-01', '2024-03-11'),
                 ('2024-05-06', '2024-05-13'), ('2024-07-01', '2024-07-02'),
                 ('2023-02-01', '2023-03-01')],
    'slugify': [('Hello World',), ('  Summer Sale 2024! ',), ('Q3_Report (final)',), ('a--b',)],
    'ship_cost': [(300, 1), (500, 2), (1200, 3), (2500, 1), (750, 4)],
    'check_digit': [('400638133393',), ('03600029145',), ('12345',), (98765,), ('1',)],
    'loyalty_points': [(10000, 'basic'), (4500, 'gold'), (2000, 'platinum'), (15000, 'gold')],
    'format_money': [(123456, 'USD'), (5, 'USD'), (250000, 'EUR'), (1999, 'GBP'), (100, 'USD')],
}

EDGE = {
    'mask_card': [('4111-1111-1111-1111',), ('4111 1111 1111 1111',), ('1234',), ('123',),
                  ('',), ('abcd',), ('12345',), (4111111111111111,), (None,)],
    'rating_band': [(4.5,), (3.5,), (5,), (0,), (4.6,), ('abc',), (-1,), (6,), (None,)],
    'discount_price': [(999, 10), (10000, 80), (10000, 50), (100, 100), (0, 10),
                       (-1000, 10), (1000, -10), (1000, 'x'), (None, 10)],
    'biz_days': [('2024-03-08', '2024-03-04'), ('2025-01-01', '2025-01-03'),
                 ('2024-12-25', '2024-12-26'), ('2022-12-23', '2022-12-27'),
                 ('2024-02-30', '2024-03-05'), ('2024-03-01', 'not a date'),
                 ('2024-03-01', '2024-03-01'), (None, '2024-03-01')],
    'slugify': [('The quick brown fox jumps over the lazy dog today',), ('café au lait',),
                ('---',), ('',), ('Ünï',), ('x' * 50,), ('A' * 39 + ' b',), (12345,), (None,)],
    'ship_cost': [(500, 5), (500, 0), (30000, 2), (30001, 2), (0, 1), (-5, 1),
                  (501, 1), (1000, -3), (None, 1)],
    'check_digit': [('4006-3813-3393',), ('abc',), ('',), ('1234567890123456',),
                    ('0',), ('A1B2',), (-12345,), ('0000000000000',), (None,)],
    'loyalty_points': [(1999, 'basic'), (-150, 'gold'), (500000, 'basic'), (3000000, 'gold'),
                       (10000, 'Gold'), (10000, None), (10000, 'vip'), (99, 'platinum'), (None, 'gold')],
    'format_money': [(-1250, 'USD'), (0, 'USD'), (250000000, 'USD'), (123456789, 'USD'),
                     (99999999, 'USD'), (100000000, 'USD'), (1250, 'XYZ'), (-250000000, 'EUR'),
                     (1250, 'usd'), (None, 'USD')],
}

AGG_TYPICAL = [[100, 200, 300], [1000, 2000, 3000, 4000], [50, 150, 100, 250, 200], [10, 20, 30]]

AGG_EDGE = [[100, 0, 200, 300], [100, -50, 200], [2000000, 3000000, 1000000],
            [1, 2, 2], [1, 2, 3, 4], [100, None, 200, 300], [], [5, 5]]

DECISIONS = {
    'mask_card': ['spaces, dashes and other non-digits are stripped before masking'],
    'rating_band': ['band thresholds are strict: an exact boundary score falls in the lower band'],
    'discount_price': ['discount percentage capped at 50', 'fractional cents round up'],
    'biz_days': ['reversed range returns 0', 'Jan 1 and Dec 25 weekdays are not working days'],
    'slugify': ['non-ASCII characters are dropped, not transliterated or hyphenated',
                'slug truncated to 40 chars with trailing hyphen removed'],
    'ship_cost': ['zone outside 1-4 priced as zone 4', 'weight over 30000 g returns NULL',
                  'weight <= 0 costs 0'],
    'check_digit': ['non-digit characters ignored', 'only last 12 digits used',
                    'no digits returns 0'],
    'loyalty_points': ['only whole dollars earn points (cents dropped)',
                       'unrecognized, differently-cased or NULL tier earns basic rate',
                       'points capped at 5000'],
    'format_money': ['negative amounts in parentheses', 'unknown currency gets uppercase code prefix with space',
                     'zero shown as a dash', 'amounts >= 1,000,000.00 abbreviated in millions, truncated to 1 decimal'],
    'order_avg': ['values <= 0 excluded', 'values capped at 1,000,000',
                  'mean rounded half up to integer', 'fewer than 3 qualifying values returns NULL'],
}

DECISION_EXAMPLES = {
    'mask_card': [('5500 0000 0000 0004',)],
    'rating_band': [(2.5,)],
    'discount_price': [(20000, 75), (333, 10)],
    'biz_days': [('2024-03-15', '2024-03-04'), ('2024-12-23', '2024-12-27')],
    'slugify': [('Crème brûlée recipes',),
                ('Annual Report for the Fiscal Year Ending December 2024 Final',)],
    'ship_cost': [(1000, 9), (45000, 2), (-100, 3)],
    'check_digit': [('7-3-9-1',), ('1234567890123456789012',), ('n/a',)],
    'loyalty_points': [(2599, 'gold'), (8000, 'bronze'), (9000000, 'basic')],
    'format_money': [(-99900, 'USD'), (123456, 'CHF'), (0, 'EUR'), (1500000000, 'USD')],
    'order_avg': [[10, -5, 20, 30, 0], [1000000, 9000000, 500000, 500000],
                  [1, 1, 2, 2], [100, 900]],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, n) in SCALARS.items():
        con.create_function(name, n, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con
