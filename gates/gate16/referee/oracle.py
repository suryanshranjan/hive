"""Company policy for 20 business SQL functions (19 scalars, 1 aggregate)."""

import calendar
import datetime
import math
import re
import sqlite3
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN, ROUND_HALF_UP


# ---------------------------------------------------------------- helpers

def _num(v):
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None
        return v
    try:
        f = float(str(v).strip())
    except (ValueError, TypeError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f


def _int(v):
    n = _num(v)
    if n is None:
        return None
    if isinstance(n, float):
        if n != int(n):
            return None
        return int(n)
    return n


def _dec(v):
    return Decimal(repr(float(v))) if isinstance(v, float) else Decimal(v)


def _cents(d, mode=ROUND_HALF_UP):
    return float(d.quantize(Decimal('0.01'), rounding=mode))


_ISO = re.compile(r'^(\d{4})-(\d{2})-(\d{2})$')


def _date(v, allow_time=False, allow_slash=False):
    if not isinstance(v, str):
        return None
    s = v.strip()
    if allow_time and len(s) > 10 and s[10] in ' T':
        s = s[:10]
    if allow_slash and re.match(r'^\d{4}/\d{2}/\d{2}$', s):
        s = s.replace('/', '-')
    m = _ISO.match(s)
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


# ---------------------------------------------------------------- scalars

def net_price(list_price, discount_pct):
    p = _num(list_price)
    if p is None:
        return None
    d = _num(discount_pct)
    if d is None:
        d = 0
    if d < 0:
        d = 0
    if d > 60:
        d = 60
    r = _dec(p) * (Decimal(100) - _dec(d)) / Decimal(100)
    step = Decimal('0.05')
    return float((r / step).to_integral_value(rounding=ROUND_FLOOR) * step)


def late_fee(days_late, invoice_amount):
    days = _num(days_late)
    amt = _num(invoice_amount)
    if days is None or amt is None:
        return None
    if amt <= 0 or days <= 3:
        return 0.0
    weeks = math.ceil(days / 7)
    pct = min(weeks, 8)
    return _cents(_dec(amt) * Decimal(pct) / Decimal(100))


def invoice_number(year, seq):
    y = _int(year)
    s = _int(seq)
    if y is None or s is None:
        return None
    if s <= 0 or y < 0:
        return None
    if y < 100:
        y += 2000
    return 'INV-%04d-%06d' % (y, s)


def star_rating(score):
    s = _num(score)
    if s is None or s < 0 or s > 100:
        return None
    return min(int(math.floor(s / 20)) + 1, 5)


def workdays_between(start_date, end_date):
    a = _date(start_date, allow_time=True)
    b = _date(end_date, allow_time=True)
    if a is None or b is None:
        return None
    if b <= a:
        return 0
    n = 0
    d = a + datetime.timedelta(days=1)
    while d <= b:
        if d.weekday() < 5 and (d.month, d.day) not in ((1, 1), (12, 25)):
            n += 1
        d += datetime.timedelta(days=1)
    return n


def normalize_sku(code):
    if code is None or not isinstance(code, str):
        return None
    s = re.sub(r'[\s-]', '', code).upper()
    if len(s) != 7:
        return None
    letters, digits = s[:3], s[3:].replace('O', '0')
    if not (letters.isascii() and letters.isalpha()):
        return None
    if not (digits.isascii() and digits.isdigit()):
        return None
    return letters + '-' + digits


def shipping_cost(weight_kg, zone):
    w = _num(weight_kg)
    z = _num(zone)
    if w is None or z is None or w <= 0:
        return None
    billable = Decimal(math.ceil(w * 2)) / 2
    mult = {1: Decimal('1'), 2: Decimal('1.5'), 3: Decimal('2')}.get(z, Decimal('2'))
    cost = (Decimal(4) + Decimal(2) * billable) * mult
    return _cents(min(cost, Decimal(60)))


def loyalty_tier(points):
    p = _num(points)
    if p is None:
        return None
    if p < 0:
        return 'Suspended'
    if p >= 25000:
        return 'Platinum'
    if p >= 5000:
        return 'Gold'
    if p >= 1000:
        return 'Silver'
    return 'Bronze'


def mask_card(card_number):
    if card_number is None:
        return None
    if isinstance(card_number, float):
        return None
    digits = re.sub(r'\D', '', str(card_number))
    if not digits:
        return None
    if len(digits) < 13:
        return '*' * len(digits)
    return '*' * (len(digits) - 4) + digits[-4:]


_TAX = {'A': Decimal('0.20'), 'B': Decimal('0.10'), 'C': Decimal('0.05')}


def tax_amount(net_amount, region):
    n = _num(net_amount)
    if n is None or region is None:
        return None
    if abs(n) < 1:
        return 0.0
    rate = _TAX.get(str(region).strip().upper(), _TAX['A'])
    return _cents(_dec(n) * rate, ROUND_HALF_EVEN)


def age_bracket(birth_year, as_of_year):
    b = _int(birth_year)
    y = _int(as_of_year)
    if b is None or y is None or y < b:
        return None
    age = y - b
    if age < 18:
        return 'under-18'
    if age <= 24:
        return '18-24'
    if age <= 34:
        return '25-34'
    if age <= 49:
        return '35-49'
    return '50+'


def split_bill(total, people):
    t = _num(total)
    if t is None:
        return None
    p = _num(people)
    if p is None or p < 1:
        p = 1
    p = int(p)
    share = (_dec(t) / Decimal(p)).quantize(Decimal('0.01'), rounding=ROUND_CEILING)
    if t > 0 and share < 1:
        share = Decimal(1)
    return float(share)


_EXT = re.compile(r'\s*(?:x|ext\.?)\s*(\d+)\s*$', re.IGNORECASE)


def format_phone(raw):
    if raw is None:
        return None
    if isinstance(raw, float):
        return None
    s = str(raw)
    ext = None
    m = _EXT.search(s)
    main = s
    if m:
        ext = m.group(1)
        main = s[:m.start()]
    digits = re.sub(r'\D', '', main)
    if len(digits) == 11 and digits[0] == '1':
        digits = digits[1:]
    if len(digits) != 10:
        return raw
    out = '(%s) %s-%s' % (digits[:3], digits[3:6], digits[6:])
    if ext:
        out += ' ext. ' + ext
    return out


def quarter_label(date):
    d = _date(date, allow_slash=True)
    if d is None:
        return None
    if d.month == 12 and d.day >= 25:
        return 'Q1 %d' % (d.year + 1)
    return 'Q%d %d' % ((d.month - 1) // 3 + 1, d.year)


def renewal_date(start_date, months):
    d = _date(start_date)
    m = _int(months)
    if d is None or m is None:
        return None
    if m <= 0:
        return d.isoformat()
    m = min(m, 36)
    total = d.month - 1 + m
    y, mo = d.year + total // 12, total % 12 + 1
    if y > 9999:
        return None
    r = datetime.date(y, mo, min(d.day, calendar.monthrange(y, mo)[1]))
    if r.weekday() >= 5:
        r += datetime.timedelta(days=7 - r.weekday())
    return r.isoformat()


def nps_category(score):
    s = _num(score)
    if s is None:
        return None
    r = int(Decimal(repr(float(s))).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    if r < 0 or r > 10:
        return None
    if r >= 9:
        return 'promoter'
    if r >= 7:
        return 'passive'
    return 'detractor'


_PARTICLES = {'van', 'von', 'de', 'der', 'da', 'di', 'la', 'le', 'du', 'den'}


def initials(full_name):
    if not isinstance(full_name, str):
        return None
    out = ''
    for word in full_name.split():
        if word.lower() in _PARTICLES:
            continue
        for part in word.split('-'):
            if part:
                out += part[0].upper()
    return out or None


def meeting_slot(minute_of_day):
    m = _num(minute_of_day)
    if m is None or m < 0 or m >= 1440:
        return None
    m = int(math.ceil(m / 15)) * 15
    if m < 480:
        m = 480
    if 720 <= m < 780:
        m = 780
    if m > 1050:
        return None
    return '%02d:%02d' % (m // 60, m % 60)


def check_digit(account_number):
    if account_number is None or isinstance(account_number, float):
        return None
    s = re.sub(r'[ -]', '', str(account_number))
    if not s or not (s.isascii() and s.isdigit()):
        return None
    total = 0
    for i, ch in enumerate(reversed(s)):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return (10 - total % 10) % 10


# ---------------------------------------------------------------- aggregate

class AvgOrderValue:
    def __init__(self):
        self.values = []

    def step(self, value):
        v = _num(value)
        if v is None or v <= 0:
            return
        self.values.append(_dec(v))

    def finalize(self):
        vals = sorted(self.values)
        if not vals:
            return 0.0
        if len(vals) >= 5:
            vals = vals[:-1]
        return _cents(sum(vals) / Decimal(len(vals)))


# ---------------------------------------------------------------- registry

SPEC = {
    'net_price': 'net_price(list_price, discount_pct): Customer-facing price after a percentage discount is applied to a list price.',
    'late_fee': 'late_fee(days_late, invoice_amount): Late-payment fee owed on an overdue invoice, charged at 1% of the invoice amount per week overdue.',
    'invoice_number': 'invoice_number(year, seq): Official invoice number for a billing year and a running sequence number, in the form INV-YYYY-NNNNNN.',
    'star_rating': 'star_rating(score): Star rating (1 to 5 stars) shown on the website for a 0-100 customer satisfaction score.',
    'workdays_between': 'workdays_between(start_date, end_date): Number of business days (Monday to Friday) between two ISO dates, used for SLA tracking.',
    'normalize_sku': 'normalize_sku(code): Canonical product SKU (three letters, a hyphen, four digits) from a code as typed by warehouse staff.',
    'shipping_cost': 'shipping_cost(weight_kg, zone): Parcel shipping charge: 4.00 plus 2.00 per kg, multiplied by 1, 1.5 or 2 for delivery zone 1, 2 or 3.',
    'loyalty_tier': 'loyalty_tier(points): Loyalty programme tier name for a points balance: Bronze from 0, Silver from 1000, Gold from 5000.',
    'mask_card': 'mask_card(card_number): Payment card number masked for display on receipts, showing only the last four digits.',
    'tax_amount': 'tax_amount(net_amount, region): Sales tax due on a net amount for a region code: A 20%, B 10%, C 5%.',
    'age_bracket': "age_bracket(birth_year, as_of_year): Marketing age bracket ('18-24', '25-34', '35-49' or '50+') of a customer in a given year.",
    'split_bill': 'split_bill(total, people): Amount each person pays when a group bill is split evenly between them.',
    'format_phone': 'format_phone(raw): Phone number in the house display format (AAA) BBB-CCCC from a number as typed by a customer.',
    'quarter_label': "quarter_label(date): Reporting quarter label such as 'Q3 2024' for an ISO date.",
    'renewal_date': 'renewal_date(start_date, months): Contract renewal date: the ISO start date moved forward by a term of whole months.',
    'nps_category': "nps_category(score): Net Promoter category of a 0-10 survey score: 'promoter' (9-10), 'passive' (7-8) or 'detractor' (0-6).",
    'initials': 'initials(full_name): Upper-case initials of a customer name, for badges and compact lists.',
    'meeting_slot': 'meeting_slot(minute_of_day): Start time (HH:MM) of the 15-minute booking slot for a requested meeting start given in minutes after midnight.',
    'check_digit': 'check_digit(account_number): Luhn check digit (0-9) to append to a customer account number.',
    'avg_order_value': 'avg_order_value(amount): Average order value of a group of orders, rounded to cents.',
}

SCALARS = {
    'net_price': (net_price, 2),
    'late_fee': (late_fee, 2),
    'invoice_number': (invoice_number, 2),
    'star_rating': (star_rating, 1),
    'workdays_between': (workdays_between, 2),
    'normalize_sku': (normalize_sku, 1),
    'shipping_cost': (shipping_cost, 2),
    'loyalty_tier': (loyalty_tier, 1),
    'mask_card': (mask_card, 1),
    'tax_amount': (tax_amount, 2),
    'age_bracket': (age_bracket, 2),
    'split_bill': (split_bill, 2),
    'format_phone': (format_phone, 1),
    'quarter_label': (quarter_label, 1),
    'renewal_date': (renewal_date, 2),
    'nps_category': (nps_category, 1),
    'initials': (initials, 1),
    'meeting_slot': (meeting_slot, 1),
    'check_digit': (check_digit, 1),
}

AGGREGATE = ('avg_order_value', AvgOrderValue)

TYPICAL = {
    'net_price': [(100, 10), (250, 20), (80, 25), (40, 50), (19.95, 0)],
    'late_fee': [(7, 1000), (14, 1000), (21, 200), (28, 500)],
    'invoice_number': [(2024, 123), (2023, 1), (2025, 45678), (2022, 999999)],
    'star_rating': [(95,), (75,), (50,), (30,), (10,)],
    'workdays_between': [('2024-03-02', '2024-03-10'), ('2024-03-09', '2024-03-24'),
                         ('2024-06-01', '2024-06-02'), ('2024-04-06', '2024-04-28')],
    'normalize_sku': [('abc1234',), ('XYZ 0042',), ('qrs-5555',), ('Lmn-0001',)],
    'shipping_cost': [(2, 1), (3, 2), (1, 3), (5, 1)],
    'loyalty_tier': [(100,), (1500,), (6000,), (0,), (4999,)],
    'mask_card': [('4111111111111111',), ('4111 1111 1111 1111',),
                  ('5500-0000-0000-0004',), ('340000000000009',)],
    'tax_amount': [(100, 'A'), (50, 'B'), (200, 'C'), (12.5, 'A'), (80, 'B')],
    'age_bracket': [(2000, 2024), (1990, 2024), (1980, 2024), (1960, 2024)],
    'split_bill': [(100, 4), (90, 3), (50, 2), (12, 4)],
    'format_phone': [('5551234567',), ('555-987-6543',), ('(555) 222 3333',), ('555.444.1212',)],
    'quarter_label': [('2024-02-15',), ('2024-05-01',), ('2023-09-30',), ('2024-11-20',)],
    'renewal_date': [('2024-01-15', 1), ('2024-03-10', 12), ('2024-04-02', 3), ('2023-06-14', 6)],
    'nps_category': [(10,), (9,), (8,), (7,), (3,), (0,)],
    'initials': [('John Smith',), ('mary ann lee',), ('Alice Brown',), ('Omar  Haddad',)],
    'meeting_slot': [(540,), (600,), (870,), (615,), (1005,)],
    'check_digit': [('7992739871',), ('12345',), ('411111111111111',), ('000123',)],
}

EDGE = {
    'net_price': [(100, 75), (19.99, 0), (100, -5), (100, None), (None, 10),
                  (0, 10), (100, 60), (33.33, 10)],
    'late_fee': [(2, 1000), (3, 1000), (4, 1000), (10, 1000), (70, 1000),
                 (365, 250), (None, 100), (0, 500), (14, 0)],
    'invoice_number': [(24, 5), (99, 1), (2024, 0), (2024, -3), (2024, 1000000),
                       (None, 5), (2024, None), (0, 7)],
    'star_rating': [(80,), (60,), (0,), (100,), (-5,), (120,), (None,), (79.9,)],
    'workdays_between': [('2024-03-04', '2024-03-08'), ('2024-03-08', '2024-03-04'),
                         ('2024-12-21', '2024-12-29'), ('2024-03-04 09:00', '2024-03-11'),
                         ('2024-03-04', '2024-03-04'), ('2024-02-30', '2024-03-10'),
                         (None, '2024-03-10'), ('2023-12-30', '2024-01-07')],
    'normalize_sku': [('ABC12O4',), ('abc-oo12',), ('AB1234',), ('ABCD1234',),
                      ('',), (None,), ('abc 12 34',), (1234567,)],
    'shipping_cost': [(2.2, 1), (0.1, 1), (2, 7), (2, 0), (20, 3), (12, 2),
                      (0, 1), (None, 1), (2, None)],
    'loyalty_tier': [(1000,), (5000,), (25000,), (99999,), (-1,), (None,), (999.5,), (24999,)],
    'mask_card': [('123456789012',), ('1234567890123',), ('1234',), ('',),
                  (None,), ('abcd',), (4111111111111111,)],
    'tax_amount': [(100, 'a'), (100, ' B '), (100, 'Z'), (10.25, 'B'), (0.99, 'A'),
                   (-50, 'A'), (None, 'A'), (100, None), (1.0, 'C')],
    'age_bracket': [(2006, 2024), (2007, 2024), (2024, 2024), (2025, 2024),
                    (None, 2024), (1974, 2024), (1999, 2024)],
    'split_bill': [(100, 3), (10, 3), (100, 0), (100, None), (100, -2), (3, 4),
                   (None, 2), (0, 3)],
    'format_phone': [('15551234567',), ('+1 555 123 4567',), ('5551234567 x89',),
                     ('555-123-4567 ext 7',), ('12345',), ('25551234567',),
                     (None,), (5551234567,)],
    'quarter_label': [('2024/08/15',), ('2024-12-25',), ('2024-12-24',), ('2024-12-31',),
                      ('2024-13-01',), ('',), (None,), ('2024-04-01',)],
    'renewal_date': [('2024-01-31', 1), ('2024-01-10', 1), ('2024-05-20', 0),
                     ('2024-05-20', -2), ('2024-01-15', 48), ('2024-02-30', 1),
                     (None, 3), ('2024-01-15', None)],
    'nps_category': [(8.5,), (6.5,), (8.4,), (11,), (-1,), (None,), (6.49,)],
    'initials': [('Ludwig van Beethoven',), ('Jean-Luc Picard',), ('Anna de la Cruz',),
                 ('',), (None,), ('cher',), ('Mary-Kate Olsen-Smith',)],
    'meeting_slot': [(541,), (544.5,), (300,), (0,), (720,), (765,), (1050,),
                     (1051,), (1500,), (None,)],
    'check_digit': [('7992 7398 71',), ('7992-7398-71',), ('79a2',), ('',),
                    (None,), ('0',), (' ',)],
}

AGG_TYPICAL = [[10, 20, 30], [25.5, 24.5], [100, 200, 300, 400], [7]]

AGG_EDGE = [[10, -5, 20], [-3, 0], [None, None], [10, 20, 30, 40, 1000], [10, None, 30],
            [0, 0, 50], [10, 10, 10, 10, 10, 10], [1, 2, 2]]

DECISIONS = {
    'net_price': ['discount capped at 60%', 'result rounded down to the nearest 0.05',
                  'negative discount treated as no discount', 'NULL discount treated as no discount'],
    'late_fee': ['no fee within a 3-day grace period', 'a started week counts as a full week',
                 'fee capped at 8% of the invoice amount'],
    'invoice_number': ['two-digit year means 20YY', 'sequence of zero or below gives NULL'],
    'star_rating': ['a score exactly on a 20-point boundary gets the higher star',
                    'score below 0 or above 100 gives NULL'],
    'workdays_between': ['start date excluded, end date included',
                         'end date on or before start date gives 0',
                         '1 January and 25 December are not business days',
                         'a time part after the date is ignored'],
    'normalize_sku': ['letter O in the digit part is read as zero'],
    'shipping_cost': ['weight billed up to the next half kilogram',
                      'unknown zone charged at the zone 3 rate',
                      'charge capped at 60.00 per parcel'],
    'loyalty_tier': ['Platinum tier from 25000 points', "negative balance gives 'Suspended'"],
    'mask_card': ['numbers under 13 digits are masked completely'],
    'tax_amount': ['region code is case-insensitive and trimmed',
                   'unknown region taxed at the region A rate',
                   'tax rounded half-to-even to the cent',
                   'net amounts under 1.00 in absolute value carry no tax'],
    'age_bracket': ["under 18 gives 'under-18'"],
    'split_bill': ['each share rounded up to the cent', 'people below 1 or NULL treated as 1',
                   'minimum share of 1.00 on a positive bill'],
    'format_phone': ['leading country code 1 on 11 digits is dropped',
                     "extension kept as ' ext. N'",
                     'input that is not 10 digits is returned unchanged'],
    'quarter_label': ['YYYY/MM/DD dates accepted',
                      '25-31 December counts as Q1 of the next year'],
    'renewal_date': ['day clamped to the last day of a shorter month',
                     'renewal on a weekend moves to the next Monday',
                     'term of zero or fewer months returns the start date',
                     'term capped at 36 months'],
    'nps_category': ['fractional score rounded to the nearest integer, halves up'],
    'initials': ['name particles (van, von, de, la, ...) skipped',
                 'each part of a hyphenated name gives an initial'],
    'meeting_slot': ['off-slot times rounded up to the next quarter hour',
                     'requests before 08:00 get 08:00',
                     'slots after 17:30 give NULL',
                     'slots in the 12:00 lunch hour move to 13:00'],
    'check_digit': ['spaces and hyphens in the number are ignored'],
    'avg_order_value': ['zero and negative amounts (refunds) excluded',
                        'no qualifying orders gives 0.0',
                        'single highest amount dropped when there are 5 or more orders'],
}

DECISION_EXAMPLES = {
    'net_price': [(200, 90), (10.03, 0), (50, -20), (75, None)],
    'late_fee': [(1, 800), (15, 600), (100, 300)],
    'invoice_number': [(25, 77), (2023, -1)],
    'star_rating': [(40,), (101,)],
    'workdays_between': [('2024-05-06', '2024-05-10'), ('2024-05-20', '2024-05-13'),
                         ('2025-12-20', '2025-12-28'), ('2024-05-06T08:30', '2024-05-13')],
    'normalize_sku': [('KLM5O55',)],
    'shipping_cost': [(1.3, 1), (1, 9), (30, 1)],
    'loyalty_tier': [(30000,), (-250,)],
    'mask_card': [('98765',)],
    'tax_amount': [(60, 'c'), (40, 'Q'), (10.45, 'B'), (0.5, 'B')],
    'age_bracket': [(2010, 2024)],
    'split_bill': [(20, 3), (45, 0), (2, 5)],
    'format_phone': [('1-555-222-3333',), ('5552223333x5',), ('555-0000',)],
    'quarter_label': [('2025/03/03',), ('2023-12-28',)],
    'renewal_date': [('2024-03-31', 1), ('2024-08-22', 1), ('2024-07-01', 0), ('2024-02-01', 60)],
    'nps_category': [(6.6,)],
    'initials': [('Vincent van Gogh',), ('Anne-Marie Dupont',)],
    'meeting_slot': [(601,), (420,), (1100,), (735,)],
    'check_digit': [('1234 5678',)],
    'avg_order_value': [[40, -40, 60], [-10], [5, 5, 5, 5, 500]],
}

HANDBOOK_STATUS = {
    'net_price': ['clear', 'clear', 'vague', 'omitted'],
    'late_fee': ['clear', 'vague', 'clear'],
    'invoice_number': ['vague', 'omitted'],
    'star_rating': ['clear', 'omitted'],
    'workdays_between': ['vague', 'omitted', 'clear', 'omitted'],
    'normalize_sku': ['clear'],
    'shipping_cost': ['clear', 'vague', 'clear'],
    'loyalty_tier': ['vague', 'clear'],
    'mask_card': ['vague'],
    'tax_amount': ['omitted', 'clear', 'clear', 'vague'],
    'age_bracket': ['omitted'],
    'split_bill': ['clear', 'omitted', 'vague'],
    'format_phone': ['vague', 'clear', 'omitted'],
    'quarter_label': ['omitted', 'vague'],
    'renewal_date': ['clear', 'clear', 'omitted', 'vague'],
    'nps_category': ['omitted'],
    'initials': ['vague', 'clear'],
    'meeting_slot': ['clear', 'vague', 'omitted', 'clear'],
    'check_digit': ['omitted'],
    'avg_order_value': ['clear', 'omitted', 'vague'],
}

HANDBOOK = """\
Commercial Operations Handbook -- Pricing, Billing, Logistics and Customer Data
Internal. Maintained by the Product Office. Revision 7.

1. Why this handbook exists

For most of the company's history our commercial rules lived in three places at
once: the old order-entry system, a set of spreadsheets kept by Finance, and the
heads of a few long-serving staff. When the order-entry system was retired, a
number of those rules turned out to exist nowhere in writing. This handbook is
the attempt to write down the ones we still apply. It is organised by area of
the business rather than by system, because the same rule is often enforced in
the shop, in the warehouse and in the reporting database. Where a rule is not
covered here, ask the Product Office before inventing one.

2. Prices, discounts and tax

Sales staff may grant percentage discounts off list price, but after the 2019
clearance sale, in which several lines were sold below cost, the board fixed a
hard ceiling: no discount, whatever is typed into the system, may take more
than 60% off the list price. Anything above that is applied as 60%. Equally,
the discount field must never be used to raise a price; mistakes in that field
are not allowed to work against the customer.

Our shops still handle a lot of cash, and we stopped stocking the smallest
coins years ago. For that reason every discounted price is brought down to the
nearest multiple of five cents. We always round in the customer's favour, that
is downwards, never to the nearest.

Sales tax depends on the region code of the delivery address. The three
current codes and their rates are published in the price list. Region codes are
sometimes missing or mistyped on older accounts; Finance's position is that we
would rather over-collect and refund than under-collect, so an unrecognised
region code is taxed at the region A rate, the highest we have. Tax is computed
to the cent using round-half-to-even (banker's rounding), as agreed with our
auditors, so that half-cent cases do not systematically drift upwards. Very
small amounts, such as sample fees, are not worth taxing and are treated as
exempt below a de minimis level set by Finance.

When a group of customers asks to split a bill, each share is rounded up to the
next cent so that the shares together always cover the bill; the house keeps
the odd cent or two. Card terminals also carry a minimum charge, so very small
shares are raised to that minimum.

3. Invoicing and collections

Invoice numbers carry the billing year and a six-digit running number. Some
older feeder systems still send the year in an abbreviated form; these are
interpreted sensibly rather than rejected.

Overdue invoices attract a late fee of one percent of the invoice amount for
each week overdue. Customers get a grace period: an invoice paid up to three
days late carries no fee at all. After that, weeks are counted generously in
our favour rather than the customer's. Following complaints from our largest trade customers in 2021, the
total late fee on any one invoice is capped at 8% of the invoice amount, no
matter how late it is.

For management reporting we track the average order value of a set of orders.
Refunds and zero-value orders are excluded from this figure entirely: only
orders with a positive amount count. Because one very large trade order can
distort a small branch's average, the very top of the distribution is trimmed
once a branch has enough orders for the trim to be fair.

4. Warehouse and shipping

Product SKUs are three letters followed by four digits. Warehouse staff type
them by hand from worn labels, and the commonest error by far is typing the
letter O for a zero. In the numeric part of a SKU the letter O is always read
as the digit zero.

Parcels are charged by weight and delivery zone as set out in the rate card.
Weight is billed in half-kilogram steps, and any part of a half kilogram is
billed as a full half kilogram. Addresses whose zone cannot be matched to the
rate card are charged as if they were in one of the dearer zones. No single
parcel is ever charged more than 60.00 for shipping; heavier items go by
freight and are quoted separately.

5. Calendar, scheduling and contracts

Service-level agreements are measured in business days. The count is meant to
measure the days the customer actually waited, so one of the two ends of the
period is counted and the other is not. Besides weekends, the company is closed
on 1 January and 25 December, and those two days are never business days.

The finance year follows calendar quarters, but year-end closing starts some days
before the end of December, and activity in that closing window is booked into
the following year's first quarter.

Contracts renew after a term in whole months from the start date. If the
start date falls on a day that the renewal month does not have (for instance
the 31st), the renewal falls on the last day of that month. Renewals are never
scheduled on a Saturday or Sunday: a renewal that would fall on a weekend
moves forward to the following Monday. Terms longer than a few years are not
offered, and longer requests are shortened to our maximum term.

Meetings with customers are booked in fifteen-minute slots. A request that does
not fall exactly on a slot is moved forward to the next slot start, never
backwards, so that nobody is booked into a slot that has already begun. The
meeting rooms open early in the morning and requests before opening go to the
first slot of the day. The lunch hour from 12:00 is protected: any slot that
would start during it is moved to 13:00.

6. Customer records and privacy

Card numbers are never displayed in full. Receipts show the last four digits
and mask the rest. For numbers that are too short to be a real card, showing
any digits at all would reveal too much, so those are handled more strictly.

Phone numbers are shown in the house display format. Extensions matter to our
business customers and are kept: they are written after the number as " ext. "
followed by the extension digits. Numbers entered with an international prefix
for our own country are recognised and shown in the domestic format.

For name badges we print the customer's initials. Many of our customers have
family names with particles, and these need the same care on badges as on our
printed letters. Hyphenated names are treated as two names joined
together: each part contributes its own initial.

Marketing reports group customers into age brackets, and account numbers carry
a standard check digit so that typing errors are caught at the counter.

7. Ratings and loyalty

The website converts the 0-100 satisfaction score into stars in bands of
twenty points. A score that lands exactly on the edge between two bands is
given the higher star; we would rather round a customer's opinion of us up at
the boundary than down. Net Promoter categories follow the standard published
bands.

The loyalty programme has the three published tiers, and since the 2022
relaunch there is also a fourth, invitation-style tier for our very highest
spenders, above Gold. An account whose points balance has gone negative, which
happens after returns of points-earning purchases, is shown with the tier name
'Suspended' until the balance is restored.
"""


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, nargs) in SCALARS.items():
        con.create_function(name, nargs, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con
