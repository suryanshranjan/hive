import math
import re
import sqlite3
import datetime
from decimal import Decimal, ROUND_HALF_UP


def _num(x):
    if x is None or isinstance(x, bool):
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


# ---------------------------------------------------------------- shipping_cost
_ZONES = {1: (500, 100), 2: (800, 150), 3: (1200, 250)}


def shipping_cost(weight_g, zone):
    w = _num(weight_g)
    if w is None or w <= 0:
        return None
    z = zone if isinstance(zone, (int, float)) and not isinstance(zone, bool) and zone in _ZONES else 3
    base, per = _ZONES[z]
    if w <= 250:
        return 199
    cost = base
    if w > 500:
        cost += per * math.ceil((w - 500) / 500)
    return int(min(cost, 5000))


# ---------------------------------------------------------------- letter_grade
def letter_grade(score):
    s = _num(score)
    if s is None or s < 0:
        return 'INC'
    r = math.floor(s + 0.5)
    if r > 100:
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


# ---------------------------------------------------------------- mask_card
def mask_card(card):
    if card is None:
        return None
    s = str(card).strip()
    if re.search(r'[^0-9 \-]', s):
        return None
    d = re.sub(r'[ \-]', '', s)
    if not d:
        return None
    n = len(d)
    if n < 12:
        return '*' * n
    if n == 15 and d[:2] in ('34', '37'):
        return '*' * 10 + d[-5:]
    return '*' * (n - 4) + d[-4:]


# ---------------------------------------------------------------- workdays
_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def _parse_date(s):
    if not isinstance(s, str):
        return None
    s = s.strip()
    if not _DATE_RE.match(s):
        return None
    try:
        return datetime.datetime.strptime(s, '%Y-%m-%d').date()
    except ValueError:
        return None


def workdays(start, end):
    a, b = _parse_date(start), _parse_date(end)
    if a is None or b is None:
        return None
    if a > b:
        return 0
    count = 0
    d = a
    one = datetime.timedelta(days=1)
    while d <= b:
        if d.weekday() < 5 and not ((d.month, d.day) in ((1, 1), (12, 25))):
            count += 1
        d += one
    return count


# ---------------------------------------------------------------- norm_phone
def norm_phone(phone):
    if phone is None:
        return None
    s = str(phone).lower().split('x')[0]
    d = re.sub(r'\D', '', s)
    if len(d) == 7:
        d = '212' + d
    elif len(d) == 11 and d[0] == '1':
        d = d[1:]
    if len(d) != 10:
        return None
    if d[0] in '01':
        return None
    return '+1' + d


# ---------------------------------------------------------------- tax_amount
def tax_amount(amount_cents, rate_pct):
    a, r = _num(amount_cents), _num(rate_pct)
    if a is None or r is None:
        return None
    r = min(r, 30)
    v = Decimal(str(a)) * Decimal(str(r)) / Decimal(100)
    return int(v.quantize(Decimal(1), rounding=ROUND_HALF_UP))


# ---------------------------------------------------------------- initials
_SUFFIX = {'jr', 'sr', 'ii', 'iii', 'iv', 'phd', 'md'}


def initials(name):
    if name is None:
        return None
    words = [w for w in str(name).split() if any(c.isalpha() for c in w)]
    while len(words) > 1 and words[-1].strip('.,').lower() in _SUFFIX:
        words.pop()
    if not words:
        return None

    def ini(w):
        for c in w:
            if c.isalpha():
                return c.upper()
        return ''
    if len(words) == 1:
        return ini(words[0])
    return ini(words[0]) + ini(words[-1])


# ---------------------------------------------------------------- fmt_duration
def fmt_duration(seconds):
    n = _num(seconds)
    if n is None or n < 0:
        return None
    t = int(n)
    d, rem = divmod(t, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    parts = []
    if d:
        parts.append('%dd' % d)
    if h:
        parts.append('%dh' % h)
    if m:
        parts.append('%dm' % m)
    if s:
        parts.append('%ds' % s)
    return ' '.join(parts) if parts else '0s'


# ---------------------------------------------------------------- loyalty_points
def loyalty_points(spend_cents):
    s = _num(spend_cents)
    if s is None:
        return None
    if s < 500:
        return 0
    return int(s // 100)


# ---------------------------------------------------------------- avg_rating
class AvgRating:
    def __init__(self):
        self.total = 0.0
        self.n = 0

    def step(self, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return
        if isinstance(value, float) and not math.isfinite(value):
            return
        if 1 <= value <= 5:
            self.total += value
            self.n += 1

    def finalize(self):
        if self.n == 0:
            return None
        return round(self.total / self.n, 2)


SPEC = {
    'shipping_cost': 'shipping_cost(weight_g, zone): Shipping charge in cents for a parcel of the given weight in grams sent to delivery zone 1, 2 or 3.',
    'letter_grade': 'letter_grade(score): Converts a 0-100 exam score into the letter grade shown on report cards.',
    'mask_card': 'mask_card(card_number): Masks a payment card number for display on receipts, keeping only the trailing digits visible.',
    'workdays': 'workdays(start_date, end_date): Counts the working days between two ISO dates (YYYY-MM-DD) for delivery and SLA planning.',
    'norm_phone': 'norm_phone(phone): Normalizes a customer-entered US phone number into E.164 format for the CRM.',
    'tax_amount': 'tax_amount(amount_cents, rate_pct): Sales tax in whole cents due on an amount in cents at a percentage rate.',
    'initials': 'initials(full_name): Builds the uppercase initials shown in a user avatar from a person\'s full name.',
    'fmt_duration': 'fmt_duration(seconds): Formats a number of seconds as a short human-readable duration for dashboards.',
    'loyalty_points': 'loyalty_points(spend_cents): Loyalty points a customer earns for a purchase of the given amount in cents.',
    'avg_rating': 'avg_rating(rating): Average customer rating on the 1-5 star scale across a group of reviews.',
}

SCALARS = {
    'shipping_cost': (shipping_cost, 2),
    'letter_grade': (letter_grade, 1),
    'mask_card': (mask_card, 1),
    'workdays': (workdays, 2),
    'norm_phone': (norm_phone, 1),
    'tax_amount': (tax_amount, 2),
    'initials': (initials, 1),
    'fmt_duration': (fmt_duration, 1),
    'loyalty_points': (loyalty_points, 1),
}

AGGREGATE = ('avg_rating', AvgRating)

TYPICAL = {
    'shipping_cost': [(1000, 1), (2000, 2), (500, 3), (1500, 3), (800, 2)],
    'letter_grade': [(95,), (85,), (75,), (65,), (30,)],
    'mask_card': [('4111111111111111',), ('5500005555555559',), ('6011000990139424',), ('3530111333300000',)],
    'workdays': [('2024-03-04', '2024-03-08'), ('2024-03-01', '2024-03-31'), ('2024-03-09', '2024-03-10'),
                 ('2024-03-06', '2024-03-06'), ('2024-05-01', '2024-05-31')],
    'norm_phone': [('(415) 555-2671',), ('415-555-2671',), ('415.555.2671',), ('+1 415 555 2671',), ('1-650-555-0100',)],
    'tax_amount': [(10000, 8), (2500, 10), (20000, 5), (1000, 20), (4000, 7.5)],
    'initials': [('John Smith',), ('ada lovelace',), ('Grace Hopper',), ('  Alan   Turing ',)],
    'fmt_duration': [(45,), (125,), (3725,), (7200,), (0,)],
    'loyalty_points': [(1000,), (2550,), (12000,), (50000,), (999,)],
}

EDGE = {
    'shipping_cost': [(20000, 3), (30000, 3), (200, 1), (250, 2), (-10, 1), (None, 2), (1000, 7), (1000, None), ('abc', 1), (1200, 2)],
    'letter_grade': [(89.5,), (89.4,), (101,), (100,), (100.2,), (-5,), (None,), ('abc',), (59.5,), (0,)],
    'mask_card': [('4111 1111 1111 1111',), ('4111-1111-1111-1111',), ('12345678',), ('378282246310005',),
                  ('411111111111',), ('4111x111',), (None,), ('',), ('491630000000',)],
    'workdays': [('2024-12-23', '2024-12-27'), ('2024-12-30', '2025-01-03'), ('2024-03-08', '2024-03-04'),
                 ('2024-02-30', '2024-03-05'), ('bad', '2024-03-05'), (None, '2024-03-05'),
                 ('2024-01-01', '2024-01-01'), ('2024-02-26', '2024-03-01'), ('2024-12-25', '2024-12-26')],
    'norm_phone': [('555-1234',), ('415-555-2671 x123',), ('(015) 555-2671',), ('123',), (None,),
                   ('415-555-2671 ext. 9',), ('(115) 555-1234',), ('+1 (212) 555-0100',), ('',)],
    'tax_amount': [(5, 10), (-5, 10), (10000, 45), (10000, 30), (0, 8), (1999, 7.5), (None, 8), (1000, None)],
    'initials': [('Cher',), ('',), ('   ',), ('John Ronald Tolkien',), ('Martin Luther King Jr.',),
                 ('Mary-Jane Watson',), (None,), ('Jr',), ('Sammy Davis III',)],
    'fmt_duration': [(86400,), (90061,), (200000,), (-5,), (None,), (59,), (3600,), (3599,), (60,)],
    'loyalty_points': [(499,), (500,), (0,), (-1000,), (None,), (599,), (12345,), (450,)],
}

AGG_TYPICAL = [[5, 4, 3], [4, 4, 5, 5], [3, None, 4, 5], [2, 3]]
AGG_EDGE = [[], [None, None], [0, 3], [4.5, 5], [6, 9], [0.99, 1], [3, 4, 5, -1, 100], [1]]

DECISIONS = {
    'shipping_cost': ['charge capped at 5000 cents', 'unknown or missing zone billed as zone 3',
                      'non-positive, missing or non-numeric weight gives NULL', 'parcels up to 250 g pay a flat 199 in any zone'],
    'letter_grade': ['score rounded half up before banding', 'scores above 100 after rounding give A+',
                     'negative, missing or non-numeric score gives INC'],
    'mask_card': ['spaces and dashes are removed from the input', 'numbers under 12 digits are fully masked',
                  '15-digit numbers starting 34/37 show last 5 digits', 'any other character gives NULL'],
    'workdays': ['both ends inclusive but start after end gives 0', 'Jan 1 and Dec 25 are non-working holidays',
                 'invalid or missing date gives NULL'],
    'norm_phone': ['extension after x is dropped', '7-digit numbers get area code 212',
                   'area code starting with 0 or 1 gives NULL'],
    'tax_amount': ['rate capped at 30 percent', 'half cents round away from zero'],
    'initials': ['only first and last word used', 'generational/title suffixes ignored'],
    'fmt_duration': ['days unit used from 86400 s', 'negative gives NULL'],
    'loyalty_points': ['purchases under 500 cents earn 0'],
    'avg_rating': ['ratings outside 1-5 are ignored'],
}

DECISION_EXAMPLES = {
    'shipping_cost': [(40000, 2), (1000, 'express'), (0, 1), (100, 3)],
    'letter_grade': [(69.5,), (120,), ('n/a',)],
    'mask_card': [('5500 0055 5555 5559',), ('1234567',), ('340000000000009',), ('4111.1111',)],
    'workdays': [('2024-06-10', '2024-06-03'), ('2023-12-25', '2023-12-29'), ('2024-13-01', '2024-06-03')],
    'norm_phone': [('212-555-0100 ext 44',), ('555-0199',), ('(055) 555-0100',)],
    'tax_amount': [(1000, 50), (15, 10)],
    'initials': [('Anna Maria Louise Bell',), ('Robert Downey Jr',)],
    'fmt_duration': [(100000,), (-60,)],
    'loyalty_points': [(300,)],
    'avg_rating': [[10, 2, 4, 0]],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, n) in SCALARS.items():
        con.create_function(name, n, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con
