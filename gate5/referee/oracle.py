"""Business-function policy oracle for the company SQL engine.

This module is the reference implementation of company policy for 19 scalar
functions and 1 aggregate.  Every function is deterministic and returns NULL
(None) rather than raising for inputs it does not accept.
"""

import calendar
import datetime
import functools
import math
import re
import sqlite3
import unicodedata
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_INT64_MIN = -(2 ** 63)
_INT64_MAX = 2 ** 63 - 1
_NUM_RE = re.compile(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?')
_DATE_RE = re.compile(
    r'([0-9]{4})-([0-9]{2})-([0-9]{2})'
    r'(?:[ T]([0-9]{2}):([0-9]{2})(?::([0-9]{2})(?:\.[0-9]+)?)?)?'
)
_TIME_RE = re.compile(r'([0-9]{1,2}):([0-9]{2})(?::([0-9]{2}))?')
_CENT = Decimal('0.01')


def _clean(value):
    """Coerce a Python result into something SQLite accepts without error."""
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value if _INT64_MIN <= value <= _INT64_MAX else None
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, str):
        return value
    return None


def _safe(fn):
    @functools.wraps(fn)
    def wrapper(*args):
        try:
            return _clean(fn(*args))
        except Exception:
            return None
    return wrapper


def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _num(x):
    """SQL value -> int/float, accepting numeric text; anything else -> None."""
    if x is None or isinstance(x, bool):
        return None
    if isinstance(x, int):
        return x
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    if isinstance(x, str):
        s = x.strip()
        if not _NUM_RE.fullmatch(s):
            return None
        try:
            return int(s)
        except ValueError:
            pass
        v = float(s)
        return v if math.isfinite(v) else None
    return None


def _whole(x):
    """Number that must be a whole number -> int, else None."""
    n = _num(x)
    if n is None:
        return None
    if isinstance(n, float):
        if not n.is_integer():
            return None
        return int(n)
    return n


def _dec(x):
    if isinstance(x, Decimal):
        return x
    if isinstance(x, int):
        return Decimal(x)
    return Decimal(repr(float(x)))


def _money(d, rounding=ROUND_HALF_UP):
    return float(_dec(d).quantize(_CENT, rounding=rounding)) + 0.0


def _parse_dt(x):
    if not isinstance(x, str):
        return None
    m = _DATE_RE.fullmatch(x.strip())
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    hh = int(m.group(4)) if m.group(4) else 0
    mi = int(m.group(5)) if m.group(5) else 0
    ss = int(m.group(6)) if m.group(6) else 0
    try:
        return datetime.datetime(y, mo, d, hh, mi, ss)
    except ValueError:
        return None


def _parse_date(x):
    dt = _parse_dt(x)
    return None if dt is None else dt.date()


# ---------------------------------------------------------------------------
# 1. invoice_total
# ---------------------------------------------------------------------------

@_safe
def invoice_total(subtotal, tax_pct, discount_pct):
    s = _num(subtotal)
    t = _num(tax_pct)
    if s is None or t is None:
        return None
    if discount_pct is None:
        d = 0
    else:
        d = _num(discount_pct)
        if d is None:
            return None
    if t < 0 or d < 0:
        return None
    disc = min(_dec(d), Decimal(25))
    sub = _dec(s)
    tax_factor = 1 + _dec(t) / 100
    if sub < 0:
        amount = sub * tax_factor
    else:
        amount = sub * (1 - disc / 100) * tax_factor
    return _money(amount)


# ---------------------------------------------------------------------------
# 2. late_fee
# ---------------------------------------------------------------------------

@_safe
def late_fee(balance, days_late):
    b = _num(balance)
    n = _num(days_late)
    if b is None or n is None:
        return None
    if b <= 0 or n <= 5:
        return 0.0
    periods = math.ceil(n / 30)
    bal = _dec(b)
    fee = bal * Decimal('0.015') * periods
    fee = max(fee, Decimal('10'))
    fee = min(fee, bal * Decimal('0.10'))
    return _money(fee)


# ---------------------------------------------------------------------------
# 3. business_days
# ---------------------------------------------------------------------------

_HOLIDAYS = ((1, 1), (7, 4), (12, 25), (12, 26))


@_safe
def business_days(start_date, end_date):
    a = _parse_date(start_date)
    b = _parse_date(end_date)
    if a is None or b is None:
        return None
    sign = 1
    if b < a:
        a, b, sign = b, a, -1
    total = (b - a).days
    weeks, rem = divmod(total, 7)
    count = weeks * 5
    d = a + datetime.timedelta(days=weeks * 7)
    for _ in range(rem):
        d += datetime.timedelta(days=1)
        if d.weekday() < 5:
            count += 1
    for y in range(a.year, b.year + 1):
        for (m, dd) in _HOLIDAYS:
            h = datetime.date(y, m, dd)
            if a < h <= b and h.weekday() < 5:
                count -= 1
    return sign * count


# ---------------------------------------------------------------------------
# 4. fiscal_quarter
# ---------------------------------------------------------------------------

@_safe
def fiscal_quarter(date):
    if _is_int(date):
        if not (10000101 <= date <= 99991231):
            return None
        y, md = divmod(date, 10000)
        m, d = divmod(md, 100)
        try:
            dt = datetime.datetime(y, m, d)
        except ValueError:
            return None
    else:
        dt = _parse_dt(date)
        if dt is None:
            return None
    day = dt.date()
    if dt.hour >= 18:
        day += datetime.timedelta(days=1)
    fy = day.year + 1 if day.month >= 4 else day.year
    q = ((day.month - 4) % 12) // 3 + 1
    return 'FY%d-Q%d' % (fy, q)


# ---------------------------------------------------------------------------
# 5. sku_normalize
# ---------------------------------------------------------------------------

_SKU_RE = re.compile(r'([A-Z]{3})([0-9OIL]{1,4})')
_SKU_FIX = str.maketrans('OIL', '011')


@_safe
def sku_normalize(code):
    if not isinstance(code, str):
        return None
    s = re.sub(r'[\s\-_./]', '', code).upper()
    m = _SKU_RE.fullmatch(s)
    if not m:
        return None
    prefix, digits = m.groups()
    if prefix == 'TST':
        return None
    digits = digits.translate(_SKU_FIX).rjust(4, '0')
    return prefix + '-' + digits


# ---------------------------------------------------------------------------
# 6. star_rating
# ---------------------------------------------------------------------------

@_safe
def star_rating(score):
    s = _num(score)
    if s is None:
        return None
    if s <= 0 or s > 100:
        return None
    return min(5, max(1, math.ceil(s / 20)))


# ---------------------------------------------------------------------------
# 7. shipping_cost
# ---------------------------------------------------------------------------

_ZONES = {
    'A': (Decimal('5.00'), Decimal('1.20')),
    'B': (Decimal('8.00'), Decimal('1.80')),
    'C': (Decimal('12.00'), Decimal('2.50')),
}


@_safe
def shipping_cost(weight_kg, zone):
    w = _num(weight_kg)
    if w is None or w <= 0:
        return None
    if not isinstance(zone, str):
        return None
    rate = _ZONES.get(zone.strip().upper())
    if rate is None:
        return None
    billable = math.ceil(w)
    cost = rate[0] + rate[1] * billable
    if billable > 30:
        cost += Decimal('20.00')
    return _money(cost)


# ---------------------------------------------------------------------------
# 8. mask_card
# ---------------------------------------------------------------------------

@_safe
def mask_card(card_number):
    if _is_int(card_number):
        if card_number < 0:
            return None
        s = str(card_number)
    elif isinstance(card_number, str):
        s = re.sub(r'[ \-]', '', card_number.strip())
    else:
        return None
    if not re.fullmatch(r'[0-9]{12,19}', s):
        return None
    return '*' * (len(s) - 4) + s[-4:]


# ---------------------------------------------------------------------------
# 9. name_initials
# ---------------------------------------------------------------------------

_PARTICLES = frozenset([
    'van', 'von', 'de', 'del', 'della', 'der', 'den', 'da', 'di', 'du',
    'la', 'le', 'dos', 'das', 'bin', 'al',
])


@_safe
def name_initials(full_name):
    if not isinstance(full_name, str):
        return None
    letters = []
    for word in full_name.split():
        if word in _PARTICLES:
            continue
        for part in word.split('-'):
            for ch in part:
                if ch.isalpha():
                    letters.append(ch.upper())
                    break
    if not letters:
        return None
    if len(letters) > 3:
        letters = letters[:2] + [letters[-1]]
    return ''.join(letters)


# ---------------------------------------------------------------------------
# 10. age_band
# ---------------------------------------------------------------------------

_BANDS = ((24, '18-24'), (34, '25-34'), (44, '35-44'), (54, '45-54'), (64, '55-64'))


@_safe
def age_band(birth_date, as_of_date):
    b = _parse_date(birth_date)
    a = _parse_date(as_of_date)
    if b is None or a is None:
        return None
    if b > a:
        return None
    bm, bd = b.month, b.day
    if bm == 2 and bd == 29 and not calendar.isleap(a.year):
        bd = 28
    age = a.year - b.year - (1 if (a.month, a.day) < (bm, bd) else 0)
    if age > 120:
        return None
    if age < 18:
        return 'MINOR'
    for hi, label in _BANDS:
        if age <= hi:
            return label
    return '65+'


# ---------------------------------------------------------------------------
# 11. next_billing_date
# ---------------------------------------------------------------------------

@_safe
def next_billing_date(start_date, months):
    d = _parse_date(start_date)
    if d is None:
        return None
    n = _whole(months)
    if n is None or n < 1:
        return None
    total = d.year * 12 + (d.month - 1) + n
    y, m0 = divmod(total, 12)
    if y > 9999:
        return None
    last = calendar.monthrange(y, m0 + 1)[1]
    res = datetime.date(y, m0 + 1, min(d.day, last))
    wd = res.weekday()
    if wd == 5:
        res += datetime.timedelta(days=2)
    elif wd == 6:
        res += datetime.timedelta(days=1)
    return res.isoformat()


# ---------------------------------------------------------------------------
# 12. loyalty_tier
# ---------------------------------------------------------------------------

_TIERS = ('Bronze', 'Silver', 'Gold', 'Platinum')


@_safe
def loyalty_tier(points, years_member):
    if points is None:
        p = 0
    else:
        p = _num(points)
        if p is None:
            return None
    if p < 0:
        return None
    if years_member is None:
        y = 0
    else:
        y = _num(years_member)
        if y is None:
            return None
    if p < 1000:
        idx = 0
    elif p < 5000:
        idx = 1
    elif p < 20000:
        idx = 2
    else:
        idx = 3
    if y >= 10:
        idx = min(3, idx + 1)
    return _TIERS[idx]


# ---------------------------------------------------------------------------
# 13. us_phone_e164
# ---------------------------------------------------------------------------

_KEYPAD = {}
for _digit, _letters in (('2', 'ABC'), ('3', 'DEF'), ('4', 'GHI'), ('5', 'JKL'),
                         ('6', 'MNO'), ('7', 'PQRS'), ('8', 'TUV'), ('9', 'WXYZ')):
    for _ch in _letters:
        _KEYPAD[_ch] = _digit
_EXT_RE = re.compile(r'\s*(?:x|ext\.?|extension)\s*[0-9]+\s*$', re.IGNORECASE)


@_safe
def us_phone_e164(phone):
    if _is_int(phone):
        if phone < 0:
            return None
        s = str(phone)
    elif isinstance(phone, str):
        s = phone.strip()
    else:
        return None
    s = _EXT_RE.sub('', s).strip()
    if not re.fullmatch(r'[0-9A-Za-z \-.()+]*', s):
        return None
    plus = s.count('+')
    if plus > 1 or (plus == 1 and not s.startswith('+')):
        return None
    digits = ''.join(_KEYPAD.get(c.upper(), c) for c in s if c.isalnum())
    if plus == 1 and not (len(digits) == 11 and digits[0] == '1'):
        return None
    if len(digits) == 11 and digits[0] == '1':
        digits = digits[1:]
    if len(digits) != 10:
        return None
    if digits[0] in '01' or digits[3] in '01':
        return None
    return '+1' + digits


# ---------------------------------------------------------------------------
# 14. prorate_charge
# ---------------------------------------------------------------------------

@_safe
def prorate_charge(monthly_price, days_used, days_in_month):
    p = _num(monthly_price)
    u = _num(days_used)
    if p is None or u is None:
        return None
    if days_in_month is None:
        dim = 30
    else:
        dim = _num(days_in_month)
        if dim is None:
            return None
    if p < 0 or dim <= 0:
        return None
    if u <= 0:
        return 0.0
    if u >= dim:
        amount = _dec(p)
    else:
        amount = _dec(p) * _dec(u) / _dec(dim)
    return _money(amount, ROUND_CEILING)


# ---------------------------------------------------------------------------
# 15. title_slug
# ---------------------------------------------------------------------------

_TRANSLIT = {
    'ß': 'ss', 'æ': 'ae', 'Æ': 'AE', 'ø': 'o', 'Ø': 'O', 'œ': 'oe',
    'Œ': 'OE', 'đ': 'd', 'Đ': 'D', 'ł': 'l', 'Ł': 'L', 'þ': 'th', 'Þ': 'TH',
}
_SLUG_MAX = 50


@_safe
def title_slug(title):
    if not isinstance(title, str):
        return None
    s = ''.join(_TRANSLIT.get(c, c) for c in title)
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.replace('&', ' and ')
    s = re.sub("['’‘`]", '', s)
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    if len(s) > _SLUG_MAX:
        cut = s[:_SLUG_MAX]
        if s[_SLUG_MAX] != '-':
            i = cut.rfind('-')
            if i > 0:
                cut = cut[:i]
        s = cut.strip('-')
    return s or None


# ---------------------------------------------------------------------------
# 16. tip_share
# ---------------------------------------------------------------------------

_NICKEL = Decimal('0.05')


@_safe
def tip_share(bill, tip_pct, people):
    b = _num(bill)
    if b is None or b < 0:
        return None
    if tip_pct is None:
        t = 18
    else:
        t = _num(tip_pct)
        if t is None:
            return None
    if t < 0:
        t = 0
    n = _whole(people)
    if n is None or n < 1:
        return None
    share = _dec(b) * (1 + _dec(t) / 100) / n
    nickels = (share / _NICKEL).to_integral_value(rounding=ROUND_CEILING)
    return float(nickels * _NICKEL) + 0.0


# ---------------------------------------------------------------------------
# 17. shift_hours
# ---------------------------------------------------------------------------

def _parse_hm(x):
    if not isinstance(x, str):
        return None
    m = _TIME_RE.fullmatch(x.strip())
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    if h > 23 or mi > 59:
        return None
    if m.group(3) is not None and int(m.group(3)) > 59:
        return None
    return h * 60 + mi


@_safe
def shift_hours(start_time, end_time):
    a = _parse_hm(start_time)
    b = _parse_hm(end_time)
    if a is None or b is None:
        return None
    minutes = (b - a) % 1440
    q, r = divmod(minutes, 15)
    rounded = (q + (1 if r >= 8 else 0)) * 15
    if rounded > 360:
        rounded -= 30
    return rounded / 60


# ---------------------------------------------------------------------------
# 18. weekly_pay
# ---------------------------------------------------------------------------

@_safe
def weekly_pay(hours, hourly_rate):
    h = _num(hours)
    r = _num(hourly_rate)
    if h is None or r is None:
        return None
    if h < 0 or h > 100 or r < 0:
        return None
    hrs = _dec(h)
    rate = max(_dec(r), Decimal(15))
    regular = min(hrs, Decimal(40))
    overtime = min(max(hrs - 40, Decimal(0)), Decimal(20))
    double = max(hrs - 60, Decimal(0))
    pay = rate * regular + rate * Decimal('1.5') * overtime + rate * 2 * double
    return _money(pay)


# ---------------------------------------------------------------------------
# 19. isbn13
# ---------------------------------------------------------------------------

def _isbn10_ok(s):
    total = sum((10 - i) * (10 if c == 'X' else int(c)) for i, c in enumerate(s))
    return total % 11 == 0


def _ean_check(d12):
    total = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(d12))
    return str((10 - total % 10) % 10)


@_safe
def isbn13(isbn):
    if _is_int(isbn):
        if isbn < 0:
            return None
        s = str(isbn)
        if len(s) <= 10:
            s = s.zfill(10)
    elif isinstance(isbn, str):
        s = re.sub(r'[ \-]', '', isbn.strip()).upper()
    else:
        return None
    if re.fullmatch(r'[0-9]{9}[0-9X]', s):
        if not _isbn10_ok(s):
            return None
        core = '978' + s[:9]
        return core + _ean_check(core)
    if re.fullmatch(r'97[89][0-9]{10}', s):
        return s if _ean_check(s[:12]) == s[12] else None
    return None


# ---------------------------------------------------------------------------
# 20. nps_score (aggregate)
# ---------------------------------------------------------------------------

class NpsScore:
    def __init__(self):
        self.n = 0
        self.promoters = 0
        self.detractors = 0

    def step(self, value):
        try:
            v = _num(value)
            if v is None or v < 0 or v > 10:
                return
            r = int(_dec(v).quantize(Decimal(1), rounding=ROUND_HALF_UP))
            self.n += 1
            if r >= 9:
                self.promoters += 1
            elif r <= 6:
                self.detractors += 1
        except Exception:
            pass

    def finalize(self):
        try:
            if self.n < 3:
                return None
            x = Decimal(100 * (self.promoters - self.detractors)) / Decimal(self.n)
            return int(x.quantize(Decimal(1), rounding=ROUND_HALF_UP))
        except Exception:
            return None


# ---------------------------------------------------------------------------
# Public tables
# ---------------------------------------------------------------------------

SPEC = {
    'invoice_total': 'invoice_total(subtotal, tax_pct, discount_pct): Amount due on an invoice: the subtotal less the customer discount percentage, plus sales tax percentage, in currency to the cent.',
    'late_fee': 'late_fee(balance, days_late): Late-payment fee on an overdue invoice balance: 1.5% of the balance for every started 30-day period the payment is late.',
    'business_days': 'business_days(start_date, end_date): Number of working days after start_date up to and including end_date (weekends excluded), used for SLA and delivery-time reporting; dates are ISO YYYY-MM-DD.',
    'fiscal_quarter': 'fiscal_quarter(date): Fiscal quarter label such as FY2027-Q1 for a transaction date; the fiscal year starts on 1 April and is named after the calendar year in which it ends.',
    'sku_normalize': 'sku_normalize(code): Canonical form AAA-0000 (three letters, hyphen, four digits) of a product SKU as typed by staff or customers.',
    'star_rating': 'star_rating(score): Star rating from 1 to 5 shown on product pages for a 0-100 review score.',
    'shipping_cost': 'shipping_cost(weight_kg, zone): Parcel shipping charge for a package weight and destination zone: zone A 5.00 + 1.20 per kg, zone B 8.00 + 1.80 per kg, zone C 12.00 + 2.50 per kg.',
    'mask_card': 'mask_card(card_number): Card number masked for receipts and support screens so that only the last four digits remain visible.',
    'name_initials': "name_initials(full_name): Uppercase initials of a person's full name, used for avatars and compact staff rosters.",
    'age_band': 'age_band(birth_date, as_of_date): Marketing age band (18-24, 25-34, 35-44, 45-54, 55-64 or 65+) of a customer on a given date; dates are ISO YYYY-MM-DD.',
    'next_billing_date': 'next_billing_date(start_date, months): ISO date on which a subscription is billed a given number of months after its start date, on the same day of the month.',
    'loyalty_tier': 'loyalty_tier(points, years_member): Loyalty programme tier of a customer: Bronze below 1,000 points, Silver from 1,000, Gold from 5,000 and Platinum from 20,000.',
    'us_phone_e164': 'us_phone_e164(phone): North American phone number as typed into web forms, normalised to E.164 format (+1 followed by ten digits).',
    'prorate_charge': 'prorate_charge(monthly_price, days_used, days_in_month): Prorated subscription charge for a partial month, proportional to the days of service used.',
    'title_slug': 'title_slug(title): URL slug for a blog post or product page title: lowercase words and numbers joined by single hyphens.',
    'tip_share': 'tip_share(bill, tip_pct, people): Amount each diner pays when a restaurant bill plus a tip percentage is split evenly across the party.',
    'shift_hours': 'shift_hours(start_time, end_time): Paid hours for one work shift, from clock-in and clock-out times given as HH:MM.',
    'weekly_pay': 'weekly_pay(hours, hourly_rate): Gross weekly pay for an hourly employee, with hours beyond 40 paid at time-and-a-half.',
    'isbn13': 'isbn13(isbn): The 13-digit ISBN (978 prefix, digits only) used in our catalogue for a book identified by its ISBN-10.',
    'nps_score': 'nps_score(rating): Net Promoter Score of a set of 0-10 survey ratings: percentage of promoters (9-10) minus percentage of detractors (0-6), as a whole number.',
}

SCALARS = {
    'invoice_total': (invoice_total, 3),
    'late_fee': (late_fee, 2),
    'business_days': (business_days, 2),
    'fiscal_quarter': (fiscal_quarter, 1),
    'sku_normalize': (sku_normalize, 1),
    'star_rating': (star_rating, 1),
    'shipping_cost': (shipping_cost, 2),
    'mask_card': (mask_card, 1),
    'name_initials': (name_initials, 1),
    'age_band': (age_band, 2),
    'next_billing_date': (next_billing_date, 2),
    'loyalty_tier': (loyalty_tier, 2),
    'us_phone_e164': (us_phone_e164, 1),
    'prorate_charge': (prorate_charge, 3),
    'title_slug': (title_slug, 1),
    'tip_share': (tip_share, 3),
    'shift_hours': (shift_hours, 2),
    'weekly_pay': (weekly_pay, 2),
    'isbn13': (isbn13, 1),
}

AGGREGATE = ('nps_score', NpsScore)

TYPICAL = {
    'invoice_total': [(100, 8, 10), (250, 5, 0), (80, 10, 5), (1200, 7.5, 15)],
    'late_fee': [(1000, 45), (2000, 10), (5000, 75), (800, 31)],
    'business_days': [('2026-03-02', '2026-03-06'), ('2026-03-06', '2026-03-09'),
                      ('2026-02-02', '2026-02-16'), ('2026-05-04', '2026-05-29')],
    'fiscal_quarter': [('2026-05-15',), ('2026-11-02',), ('2027-02-20',), ('2026-08-31',)],
    'sku_normalize': [('abc-1234',), ('XYZ 0042',), ('kln5678',), ('Def-9001',)],
    'star_rating': [(45,), (72,), (15,), (93,), (33,)],
    'shipping_cost': [(2, 'A'), (5, 'B'), (10, 'C'), (3, 'C')],
    'mask_card': [('4111111111111111',), ('5500005555555559',), ('4012888888881881',),
                  ('378282246310005',)],
    'name_initials': [('John Smith',), ('mary ann jones',), ('Alice Walker',), ('Robert Downey',)],
    'age_band': [('1990-05-10', '2026-01-01'), ('2000-03-15', '2026-06-01'),
                 ('1955-07-04', '2026-10-01'), ('1980-01-20', '2026-03-01'),
                 ('2005-02-10', '2026-05-01')],
    'next_billing_date': [('2026-01-12', 1), ('2026-03-10', 3), ('2026-07-22', 3),
                          ('2026-10-06', 3), ('2026-09-14', 3)],
    'loyalty_tier': [(500, 1), (2500, 3), (7000, 2), (25000, 4)],
    'us_phone_e164': [('(415) 555-0132',), ('212.555.0198',), ('646 555 0123',), ('3125550147',)],
    'prorate_charge': [(30, 10, 30), (62, 15, 31), (100, 14, 28), (90, 20, 30)],
    'title_slug': [('Hello World',), ('Top 10 Gift Ideas',), ('Spring Sale: Up to 50% Off',),
                   ('  Our New Office  ',)],
    'tip_share': [(100, 20, 4), (60, 15, 3), (80, 10, 2), (45, 20, 1)],
    'shift_hours': [('09:00', '13:30'), ('08:15', '12:15'), ('13:00', '17:45'), ('07:30', '11:45')],
    'weekly_pay': [(38, 20), (45, 20), (40, 18.5), (50, 22)],
    'isbn13': [('0306406152',), ('0-19-852663-6',), ('1-56619-909-3',), ('0-262-03384-4',)],
}

EDGE = {
    'invoice_total': [
        (100, 8, 40), (100, 8, 25), (-50, 10, 10), (1.25, 0, 10), (100, 8, None),
        (100, None, 10), (None, 8, 10), (100, -5, 0), ('250.00', '5', '0'), (0, 8, 10),
    ],
    'late_fee': [
        (1000, 5), (1000, 6), (200, 20), (50, 20), (1000, 400),
        (0, 50), (-100, 50), (1000, -3), (1000, 30.5), (None, 10),
    ],
    'business_days': [
        ('2026-12-24', '2026-12-28'), ('2025-12-31', '2026-01-02'),
        ('2026-06-29', '2026-07-06'), ('2025-12-24', '2025-12-29'),
        ('2026-03-06', '2026-03-02'), ('2026-03-02', '2026-03-02'),
        ('2026-02-30', '2026-03-02'), ('2026-03-02 09:30', '2026-03-06T17:00'),
        (20260302, '2026-03-06'), (None, '2026-03-06'),
    ],
    'fiscal_quarter': [
        ('2026-03-31 18:00',), ('2026-03-31 17:59',), ('2026-12-31 23:30',),
        ('2026-06-30T18:00:00',), (20260401,), (20261340,), ('20260401',),
        ('2026-13-01',), (None,), ('2026-04-01',),
    ],
    'sku_normalize': [
        ('abc-0O42',), ('ABC-I23L',), ('abc-42',), ('ABC-12345',), ('tst-1234',),
        ('AB-1234',), ('  qrs_77 ',), (1234,), ('ABC-',), (None,),
    ],
    'star_rating': [
        (20,), (40,), (80,), (0,), (100,), (101,), (-5,), (80.01,), ('60',), (0.5,),
    ],
    'shipping_cost': [
        (2.1, 'A'), (30, 'A'), (30.2, 'A'), (31, 'C'), (2, 'a'),
        (2, ' b '), (2, 'D'), (0, 'A'), (0.3, 'C'), (5, None),
    ],
    'mask_card': [
        ('4111 1111 1111 1111',), ('4111-1111-1111-1111',), (4111111111111111,),
        ('123456789012',), ('12345678901',), ('1234567890123456789',),
        ('12345678901234567890',), ('4111x11111111111',), ('',), (None,),
    ],
    'name_initials': [
        ('Ludwig van Beethoven',), ('Van Morrison',), ('Mary-Jane Watson',),
        ('John Ronald Reuel Tolkien',), ('Jean-Luc de la Cruz-Ortiz',),
        ("seán o'brien",), ('cher',), ('   ',), (42,), (None,),
    ],
    'age_band': [
        ('2008-10-27', '2026-10-27'), ('2008-10-28', '2026-10-27'),
        ('2008-02-29', '2026-02-28'), ('2008-02-29', '2026-02-27'),
        ('1961-06-15', '2026-06-15'), ('2030-01-01', '2026-01-01'),
        ('1890-01-01', '2026-01-01'), ('1990-05-10', None),
        ('1990-02-30', '2026-01-01'), ('2026-01-01', '2026-01-01'),
    ],
    'next_billing_date': [
        ('2026-02-08', 1), ('2026-08-14', 3), ('2026-01-31', 1), ('2026-03-31', 1),
        ('2027-12-31', 2), ('2026-08-31', 6), ('2026-05-08', 0), ('2026-05-08', 1.5),
        ('2026-05-08', '2'), ('2026-05-08', 100000),
    ],
    'loyalty_tier': [
        (500, 10), (25000, 15), (4999, 9), (4999, 10), (999.99, 0),
        (None, 2), (-1, 2), (1000, None), ('abc', 1), (None, 12),
    ],
    'us_phone_e164': [
        ('1-800-FLOWERS',), ('+1 415 555 0132',), ('14155550132',),
        ('(415) 555-0132 x204',), ('415-555-0132 ext. 7',), ('015-555-0132',),
        ('415-155-0132',), ('+44 20 7946 0958',), (4155550132,), ('555-0132',),
    ],
    'prorate_charge': [
        (10, 1, 3), (50, 40, 30), (30, 10, None), (31, 10, None), (30, 0, 30),
        (30, -5, 30), (-30, 10, 30), (30, 10, 0), (19.99, 7, 31), (None, 10, 30),
    ],
    'title_slug': [
        ('Café Déjà Vu',), ('Fish & Chips',), ("Don't Panic",),
        ('It’s Here',), ('Straße Guide',),
        ('The Complete Beginners Guide to Sourdough Baking at Home in Small Kitchens',),
        ('!!!',), ('東京ガイド',), (2026,), (None,),
    ],
    'tip_share': [
        (100, 18, 3), (100, None, 4), (100, 20, 0), (100, 20, 2.5), (100, -10, 2),
        (-50, 10, 2), (10, 15, 3), (99.99, 20, 7), (100, 20, None), (100, 20, 4.0),
    ],
    'shift_hours': [
        ('22:00', '02:00'), ('09:00', '17:00'), ('09:00', '15:07'), ('09:00', '15:08'),
        ('09:00', '09:00'), ('9:05', '12:00'), ('21:00', '09:00'), ('25:00', '12:00'),
        ('08:00:59', '12:00:00'), ('09:00', None),
    ],
    'weekly_pay': [
        (65, 20), (60, 20), (40, 10), (100, 20), (101, 20),
        (-1, 20), (0, 20), (40.33, 17.17), (1, 15.005), (None, 20),
    ],
    'isbn13': [
        ('0306406153',), ('9780306406157',), ('9780306406158',), (306406152,),
        ('080442957x',), ('0 306 40615 2',), ('123',), ('X306406152',),
        ('979-10-90636-07-1',), (None,),
    ],
}

AGG_TYPICAL = [
    [10, 9, 8, 7, 3],
    [10, 10, 9, 6],
    [5, 6, 7, 8, 9],
    [9, 9, 9, 9],
    [0, 1, 2, 10],
]

AGG_EDGE = [
    [10, 9],
    [],
    [10, None, 9, None, 3],
    [10, 11, -1, 'great', 9, 6],
    [8.5, 6.5, 9, 7],
    [10, 7, 7, 7, 7, 7, 7, 7],
    [3, 7, 7, 7, 7, 7, 7, 7],
    ['9', '10', '4'],
]


def connect():
    conn = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, nargs) in SCALARS.items():
        conn.create_function(name, nargs, fn, deterministic=True)
    conn.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return conn
