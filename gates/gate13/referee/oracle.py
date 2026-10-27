"""Business function policy for the SQL engine (20 functions: 19 scalars, 1 aggregate)."""

import datetime
import math
import re
import sqlite3
import unicodedata
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP


# ---------------------------------------------------------------- helpers

def _num(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return None
    return x


def _dec(x):
    return Decimal(repr(x)) if isinstance(x, float) else Decimal(x)


def _cents(d, rounding=ROUND_HALF_UP):
    return float(d.quantize(Decimal('0.01'), rounding=rounding))


def _date(s, seps='-'):
    if not isinstance(s, str):
        return None
    m = re.fullmatch(r'(\d{4})([%s])(\d{2})\2(\d{2})' % re.escape(seps), s)
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(3)), int(m.group(4)))
    except ValueError:
        return None


# ---------------------------------------------------------------- 1 decision

def tip_amount(bill, pct):
    bill, pct = _num(bill), _num(pct)
    if bill is None or pct is None:
        return None
    return _cents(_dec(bill) * _dec(pct) / 100, ROUND_CEILING)


def initials(name):
    if not isinstance(name, str):
        return None
    out = []
    for word in name.split():
        for part in word.split('-'):
            if part:
                out.append(part[0].upper())
    return ''.join(out)


def days_between(d1, d2):
    a, b = _date(d1), _date(d2)
    if a is None or b is None:
        return None
    return abs((b - a).days)


def mask_card(card):
    if isinstance(card, int) and not isinstance(card, bool):
        card = str(card)
    if not isinstance(card, str):
        return None
    digits = card.replace(' ', '').replace('-', '')
    if not re.fullmatch(r'[0-9]{5,}', digits):
        return None
    return '*' * (len(digits) - 4) + digits[-4:]


def grade_letter(score):
    score = _num(score)
    if score is None:
        return None
    if score > 100:
        return 'A+'
    for cut, letter in ((90, 'A'), (80, 'B'), (70, 'C'), (60, 'D')):
        if score >= cut:
            return letter
    return 'F'


# ---------------------------------------------------------------- 2 decisions

def late_fee(days_late, amount_due):
    days, amount = _num(days_late), _num(amount_due)
    if days is None or amount is None:
        return None
    if days <= 0 or amount <= 0:
        return 0.0
    fee = _dec(amount) * Decimal('0.02') * _dec(days)
    fee = min(fee, _dec(amount) * Decimal('0.25'))
    fee = max(fee, Decimal('1.00'))
    return _cents(fee)


def normalize_phone(text):
    if isinstance(text, int) and not isinstance(text, bool):
        text = str(text)
    if not isinstance(text, str):
        return None
    digits = re.sub(r'[^0-9]', '', text)
    if len(digits) == 11 and digits[0] == '1':
        digits = digits[1:]
    if len(digits) != 10:
        return None
    return '(%s) %s-%s' % (digits[:3], digits[3:6], digits[6:])


def shipping_cost(weight_kg, zone):
    w, z = _num(weight_kg), _num(zone)
    if w is None or z is None or z != int(z) or int(z) not in (1, 2, 3) or w <= 0:
        return None
    base = {1: 5.0, 2: 7.0, 3: 9.0}[int(z)]
    cost = base + 2.0 * math.ceil(w)
    if w > 30:
        cost += 25.0
    return cost


_SMALL = {'a', 'an', 'the', 'of', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'but', 'by'}


def title_case(text):
    if not isinstance(text, str):
        return None
    parts = re.split(r'(\s+)', text)
    out, idx = [], 0
    for p in parts:
        if not p or p.isspace():
            out.append(p)
            continue
        if len(p) >= 2 and p.isalpha() and p.isupper():
            out.append(p)
        elif idx > 0 and p.lower() in _SMALL:
            out.append(p.lower())
        else:
            out.append(p[0].upper() + p[1:].lower())
        idx += 1
    return ''.join(out)


def percent_change(old, new):
    old, new = _num(old), _num(new)
    if old is None or new is None or old == 0:
        return None
    pct = (_dec(new) - _dec(old)) / abs(_dec(old)) * 100
    return float(pct.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))


# ---------------------------------------------------------------- 3 decisions

_TIERS = {'silver': 1, 'gold': 2, 'platinum': 3}


def loyalty_points(amount_spent, tier):
    amount = _num(amount_spent)
    if amount is None:
        return None
    key = tier.strip().lower() if isinstance(tier, str) else None
    mult = _TIERS.get(key, 1)
    return int(amount) * mult


def sku_check(code):
    if code is None:
        return None
    if not isinstance(code, str):
        return 0
    return 1 if re.fullmatch(r'[A-Za-z]{3}-?[0-9]{5}', code.strip()) else 0


def due_date(start_date, net_days):
    start = _date(start_date)
    if start is None:
        return None
    if net_days is None:
        net = 30
    else:
        net = _num(net_days)
        if net is None:
            return None
        net = max(int(net), 0)
    due = start + datetime.timedelta(days=net)
    if due.weekday() >= 5:
        due += datetime.timedelta(days=7 - due.weekday())
    return due.isoformat()


def discount_price(price, discount_pct):
    price, pct = _num(price), _num(discount_pct)
    if price is None or pct is None:
        return None
    pct = min(max(pct, 0), 50)
    return _cents(_dec(price) * (100 - _dec(pct)) / 100)


def slugify(text):
    if not isinstance(text, str):
        return None
    s = text.replace('&', ' and ')
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:40].rstrip('-')


# ---------------------------------------------------------------- 4 decisions

def age_years(birth_date, on_date):
    b, on = _date(birth_date, '-/'), _date(on_date, '-/')
    if b is None or on is None or on < b:
        return None
    bday = (b.month, b.day)
    if bday == (2, 29) and not _leap(on.year):
        bday = (2, 28)
    age = on.year - b.year - (1 if (on.month, on.day) < bday else 0)
    return None if age > 150 else age


def _leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


_SYMBOLS = {'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥'}


def format_money(amount, currency):
    amount = _num(amount)
    if amount is None or not isinstance(currency, str):
        return None
    code = currency.upper()
    places = Decimal('1') if code == 'JPY' else Decimal('0.01')
    d = _dec(amount).quantize(places, rounding=ROUND_HALF_UP)
    neg = d < 0
    body = '{:,}'.format(abs(d))
    body = (_SYMBOLS[code] + body) if code in _SYMBOLS else (code + ' ' + body)
    return '(' + body + ')' if neg else body


def _bday(s):
    if isinstance(s, str) and len(s) > 10 and s[10] in ' T':
        s = s[:10]
    return _date(s)


def _holidays(y0, y1):
    out = set()
    for y in range(y0 - 1, y1 + 2):
        for m, d in ((1, 1), (12, 25)):
            h = datetime.date(y, m, d)
            if h.weekday() == 5:
                h -= datetime.timedelta(days=1)
            elif h.weekday() == 6:
                h += datetime.timedelta(days=1)
            out.add(h)
    return out


def business_days(start, end):
    a, b = _bday(start), _bday(end)
    if a is None or b is None:
        return None
    sign = 1
    if b < a:
        a, b, sign = b, a, -1
    hol = _holidays(a.year, b.year)
    n, d = 0, a
    while d < b:
        if d.weekday() < 5 and d not in hol:
            n += 1
        d += datetime.timedelta(days=1)
    return sign * n


def rating_stars(score):
    if isinstance(score, str):
        try:
            score = float(score.strip())
        except ValueError:
            return None
    score = _num(score)
    if score is None or score < 0 or score > 10:
        return None
    return max(math.floor(score) / 2.0, 1.0)


class MedianSpend:
    def __init__(self):
        self.vals = []

    def step(self, value):
        if isinstance(value, str):
            try:
                value = float(value.strip())
            except ValueError:
                return
        value = _num(value)
        if value is None or value == 0:
            return
        self.vals.append(float(value))

    def finalize(self):
        if not self.vals:
            return 0.0
        v = sorted(self.vals)
        return v[(len(v) - 1) // 2]


# ---------------------------------------------------------------- registry

SPEC = {
    'tip_amount': 'tip_amount(bill, pct): suggested tip in dollars for a restaurant bill at the given tip percentage.',
    'initials': "initials(full_name): a person's initials in upper case, for badges and avatars.",
    'days_between': "days_between(date1, date2): number of calendar days between two ISO dates (YYYY-MM-DD).",
    'mask_card': 'mask_card(card_number): payment card number masked for display, showing only the last four digits.',
    'grade_letter': 'grade_letter(score): letter grade (A-F) for a 0-100 training assessment score.',
    'late_fee': 'late_fee(days_late, amount_due): late-payment fee in dollars, accruing at 2% of the amount due per day late.',
    'normalize_phone': 'normalize_phone(phone): US phone number normalized to the display format (555) 123-4567.',
    'shipping_cost': 'shipping_cost(weight_kg, zone): parcel shipping charge in dollars for a weight in kg to delivery zone 1, 2 or 3.',
    'title_case': 'title_case(text): headline-style capitalisation for product and report titles.',
    'percent_change': 'percent_change(old_value, new_value): percentage change from the old value to the new one, to one decimal place.',
    'loyalty_points': "loyalty_points(amount_spent, tier): loyalty points earned on a purchase for the customer's tier (silver, gold, platinum).",
    'sku_check': 'sku_check(code): 1 if the text is a valid product SKU of the form ABC-12345, else 0.',
    'due_date': 'due_date(invoice_date, net_days): payment due date (ISO) for an invoice with net payment terms.',
    'discount_price': 'discount_price(price, discount_pct): sale price in dollars after applying a percentage discount.',
    'slugify': 'slugify(title): URL slug for a page title: lower case words joined by hyphens.',
    'age_years': 'age_years(birth_date, on_date): age in completed years of a person on a given date.',
    'format_money': "format_money(amount, currency): amount formatted for invoices with currency symbol and thousands separators, e.g. $1,234.50.",
    'business_days': 'business_days(start_date, end_date): number of working days from the start date up to (not including) the end date.',
    'rating_stars': 'rating_stars(score): converts a 0-10 review score into a star rating out of 5, in half stars.',
    'median_spend': 'median_spend(amount): median customer spend over a set of orders.',
}

SCALARS = {
    'tip_amount': (tip_amount, 2),
    'initials': (initials, 1),
    'days_between': (days_between, 2),
    'mask_card': (mask_card, 1),
    'grade_letter': (grade_letter, 1),
    'late_fee': (late_fee, 2),
    'normalize_phone': (normalize_phone, 1),
    'shipping_cost': (shipping_cost, 2),
    'title_case': (title_case, 1),
    'percent_change': (percent_change, 2),
    'loyalty_points': (loyalty_points, 2),
    'sku_check': (sku_check, 1),
    'due_date': (due_date, 2),
    'discount_price': (discount_price, 2),
    'slugify': (slugify, 1),
    'age_years': (age_years, 2),
    'format_money': (format_money, 2),
    'business_days': (business_days, 2),
    'rating_stars': (rating_stars, 1),
}

AGGREGATE = ('median_spend', MedianSpend)

TYPICAL = {
    'tip_amount': [(50, 20), (80, 15), (42.5, 20), (100, 18)],
    'initials': [('John Smith',), ('ada lovelace',), ('Grace Brewster Hopper',), ('alan turing',)],
    'days_between': [('2024-01-01', '2024-01-31'), ('2024-02-01', '2024-03-01'),
                     ('2023-12-25', '2024-01-01'), ('2024-07-04', '2024-07-14')],
    'mask_card': [('4111111111111111',), ('5500000000000004',), ('340000000000009',), ('6011000990139424',)],
    'grade_letter': [(95,), (85,), (72,), (50,)],
    'late_fee': [(3, 1000), (5, 500), (10, 200), (1, 250)],
    'normalize_phone': [('5551234567',), ('555-123-4567',), ('(555) 123 4567',), ('555.987.6543',)],
    'shipping_cost': [(2, 1), (5, 1), (3, 2), (1, 3), (10, 2)],
    'title_case': [('hello world',), ('monthly sales report',), ('jOHN sMITH',), ('big data platform',)],
    'percent_change': [(100, 120), (200, 150), (50, 75), (80, 100)],
    'loyalty_points': [(19.99, 'silver'), (100, 'gold'), (50.5, 'platinum'), (10, 'silver')],
    'sku_check': [('ABC-12345',), ('XYZ-00001',), ('AB-12345',), ('ABCD-12345',), ('ABC-1234',)],
    'due_date': [('2024-01-01', 30), ('2024-03-01', 14), ('2024-05-06', 10), ('2024-09-02', 60)],
    'discount_price': [(100, 10), (80, 25), (19.99, 0), (200, 50)],
    'slugify': [('Hello World',), ('Top 10 Tips!',), ('Quarterly Report, 2024',), ('  Spaces  everywhere ',)],
    'age_years': [('1990-05-15', '2024-05-14'), ('1990-05-15', '2024-05-15'),
                  ('2000-01-01', '2024-06-30'), ('1985-12-31', '2025-01-01')],
    'format_money': [(1234.5, 'USD'), (99.99, 'EUR'), (1000000, 'GBP'), (0.5, 'USD')],
    'business_days': [('2024-03-04', '2024-03-08'), ('2024-03-04', '2024-03-11'),
                      ('2024-03-01', '2024-03-04'), ('2024-06-03', '2024-06-17')],
    'rating_stars': [(8,), (6,), (10,), (7,), (5,)],
}

EDGE = {
    'tip_amount': [(33.33, 15), (10.01, 15), (0, 20), (None, 15), (50, 0), (-20, 10), ('abc', 10), (19.99, 18)],
    'initials': [('  John   Smith ',), ('',), (None,), ('Jean-Luc Picard',), ('Madonna',),
                 ("o'brien pat",), (123,), ('-x y',)],
    'days_between': [('2024-03-10', '2024-03-01'), ('2024-02-30', '2024-03-01'), (None, '2024-01-01'),
                     ('2024-05-05', '2024-05-05'), ('2023-01-01', '2025-01-01'), ('2024/01/01', '2024/01/02'),
                     ('2024-1-5', '2024-01-10')],
    'mask_card': [('4111 1111 1111 1111',), ('1234',), ('',), (None,), ('abcd1234',),
                  (4111111111111111,), ('12345',), ('4111.1111.1111.1111',)],
    'grade_letter': [(90,), (89.99,), (100,), (0,), (-5,), (None,), ('x',), (60,), (100.5,)],
    'late_fee': [(0, 1000), (-2, 100), (13, 100), (1, 10), (30, 1000), (None, 100), (5, 0), (2, 'x')],
    'normalize_phone': [('1-555-123-4567',), ('+1 (555) 123-4567',), ('123456',), ('25551234567',),
                        ('',), (None,), ('555-1234-56789',), (5551234567,)],
    'shipping_cost': [(2.3, 1), (30, 1), (30.5, 1), (0, 1), (5, 4), (None, 1), (5, None), (0.1, 3), (5, 1.5)],
    'title_case': [('the lord of the rings',), ('',), (None,), ('a',), ('I',), ('  spaced   out  ',),
                   ('USA today',), ('well-known brand',), ('NASA and the moon',)],
    'percent_change': [(0, 0), (0, 10), (-100, -50), (None, 5), (100, 100), (3, 4), (7, 8), (100, 'x')],
    'loyalty_points': [(100, ' Gold '), (100, 'diamond'), (100, None), (-25.5, 'gold'), (0, 'gold'),
                       (None, 'gold'), (100, 'PLATINUM'), ('50', 'gold')],
    'sku_check': [('abc-12345',), (' ABC-12345 ',), ('ABC12345',), ('',), (None,), ('ABC--12345',),
                  ('ABC 12345',), (12345,)],
    'due_date': [('2024-03-01', 15), ('2024-03-01', None), ('2024-03-01', -5), ('2024-02-30', 10),
                 (None, 10), ('2024-03-02', 0), ('2024-03-01', 10.7), ('2024-03-01', 'x')],
    'discount_price': [(100, 75), (100, -10), (0.05, 50), (None, 10), (100, None), (0, 20),
                       (10.45, 10), (100, 50.5)],
    'slugify': [('Salt & Pepper',), ('Café Déjà Vu',),
                ('The Complete Guide to Enterprise Data Warehousing in 2024',), ('',), (None,), ('!!!',),
                ('already-a-slug',), ('AT&T',)],
    'age_years': [('2000-02-29', '2023-02-28'), ('2000-02-29', '2024-02-28'), ('2024-01-01', '2023-01-01'),
                  ('1800-01-01', '2024-01-01'), ('1990/05/15', '2024/05/15'), (None, '2024-01-01'),
                  ('bad', '2024-01-01'), ('2020-08-08', '2020-08-08'), ('1874-01-01', '2024-01-01')],
    'format_money': [(-12, 'USD'), (1500, 'JPY'), (1234.5, 'CHF'), (10, 'usd'), (0, 'USD'),
                     (None, 'USD'), (5, None), (1234.567, 'USD'), (-0.001, 'USD'), (2.5, 'jpy')],
    'business_days': [('2024-03-08', '2024-03-04'), ('2024-12-23', '2024-12-27'), ('2022-12-23', '2022-12-28'),
                      ('2024-03-04 09:00', '2024-03-08 17:00'), ('2024-03-04', '2024-03-04'),
                      ('2024-02-30', '2024-03-04'), (None, '2024-03-04'), ('2024-03-09', '2024-03-11')],
    'rating_stars': [(7.9,), (0,), (1,), (2.5,), (10.5,), (-1,), ('8',), ('abc',), (None,)],
}

AGG_TYPICAL = [[10, 20, 30], [5, 1, 3, 9, 7], [100.5, 200.25, 50]]

AGG_EDGE = [
    [10, 20, 30, 40],
    [0, 0, 10, 20, 30],
    [None, None],
    ['15', 'x', 5, 25],
    [0],
    [None, 10, 20, 30],
    [-5, 5, 15],
]

DECISIONS = {
    'tip_amount': ['rounds up to the next cent'],
    'initials': ['each part of a hyphenated name gives an initial'],
    'days_between': ['result is absolute (order of dates ignored)'],
    'mask_card': ['spaces and dashes stripped before masking'],
    'grade_letter': ['scores above 100 get A+'],
    'late_fee': ['fee capped at 25% of amount due', 'minimum fee $1.00 when late'],
    'normalize_phone': ['11 digits with leading 1: country code dropped', 'not 10 digits after cleanup: NULL'],
    'shipping_cost': ['weight rounded up to whole kg', 'over 30 kg: $25 heavy surcharge'],
    'title_case': ['small words lower case except first word', 'all-caps acronyms kept'],
    'percent_change': ['old value 0: NULL', 'negative old value: divide by its absolute value'],
    'loyalty_points': ['tier trimmed and case-insensitive', 'unknown or missing tier earns as silver',
                       'negative amount deducts points, truncated toward zero'],
    'sku_check': ['lower-case letters accepted', 'surrounding whitespace ignored', 'dash optional'],
    'due_date': ['weekend due date moves to next Monday', 'missing net_days defaults to 30',
                 'negative net_days treated as 0'],
    'discount_price': ['discount capped at 50%', 'negative discount treated as 0', 'round half up to cents'],
    'slugify': ['& becomes "and"', 'accents transliterated', 'max 40 chars, trailing hyphen trimmed'],
    'age_years': ['Feb 29 birthday counts on Feb 28 in non-leap years', 'on_date before birth: NULL',
                  'age over 150: NULL', 'slash-separated dates accepted'],
    'format_money': ['negative in parentheses', 'JPY has no decimals', 'unknown code: "CODE 1,234.50"',
                     'currency code case-insensitive'],
    'business_days': ['end before start: negative count', 'Jan 1 and Dec 25 are holidays',
                      'weekend holiday observed on Fri (Sat) or Mon (Sun)', 'time portion ignored'],
    'rating_stars': ['half-star rounding is downward', 'minimum 1.0 star', 'score outside 0-10: NULL',
                     'numeric text accepted'],
    'median_spend': ['even count: lower middle value', 'zero amounts excluded',
                     'numeric text parsed, other text ignored', 'no amounts: 0.0'],
}

DECISION_EXAMPLES = {
    'tip_amount': [(12.34, 15)],
    'initials': [('Mary-Kate Olsen',)],
    'days_between': [('2025-06-30', '2025-06-01')],
    'mask_card': [('5500-0000-0000-0004',)],
    'grade_letter': [(105,)],
    'late_fee': [(20, 400), (2, 20)],
    'normalize_phone': [('15559876543',), ('55512345',)],
    'shipping_cost': [(4.01, 2), (40, 3)],
    'title_case': [('war and peace',), ('new IBM servers',)],
    'percent_change': [(0, 25), (-50, -25)],
    'loyalty_points': [(40, 'GOLD'), (40, 'bronze'), (-9.99, 'silver')],
    'sku_check': [('qrs-55555',), ('\tDEF-67890\n',), ('GHI67890',)],
    'due_date': [('2024-06-05', 3), ('2024-04-01', None), ('2024-04-03', -2)],
    'discount_price': [(60, 80), (45, -5), (1.25, 10)],
    'slugify': [('R&D Budget',), ('Crème Brûlée',),
                ('Annual Shareholder Meeting Minutes and Resolutions',)],
    'age_years': [('2004-02-29', '2021-02-28'), ('2010-06-01', '2009-06-01'),
                  ('1850-03-03', '2020-03-03'), ('2001/09/09', '2021/09/09')],
    'format_money': [(-250.75, 'EUR'), (98765.4, 'JPY'), (42, 'SEK'), (3.5, 'gbp')],
    'business_days': [('2024-04-12', '2024-04-08'), ('2025-12-22', '2025-12-29'),
                      ('2021-12-27', '2022-01-04'), ('2024-05-06T08:00', '2024-05-10')],
    'rating_stars': [(9.6,), (0.5,), (11,), ('6',)],
    'median_spend': [[1, 2, 3, 4, 5, 6], [0, 0, 0, 7, 8, 9], ['12.5', 'n/a', 30, 1], [None]],
}


def connect():
    conn = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, nargs) in SCALARS.items():
        conn.create_function(name, nargs, fn, deterministic=True)
    conn.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return conn
