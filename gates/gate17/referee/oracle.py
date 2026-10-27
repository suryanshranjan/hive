"""Brightwater Supply Co. business functions for the SQL engine: the policy oracle.

Private. Conventions shared by every function (not policy decisions):
NULL in -> NULL out, and an argument of the wrong SQL type gives NULL.
"""
import datetime
import math
import re
import sqlite3
import unicodedata
from decimal import Decimal, ROUND_DOWN, ROUND_CEILING, ROUND_HALF_UP


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _dec(x):
    return Decimal(repr(x)) if isinstance(x, float) else Decimal(x)


CENT = Decimal('0.01')


# ---------------------------------------------------------------- money

def vat_amount(net, rate_pct):
    if not (_num(net) and _num(rate_pct)):
        return None
    vat = _dec(net) * _dec(rate_pct) / 100
    return float(vat.quantize(CENT, rounding=ROUND_DOWN))  # truncate to cents


def late_fee(days_late, amount):
    if not (_num(days_late) and _num(amount)):
        return None
    if amount < 0:                       # credit notes never accrue a fee
        return 0.0
    days = math.ceil(days_late)          # a started day counts as a day
    if days <= 0 or amount == 0:
        return 0.0
    pct = min(days, 25)                  # cap at 25% of the invoice
    fee = (_dec(amount) * pct / 100).quantize(CENT, rounding=ROUND_HALF_UP)
    if fee < 5:                          # minimum fee when any fee applies
        fee = Decimal(5)
    return float(fee)


def pro_rata(monthly_price, days_used, days_in_month):
    if not (_num(monthly_price) and _num(days_used) and _num(days_in_month)):
        return None
    if days_in_month <= 0 or days_used < 0:
        return None
    if days_used >= days_in_month:       # never more than the full price
        return float(_dec(monthly_price))
    share = _dec(monthly_price) * _dec(days_used) / _dec(days_in_month)
    return float(share.quantize(CENT, rounding=ROUND_CEILING))  # round up


_COUPON = re.compile(r'SAVE(\d{1,3})')


def discount_price(price, code):
    if not _num(price):
        return None
    if code is None:                     # no coupon: price unchanged
        return float(price)
    if not isinstance(code, str):
        return None
    m = _COUPON.fullmatch(code.upper())  # codes are case-insensitive
    if not m or int(m.group(1)) == 0:    # unknown code: price unchanged
        return float(price)
    pct = min(int(m.group(1)), 50)       # coupons cut at most 50%
    out = _dec(price) * (100 - pct) / 100
    return float(out.quantize(CENT, rounding=ROUND_HALF_UP))


def charm_price(price):
    if not _num(price):
        return None
    d = _dec(price)
    if d < 1:                            # small prices left alone
        return float(d)
    if d >= 1000:                        # luxury: nearest whole amount
        return float(d.quantize(Decimal(1), rounding=ROUND_HALF_UP))
    whole = d.to_integral_value(rounding=ROUND_DOWN)
    if d == whole:                       # whole amounts drop to the .99 below
        return float(whole - 1 + Decimal('0.99'))
    out = whole + Decimal('0.99')
    return float(max(out, d))


# ---------------------------------------------------------------- customers

def loyalty_points(amount):
    if not _num(amount):
        return None
    if amount < 5:                       # purchases under 5.00 earn nothing
        return 0
    return int(math.floor(amount))


class AvgStarRating:
    def __init__(self):
        self.vals = []

    def step(self, value):
        if not _num(value):
            return
        if value != int(value):          # half stars are not valid ratings
            return
        if 1 <= value <= 5:              # off-scale values skipped
            self.vals.append(int(value))

    def finalize(self):
        if len(self.vals) < 3:           # need at least three ratings
            return None
        avg = Decimal(sum(self.vals)) / len(self.vals)
        return float(avg.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))


def age_band(age):
    if not _num(age):
        return None
    if age < 0 or age > 120:             # implausible ages
        return None
    a = int(math.floor(age))
    if a < 18:
        return 'minor'
    for lo, hi in ((18, 24), (25, 34), (35, 44), (45, 54), (55, 64)):
        if a <= hi:
            return '%d-%d' % (lo, hi)
    return '65+'


# ---------------------------------------------------------------- identifiers

def mask_card(card):
    if not isinstance(card, str):
        return None
    digits = re.sub(r'[ \-]', '', card)  # separators removed first
    if not digits.isdigit() or not digits.isascii() or len(digits) < 12:
        return None
    return '*' * (len(digits) - 4) + digits[-4:]


def iban_check(iban):
    if not isinstance(iban, str):
        return None
    s = iban.replace(' ', '')            # printed groups allowed
    if re.search(r'[a-z]', s):           # lowercase is rejected
        return 0
    if not re.fullmatch(r'[A-Z]{2}\d{2}[A-Z0-9]{11,30}', s):
        return 0
    r = s[4:] + s[:4]
    n = ''.join(str(int(c, 36)) for c in r)
    return 1 if int(n) % 97 == 1 else 0


def phone_e164(phone):
    if not isinstance(phone, str):
        return None
    s = re.sub(r'(ext\.?|x).*$', '', phone.lower())   # drop extensions
    digits = re.sub(r'\D', '', s)
    if s.strip().startswith('+'):
        if digits.startswith('1'):
            return '+' + digits if len(digits) == 11 else None
        return '+' + digits if 7 <= len(digits) <= 15 else None  # foreign kept
    if len(digits) == 10:
        return '+1' + digits
    if len(digits) == 11 and digits.startswith('1'):  # leading 1 accepted
        return '+' + digits
    return None


def invoice_number(year, seq):
    if not (_num(year) and _num(seq)):
        return None
    if year != int(year) or seq != int(seq):
        return None
    year, seq = int(year), int(seq)
    if 0 <= year <= 99:                  # short legacy years
        year += 2000
    if seq <= 0:
        return None
    if seq > 999999:                     # six-digit counter is the limit
        return None
    if year < 1000 or year > 9999:
        return None
    return 'INV-%04d-%06d' % (year, seq)


# ---------------------------------------------------------------- calendar

def _parse_date(s, allow_time=False):
    if not isinstance(s, str):
        return None
    if allow_time and len(s) > 10 and s[10] in ' T':
        s = s[:10]
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', s):
        return None
    try:
        return datetime.date(int(s[:4]), int(s[5:7]), int(s[8:]))
    except ValueError:
        return None


def fiscal_quarter(iso_date):
    d = _parse_date(iso_date, allow_time=True)   # timestamps accepted
    if d is None:
        return None
    if d < datetime.date(2000, 4, 1):            # before first fiscal year
        return None
    fy = d.year + 1 if d.month >= 4 else d.year
    q = ((d.month - 4) % 12) // 3 + 1
    return 'FY%d-Q%d' % (fy, q)


def _workday(d):
    if d.weekday() >= 5:
        return False
    if (d.month, d.day) in ((12, 25), (1, 1)):   # company holidays
        return False
    return True


def business_days(start_date, end_date):
    a = _parse_date(start_date)
    b = _parse_date(end_date)
    if a is None or b is None:
        return None
    if abs((b - a).days) > 366:                  # reporting limit
        return None
    sign = 1
    if b < a:                                    # reversed range: negative
        a, b, sign = b, a, -1
    n = 0
    d = a + datetime.timedelta(days=1)
    while d <= b:
        n += _workday(d)
        d += datetime.timedelta(days=1)
    return sign * n


def minutes_to_hhmm(minutes):
    if not _num(minutes):
        return None
    m = int(math.floor(minutes))
    sign = '-' if m < 0 else ''
    m = abs(m)
    days, rest = divmod(m, 1440)
    hhmm = '%d:%02d' % divmod(rest, 60)
    if days:                                     # day component
        return '%s%dd %s' % (sign, days, hhmm)
    return sign + hhmm


_UNIT = {'d': 8 * 3600, 'h': 3600, 'm': 60, 's': 1}   # a day is 8 hours


def parse_duration(text):
    if not isinstance(text, str):
        return None
    s = re.sub(r'\s+', '', text.lower())        # spaces allowed
    if re.fullmatch(r'\d+', s):                  # bare number = minutes
        return int(s)
    if not re.fullmatch(r'(\d+[dhms])+', s):
        return None
    secs = sum(int(n) * _UNIT[u] for n, u in re.findall(r'(\d+)([dhms])', s))
    return -(-secs // 60)                        # seconds round up


# ---------------------------------------------------------------- people, content

def initials(full_name):
    if not isinstance(full_name, str):
        return None
    parts = [p for p in re.split(r'[\s\-]+', full_name) if p]  # hyphens split
    return ''.join(p[0].upper() for p in parts)


def slugify_title(title):
    if not isinstance(title, str):
        return None
    s = unicodedata.normalize('NFKD', title)
    s = ''.join(c for c in s if not unicodedata.combining(c))  # accents
    s = s.replace('&', ' and ')
    words = re.findall(r'[a-z0-9]+', s.lower())
    if not words:
        return 'untitled'
    slug = ''
    for w in words:                                  # max 40, word boundary
        cand = w if not slug else slug + '-' + w
        if len(cand) > 40:
            break
        slug = cand
    if not slug:
        slug = words[0][:40]
    return slug


def password_strength(pw):
    if not isinstance(pw, str):
        return None
    if 'password' in pw.lower():                     # banned word
        return 0
    score = 0
    score += len(pw) >= 8
    score += any(c.isdigit() for c in pw)
    score += any(c.isupper() for c in pw) and any(c.islower() for c in pw)
    score += any(not c.isalnum() for c in pw)
    return int(score)


# ---------------------------------------------------------------- audits

def grade_rating(score):
    if not _num(score):
        return None
    if score < 0 or score > 100:                     # outside the scale
        return None
    s = int(_dec(score).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    if s == 100:                                     # perfect score
        return 'A+'
    for cut, g in ((90, 'A'), (80, 'B'), (70, 'C'), (60, 'D')):
        if s >= cut:
            return g
    return 'F'


# ---------------------------------------------------------------- registry

SPEC = {
    'vat_amount': 'vat_amount(net, rate_pct): VAT due on a net amount at the given percentage rate, in currency units with cents.',
    'late_fee': 'late_fee(days_late, amount): late fee owed on an overdue invoice, 1% of the invoice amount for each day it is late.',
    'pro_rata': 'pro_rata(monthly_price, days_used, days_in_month): charge for part of a month of a subscription, in proportion to the days used.',
    'discount_price': "discount_price(price, coupon_code): price after applying a coupon code of the form 'SAVEnn', which takes nn percent off.",
    'charm_price': 'charm_price(price): storefront price ending in .99, taken from the list price.',
    'loyalty_points': 'loyalty_points(amount): loyalty points earned on a purchase, one point per whole currency unit spent.',
    'avg_star_rating': 'avg_star_rating(stars): aggregate; average customer star rating (1 to 5 stars) shown on a product page.',
    'age_band': "age_band(age): marketing age band for a customer's age, such as '25-34' or '65+'.",
    'mask_card': 'mask_card(card_number): card number safe for display, with every digit but the last four replaced by *.',
    'iban_check': 'iban_check(iban): 1 if the IBAN passes the ISO 13616 mod-97 checksum, else 0.',
    'phone_e164': "phone_e164(phone): a customer's US phone number in E.164 form, '+1' followed by ten digits.",
    'invoice_number': "invoice_number(year, seq): invoice number 'INV-YYYY-NNNNNN' from the year and the sequence number.",
    'fiscal_quarter': "fiscal_quarter(iso_date): fiscal quarter label 'FYyyyy-Qn' of a date; the fiscal year starts on 1 April and is named after the year in which it ends.",
    'business_days': 'business_days(start_date, end_date): working days (Monday to Friday) after the start date up to and including the end date.',
    'minutes_to_hhmm': "minutes_to_hhmm(minutes): a duration in minutes shown as 'H:MM' on timesheets.",
    'parse_duration': "parse_duration(text): minutes in a duration typed as text, such as '2h' or '1h15m'.",
    'initials': "initials(full_name): a person's initials in capitals, for avatars and sign-offs.",
    'slugify_title': 'slugify_title(title): URL slug of an article title: lowercase words joined by hyphens.',
    'password_strength': 'password_strength(password): strength score 0 to 4: one point each for length 8 or more, a digit, mixed case, and a symbol.',
    'grade_rating': 'grade_rating(score): letter grade of a supplier audit score out of 100: A from 90, B from 80, C from 70, D from 60, else F.',
}

_FUNCS = [vat_amount, late_fee, pro_rata, discount_price, charm_price,
          loyalty_points, age_band, mask_card, iban_check, phone_e164,
          invoice_number, fiscal_quarter, business_days, minutes_to_hhmm,
          parse_duration, initials, slugify_title, password_strength,
          grade_rating]
SCALARS = {f.__name__: (f, f.__code__.co_argcount) for f in _FUNCS}

AGGREGATE = ('avg_star_rating', AvgStarRating)

TYPICAL = {
    'vat_amount': [(100, 20), (59.5, 20), (250, 7), (80, 12.5)],
    'late_fee': [(10, 1000), (5, 2000), (20, 600), (3, 500)],
    'pro_rata': [(30, 10, 30), (31, 15, 31), (100, 14, 28), (60, 5, 30)],
    'discount_price': [(100, 'SAVE10'), (80, 'SAVE25'), (40, 'SAVE5'), (200, 'SAVE15')],
    'charm_price': [(12.3,), (45.5,), (3.1,), (7.99,)],
    'loyalty_points': [(23.4,), (250,), (7.2,), (99.99,)],
    'age_band': [(20,), (30,), (47,), (70,), (58,)],
    'mask_card': [('4111111111111111',), ('5500000000000004',), ('378282246310005',), ('6011000990139424',)],
    'iban_check': [('GB82WEST12345698765432',), ('DE89370400440532013000',), ('GB82WEST12345698765431',), ('FR1420041010050500013M02606',)],
    'phone_e164': [('(555) 123-4567',), ('555.123.4567',), ('555-987-6543',), ('5551230000',)],
    'invoice_number': [(2025, 123), (2024, 1), (2026, 45678), (2025, 999)],
    'fiscal_quarter': [('2025-05-10',), ('2025-08-01',), ('2025-11-30',), ('2026-02-14',)],
    'business_days': [('2025-03-03', '2025-03-07'), ('2025-03-07', '2025-03-10'), ('2025-06-02', '2025-06-16'), ('2025-03-03', '2025-03-03')],
    'minutes_to_hhmm': [(90,), (5,), (600,), (125,)],
    'parse_duration': [('2h',), ('45m',), ('1h15m',), ('3h05m',)],
    'initials': [('john smith',), ('Ada Lovelace',), ('mary ann evans',), ('Plato',)],
    'slugify_title': [('Hello World',), ('Q3 Results: Final!',), ('  Spring   Sale 2025 ',), ('Top 10 Tips',)],
    'password_strength': [('abc',), ('Hello123',), ('Tr0ub4dor&3',), ('sunshine',)],
    'grade_rating': [(95,), (85,), (72,), (40,), (63,)],
}

EDGE = {
    'vat_amount': [(19.99, 20), (7.77, 15), (33.33, 7), (0, 20), (-50, 20), (100, 0), (None, 20), (100, None)],
    'late_fee': [(25, 400), (26, 400), (100, 80), (1, 50), (0, 1000), (-3, 1000), (0.2, 1000), (5, -100), (7, 0), (None, 100)],
    'pro_rata': [(50, 31, 30), (100, 1, 30), (99, 1, 31), (30, 30, 30), (0, 10, 30), (30, 0, 30), (None, 1, 30)],
    'discount_price': [(60, 'Save20'), (100, 'SAVE50'), (100, 'SAVE51'), (100, 'SAVE100'), (100, 'SAVE'), (100, 'SAVE0'), (100, ''), (100, 'XSAVE10'), (None, 'SAVE10')],
    'charm_price': [(100,), (1,), (0.99,), (0,), (999.5,), (1000,), (2345.49,), (None,)],
    'loyalty_points': [(5,), (4.99,), (3,), (0,), (-20,), (1000.5,), (None,)],
    'age_band': [(17,), (18,), (0,), (64,), (65,), (120,), (121,), (None,)],
    'mask_card': [('4012-8888-8888-1881',), ('5105 1051 0510 5100',), ('123456789012',), ('99999999999',), ('1234',), ('',), (None,)],
    'iban_check': [('DE89 3704 0044 0532 0130 00',), ('de89370400440532013000',), ('Gb82WEST12345698765432',), ('NL91ABNA0417164300',), ('GB82',), ('',), (None,)],
    'phone_e164': [('+1 555 222 3333',), ('15559876543',), ('(555) 000-1111 ext. 12',), ('555.444.3333 X7',), ('+33 1 23 45 67 89',), (None,)],
    'invoice_number': [(99, 5), (0, 3), (2025, -4), (2025, 999999), (2025, 1234567), (None, 5), (2025, None)],
    'fiscal_quarter': [('2025-04-01',), ('2025-03-31',), ('2024-12-31T23:59:59',), ('2026-01-01 00:00',), ('2000-03-31',), ('2000-04-01',), (None,)],
    'business_days': [('2025-03-07', '2025-03-03'), ('2026-12-31', '2027-01-04'), ('2025-01-01', '2026-01-02'), ('2025-01-01', '2026-01-03'), ('2025-03-08', '2025-03-09'), (None, '2025-03-03')],
    'minutes_to_hhmm': [(1440,), (1439,), (3000,), (0,), (60,), (None,)],
    'parse_duration': [('2d4h',), ('2h 15m',), ('120',), ('0',), ('1m30s',), ('30s',), ('',), ('abc',), (None,)],
    'initials': [('Jean-Luc Picard',), ('x-y-z',), ('  extra   spaces ',), ("o'brien",), ('',), (None,)],
    'slugify_title': [('Niño Año',), ('R&D Update',), ('Rock&Roll',), ('The Complete Guide To Managing Remote Engineering Teams',), ('Supercalifragilisticexpialidociousnessxyzabc',), ('???  ',), ('',), (None,)],
    'password_strength': [('PASSWORD',), ('xpasswordx9',), ('Abcdefg1',), ('abcdefgh',), ('A1!',), ('',), (None,)],
    'grade_rating': [(-1,), (150,), (89.5,), (89.4,), (99.6,), (90,), (60,), (0,), (None,)],
}

AGG_TYPICAL = [[4, 5, 3], [5, 5, 4, 4, 2], [3, 4, 5, 4], [1, 2, 3, 4, 5]]
AGG_EDGE = [
    [3, 3, 6, -1, 3],
    [4, 5, 5],
    [3] * 19 + [4],
    [None, 5, 5],
    [],
    [5, 5, 5, 4.5, 3.5],
    [2, 3, None, 4, 7],
]

DECISIONS = {
    'vat_amount': ['VAT truncated (not rounded) to whole cents'],
    'loyalty_points': ['purchases under 5.00 earn 0 points'],
    'initials': ['each hyphenated part of a name gives an initial'],
    'minutes_to_hhmm': ["1440 minutes or more shown as 'Nd H:MM'"],
    'password_strength': ["password containing 'password' (any case) scores 0"],
    'mask_card': ['spaces and dashes stripped before masking', 'fewer than 12 digits gives NULL'],
    'fiscal_quarter': ['timestamps accepted, date part used', 'dates before 2000-04-01 give NULL'],
    'pro_rata': ['days used at or above days in month charge the full price', 'charge rounded up to the next cent'],
    'age_band': ["ages under 18 give 'minor'", 'ages over 120 give NULL'],
    'iban_check': ['spaces allowed and ignored', 'any lowercase letter gives 0'],
    'grade_rating': ['scores outside 0..100 give NULL', 'fractional scores rounded half-up before banding', "a score of 100 gives 'A+'"],
    'business_days': ['end before start gives a negative count', '25 Dec and 1 Jan are not working days', 'spans over 366 days give NULL'],
    'phone_e164': ['11 digits with leading 1 accepted', "extensions ('x', 'ext') dropped", "foreign '+' numbers kept, digits only"],
    'invoice_number': ['years 0..99 mean 2000..2099', 'sequence 0 or below gives NULL', 'sequence above 999999 gives NULL'],
    'charm_price': ['whole amounts drop to the .99 below', 'prices under 1.00 unchanged', 'prices 1000 or more rounded half-up to a whole amount'],
    'late_fee': ['fee capped at 25% of the invoice', 'minimum fee 5.00 when any fee applies', 'credit notes (negative amount) give 0', 'partial days round up to whole days'],
    'slugify_title': ['accented letters transliterated to ASCII', 'slug at most 40 characters, cut at a word boundary', "'&' becomes 'and'", "empty slug becomes 'untitled'"],
    'discount_price': ['coupon codes case-insensitive', 'discount capped at 50%', 'unknown or malformed code leaves the price unchanged', 'NULL code leaves the price unchanged'],
    'parse_duration': ['bare number means minutes', "'d' is an 8-hour working day", 'whitespace between parts allowed', 'seconds round the total up to whole minutes'],
    'avg_star_rating': ['ratings outside 1..5 ignored', 'average rounded half-up to 1 decimal', 'fewer than 3 valid ratings gives NULL', 'fractional ratings ignored'],
}

DECISION_EXAMPLES = {
    'vat_amount': [(10.99, 20)],
    'loyalty_points': [(4.5,)],
    'initials': [('Anne-Marie Duval',)],
    'minutes_to_hhmm': [(1500,)],
    'password_strength': [('MyPassword1!',)],
    'mask_card': [('4111 1111 1111 1111',), ('12345678901',)],
    'fiscal_quarter': [('2025-07-04 13:45:00',), ('1999-12-31',)],
    'pro_rata': [(100, 40, 30), (10, 1, 3)],
    'age_band': [(16,), (130,)],
    'iban_check': [('GB82 WEST 1234 5698 7654 32',), ('gb82west12345698765432',)],
    'grade_rating': [(101,), (79.5,), (100,)],
    'business_days': [('2025-03-10', '2025-03-03'), ('2025-12-22', '2025-12-29'), ('2024-01-01', '2025-06-01')],
    'phone_e164': [('1-555-123-4567',), ('555-123-4567 x89',), ('+44 20 7946 0958',)],
    'invoice_number': [(25, 7), (2025, 0), (2025, 1000000)],
    'charm_price': [(20,), (0.5,), (1499.5,)],
    'late_fee': [(40, 1000), (2, 100), (10, -300), (2.5, 1000)],
    'slugify_title': [('Café Crème',), ('An Unusually Long Title For Our Quarterly Newsletter Issue',), ('Salt & Pepper',), ('!!!',)],
    'discount_price': [(100, 'save10'), (100, 'SAVE80'), (100, 'FREESHIP'), (100, None)],
    'parse_duration': [('90',), ('1d',), ('1h 30m',), ('90s',)],
    'avg_star_rating': [[4, 4, 4, 0, 10], [5] * 5 + [4] * 15, [5, 5], [4, 4, 4, 4.5]],
}

HANDBOOK = """\
BRIGHTWATER SUPPLY CO. -- BUSINESS RULES HANDBOOK FOR REPORTING AND BILLING

About this handbook

This handbook was first put together in 2019, when Finance and Engineering agreed
that the rules behind our invoices, storefront and reports should live in one
place instead of in a dozen spreadsheets. It has been amended many times since,
usually after an audit, a customer dispute or a change in the storefront. It is
organised by business area, not by system. Where it is silent, the product owner
decides; please ask rather than guess.

1. Money: tax, fees and prices

Tax. VAT is charged on the net amount at the applicable rate. After the 2021 tax
review we settled the old argument about fractions of a cent: VAT is always
truncated to whole cents, never rounded. Any fraction of a cent is simply
dropped, which favours the customer and matches what our tills have always done.

Late payment. An overdue invoice accrues a late fee of one percent of the
invoice amount for each day it is late. After a long dispute with a wholesale
customer in 2022, Collections introduced a ceiling: the late fee never exceeds
25% of the invoice amount, however late the payment. At the other end, chasing a
payment costs us money, so whenever a late fee applies at all it is at least
5.00. Credit notes are a different animal from ordinary invoices, and Collections
does not treat them the same way when it comes to late fees.

Subscriptions. Customers who join or leave part way through a month pay a
share of the monthly price in proportion to the days they used. Whatever the
day counts say, a customer is never charged more than the full monthly price
for one month.

Coupons. Marketing issues percentage-off coupon codes, where the number in the
code is the percentage taken off. Customers type them in all sorts of ways,
so codes are matched without regard to letter case. Marketing also keeps a
ceiling on how deep any single coupon can cut a price, whatever number is
printed on it.

Storefront prices. Since the 2020 relaunch the storefront shows prices ending in
.99, moving the list price up to the next .99. A list price that is already a
whole amount is not pushed up by almost a full unit: it drops to the .99 just
below it instead. Our luxury range is presented differently; above a certain
price level we show plain whole amounts, since .99 endings look cheap there.

2. Customers, loyalty and reviews

Loyalty. Members earn one point for each whole currency unit spent. The scheme
was never meant to reward the smallest purchases, and very small baskets earn
nothing at all.

Reviews. The average star rating shown on a product page counts only genuine
ratings on our 1 to 5 star scale; anything outside that scale comes from old
import errors and is skipped. A product needs at least three ratings before we
show an average at all, so that one enthusiastic friend cannot make a product
look perfect. The average is rounded for display.

Age reporting. Marketing reports customers in the standard age bands. Under-age
customers are not split further: every customer under 18 is reported in a
single band labelled 'minor'.

3. Payments and identifiers

Cards. A card number is never displayed in full; only the last four digits are
shown and the rest are starred out. Customers often paste numbers with spaces or
dashes between the groups, and those separators are removed before masking, so
the masked result contains only stars and digits. A string that is too short to
be a real card number is not masked at all.

Bank accounts. IBANs are validated with the international mod-97 checksum before
we store them. The validator is forgiving of the way IBANs are usually printed
on paper and in emails.

Phone numbers. We store US customer numbers in E.164 form. Customers who write
the country code 1 in front of their ten-digit number are accepted just the same
as those who do not. Extensions belong to the customer's switchboard, not to
the number we store.

Invoice numbers. Invoice numbers have the form INV, the year and a six-digit
sequence number. Sequence numbers start at one: a sequence of zero or below is
not a valid invoice and gives no invoice number (NULL). Some legacy systems still
send years in a shortened form, and the function copes with them.

4. Calendar and time

Fiscal year. Our fiscal year starts on 1 April and is named after the calendar
year in which it ends. The company's first fiscal year began on 1 April 2000;
earlier dates have no fiscal quarter and give NULL.

Working days. Service levels are measured in working days, Monday to Friday. The
whole company closes on Christmas Day (25 December) and New Year's Day
(1 January), and those two days never count as working days, whatever the
weekday. The working-day count is meant for service levels and short projects;
very long spans are outside what it is for.

Timesheets. Durations on timesheets are shown as hours and minutes. Very long
durations, such as multi-day jobs, carry a day component in front of the hours.

Typed durations. Staff type durations as text with h and m units. A plain number
with no unit is read as minutes, because that is what the old timesheet screen
expected. A day in this context is a working day, not a calendar day. Seconds
are accepted from the machine logs, but we bill in whole minutes.

5. People and content

Initials. Initials are used for avatars and sign-offs on internal documents.

Article slugs. Every article on the help centre gets a URL slug made from its
title. Slugs stay within plain web-safe characters, but accented letters are not
lost from the slug. An ampersand in a title becomes the word 'and' in the slug.
A title that leaves nothing usable gets the slug 'untitled' rather than an empty
slug.

Passwords. The strength meter gives one point each for length, digits, mixed
case and symbols. After the 2023 security review, any password that contains the
word 'password', in any mix of capitals, scores zero, however good the rest of it
is.

6. Supplier audits

Suppliers are audited yearly and scored out of 100, then graded A to F. A score
below zero or above 100 is a data-entry error and gets no grade (NULL). Auditors
sometimes record half points, and these are settled to a whole point before
grading. A perfect score of exactly 100 is graded 'A+', a distinction the
supplier team introduced in 2022 to recognise outstanding suppliers.
"""

HANDBOOK_STATUS = {
    'vat_amount': ['clear'],
    'loyalty_points': ['vague'],
    'initials': ['omitted'],
    'minutes_to_hhmm': ['vague'],
    'password_strength': ['clear'],
    'mask_card': ['clear', 'vague'],
    'fiscal_quarter': ['omitted', 'clear'],
    'pro_rata': ['clear', 'omitted'],
    'age_band': ['clear', 'omitted'],
    'iban_check': ['vague', 'omitted'],
    'grade_rating': ['clear', 'vague', 'clear'],
    'business_days': ['omitted', 'clear', 'vague'],
    'phone_e164': ['clear', 'vague', 'omitted'],
    'invoice_number': ['vague', 'clear', 'omitted'],
    'charm_price': ['clear', 'omitted', 'vague'],
    'late_fee': ['clear', 'clear', 'vague', 'omitted'],
    'slugify_title': ['vague', 'omitted', 'clear', 'clear'],
    'discount_price': ['clear', 'vague', 'omitted', 'omitted'],
    'parse_duration': ['clear', 'vague', 'omitted', 'vague'],
    'avg_star_rating': ['clear', 'vague', 'clear', 'omitted'],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, nargs) in SCALARS.items():
        con.create_function(name, nargs, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con
