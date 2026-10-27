"""Business function policy for the company SQL engine (Gate 15 oracle).

Standard library only. Every function returns NULL for NULL inputs unless a
policy decision says otherwise, and none of them raises.
"""

import calendar
import datetime
import math
import re
import sqlite3
import unicodedata
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP


# ---------------------------------------------------------------- helpers

def _num(x):
    """int/float value, or None for NULL, text, blobs and non-finite floats."""
    if isinstance(x, bool):
        return int(x)
    if isinstance(x, int):
        return x
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    return None


def _text(x):
    if x is None:
        return None
    if isinstance(x, str):
        return x
    if isinstance(x, (bytes, bytearray)):
        return bytes(x).decode('utf-8', 'replace')
    return str(x)


def _dec(x):
    return Decimal(repr(x)) if isinstance(x, float) else Decimal(x)


_DATE_RE = re.compile(r'\d{4}-\d{2}-\d{2}')


def _date(x):
    if not isinstance(x, str) or not _DATE_RE.fullmatch(x):
        return None
    try:
        return datetime.date(int(x[:4]), int(x[5:7]), int(x[8:]))
    except ValueError:
        return None


# ---------------------------------------------------------------- scalars

def loyalty_tier(points):
    p = _num(points)
    if p is None:
        return None
    if p < 0:
        return 'review'
    if p < 1000:
        return 'bronze'
    if p < 5000:
        return 'silver'
    if p < 20000:
        return 'gold'
    return 'platinum'


def invoice_number(seq):
    n = _num(seq)
    if n is None:
        return None
    n = int(n)
    if n <= 0:
        return 'INV-VOID'
    return 'INV-%06d' % n


def initials(full_name):
    s = _text(full_name)
    if s is None:
        return None
    return ''.join(w[0].upper() for w in s.replace('-', ' ').split())


def reading_time(article_text):
    s = _text(article_text)
    if s is None:
        return None
    n = len(s.split())
    return -(-n // 200)


def hours_billed(minutes):
    m = _num(minutes)
    if m is None:
        return None
    if m <= 0:
        return 0.0
    return math.ceil(m / 15) * 0.25


def stars_display(rating):
    r = _num(rating)
    if r is None:
        return None
    k = max(0, min(5, int(math.floor(r))))
    return '★' * k + '☆' * (5 - k)


def days_overdue(due_date, paid_date):
    d, p = _date(due_date), _date(paid_date)
    if d is None or p is None:
        return None
    if d.weekday() >= 5:
        d += datetime.timedelta(days=7 - d.weekday())
    late = (p - d).days
    return 0 if late <= 3 else late


def mask_card(card_number):
    s = _text(card_number)
    if s is None:
        return None
    s = s.replace(' ', '').replace('-', '')
    if len(s) < 12:
        return '*' * len(s)
    return '*' * (len(s) - 4) + s[-4:]


def phone_format(phone):
    s = _text(phone)
    if s is None:
        return None
    digits = ''.join(c for c in s if c in '0123456789')
    if len(digits) == 11 and digits[0] == '1':
        digits = digits[1:]
    if len(digits) != 10:
        return phone
    return '(%s) %s-%s' % (digits[:3], digits[3:6], digits[6:])


_BANNED_PASSWORDS = {
    'password', 'password1', 'password123', 'qwerty', 'qwerty123',
    '12345678', '123456789', 'letmein', 'welcome1', 'iloveyou', 'admin123',
}


def password_strength(password):
    s = _text(password)
    if s is None:
        return None
    if s.lower() in _BANNED_PASSWORDS:
        return 0
    score = 0
    score += len(s) >= 8
    score += any(c.islower() for c in s) and any(c.isupper() for c in s)
    score += any(c.isdigit() for c in s)
    score += any(not c.isalnum() and not c.isspace() for c in s)
    return int(score)


def split_bill(total, people):
    t, n = _num(total), _num(people)
    if t is None or n is None:
        return None
    n = int(math.floor(n))
    if n < 1:
        n = 1
    amount = _dec(t)
    if n >= 8:
        amount = amount * Decimal('1.10')
    share = (amount / n).quantize(Decimal('0.01'), rounding=ROUND_CEILING)
    return float(share)


_SKU_RE = re.compile(r'([A-Z]{3})[ \-]?([0-9O]{1,5})')


def sku_normalize(sku):
    s = _text(sku)
    if s is None:
        return None
    m = _SKU_RE.fullmatch(s.strip().upper())
    if not m:
        return 'UNKNOWN'
    return '%s-%s' % (m.group(1), m.group(2).replace('O', '0').zfill(5))


def _is_business_day(d):
    return d.weekday() < 5 and (d.month, d.day) not in ((1, 1), (12, 25))


def business_days_add(start_date, days):
    d, n = _date(start_date), _num(days)
    if d is None or n is None:
        return None
    n = int(math.floor(n))
    if n < 0 or n > 1000000:
        return None
    one = datetime.timedelta(days=1)
    try:
        while not _is_business_day(d):
            d += one
        count = 0
        while count < n:
            d += one
            if _is_business_day(d):
                count += 1
    except OverflowError:
        return None
    return d.isoformat()


def grade_letter(score):
    s = _num(score)
    if s is None:
        return None
    if s < 0 or s > 100:
        return 'X'
    r = int((_dec(s)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    if r >= 90:
        letter = 'A'
    elif r >= 80:
        letter = 'B'
    elif r >= 70:
        letter = 'C'
    elif r >= 60:
        letter = 'D'
    else:
        return 'F'
    if r == 100 or r % 10 >= 7:
        letter += '+'
    return letter


def prorate_rent(monthly_rent, move_in_date):
    r, d = _num(monthly_rent), _date(move_in_date)
    if r is None or d is None:
        return None
    if d.day >= 25:
        return 0.0
    dim = 28 if d.month == 2 else calendar.monthrange(d.year, d.month)[1]
    days = dim - d.day + 1
    amount = (_dec(r) * days / dim).quantize(Decimal(1), rounding=ROUND_FLOOR)
    return float(amount)


def late_fee(balance, days_late):
    b, n = _num(balance), _num(days_late)
    if b is None or n is None:
        return None
    if b < 10 or n <= 0:
        return 0.0
    periods = math.ceil(n / 30)
    bal = _dec(b)
    fee = bal * Decimal('0.015') * periods
    fee = min(fee, bal * Decimal('0.25'))
    fee = max(fee, Decimal('5'))
    return float(fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def discount_price(price, percent_off):
    p, q = _num(price), _num(percent_off)
    if p is None or q is None:
        return None
    if p < 1:
        return float(p)
    q = max(0, min(q, 70))
    sale = _dec(p) * (100 - _dec(q)) / 100
    sale = sale.quantize(Decimal('0.01'), rounding=ROUND_FLOOR)
    if sale < 1:
        sale = Decimal(1)
    return float(sale)


_ZONE_RATES = {1: 1.5, 2: 2.5, 3: 4.0}


def parcel_cost(weight_kg, zone):
    w = _num(weight_kg)
    if w is None or zone is None:
        return None
    if w <= 0:
        return None
    if w > 30:
        return 150.0
    z = _num(zone)
    rate = _ZONE_RATES.get(int(z), 4.0) if z is not None and z == int(z) else 4.0
    return float(4 + math.ceil(w) * rate)


def username_slug(display_name):
    s = _text(display_name)
    if s is None:
        return None
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    words = [''.join(c for c in w if c.isalnum()).lower() for w in s.split()]
    words = [w for w in words if w]
    if len(words) > 2:
        words = [words[0], words[-1]]
    return '.'.join(words)[:20]


# ---------------------------------------------------------------- aggregate

class TypicalOrderValue:
    def __init__(self):
        self.values = []

    def step(self, value):
        v = _num(value)
        if v is not None and v > 0:
            self.values.append(v)

    def finalize(self):
        if not self.values:
            return 0.0
        vals = sorted(self.values)
        return round(float(vals[(len(vals) - 1) // 2]), 2)


# ---------------------------------------------------------------- spec

SPEC = {
    'loyalty_tier': "loyalty_tier(points): membership tier for a loyalty points balance: 'bronze' under 1000 points, 'silver' from 1000, 'gold' from 5000 and 'platinum' from 20000.",
    'invoice_number': "invoice_number(seq): printable invoice number for an invoice sequence number: 'INV-' followed by the number zero-padded to at least 6 digits.",
    'initials': "initials(full_name): a person's initials for badges and avatars: the first letter of each word of the name, upper-cased, with no separators.",
    'reading_time': "reading_time(article_text): estimated reading time of an article in whole minutes, at 200 words per minute.",
    'hours_billed': "hours_billed(minutes): billable hours for a timesheet entry recorded in minutes, billed in quarter-hour increments.",
    'stars_display': "stars_display(rating): a 0-5 product rating shown as five characters of filled '★' and empty '☆' stars.",
    'days_overdue': "days_overdue(due_date, paid_date): how many days late an invoice was paid, given dates as 'YYYY-MM-DD'; 0 when it was paid on or before the due date.",
    'mask_card': "mask_card(card_number): a payment card number masked for receipts and screens: every digit replaced by '*' except the last four.",
    'phone_format': "phone_format(phone): a 10-digit national phone number formatted for display as '(555) 123-4567'.",
    'password_strength': "password_strength(password): a 0-4 strength score for a new password: one point each for a length of at least 8, both upper- and lower-case letters, a digit, and a symbol.",
    'split_bill': "split_bill(total, people): each diner's share of a restaurant bill split evenly, in currency with two decimals.",
    'sku_normalize': "sku_normalize(sku): a product SKU in canonical form: the three-letter family code in upper case, a hyphen, then the five-digit item number.",
    'business_days_add': "business_days_add(start_date, days): the date ('YYYY-MM-DD') that falls a given number of business days after a start date, skipping weekends.",
    'grade_letter': "grade_letter(score): letter grade for a training exam scored out of 100: A for 90 and above, B for the 80s, C for the 70s, D for the 60s, F below 60.",
    'prorate_rent': "prorate_rent(monthly_rent, move_in_date): rent due for a tenant's first, partial month: the monthly rent prorated by the days from the move-in date ('YYYY-MM-DD') to the end of that month, inclusive.",
    'late_fee': "late_fee(balance, days_late): late fee on an overdue account balance: 1.5% of the balance for each 30 days the payment is late.",
    'discount_price': "discount_price(price, percent_off): sale price of an item after a percentage discount, in currency to the cent.",
    'parcel_cost': "parcel_cost(weight_kg, zone): shipping charge for a parcel: a 4.00 base fee plus a per-kg rate of 1.50 in zone 1, 2.50 in zone 2 and 4.00 in zone 3.",
    'username_slug': "username_slug(display_name): a login username built from a person's display name: lower case, with the words joined by dots.",
    'typical_order_value': "typical_order_value(amount): aggregate; the typical order value across a set of orders, taken as the median order amount.",
}

SCALARS = {
    'loyalty_tier': (loyalty_tier, 1),
    'invoice_number': (invoice_number, 1),
    'initials': (initials, 1),
    'reading_time': (reading_time, 1),
    'hours_billed': (hours_billed, 1),
    'stars_display': (stars_display, 1),
    'days_overdue': (days_overdue, 2),
    'mask_card': (mask_card, 1),
    'phone_format': (phone_format, 1),
    'password_strength': (password_strength, 1),
    'split_bill': (split_bill, 2),
    'sku_normalize': (sku_normalize, 1),
    'business_days_add': (business_days_add, 2),
    'grade_letter': (grade_letter, 1),
    'prorate_rent': (prorate_rent, 2),
    'late_fee': (late_fee, 2),
    'discount_price': (discount_price, 2),
    'parcel_cost': (parcel_cost, 2),
    'username_slug': (username_slug, 1),
}

AGGREGATE = ('typical_order_value', TypicalOrderValue)


# ---------------------------------------------------------------- examples

_VOCAB = ('the market opened early and traders watched prices climb while '
          'analysts debated what the quarterly numbers would mean for '
          'customers suppliers and staff across every region').split()


def _words(n, sep=' '):
    return sep.join(_VOCAB[i % len(_VOCAB)] for i in range(n))


TYPICAL = {
    'loyalty_tier': [(250,), (1500,), (7000,), (45000,)],
    'invoice_number': [(42,), (1001,), (123456,), (7,)],
    'initials': [('ada lovelace',), ('Grace Brewster Hopper',), ('Alan Turing',), ('Linus Torvalds',)],
    'reading_time': [(_words(200),), (_words(400),), (_words(600),), (_words(1000),)],
    'hours_billed': [(60,), (90,), (135,), (480,)],
    'stars_display': [(3,), (5,), (0,), (4,)],
    'days_overdue': [('2025-01-15', '2025-01-25'), ('2025-01-15', '2025-01-10'),
                     ('2025-01-15', '2025-01-15'), ('2025-03-12', '2025-04-11')],
    'mask_card': [('4111111111111111',), ('5500000000000004',), ('340000000000009',), ('6011000000000004',)],
    'phone_format': [('5551234567',), ('2125550199',), ('4155550123',), ('3125550142',)],
    'password_strength': [('abc',), ('Sunshine',), ('Tr0ub4dor&3',), ('kitten12',), ('Abc1!',)],
    'split_bill': [(100, 4), (90, 3), (60.5, 2), (120, 6)],
    'sku_normalize': [('abc-12345',), ('XYZ 00042',), ('kln12345',), ('Def-54321',)],
    'business_days_add': [('2025-01-13', 3), ('2025-01-15', 5), ('2025-01-17', 1), ('2025-03-11', 10)],
    'grade_letter': [(92,), (85,), (72,), (64,), (45,)],
    'prorate_rent': [(3100, '2025-07-17'), (3000, '2025-06-01'), (3000, '2025-09-16'),
                     (3100, '2025-03-02'), (1240, '2025-05-01')],
    'late_fee': [(1000, 30), (1000, 60), (2000, 90), (500, 120)],
    'discount_price': [(100, 20), (59.99, 10), (250, 15), (80, 25)],
    'parcel_cost': [(2, 1), (3, 2), (5, 3), (10, 1)],
    'username_slug': [('Ada Lovelace',), ('alan turing',), ('GRACE HOPPER',), ('Linus Torvalds',)],
}

EDGE = {
    'loyalty_tier': [(0,), (999,), (1000,), (4999,), (5000,), (19999,), (20000,), (-10,), (None,)],
    'invoice_number': [(1,), (999999,), (1000000,), (0,), (-5,), (None,)],
    'initials': [('  Ada   Lovelace ',), ('Mary-Jane Watson',), ('',), ('cher',), (None,),
                 ('Ludwig van Beethoven',)],
    'reading_time': [(_words(100),), (_words(199),), (_words(250),), (_words(401),), ('',), (None,),
                     (_words(400, sep=' \n  '),)],
    'hours_billed': [(0,), (15,), (1,), (59,), (61,), (44.5,), (None,)],
    'stars_display': [(4.9,), (2.5,), (0.99,), (5.0,), (7,), (-2,), (None,)],
    'days_overdue': [('2025-01-15', '2025-01-18'), ('2025-01-15', '2025-01-19'),
                     ('2025-02-15', '2025-02-17'), ('2025-02-15', '2025-02-24'),
                     ('2024-02-28', '2024-03-05'), (None, '2025-01-01'), ('2025-01-15', None),
                     ('2025-13-01', '2025-01-01')],
    'mask_card': [('4111 1111 1111 1111',), ('4111-1111-1111-1111',), ('12345',), ('123456789012',),
                  ('',), (None,), (4111111111111111,)],
    'phone_format': [('15551234567',), ('25551234567',), ('555123456',), (5551234567,), ('',), (None,)],
    'password_strength': [('',), (None,), ('Password1',), ('12345678',), ('abcdefg',), ('ABCDEFGH',),
                          ('my pass word',), ('ÄbcdefgH',)],
    'split_bill': [(100, 3), (10, 0), (200, 8), (70, 7), (80, 10), (0, 5), (None, 4), (100, None)],
    'sku_normalize': [('  abc-12345 ',), ('abc-7',), ('ab-12345',), ('abc-123456',), ('ABC-1O0O1',),
                      ('',), ('12345',), (None,)],
    'business_days_add': [('2025-01-18', 1), ('2025-01-18', 0), ('2025-12-24', 1), ('2025-12-31', 1),
                          ('2025-01-13', 0), ('2025-01-13', -2), ('2025-12-22', 5), (None, 3),
                          ('2025-02-30', 1)],
    'grade_letter': [(100,), (90,), (89.5,), (79.4,), (67,), (59,), (0,), (101,), (-5,), (None,)],
    'prorate_rent': [(3100, '2025-07-31'), (3000, '2025-06-24'), (3000, '2025-06-25'),
                     (1000, '2025-01-15'), (2900, '2024-02-01'), (2800, '2025-02-15'),
                     (1400, '2028-02-08'), (1000, '2025-02-31'), (None, '2025-01-01'), (1000, None)],
    'late_fee': [(1000, 0), (1000, -5), (1000, 1), (1000, 1200), (100, 30), (200, 45), (9.99, 60),
                 (None, 30), (1000, None)],
    'discount_price': [(100, 0), (100, 100), (100, -10), (10.05, 50), (2, 60), (0.5, 20),
                       (None, 10), (100, None)],
    'parcel_cost': [(2.3, 1), (0.1, 2), (30, 3), (30.5, 1), (2, 7), (0, 1), (-3, 2), (None, 1), (2, None)],
    'username_slug': [('José Álvarez',), ("Conan O'Brien",), ('Grace Brewster Murray Hopper',),
                      ('Maximilian Schwarzenegger',), ('Cher',), ('',), ('  Ada   Lovelace  ',), (None,)],
}

AGG_TYPICAL = [
    [10, 20, 30],
    [5.5, 12.25, 40, 8, 100],
    [99.99],
    [3, 1, 2],
]

AGG_EDGE = [
    [10, 20, 30, 40],
    [10, -5, 0, 30, 20],
    [None, 15, None],
    [None, None],
    [-10, 0],
    [12.3456, 1, 50],
    [7, 7, 7, 7],
]


# ---------------------------------------------------------------- private policy

DECISIONS = {
    'loyalty_tier': ['negative balance is tier review'],
    'invoice_number': ['zero or negative sequence gives INV-VOID'],
    'initials': ['each part of a hyphenated name gives an initial'],
    'reading_time': ['partial minutes round up'],
    'hours_billed': ['started quarter hour billed in full (round up)'],
    'stars_display': ['fractional ratings round down', 'out-of-range ratings clamp to 0..5'],
    'days_overdue': ['weekend due date moves to next Monday', 'up to 3 days late counts as 0; beyond that full count'],
    'mask_card': ['spaces and dashes removed before masking', 'under 12 characters fully masked'],
    'phone_format': ['11 digits starting with 1: country code dropped', 'not 10 digits: input returned unchanged'],
    'password_strength': ['common banned passwords score 0 (case-insensitive)', 'whitespace is not a symbol'],
    'split_bill': ['share rounded up to the cent', 'people below 1 treated as 1', '10% service charge for 8 or more people'],
    'sku_normalize': ['item numbers under 5 digits zero-padded', 'letter O in item number read as zero', 'unparseable SKU gives UNKNOWN'],
    'business_days_add': ['non-business start date rolls forward before counting', '1 Jan and 25 Dec are not business days', 'negative day count gives NULL'],
    'grade_letter': ['fractional scores round half up before grading', 'score outside 0..100 gives X', 'plus for last digit 7-9 (and 100), not for F'],
    'prorate_rent': ['move-in on day 25 or later charges 0', 'amount rounded down to whole unit', 'February always counts 28 days'],
    'late_fee': ['partial 30-day period counts as full', 'fee capped at 25% of balance', 'minimum fee 5.00', 'balance under 10.00 waived (0)'],
    'discount_price': ['discount capped at 70%', 'negative discount treated as 0', 'price rounded down to the cent', 'minimum sale price 1.00; items under 1.00 not discounted'],
    'parcel_cost': ['weight rounded up to whole kg', 'over 30 kg flat freight 150.00', 'unknown zone charged at zone 3 rate', 'zero or negative weight gives NULL'],
    'username_slug': ['accents stripped', 'non-alphanumeric characters dropped', 'only first and last words kept', 'truncated to 20 characters'],
    'typical_order_value': ['even count takes the lower middle value', 'amounts 0 or below excluded', 'result rounded to 2 decimals', 'no qualifying orders gives 0.0'],
}

DECISION_EXAMPLES = {
    'loyalty_tier': [(-1,)],
    'invoice_number': [(-42,)],
    'initials': [('Jean-Luc Picard',)],
    'reading_time': [(_words(30),)],
    'hours_billed': [(106,)],
    'stars_display': [(3.7,), (6,)],
    'days_overdue': [('2025-03-01', '2025-03-07'), ('2025-01-08', '2025-01-10')],
    'mask_card': [('5500 0000 0000 0004',), ('1234567',)],
    'phone_format': [('12125550199',), ('12345',)],
    'password_strength': [('QWERTY123',), ('long pass phrase',)],
    'split_bill': [(10, 3), (45, -2), (90, 9)],
    'sku_normalize': [('qrs-345',), ('MNO-2OO25',), ('widget',)],
    'business_days_add': [('2025-03-08', 2), ('2026-12-24', 1), ('2025-03-10', -1)],
    'grade_letter': [(69.5,), (150,), (88,)],
    'prorate_rent': [(2000, '2025-08-27'), (1000, '2025-07-10'), (2800, '2024-02-10')],
    'late_fee': [(2000, 31), (400, 600), (50, 30), (5, 90)],
    'discount_price': [(200, 90), (50, -20), (7.75, 10), (1.5, 50)],
    'parcel_cost': [(4.01, 2), (45, 2), (3, 0), (-1, 1)],
    'username_slug': [('Zoë Saldaña',), ('Mary-Kate Olsen',), ('John Ronald Reuel Tolkien',),
                      ('Christopher Wellington',)],
    'typical_order_value': [[1, 2, 3, 4, 5, 6], [25, -25, 0, 40, 50], [1.23456, 2.5, 0.9], [None, -3]],
}

HANDBOOK_STATUS = {
    'loyalty_tier': ['clear'],
    'invoice_number': ['omitted'],
    'initials': ['vague'],
    'reading_time': ['clear'],
    'hours_billed': ['clear'],
    'stars_display': ['vague', 'omitted'],
    'days_overdue': ['clear', 'clear'],
    'mask_card': ['omitted', 'vague'],
    'phone_format': ['clear', 'omitted'],
    'password_strength': ['vague', 'omitted'],
    'split_bill': ['clear', 'omitted', 'vague'],
    'sku_normalize': ['clear', 'vague', 'omitted'],
    'business_days_add': ['vague', 'clear', 'omitted'],
    'grade_letter': ['clear', 'omitted', 'vague'],
    'prorate_rent': ['clear', 'vague', 'clear'],
    'late_fee': ['clear', 'clear', 'vague', 'omitted'],
    'discount_price': ['clear', 'vague', 'omitted', 'clear'],
    'parcel_cost': ['clear', 'clear', 'vague', 'omitted'],
    'username_slug': ['vague', 'omitted', 'clear', 'vague'],
    'typical_order_value': ['omitted', 'clear', 'omitted', 'vague'],
}

HANDBOOK = """\
LARKSPUR TRADING CO. - BUSINESS RULES HANDBOOK FOR DATA FUNCTIONS
Internal. Maintained by the Product Office. Revision 7.

Why this handbook exists

For most of the company's history our business rules lived wherever someone
happened to need them: a macro in the finance workbook, a stored procedure in
the old billing system, a script on the warehouse label printer. When the
2019 consolidation moved reporting onto the shared SQL engine, we found three
different answers to "how late was this invoice?" and two different loyalty
tier tables. Since then the Product Office has owned the rules, and the
engine's business functions are the single place they are implemented. This
handbook explains the rules by area of the business, with some of the
history behind them. Where it is silent, the behaviour agreed with the
function owners stands, and engineers should ask rather than guess.

Customers and loyalty

The loyalty programme started in 2016 with three tiers and gained platinum in
2021, when we wanted to recognise our largest trade accounts. Tiers are set
purely by points balance: bronze below 1000 points, silver from 1000, gold
from 5000 and platinum from 20000. Balances can go below zero when points are
clawed back after a returned purchase. Such accounts get no tier at all: the
tier is shown as 'review' until Customer Care has looked at the account.

Badges, avatars and the staff directory use a person's initials. After a
round of complaints from colleagues with double-barrelled names, the badge
team asked that nobody lose half of their name on a badge, and the initials
rule was adjusted accordingly.

Login usernames are made from the display name, in lower case with the words
joined by dots. Only a person's first and last names are used; middle names
are dropped. Usernames still have to survive the directory we migrated from
in 2014, which was fussy about accented letters and had a hard limit on how
long a username could be; the username function takes care of both, and we
still honour that length limit today.

Billing, payments and collections

Invoices carry a printable number made of the prefix INV- and the invoice
sequence number, zero-padded to six digits. Larger sequence numbers simply
print with more digits.

Our payment terms count calendar days from the due date. Because nobody can
pay us on a day the office is shut, a due date that falls on a Saturday or a
Sunday moves to the following Monday. Customers also get a three-day grace
period: a payment received up to three days after the (adjusted) due date
counts as on time, so it is reported as 0 days overdue. Once a payment is
later than that, the full number of days since the due date is reported,
grace days included.

Late fees were introduced in 2018 at 1.5% of the outstanding balance for each
30-day period of lateness. A payment that is even one day into a new 30-day
period is charged for the whole of that period. The total fee on an account
is never more than a quarter of the balance, however late the payment.
Because very small fees cost more to collect than they bring in, a minimum
charge applies whenever a fee is due at all.

Promotions are priced with the discount function. After an incident in 2022
in which a mistyped promotion gave away stock at 95% off, no discount may
take more than 70% off a price; any larger percentage is reduced to 70%.
Data-entry slips in the other direction happen too, and a 'discount' is
never allowed to raise a price. No item is ever sold for less than 1.00
after a discount, and an item whose regular price is already under 1.00 is
sold at its regular price.

The staff canteen and our client dining rooms split bills evenly between
diners. Each share is rounded up to the next cent, so that the restaurant is
never left short. Large tables attract a service charge, which is shared out
along with the bill.

Staff housing

The company lets apartments to relocating staff. Rent for the first, partial
month is prorated by the days from the move-in date to the end of that
month, inclusive. Tenants who move in on the 25th of the month or later pay
nothing for that month; their first rent is the following full month.
February is always treated as a 28-day month, leap year or not, a convention
inherited from the original lease template. Prorated amounts are kept to
tidy figures, always in the tenant's favour.

Time and scheduling

Consultants record time in minutes and bill in quarter hours. Any quarter
hour that has been started is billed in full.

Service-level commitments are counted in business days. Our business days
are Monday to Friday, except 1 January and 25 December, when every office is
closed. Requests that arrive while we are closed are treated a little
differently from those that arrive during the working week, since nobody is
there to receive them.

Catalogue, warehouse and shipping

Every product has a SKU made of a three-letter family code and a five-digit
item number. Older items were catalogued with shorter numbers; they are
padded with leading zeros to five digits. Pickers keying codes by hand
sometimes type a letter where a digit belongs, and the normaliser forgives
the most common such slip.

Parcel charges are a base fee plus a per-kilogram rate for the destination
zone. Weights are rounded up to the next whole kilogram before pricing.
Anything heavier than 30 kg goes as freight at a flat 150.00, whatever the
zone. A parcel addressed with a zone code we do not recognise is still sent
and still charged, at one of the standard zone rates.

Product ratings are shown on the website as five stars, filled and empty.
When an average rating falls between whole stars, the display errs on the
side of modesty.

Security and contact details

Card numbers are never shown in full: receipts and screens show only the
last four digits. Strings that are too short to be a genuine card number get
even stricter treatment.

Phone numbers are displayed in the national format with the area code in
brackets. An eleven-digit number that starts with the country code 1 has the
country code removed before formatting.

New passwords get a strength score from 0 to 4, one point each for length,
mixed case, a digit and a symbol. Security keeps a short list of notoriously
common passwords that score nothing, whatever they contain.

Training academy

The academy grades its internal exams out of 100 on the usual A to F scale.
Fractional scores are rounded to the nearest whole point, with halves
rounded up, before the grade is decided. Strong results near the top of a
band are marked with a plus.

Content

Articles on the intranet and the customer blog show an estimated reading
time at 200 words per minute, always rounded up to the next whole minute.

Reporting

The weekly trading report shows the typical order value, which is the
median order amount rather than the mean, so that a handful of very large
trade orders do not distort the picture. Refunds and zero-value orders, that
is any amount of 0 or below, are left out of the calculation. When a period
has no qualifying orders, the report shows a neutral figure instead of
leaving the cell blank.
"""


# ---------------------------------------------------------------- connection

def connect():
    conn = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, nargs) in SCALARS.items():
        conn.create_function(name, nargs, fn, deterministic=True)
    conn.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return conn
