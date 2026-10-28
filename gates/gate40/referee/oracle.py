import math
import re
import sqlite3
import unicodedata
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction


def _num(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    if isinstance(x, float) and not math.isfinite(x):
        return None
    return x


def _dec(x):
    return Decimal(str(x))


def _cents(d):
    return float(d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def _parse_date(s):
    if not isinstance(s, str):
        return None
    m = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})', s.strip())
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


# ---------------------------------------------------------------- net_price
def net_price(price, discount_pct):
    p, d = _num(price), _num(discount_pct)
    if p is None or d is None or p < 0:
        return None
    d = max(0, min(50, d))
    return _cents(_dec(p) * (Decimal(100) - _dec(d)) / Decimal(100))


# ---------------------------------------------------------------- add_bdays
def _is_bday(d):
    return d.weekday() < 5 and (d.month, d.day) not in ((12, 25), (1, 1))


def add_bdays(start, n):
    d = _parse_date(start)
    if d is None or isinstance(n, bool) or not isinstance(n, int):
        return None
    if n < 0:
        return None
    n = min(n, 260)
    try:
        while not _is_bday(d):
            d += timedelta(days=1)
        while n > 0:
            d += timedelta(days=1)
            if _is_bday(d):
                n -= 1
    except OverflowError:
        return None
    return d.isoformat()


# ---------------------------------------------------------------- mask_card
def mask_card(card):
    if card is None:
        return None
    if isinstance(card, bool) or isinstance(card, float):
        return None
    s = str(card).replace(' ', '').replace('-', '')
    if not s or not (s.isascii() and s.isdigit()):
        return None
    if len(s) < 8:
        return '*' * len(s)
    return '*' * (len(s) - 4) + s[-4:]


# ------------------------------------------------------------- letter_grade
def letter_grade(score, max_score):
    s, m = _num(score), _num(max_score)
    if s is None or m is None:
        return None
    if m <= 0:
        return 'N/A'
    pct = (_dec(s) / _dec(m) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    for cut, letter in ((90, 'A'), (80, 'B'), (70, 'C'), (60, 'D')):
        if pct >= cut:
            return letter
    return 'F'


# ------------------------------------------------------------------ slugify
def slugify(text):
    if text is None:
        return None
    s = text if isinstance(text, str) else str(text)
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    s = s[:40].rstrip('-')
    return s or 'untitled'


# ---------------------------------------------------------------- ship_cost
_BASE = {'A': 5.0, 'B': 8.0, 'C': 12.0}


def ship_cost(weight_kg, zone):
    w = _num(weight_kg)
    if w is None or not isinstance(zone, str):
        return None
    if w <= 0:
        return 0.0
    base = _BASE.get(zone, _BASE['C'])
    cost = base + 1.5 * math.ceil(w)
    if w > 30:
        cost += 20.0
    return round(cost, 2)


# ---------------------------------------------------------------- bmi_value
def bmi_value(weight_kg, height_cm):
    w, h = _num(weight_kg), _num(height_cm)
    if w is None or h is None or w <= 0 or h <= 0:
        return None
    m = Fraction(str(h)) / 100
    v = Fraction(str(w)) / (m * m)
    return math.floor(v * 10) / 10


# ---------------------------------------------------------------- age_years
def age_years(birth, as_of):
    b, a = _parse_date(birth), _parse_date(as_of)
    if b is None or a is None or a < b:
        return None
    leap = a.year % 4 == 0 and (a.year % 100 != 0 or a.year % 400 == 0)
    bd = (3, 1) if (b.month, b.day) == (2, 29) and not leap else (b.month, b.day)
    return a.year - b.year - (1 if (a.month, a.day) < bd else 0)


# ----------------------------------------------------------------- late_fee
def late_fee(amount_due, days_late):
    a, d = _num(amount_due), _num(days_late)
    if a is None or d is None:
        return None
    if a <= 0 or d <= 0:
        return 0.0
    raw = _dec(a) * _dec(d) / Decimal(100)
    cap = _dec(a) / Decimal(4)
    fee = max(Decimal(5), min(cap, raw))
    return _cents(fee)


# ---------------------------------------------------------------- avg_stars
class AvgStars:
    def __init__(self):
        self.vals = []

    def step(self, value):
        v = _num(value)
        if v is not None and 1 <= v <= 5:
            self.vals.append(Fraction(str(v)))

    def finalize(self):
        if len(self.vals) < 3:
            return None
        mean = sum(self.vals) / len(self.vals)
        return math.floor(mean * 2 + Fraction(1, 2)) / 2


SPEC = {
    'net_price': 'net_price(price, discount_pct): Price in dollars after applying a percentage promotional discount.',
    'add_bdays': "add_bdays(start_date, n): Date (YYYY-MM-DD) that falls n business days after the given start date.",
    'mask_card': 'mask_card(card_number): Display-safe version of a payment card number for receipts and logs.',
    'letter_grade': 'letter_grade(score, max_score): Converts a raw course score into a letter grade A-F.',
    'slugify': 'slugify(title): URL-friendly slug generated from a page or product title.',
    'ship_cost': "ship_cost(weight_kg, zone): Shipping charge in dollars for a parcel going to delivery zone 'A', 'B' or 'C'.",
    'bmi_value': 'bmi_value(weight_kg, height_cm): Body mass index for wellness reports.',
    'age_years': 'age_years(birth_date, as_of_date): Whole years of age on a given date, from YYYY-MM-DD dates.',
    'late_fee': 'late_fee(amount_due, days_late): Late-payment penalty in dollars for an overdue invoice.',
    'avg_stars': 'avg_stars(rating): Aggregate giving the headline star rating shown for a product from individual 1-5 ratings.',
}

SCALARS = {
    'net_price': (net_price, 2),
    'add_bdays': (add_bdays, 2),
    'mask_card': (mask_card, 1),
    'letter_grade': (letter_grade, 2),
    'slugify': (slugify, 1),
    'ship_cost': (ship_cost, 2),
    'bmi_value': (bmi_value, 2),
    'age_years': (age_years, 2),
    'late_fee': (late_fee, 2),
}

AGGREGATE = ('avg_stars', AvgStars)

TYPICAL = {
    'net_price': [(100, 10), (50, 20), (19.99, 0), (80, 25), (200, 15)],
    'add_bdays': [('2024-03-04', 1), ('2024-03-06', 3), ('2024-05-01', 10), ('2024-07-10', 5), ('2024-02-12', 0)],
    'mask_card': [('4111111111111111',), ('5500000000000004',), ('378282246310005',), ('4012888888881881',)],
    'letter_grade': [(45, 50), (70, 100), (5, 10), (8, 10), (95, 100)],
    'slugify': [('Hello World',), ('Q3 Sales Report',), ('Spring Sale 2024',), ('Annual Report - Final',)],
    'ship_cost': [(2, 'A'), (10, 'B'), (1, 'C'), (5, 'A'), (12, 'C')],
    'bmi_value': [(70, 170), (60, 160), (50, 150), (100, 200)],
    'age_years': [('1990-05-15', '2024-05-14'), ('1985-12-01', '2024-12-01'), ('2000-01-01', '2024-06-30'), ('1970-07-20', '2020-01-01')],
    'late_fee': [(1000, 3), (500, 10), (2000, 5), (800, 12)],
}

EDGE = {
    'net_price': [(10.05, 50), (100, 80), (100, 50), (0.01, 50), (-5, 10), (100, -5), (100, 'x'), (None, 5)],
    'add_bdays': [('2024-03-09', 1), ('2024-03-09', 0), ('2024-03-04', -1), ('2024-12-24', 1),
                  ('2024-12-31', 1), ('2024-03-04', 300), ('not a date', 1), ('2024-02-30', 1), ('2024-03-04', None)],
    'mask_card': [('4111-1111-1111-1111',), ('4111 1111 1111 1111',), ('1234567',), ('12345678',),
                  ('41111111abcd1111',), ('',), (4111111111111111,), ('4111/1111/1111/1111',), (None,)],
    'letter_grade': [(89.4, 100), (179, 200), (0, 0), (5, -10), (110, 100), (-5, 100), (59.5, 100), (None, 100)],
    'slugify': [('The quick brown fox jumps over the lazy dog and the cat',), ('Café Münster',), ('!!!',), ('',),
                ('a' * 45,), ('word ' * 10,), (None,), ('  --Mixed   CASE--  ',)],
    'ship_cost': [(0, 'A'), (-2, 'A'), (2.2, 'A'), (30, 'B'), (30.5, 'B'), (3, 'Z'), (3, 'a'), (None, 'A'), (4, None)],
    'bmi_value': [(70, 175), (80, 180), (0, 170), (70, 0), (None, 170), (70, 'x'), (200, 100)],
    'age_years': [('2000-02-29', '2023-02-28'), ('2000-02-29', '2023-03-01'), ('2000-02-29', '2024-02-29'),
                  ('2000-02-29', '2024-02-28'), ('2024-01-01', '2023-01-01'), ('bad', '2024-01-01'),
                  ('2024-06-01', '2024-06-01'), (None, '2024-01-01')],
    'late_fee': [(100, 1), (100, 30), (100, 25), (1000, 0), (1000, -3), (500, 200), (-50, 3), (None, 3)],
}

AGG_TYPICAL = [[4, 5, 4, 5, 4, 5], [3, 3, 3], [2, 4, 3, 5], [1, 1, 1, 1]]
AGG_EDGE = [[5, 5, 4], [5, 6, 4, 3], [4, 5], [None, None, None, None], [1, 2.5, 'x', 5], [4, 4, 4, 5], [0, 0, 0, 5, 5, 5]]

DECISIONS = {
    'net_price': ['discount capped at 50%', 'half-up rounding to cents'],
    'add_bdays': ['weekend start rolls to Monday before counting', 'negative n returns NULL',
                  'Dec 25 and Jan 1 are not business days', 'n capped at 260'],
    'mask_card': ['spaces and dashes stripped from output', 'fewer than 8 digits fully masked', 'other characters give NULL'],
    'letter_grade': ['percent rounded half-up to integer before banding', 'max_score <= 0 gives N/A'],
    'slugify': ['truncate to 40 chars then strip trailing hyphen', 'accents folded to base letters', 'empty result is untitled'],
    'ship_cost': ['weight rounded up to whole kg', 'unknown zone billed at zone C', 'surcharge 20 when weight over 30kg',
                  'non-positive weight costs 0'],
    'bmi_value': ['truncated rather than rounded to 1 decimal'],
    'age_years': ['Feb 29 birthday turns on Mar 1 in non-leap years'],
    'late_fee': ['fee capped at 25% of amount', 'minimum fee of 5.00'],
    'avg_stars': ['result rounded to nearest 0.5 (ties up)', 'ratings outside 1-5 ignored', 'fewer than 3 valid ratings gives NULL'],
}

DECISION_EXAMPLES = {
    'net_price': [(200, 75), (3.45, 50)],
    'add_bdays': [('2024-06-15', 2), ('2024-06-12', -3), ('2025-12-24', 2), ('2024-01-02', 1000)],
    'mask_card': [('3782-822463-10005',), ('123456',), ('4111x11111111111',)],
    'letter_grade': [(69.5, 100), (7, 0)],
    'slugify': [('The quick brown fox jumps over the lazy dog today',), ('Crème Brûlée',), ('***',)],
    'ship_cost': [(7.1, 'B'), (6, 'Q'), (40, 'A'), (0, 'C')],
    'bmi_value': [(90, 190)],
    'age_years': [('1996-02-29', '2022-03-01')],
    'late_fee': [(400, 90), (200, 2)],
    'avg_stars': [[3, 4, 4], [5, 5, 5, 9, -1], [3, 4]],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, n) in SCALARS.items():
        con.create_function(name, n, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con
