import math
import re
import sqlite3
import datetime
from fractions import Fraction


def _num(x):
    if x is None or isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return x
    if isinstance(x, str):
        try:
            return int(x.strip())
        except ValueError:
            try:
                f = float(x.strip())
                return f if math.isfinite(f) else None
            except ValueError:
                return None
    return None


# ---------------------------------------------------------------- scalars

def loyalty_points(spend_cents, tier):
    s = _num(spend_cents)
    if s is None or s < 0:
        return 0
    rate = {'basic': 1, 'silver': 2, 'gold': 3}.get(
        tier.strip().lower() if isinstance(tier, str) else None, 1)
    pts = int(math.floor(s / 100)) * rate
    return min(pts, 5000)


def _weekdays_before(d):
    # weekdays in [date(1,1,1), d)
    n = d.toordinal() - 1
    full, rem = divmod(n, 7)
    count = full * 5
    start_wd = datetime.date(1, 1, 1).weekday()  # Monday
    for i in range(rem):
        if (start_wd + i) % 7 < 5:
            count += 1
    return count


def workdays_between(start, end):
    if start is None or end is None:
        return None
    try:
        a = datetime.date.fromisoformat(start.strip())
        b = datetime.date.fromisoformat(end.strip())
    except (ValueError, AttributeError, TypeError):
        return -1
    if b <= a:
        return 0
    count = _weekdays_before(b) - _weekdays_before(a)
    for y in range(a.year, b.year + 1):
        h = datetime.date(y, 12, 25)
        if a <= h < b and h.weekday() < 5:
            count -= 1
    return count


def mask_card(text):
    if text is None:
        return None
    s = text if isinstance(text, str) else str(text)
    s = s.replace(' ', '').replace('-', '')
    if not all(c in '0123456789' for c in s):
        return None
    if len(s) < 8:
        return 'INVALID'
    return '*' * (len(s) - 4) + s[-4:]


def grade_letter(score, scale_max):
    sc = _num(score)
    mx = _num(scale_max)
    if sc is None or mx is None:
        return None
    if mx <= 0:
        return 'N/A'
    if sc > mx:
        return 'X'
    pct = Fraction(sc) / Fraction(mx) * 100
    p = math.floor(pct + Fraction(1, 2))
    if p >= 90:
        return 'A'
    if p >= 80:
        return 'B'
    if p >= 70:
        return 'C'
    if p >= 60:
        return 'D'
    return 'F'


def tax_cents(price_cents, rate_bp):
    p = _num(price_cents)
    r = _num(rate_bp)
    if p is None or r is None:
        return None
    r = min(r, 3000)
    return int(round(Fraction(p) * Fraction(r) / 10000))


def slugify(text):
    if text is None:
        return None
    s = text if isinstance(text, str) else str(text)
    s = ''.join(c for c in s if ord(c) < 128).lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    s = s[:40].rstrip('-')
    return s if s else 'untitled'


def parcel_fee(weight_g, zone):
    w = _num(weight_g)
    if w is None:
        return None
    if w <= 0:
        return 0
    if w <= 250:
        return 300
    z = _num(zone)
    base = {1: 500, 2: 800, 3: 1200}.get(z, 1200) if z is not None else 1200
    fee = base + 100 * (int(math.ceil(w / 1000)) - 1)
    if w > 30000:
        fee += 2500
    return fee


def ticket_priority(severity, hours_open):
    sv = _num(severity)
    h = _num(hours_open)
    if sv is None or h is None:
        return None
    level = int(sv) if sv in (1, 2, 3, 4) else 4
    if h >= 48:
        level = max(1, level - 1)
    return 'P%d' % level


def charm_price(cents):
    c = _num(cents)
    if c is None:
        return None
    if c < 100:
        return c
    n = int(math.ceil(c))
    return n + ((99 - n % 100) % 100)


# -------------------------------------------------------------- aggregate

class MedianAmount:
    def __init__(self):
        self.vals = []

    def step(self, value):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            self.vals.append(value)

    def finalize(self):
        if not self.vals:
            return None
        s = sorted(self.vals)
        n = len(s)
        if n % 2:
            return s[n // 2]
        return s[n // 2 - 1]


# ---------------------------------------------------------------- exports

SPEC = {
    'loyalty_points': 'loyalty_points(spend_cents, tier): Loyalty points earned by a customer for a purchase, given the spend in cents and the membership tier name.',
    'workdays_between': 'workdays_between(start_date, end_date): Number of working days (Monday to Friday) from start_date up to end_date, with dates as YYYY-MM-DD text.',
    'mask_card': 'mask_card(card_number): Display-safe version of a payment card number for receipts and logs.',
    'grade_letter': 'grade_letter(score, scale_max): Letter grade (A to F) for a score on a scale running from 0 to scale_max.',
    'tax_cents': 'tax_cents(price_cents, rate_bp): Sales tax in whole cents for a price in cents at a rate given in basis points.',
    'slugify': 'slugify(title): URL-friendly slug generated from a page or product title.',
    'parcel_fee': 'parcel_fee(weight_g, zone): Shipping fee in cents for a parcel of the given weight in grams sent to a delivery zone (1, 2 or 3).',
    'ticket_priority': 'ticket_priority(severity, hours_open): Support ticket priority label (P1 most urgent to P4 least) from its severity (1 to 4) and how long it has been open.',
    'charm_price': 'charm_price(cents): Marketing-friendly shelf price in cents, ending in 99, derived from a raw price in cents.',
    'median_amount': 'median_amount(value): Aggregate giving the median of the numeric values in a group.',
}

SCALARS = {
    'loyalty_points': (loyalty_points, 2),
    'workdays_between': (workdays_between, 2),
    'mask_card': (mask_card, 1),
    'grade_letter': (grade_letter, 2),
    'tax_cents': (tax_cents, 2),
    'slugify': (slugify, 1),
    'parcel_fee': (parcel_fee, 2),
    'ticket_priority': (ticket_priority, 2),
    'charm_price': (charm_price, 1),
}

AGGREGATE = ('median_amount', MedianAmount)

TYPICAL = {
    'loyalty_points': [(12345, 'gold'), (5000, 'silver'), (999, 'basic'), (25000, 'gold'), (7777, 'silver')],
    'workdays_between': [('2024-03-04', '2024-03-08'), ('2024-03-01', '2024-03-11'),
                         ('2024-03-02', '2024-03-04'), ('2024-01-01', '2024-02-01')],
    'mask_card': [('4111111111111111',), ('4111 1111 1111 1111',), ('5500-0000-0000-0004',), (378282246310005,)],
    'grade_letter': [(95, 100), (85, 100), (45, 50), (30, 50), (10, 100), (35, 50)],
    'tax_cents': [(10000, 825), (2599, 700), (1999, 500), (5000, 1000)],
    'slugify': [('Hello World',), ("Don't Stop Believing",), ('  Spring  Sale 2024! ',), ('a_b_c',)],
    'parcel_fee': [(500, 1), (1000, 2), (1500, 2), (2500, 3), (10000, 1)],
    'ticket_priority': [(1, 2), (2, 10), (3, 0), (4, 5), (3, 47)],
    'charm_price': [(1234,), (1250,), (4001,), (1299,), (9999,), (15000,)],
}

EDGE = {
    'loyalty_points': [(None, 'gold'), (-500, 'gold'), (1000000, 'gold'), (5000, 'platinum'),
                       (5000, None), (5000, 'GOLD'), (0, 'basic'), (99, 'silver')],
    'workdays_between': [('2024-03-04', '2024-03-04'), ('2024-03-08', '2024-03-04'),
                         ('2024-12-23', '2024-12-27'), ('abc', '2024-01-01'), (None, '2024-01-01'),
                         ('2022-12-23', '2022-12-27'), ('2024-01-01', '2025-01-01'),
                         ('2024-02-28', '2024-03-01')],
    'mask_card': [('1234567',), ('12345678',), ('4111-1111-abcd-1111',), ('',), (None,), ('   ',), ('1234 5678 9',)],
    'grade_letter': [(89.5, 100), (89.4, 100), (101, 100), (50, 0), (50, -10), (-5, 100),
                     (100, 100), (None, 100), (79.5, 100)],
    'tax_cents': [(1050, 100), (1150, 100), (-1050, 100), (10000, 3000), (10000, 3001),
                  (0, 500), (None, 500), (10000, 0), (10000, -500)],
    'slugify': [('Café Déjà Vu',), ('abcdefghi ' * 5,),
                ('the quick brown fox jumps over the lazy dog again and again',),
                ('!!!',), ('',), ('日本語',), (None,), (12345,)],
    'parcel_fee': [(250, 1), (251, 1), (0, 1), (-5, 2), (30000, 3), (30001, 3), (5000, 7),
                   (5000, None), (None, 1), (1000.5, 2)],
    'ticket_priority': [(3, 48), (1, 100), (4, 48), (0, 5), (9, 1), (5, 72), (2, 47.9), (None, 5), (2, None)],
    'charm_price': [(99,), (100,), (0,), (-500,), (50,), (12.5,), (199.5,), (1299.2,), (None,)],
}

AGG_TYPICAL = [[1, 3, 2], [5, 1, 9, 7, 3], [10, 20, 30]]

AGG_EDGE = [[1, 2, 3, 4], [None, None], [], [None, 4, None], [2.5, 1.5], [7], [-1, -3, 5, 9], ['a', 5, 1]]

DECISIONS = {
    'loyalty_points': ['NULL spend yields 0', 'negative spend yields 0', 'points capped at 5000', 'unknown or NULL tier earns basic rate'],
    'workdays_between': ['reversed range yields 0', 'Dec 25 is a holiday', 'unparseable date yields -1'],
    'mask_card': ['fewer than 8 digits yields INVALID', 'other non-digit characters yield NULL'],
    'grade_letter': ['percentage rounded half up before grading', 'non-positive scale_max yields N/A', 'score above scale_max yields X'],
    'tax_cents': ['half-even rounding', 'rate capped at 3000 bp'],
    'slugify': ['truncate to 40 chars and strip trailing hyphen', 'empty result yields untitled', 'non-ASCII characters dropped without separator'],
    'parcel_fee': ['unknown or NULL zone uses zone 3 rate', 'non-positive weight is free', 'over 30000 g adds 2500 surcharge', 'up to 250 g flat letter rate of 300'],
    'ticket_priority': ['48 hours or more escalates one level', 'out-of-range severity treated as 4'],
    'charm_price': ['prices under 100 cents unchanged'],
    'median_amount': ['even count takes lower middle value'],
}

DECISION_EXAMPLES = {
    'loyalty_points': [(None, 'silver'), (-1234, 'basic'), (300000, 'silver'), (4200, 'platinum')],
    'workdays_between': [('2024-03-08', '2024-03-01'), ('2025-12-24', '2025-12-29'), ('2024-13-45', '2024-12-01')],
    'mask_card': [('99999',), ('41x1 1111 1111 1111',)],
    'grade_letter': [(59.5, 100), (7, 0), (60, 50)],
    'tax_cents': [(450, 100), (20000, 4500)],
    'slugify': [('word ' * 20,), ('???',), ('naïve résumé',)],
    'parcel_fee': [(3000, 9), (-300, 3), (45000, 1), (120, 3)],
    'ticket_priority': [(4, 60), (7, 3)],
    'charm_price': [(75,)],
    'median_amount': [[10, 20, 30, 40, 50, 60]],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, n) in SCALARS.items():
        con.create_function(name, n, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con
