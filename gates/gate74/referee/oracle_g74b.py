import math
import sqlite3
from decimal import Decimal, ROUND_HALF_UP


def _num(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return None
    return x


# 1. late_fee --------------------------------------------------------------
def late_fee(amount, days_late):
    a, d = _num(amount), _num(days_late)
    if a is None or d is None:
        return None
    if a < 0:
        return 0.0
    if d <= 3:
        return 0.0
    fee = a * 0.005 * d
    fee = min(fee, a * 0.25)
    if fee > 0:
        fee = max(fee, 5.0)
    return round(fee, 2)


# 2. ship_cost -------------------------------------------------------------
_BASE = {'A': 4.0, 'B': 7.0, 'C': 12.0}


def ship_cost(weight_g, zone):
    w = _num(weight_g)
    if w is None or zone is None:
        return None
    if w <= 0:
        return None
    base = _BASE.get(zone, 12.0) if isinstance(zone, str) else 12.0
    if w <= 100:
        return 1.0
    n = math.ceil(w / 500)
    cost = base + 1.5 * (n - 1)
    if w > 20000:
        cost += 25.0
    return round(cost, 2)


# 3. mask_card -------------------------------------------------------------
def mask_card(card):
    if isinstance(card, int) and not isinstance(card, bool):
        card = str(card)
    if not isinstance(card, str):
        return None
    s = card.replace(' ', '').replace('-', '')
    if not all(c in '0123456789' for c in s):
        return None
    n = len(s)
    if n <= 4:
        return '*' * n
    return '*' * (n - 4) + s[-4:]


# 4. rating_bucket ---------------------------------------------------------
def rating_bucket(score, votes):
    s, v = _num(score), _num(votes)
    if s is None or v is None:
        return None
    if v < 10 or s < 0 or s > 5:
        return 'NR'
    if s >= 4.5:
        return 'A'
    if s >= 3.5:
        return 'B'
    if s >= 2.5:
        return 'C'
    return 'D'


# 5. meeting_slot ----------------------------------------------------------
def meeting_slot(start, duration_min):
    d = _num(duration_min)
    if d is None or not isinstance(start, str):
        return None
    if len(start) != 5 or start[2] != ':' or not (start[:2].isdigit() and start[3:].isdigit()
                                                  and start.isascii()):
        return None
    h, m = int(start[:2]), int(start[3:])
    if h > 23 or m > 59 or d <= 0:
        return None
    d = math.ceil(d / 15) * 15
    total = h * 60 + m + d
    day, rem = divmod(total, 1440)
    out = '%02d:%02d' % (rem // 60, rem % 60)
    if day:
        out += '+%d' % day
    return out


# 6. initials --------------------------------------------------------------
_PART = {'van', 'von', 'de', 'da', 'di', 'la', 'le', 'del', 'der', 'den', 'bin'}


def initials(name):
    if not isinstance(name, str):
        return None
    toks = name.split()
    if not toks:
        return None
    out = [toks[0][0].upper()]
    for t in toks[1:]:
        if t.lower() in _PART:
            continue
        out.append(t[0].upper())
    out = out[:3]
    return ''.join(c + '.' for c in out)


# 7. tier_total ------------------------------------------------------------
def tier_total(qty, unit_price):
    q, p = _num(qty), _num(unit_price)
    if q is None or p is None:
        return None
    if q <= 0:
        return 0.0
    if q >= 100:
        disc = Decimal('0.90')
    elif q >= 20:
        disc = Decimal('0.95')
    else:
        disc = Decimal('1')
    tot = Decimal(str(q)) * Decimal(str(p)) * disc
    return float(tot.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


# 8. percent_change --------------------------------------------------------
def percent_change(old, new):
    o, n = _num(old), _num(new)
    if o is None or n is None:
        return None
    if o == 0:
        return None
    return round((n - o) / abs(o) * 100, 1)


# 9. sku_normalize ---------------------------------------------------------
_OK = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-')


def sku_normalize(text):
    if not isinstance(text, str):
        return None
    parts = []
    for t in text.upper().split():
        t = ''.join(c for c in t if c in _OK)
        if t:
            parts.append(t)
    return '-'.join(parts)


# 10. aggregate: mid_value -------------------------------------------------
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
        s = sorted(self.vals)
        return s[(len(s) - 1) // 2]


SPEC = {
    'late_fee': 'late_fee(amount, days_late): late-payment penalty charged on an overdue invoice amount.',
    'ship_cost': 'ship_cost(weight_g, zone): shipping charge for a parcel of given weight in grams to a delivery zone.',
    'mask_card': 'mask_card(card): masks a payment card number for display on receipts.',
    'rating_bucket': 'rating_bucket(score, votes): letter grade for a product from its average review score and number of reviews.',
    'meeting_slot': 'meeting_slot(start, duration_min): end time of a calendar booking given its HH:MM start and length in minutes.',
    'initials': 'initials(name): short dotted initials for a person\'s full name, for badges and signatures.',
    'tier_total': 'tier_total(qty, unit_price): order line total with volume discounts applied.',
    'percent_change': 'percent_change(old, new): percentage change between two period figures for reports.',
    'sku_normalize': 'sku_normalize(text): canonical catalogue SKU code from free-form product text.',
    'mid_value': 'mid_value(x): the median-style representative value of a column of numbers.',
}

SCALARS = {
    'late_fee': (late_fee, 2),
    'ship_cost': (ship_cost, 2),
    'mask_card': (mask_card, 1),
    'rating_bucket': (rating_bucket, 2),
    'meeting_slot': (meeting_slot, 2),
    'initials': (initials, 1),
    'tier_total': (tier_total, 2),
    'percent_change': (percent_change, 2),
    'sku_normalize': (sku_normalize, 1),
}

AGGREGATE = ('mid_value', MidValue)

TYPICAL = {
    'late_fee': [(1000, 10), (2000, 20), (400, 12), (800, 30), (1500, 8)],
    'ship_cost': [(500, 'A'), (1200, 'A'), (800, 'B'), (3000, 'C'), (2000, 'B')],
    'mask_card': [('4111111111111111',), ('5500005555555559',), ('378282246310005',), ('6011111111111117',)],
    'rating_bucket': [(4.8, 120), (4.0, 50), (3.0, 30), (1.8, 200)],
    'meeting_slot': [('09:00', 60), ('13:30', 30), ('08:15', 90), ('10:00', 45)],
    'initials': [('John Smith',), ('Ada Lovelace',), ('Grace Brewster Hopper',), ('Alan Turing',)],
    'tier_total': [(5, 2.5), (20, 10.0), (100, 3.0), (50, 4.0), (10, 9.99)],
    'percent_change': [(100, 125), (80, 60), (50, 51), (200, 250), (3, 4)],
    'sku_normalize': [(' ab 12 ',), ('widget red',), ('blue',), ('x9 large size',)],
}

EDGE = {
    'late_fee': [(1000, 3), (1000, 4), (1000, 100), (10, 30), (-500, 20), (500, 0),
                 (0, 30), (None, 10), (500, None), (2000, -5)],
    'ship_cost': [(100, 'A'), (101, 'A'), (25000, 'B'), (20000, 'A'), (1000, 'Z'),
                  (0, 'A'), (-5, 'B'), (500, None), (None, 'A')],
    'mask_card': [('4111-1111-1111-1111',), ('1234',), ('12345',), ('',),
                  ('4111 1111 111A',), (None,), ('   ',), ('0000 0000 0000 0000 000',)],
    'rating_bucket': [(4.49, 50), (3.5, 200), (2.5, 30), (5.0, 100), (0.0, 15),
                      (4.9, 9), (5.01, 100), (-1, 50), (3.0, 10), (None, 5)],
    'meeting_slot': [('09:00', 20), ('09:00', 1), ('23:30', 60), ('23:00', 60), ('18:00', 1600),
                     ('09:60', 30), ('9:00', 30), ('09:00', 0), ('08:00', None), (None, 30)],
    'initials': [('Anna Maria Louise Smith',), ('Jean de la Fontaine',), ('   ',), ('',),
                 (None,), ('van Gogh',), ('Mary-Jane Watson',), ('smith',), ('Ana Von Trapp',)],
    'tier_total': [(19, 10.0), (99, 2.0), (100, 1.0), (1, 1.005), (-3, 10.0), (None, 5),
                   (5, None), (25, 0.99), (1000, 0.01)],
    'percent_change': [(0, 5), (0, 0), (-50, -25), (-10, 10), (100, 100), (1, 3),
                       (7, 22), (None, 5), (5, None)],
    'sku_normalize': [('ab#12',), ('a.b/c',), ('   ',), ('',), (None,), ('abc_def',),
                      ('A  B   C',), ('  x-1 ',), ('p&g 5%',)],
}

AGG_TYPICAL = [[3, 1, 2], [10, 20, 30, 40, 50], [5.5, 1.5, 3.5], [7, None, 9, 8]]
AGG_EDGE = [[], [None, None], [1, 2], [4, 1, 3, 2], [2.5, 1.5], [1, 2, 3, 4, 5, 6], [5, 'x', 7]]

DECISIONS = {
    'late_fee': ['grace period of 3 days', 'fee capped at 25% of amount', 'minimum fee of 5.00',
                 'negative amount yields 0.0'],
    'ship_cost': ['weights up to 100 g flat 1.00', 'unknown zone uses zone C rate',
                  'weight over 20000 g adds 25.00 surcharge', 'non-positive weight returns NULL'],
    'mask_card': ['spaces and dashes stripped from output', 'up to 4 digits fully masked',
                  'any other character returns NULL'],
    'rating_bucket': ['fewer than 10 votes is NR', 'grade boundaries inclusive at the lower edge',
                      'score outside 0..5 is NR'],
    'meeting_slot': ['duration rounded up to next 15 minutes', 'past midnight gets +N day suffix',
                     'malformed start or non-positive duration returns NULL'],
    'initials': ['name particles skipped (except first word)', 'at most 3 initials'],
    'tier_total': ['half-up rounding to cents', 'non-positive quantity gives 0.0'],
    'percent_change': ['old of zero returns NULL', 'negative old uses absolute value as base'],
    'sku_normalize': ['punctuation and symbols dropped'],
    'mid_value': ['even count returns the lower middle value'],
}

DECISION_EXAMPLES = {
    'late_fee': [(800, 2), (1000, 200), (20, 10), (-100, 30)],
    'ship_cost': [(50, 'C'), (30000, 'C'), (1000, 'X'), (-300, 'C')],
    'mask_card': [('5500 0000 0000 0004',), ('987',), ('41x11111',)],
    'rating_bucket': [(4.5, 40), (4.0, 9), (6.0, 50)],
    'meeting_slot': [('10:00', 50), ('22:30', 120), ('25:00', 30)],
    'initials': [('Pieter van der Berg',), ('One Two Three Four Five',)],
    'tier_total': [(1, 0.125), (0, 5.0)],
    'percent_change': [(0, 8), (-40, -30)],
    'sku_normalize': [('red (L)',)],
    'mid_value': [[10, 20]],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, n) in SCALARS.items():
        con.create_function(name, n, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con
