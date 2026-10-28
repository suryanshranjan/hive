"""Company SQL function policy (private oracle, set g42)."""
import datetime
import math
import re
import sqlite3
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction


def _num(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    if isinstance(x, float) and not math.isfinite(x):
        return None
    return x


def _text(x):
    if isinstance(x, str):
        return x
    if isinstance(x, int) and not isinstance(x, bool):
        return str(x)
    return None


_DATE_RE = re.compile(r'^(\d{4})-(\d{2})-(\d{2})$')


def _date(x):
    if not isinstance(x, str):
        return None
    m = _DATE_RE.match(x.strip())
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


# ---- late_fee -------------------------------------------------------------
def late_fee(balance_cents, days_late):
    if balance_cents is None or days_late is None:
        return None
    b, d = _num(balance_cents), _num(days_late)
    if b is None or d is None:
        return None
    if b <= 0 or d <= 5:
        return 0
    periods = math.ceil(d / 30)
    fee = math.ceil(Fraction(b) * 2 * periods / 100)
    fee = max(fee, 500)
    fee = min(fee, 5000)
    return int(fee)


# ---- due_date -------------------------------------------------------------
def due_date(invoice_date, terms_days):
    if invoice_date is None or terms_days is None:
        return None
    d, t = _date(invoice_date), _num(terms_days)
    if d is None or t is None:
        return None
    t = int(math.floor(t))
    t = max(0, min(365, t))
    out = d + datetime.timedelta(days=t)
    wd = out.weekday()
    if wd == 5:
        out += datetime.timedelta(days=2)
    elif wd == 6:
        out += datetime.timedelta(days=1)
    return out.isoformat()


# ---- mask_card ------------------------------------------------------------
def mask_card(card_text):
    s = _text(card_text)
    if s is None:
        return None
    digits = re.sub(r'\D', '', s)
    if len(digits) < 12:
        return '*' * len(digits)
    return '*' * (len(digits) - 4) + digits[-4:]


# ---- rating_label ---------------------------------------------------------
def rating_label(avg_score, review_count):
    if avg_score is None or review_count is None:
        return None
    a, n = _num(avg_score), _num(review_count)
    if a is None or n is None:
        return None
    if a < 0 or a > 5:
        return 'Invalid'
    if n < 5:
        return 'Unrated'
    r = Decimal(repr(float(a))).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    if r >= Decimal('4.5'):
        return 'Excellent'
    if r >= Decimal('3.5'):
        return 'Good'
    if r >= Decimal('2.5'):
        return 'Fair'
    return 'Poor'


# ---- normalize_sku --------------------------------------------------------
def normalize_sku(sku_text):
    s = _text(sku_text)
    if s is None:
        return None
    s = re.sub(r'\s+', '-', s.strip().upper())
    s = re.sub(r'[^A-Z0-9-]', '', s)
    if s == '':
        return None
    return s


# ---- shipping_cost --------------------------------------------------------
def shipping_cost(weight_grams, zone):
    if weight_grams is None or zone is None:
        return None
    w, z = _num(weight_grams), _num(zone)
    if w is None or z is None:
        return None
    if w <= 0:
        return 0
    base = {1: 500, 2: 800, 3: 1200}.get(z, 1200)
    cost = base + 100 * math.ceil(w / 500)
    if w > 20000:
        cost += 2500
    return int(min(cost, 9900))


# ---- initials -------------------------------------------------------------
_PARTICLES = {'van', 'von', 'de', 'da', 'di', 'la', 'del', 'der', 'den', 'du', 'le'}


def initials(full_name):
    s = _text(full_name)
    if s is None:
        return None
    out = ''
    for w in s.split():
        if w in _PARTICLES:
            continue
        out += w[0].upper()
    return out or None


# ---- invoice_check_digit --------------------------------------------------
def invoice_check_digit(code):
    s = _text(code)
    if s is None:
        return None
    digits = re.sub(r'\D', '', s)[-12:]
    if digits == '':
        return None
    total = 0
    for i, ch in enumerate(reversed(digits)):
        total += int(ch) * (3 if i % 2 == 0 else 1)
    return (10 - total % 10) % 10


# ---- age_years ------------------------------------------------------------
def age_years(birth_date, as_of_date):
    if birth_date is None or as_of_date is None:
        return None
    b, a = _date(birth_date), _date(as_of_date)
    if b is None or a is None or a < b:
        return None
    bm, bd = b.month, b.day
    leap = a.year % 4 == 0 and (a.year % 100 != 0 or a.year % 400 == 0)
    if bm == 2 and bd == 29 and not leap:
        bd = 28
    years = a.year - b.year
    if (a.month, a.day) < (bm, bd):
        years -= 1
    return years


# ---- nps_score (aggregate) ------------------------------------------------
class NpsScore:
    def __init__(self):
        self.n = 0
        self.p = 0
        self.d = 0

    def step(self, value):
        v = _num(value)
        if v is None or v < 0 or v > 10:
            return
        self.n += 1
        if v >= 9:
            self.p += 1
        elif v <= 6:
            self.d += 1

    def finalize(self):
        if self.n < 5:
            return None
        q = Fraction((self.p - self.d) * 100, self.n)
        r = int(math.floor(abs(q) + Fraction(1, 2)))
        return -r if q < 0 else r


SPEC = {
    'late_fee': 'late_fee(balance_cents, days_late): Late fee in cents charged on an overdue invoice balance.',
    'due_date': 'due_date(invoice_date, terms_days): Payment due date (YYYY-MM-DD) for an invoice issued on a date with net payment terms in days.',
    'mask_card': 'mask_card(card_number): Masked payment card number safe for display on receipts.',
    'rating_label': 'rating_label(avg_score, review_count): Storefront label summarising a product\'s average review score out of 5.',
    'normalize_sku': 'normalize_sku(sku): Canonical form of a product SKU used for catalogue lookups.',
    'shipping_cost': 'shipping_cost(weight_grams, zone): Shipping charge in cents for a parcel by weight and delivery zone (1-3).',
    'initials': 'initials(full_name): Uppercase initials of a person\'s full name for avatar badges.',
    'invoice_check_digit': 'invoice_check_digit(code): Check digit (0-9) appended to an invoice or product reference code.',
    'age_years': 'age_years(birth_date, as_of_date): Whole years of age on a given date, from ISO dates.',
    'nps_score': 'nps_score(score): Net Promoter Score (-100 to 100) over a column of 0-10 survey responses.',
}

SCALARS = {
    'late_fee': (late_fee, 2),
    'due_date': (due_date, 2),
    'mask_card': (mask_card, 1),
    'rating_label': (rating_label, 2),
    'normalize_sku': (normalize_sku, 1),
    'shipping_cost': (shipping_cost, 2),
    'initials': (initials, 1),
    'invoice_check_digit': (invoice_check_digit, 1),
    'age_years': (age_years, 2),
}

AGGREGATE = ('nps_score', NpsScore)

TYPICAL = {
    'late_fee': [(50000, 10), (50000, 45), (100000, 40), (60000, 12), (80000, 75)],
    'due_date': [('2024-03-01', 10), ('2024-03-04', 14), ('2024-05-15', 30),
                 ('2024-01-10', 15), ('2023-12-20', 14)],
    'mask_card': [('4111111111111111',), ('5500000000000004',), ('340000000000009',),
                  ('6011000000000012',)],
    'rating_label': [(4.8, 120), (3.9, 40), (2.7, 15), (1.5, 30), (4.0, 25)],
    'normalize_sku': [('ab 123',), (' xy-9 ',), ('abc',), ('tx 4 blue',)],
    'shipping_cost': [(500, 1), (1200, 2), (2500, 3), (700, 1), (3100, 2)],
    'initials': [('Ada Lovelace',), ('grace hopper',), ('Alan Mathison Turing',), ('Katherine Johnson',)],
    'invoice_check_digit': [('400638133393',), ('590123412345',), ('12345678',), ('96385074',)],
    'age_years': [('1990-05-20', '2024-05-20'), ('1985-11-02', '2024-03-01'),
                  ('2010-01-01', '2020-12-31'), ('1975-07-04', '2025-07-03')],
}

EDGE = {
    'late_fee': [(50000, 6), (50000, 5), (3000, 20), (0, 10), (-500, 40),
                 (250000, 100), (50000, 31), (33321, 10), (None, 10), (50000, 'x')],
    'due_date': [('2024-03-01', 30), ('2024-03-02', 0), ('2024-03-03', 0),
                 ('2024-01-02', 500), ('2024-03-05', -10), ('2024-02-30', 10),
                 ('hello', 5), (None, 5), ('2024-03-04', None), ('2024-03-04', 0)],
    'mask_card': [('4111 1111 1111 1111',), ('4111-1111-1111-1111',), ('12345678',),
                  ('123456789012',), ('12345678901',), ('',), ('abcd',),
                  (4111111111111111,), (None,)],
    'rating_label': [(4.45, 20), (3.45, 20), (3.44, 20), (5.01, 20), (-0.1, 50),
                     (4.0, 4), (7, 2), (5, 5), (0, 5), (None, 10)],
    'normalize_sku': [('ab.cd/12',), ('  tx  4   blue ',), ('!!!',), ('',), (None,),
                      ('A - B',), ('ab--12',), ('Éclair 9',)],
    'shipping_cost': [(20000, 1), (20001, 1), (-5, 2), (1000, 0), (1000, 4),
                      (45000, 2), (1, 1), (None, 1), (1000, None), (0, 2)],
    'initials': [('Ludwig van Beethoven',), ('Robert De Niro',), ('maria de la cruz',),
                 ('',), ('   ',), ('Mary-Jane Smith',), ('van',), ('Cher',),
                 ('  ada   lovelace ',), ('Jean Van Damme',)],
    'invoice_check_digit': [('4006-3813-3393',), ('INV 590123412345',),
                            ('1234567890123456789',), ('0',), ('',), ('abc',),
                            (4006381333,), (None,)],
    'age_years': [('2000-02-29', '2023-02-28'), ('2000-02-29', '2023-02-27'),
                  ('2000-02-29', '2024-02-29'), ('1990-06-15', '1990-06-15'),
                  ('1990-06-15', '1990-06-14'), ('1990-13-01', '2020-01-01'),
                  ('1985-12-31', '2024-12-30'), ('1985-12-31', '2024-12-31'),
                  (None, '2020-01-01')],
}

AGG_TYPICAL = [
    [10, 10, 9, 9, 8, 7, 3, 10, 5, 10],
    [9, 9, 9, 10, 8, 8, 6, 5, 9, 10],
    [10, 9, 9, 8, 7, 8, 6, 3, 2, 10],
    [10, 10, 10, 10, 9, 9, 8, 8],
]

AGG_EDGE = [
    [9, None, 10, 5, 3, 8, 7],
    [10, 10, 10, 10],
    [],
    [10, 9, 8, 12, 100, -5, 3, 7, 'x'],
    [10, 8, 8, 8, 8, 8, 8, 8],
    [0, 0, 0, 8, 8, 8, 8, 8],
    [9.0, 6.5, 6, 10.0, 9, 3.5],
    [None, None, None, None, None, None, 9, 9, 9, 9],
]

DECISIONS = {
    'late_fee': ['grace_period_5_days', 'minimum_fee_500', 'cap_5000', 'fee_rounds_up'],
    'due_date': ['weekend_due_rolls_to_monday', 'terms_capped_365', 'negative_terms_are_zero'],
    'mask_card': ['non_digits_dropped', 'under_12_digits_fully_masked'],
    'rating_label': ['unrated_under_5_reviews', 'out_of_range_is_invalid', 'round_to_tenth_half_up_first'],
    'normalize_sku': ['punctuation_removed', 'empty_result_is_null'],
    'shipping_cost': ['oversize_surcharge_over_20kg', 'unknown_zone_priced_as_zone_3',
                      'nonpositive_weight_free', 'cost_capped_9900'],
    'initials': ['lowercase_particles_skipped'],
    'invoice_check_digit': ['non_digits_ignored', 'only_last_12_digits_used'],
    'age_years': ['feb29_birthday_on_feb28_in_common_years'],
    'nps_score': ['out_of_range_or_nonnumeric_ignored', 'under_5_valid_is_null',
                  'round_half_away_from_zero'],
}

DECISION_EXAMPLES = {
    'late_fee': [(50000, 4), (4000, 10), (100000, 90), (41221, 12)],
    'due_date': [('2024-06-07', 1), ('2022-05-04', 400), ('2024-08-14', -3)],
    'mask_card': [('5500.0000.0000.0004',), ('123456',)],
    'rating_label': [(4.46, 50), (6.2, 50), (4.0, 3)],
    'normalize_sku': [('r2_d2#',), ('@#$',)],
    'shipping_cost': [(30000, 3), (1500, 9), (0, 1), (60000, 1)],
    'initials': [('Vincent van Gogh',)],
    'invoice_check_digit': [('5901 2341 2345',), ('99400638133393',)],
    'age_years': [('2004-02-29', '2021-02-28')],
    'nps_score': [[10, 9, 3, 7, 8, 15, -2, 99], [9, 9, 9, 9],
                  [10, 10, 10, 8, 8, 8, 8, 8]],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, nargs) in SCALARS.items():
        con.create_function(name, nargs, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con
