"""Company policy for 20 business SQL functions (19 scalars, 1 aggregate).

Standard library only. Deterministic. Never raises for valid SQL values.
"""
import datetime
import math
import re
import sqlite3
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

# ---------------------------------------------------------------- helpers


def _num(x):
    """Numeric SQL value as int/float, else None."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    if isinstance(x, float) and not math.isfinite(x):
        return None
    if abs(x) > 1e15:
        return None
    return x


def _dec(x):
    return Decimal(repr(x)) if isinstance(x, float) else Decimal(x)


def _round_half_up(x, places):
    q = Decimal(1).scaleb(-places)
    return float(_dec(x).quantize(q, rounding=ROUND_HALF_UP))


_DATE_RE = re.compile(r'^(\d{4})-(\d{2})-(\d{2})$')


def _parse_date(s):
    if not isinstance(s, str):
        return None
    m = _DATE_RE.match(s)
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _int_value(x):
    """Integer from int or integral float, else None."""
    x = _num(x)
    if x is None:
        return None
    if isinstance(x, float):
        if not x.is_integer():
            return None
        return int(x)
    return x


# ---------------------------------------------------------------- 1 decision


def tier_discount(quantity):
    q = _num(quantity)
    if q is None:
        return None
    q = math.ceil(q)
    if q >= 100:
        return 15
    if q >= 50:
        return 10
    if q >= 10:
        return 5
    return 0


def initials(full_name):
    if not isinstance(full_name, str):
        return None
    parts = [p for p in re.split(r'[\s\-]+', full_name) if p]
    return ''.join(p[0].upper() for p in parts)


def grade_letter(pct):
    p = _num(pct)
    if p is None:
        return None
    if p > 100:
        return 'A+'
    if p >= 90:
        return 'A'
    if p >= 80:
        return 'B'
    if p >= 70:
        return 'C'
    if p >= 60:
        return 'D'
    return 'F'


def invoice_no(year, seq):
    y = _int_value(year)
    s = _int_value(seq)
    if y is None or s is None:
        return None
    if not (1000 <= y <= 9999) or s < 1 or s > 99999:
        return None
    return 'INV-%04d-%05d' % (y, s)


def percent_change(old, new):
    o = _num(old)
    n = _num(new)
    if o is None or n is None or o == 0:
        return None
    change = (_dec(n) - _dec(o)) / abs(_dec(o)) * 100
    return float(change.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))


# ---------------------------------------------------------------- 2 decisions


def phone_digits(phone):
    if isinstance(phone, int) and not isinstance(phone, bool):
        phone = str(phone)
    if not isinstance(phone, str):
        return None
    s = phone.strip()
    digits = ''.join(c for c in s if c.isdigit() and c.isascii())
    if not digits:
        return None
    if s.startswith('+'):
        return '+' + digits
    if digits.startswith('00') and len(digits) > 2:
        return '+' + digits[2:]
    return digits


def minutes_to_hhmm(minutes):
    m = _num(minutes)
    if m is None or m < 0:
        return None
    m = int(m)
    return '%d:%02d' % (m // 60, m % 60)


def mask_card(card_number):
    if isinstance(card_number, int) and not isinstance(card_number, bool):
        card_number = str(card_number)
    if not isinstance(card_number, str):
        return None
    s = card_number.replace(' ', '').replace('-', '')
    if not s or not (s.isdigit() and s.isascii()):
        return None
    if len(s) < 12 or len(s) > 19:
        return None
    return '*' * (len(s) - 4) + s[-4:]


def fiscal_quarter(d):
    if isinstance(d, int) and not isinstance(d, bool):
        if not (10000101 <= d <= 99991231):
            return None
        d = '%04d-%02d-%02d' % (d // 10000, d // 100 % 100, d % 100)
    if not isinstance(d, str):
        return None
    if len(d) > 10 and d[10] in ' T':
        d = d[:10]
    dt = _parse_date(d)
    if dt is None:
        return None
    fy = dt.year + 1 if dt.month >= 4 else dt.year
    q = ((dt.month - 4) % 12) // 3 + 1
    return 'FY%d-Q%d' % (fy, q)


def split_bill(total, people):
    t = _num(total)
    p = _num(people)
    if t is None or p is None:
        return None
    p = int(p)
    if p < 1:
        p = 1
    share = (_dec(t) / p).quantize(Decimal('0.01'), rounding=ROUND_CEILING)
    return float(share)


# ---------------------------------------------------------------- 3 decisions


def net_price(price, discount_pct):
    pr = _num(price)
    d = _num(discount_pct)
    if pr is None or d is None:
        return None
    d = max(0, min(80, d))
    v = _dec(pr) * (100 - _dec(d)) / 100
    return float(v.quantize(Decimal('0.01'), rounding=ROUND_CEILING))


def star_rating(score):
    s = _num(score)
    if s is None:
        return None
    r = int(_dec(s).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    if r < 0 or r > 100:
        return None
    return min(5, r // 20 + 1)


def _is_business_day(d):
    if d.weekday() >= 5:
        return False
    if (d.month, d.day) in ((1, 1), (12, 25)):
        return False
    return True


def business_days_add(start_date, n):
    d = _parse_date(start_date)
    k = _int_value(n)
    if d is None or k is None:
        return None
    if k < 0:
        k = 0
    if k > 100000:
        return None
    one = datetime.timedelta(days=1)
    try:
        while not _is_business_day(d):
            d += one
        while k > 0:
            d += one
            if _is_business_day(d):
                k -= 1
    except OverflowError:
        return None
    return d.isoformat()


def slugify_title(title):
    if isinstance(title, (int, float)) and not isinstance(title, bool):
        title = str(title)
    if not isinstance(title, str):
        return None
    s = title.lower().replace('&', ' and ')
    s = s.replace("'", '').replace('’', '')
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    if len(s) > 40:
        cut = s[:41]
        if cut[40] == '-':
            s = cut[:40]
        else:
            pos = cut.rfind('-', 0, 41)
            s = cut[:pos] if pos > 0 else s[:40]
        s = s.strip('-')
    return s


_BANDS = [(18, '18-24'), (25, '25-34'), (35, '35-44'), (45, '45-54'),
          (55, '55-64'), (65, '65+'), (75, '75+')]


def age_band(birth_date, as_of_date):
    b = _parse_date(birth_date)
    a = _parse_date(as_of_date)
    if b is None or a is None or b > a:
        return None
    if b.month == 2 and b.day == 29:
        try:
            bday = datetime.date(a.year, 2, 29)
        except ValueError:
            bday = datetime.date(a.year, 3, 1)
    else:
        bday = datetime.date(a.year, b.month, b.day)
    age = a.year - b.year - (1 if a < bday else 0)
    label = 'minor'
    for lo, name in _BANDS:
        if age >= lo:
            label = name
    return label


# ---------------------------------------------------------------- 4 decisions


def late_fee(days_late, amount):
    d = _num(days_late)
    a = _num(amount)
    if d is None or a is None:
        return None
    if a <= 0 or d <= 2:
        return 0.0
    weeks = math.ceil(d / 7)
    fee = _dec(a) * Decimal('0.02') * weeks
    fee = max(fee, Decimal('5.00'))
    fee = min(fee, _dec(a) * Decimal('0.20'))
    return float(fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


_SKU_RE = re.compile(r'^[A-Z]{3}-\d{4}$')


def sku_check(code):
    if not isinstance(code, str):
        return None
    s = code.strip().upper()
    if not _SKU_RE.match(s):
        return None
    if 'I' in s[:3] or 'O' in s[:3]:
        return None
    if s[4:] == '0000':
        return None
    return s


_TIERS = {'silver': 1, 'gold': 2, 'platinum': 3}


def loyalty_points(amount, tier):
    a = _num(amount)
    if a is None or not isinstance(tier, str):
        return None
    mult = _TIERS.get(tier.lower(), 1)
    pts = int(a) * mult
    return min(pts, 5000)


_ZONES = {1: Decimal('1'), 2: Decimal('1.5'), 3: Decimal('2')}


def shipping_cost(weight_kg, zone):
    w = _num(weight_kg)
    if w is None or zone is None:
        return None
    if w <= 0 or w > 30:
        return None
    z = zone if isinstance(zone, int) and not isinstance(zone, bool) else None
    if isinstance(zone, float) and zone.is_integer():
        z = int(zone)
    mult = _ZONES.get(z, _ZONES[3])
    kg = math.ceil(w)
    cost = (Decimal('5.00') + Decimal('1.50') * kg) * mult
    if w > 20:
        cost += Decimal('10.00')
    return float(cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


class AvgRating:
    def __init__(self):
        self.vals = []

    def step(self, value):
        v = _num(value)
        if v is None or v < 1 or v > 5:
            return
        self.vals.append(_dec(v))

    def finalize(self):
        vals = sorted(self.vals)
        if len(vals) < 3:
            return None
        if len(vals) >= 10:
            vals = vals[1:-1]
        mean = sum(vals) / len(vals)
        return float(mean.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))


# ---------------------------------------------------------------- spec

SPEC = {
    'tier_discount': 'tier_discount(quantity): volume discount percentage for an order line: 5 from 10 units, 10 from 50 units, 15 from 100 units, otherwise 0.',
    'initials': 'initials(full_name): a person\'s initials in uppercase, one letter per name, for avatars and compact staff lists.',
    'grade_letter': 'grade_letter(pct): letter grade for a training-assessment percentage: A from 90, B from 80, C from 70, D from 60, otherwise F.',
    'invoice_no': 'invoice_no(year, seq): formats an invoice number as INV-<year>-<sequence padded to 5 digits>.',
    'percent_change': 'percent_change(old, new): percentage change from an old value to a new value for KPI reports, rounded to one decimal place.',
    'phone_digits': 'phone_digits(phone): normalises a customer phone number as typed into a form to a compact digits-only form for matching and dialling.',
    'minutes_to_hhmm': 'minutes_to_hhmm(minutes): formats a duration given in minutes as hours and minutes (H:MM) for timesheets.',
    'mask_card': 'mask_card(card_number): masks a payment card number for display on receipts, showing only the last 4 digits.',
    'fiscal_quarter': 'fiscal_quarter(d): fiscal quarter label (FY<year>-Q<n>) of a date; the fiscal year starts on 1 April and is named after the calendar year in which it ends.',
    'split_bill': 'split_bill(total, people): each person\'s share, in currency with cents, when a bill is split evenly between people.',
    'net_price': 'net_price(price, discount_pct): customer price, in currency with cents, after applying a percentage discount to a list price.',
    'star_rating': 'star_rating(score): converts a 0-100 customer satisfaction score into a 1-5 star rating, each star covering a fifth of the scale.',
    'business_days_add': 'business_days_add(start_date, n): the date (YYYY-MM-DD) that is n business days after start_date, weekends skipped, for delivery and SLA due dates.',
    'slugify_title': 'slugify_title(title): turns a product title into a URL slug: lowercase words and numbers joined by hyphens.',
    'age_band': 'age_band(birth_date, as_of_date): insurance age band (18-24, 25-34, 35-44, 45-54, 55-64, 65+) of a customer on a given date.',
    'late_fee': 'late_fee(days_late, amount): late-payment fee on an overdue invoice: 2% of the invoice amount per started week late.',
    'sku_check': 'sku_check(code): validates a product SKU written as three letters, a hyphen and four digits; returns the SKU in canonical form, or NULL if it is not a valid SKU.',
    'loyalty_points': 'loyalty_points(amount, tier): loyalty points earned on a purchase: 1 point per whole currency unit, times the tier multiplier (silver x1, gold x2, platinum x3).',
    'shipping_cost': 'shipping_cost(weight_kg, zone): parcel shipping charge: 5.00 base plus 1.50 per started kg, multiplied by the zone factor (zone 1 x1, zone 2 x1.5, zone 3 x2).',
    'avg_rating': 'avg_rating(rating): aggregate; average customer star rating (1 to 5) of a product across its reviews.',
}

SCALARS = {
    'tier_discount': (tier_discount, 1),
    'initials': (initials, 1),
    'grade_letter': (grade_letter, 1),
    'invoice_no': (invoice_no, 2),
    'percent_change': (percent_change, 2),
    'phone_digits': (phone_digits, 1),
    'minutes_to_hhmm': (minutes_to_hhmm, 1),
    'mask_card': (mask_card, 1),
    'fiscal_quarter': (fiscal_quarter, 1),
    'split_bill': (split_bill, 2),
    'net_price': (net_price, 2),
    'star_rating': (star_rating, 1),
    'business_days_add': (business_days_add, 2),
    'slugify_title': (slugify_title, 1),
    'age_band': (age_band, 2),
    'late_fee': (late_fee, 2),
    'sku_check': (sku_check, 1),
    'loyalty_points': (loyalty_points, 2),
    'shipping_cost': (shipping_cost, 2),
}

AGGREGATE = ('avg_rating', AvgRating)

TYPICAL = {
    'tier_discount': [(5,), (15,), (60,), (150,), (49,)],
    'initials': [('John Smith',), ('ada lovelace',), ('Mary Jane Watson',), ('Cher',)],
    'grade_letter': [(95,), (85,), (72,), (64,), (30,)],
    'invoice_no': [(2026, 42), (2025, 1), (2026, 12345), (2027, 7)],
    'percent_change': [(100, 110), (200, 150), (80, 100), (50, 75)],
    'phone_digits': [('(555) 123-4567',), ('555.123.4567',), ('555 123 4567',), ('5551234567',)],
    'minutes_to_hhmm': [(75,), (5,), (600,), (61,)],
    'mask_card': [('4111111111111111',), ('5500000000000004',), ('340000000000009',), ('6011000990139424',)],
    'fiscal_quarter': [('2026-05-10',), ('2026-12-01',), ('2027-02-14',), ('2026-08-20',)],
    'split_bill': [(100, 4), (90, 3), (50, 2), (120, 5)],
    'net_price': [(100, 10), (80, 25), (59.99, 0), (250, 40), (19.9, 50)],
    'star_rating': [(10,), (35,), (50,), (70,), (95,)],
    'business_days_add': [('2026-03-02', 3), ('2026-03-05', 2), ('2026-06-10', 5), ('2026-04-01', 10)],
    'slugify_title': [('Red Running Shoes',), ('Summer Sale 2026',), ('Blue  Mug',), ('USB-C Charging Cable',), ('Kids: Rain Boots',)],
    'age_band': [('1990-06-15', '2026-01-01'), ('2000-01-10', '2026-06-01'), ('1970-03-03', '2026-09-09'),
                 ('2005-05-05', '2026-07-07'), ('1955-02-02', '2026-04-04')],
    'late_fee': [(7, 500), (14, 500), (10, 1000), (21, 300)],
    'sku_check': [('ABC-1234',), ('XYZ-0001',), ('QRS-9000',), ('AB-1234',), ('ABC-12345',)],
    'loyalty_points': [(45.80, 'silver'), (100, 'gold'), (20, 'platinum'), (9.99, 'gold')],
    'shipping_cost': [(2, 1), (1, 2), (3, 3), (0.5, 1), (4.2, 2)],
}

EDGE = {
    'tier_discount': [(9.5,), (9,), (10,), (49.2,), (99.01,), (100,), (0,), (None,)],
    'initials': [('Jean-Luc Picard',), ('Anne-Marie Duval',), ('  john   smith ',), ('Smith-Jones',),
                 ("Mary O'Neil",), (None,)],
    'grade_letter': [(100,), (100.5,), (120,), (90,), (89.99,), (60,), (0,), (None,)],
    'invoice_no': [(2026, 99999), (2026, 100000), (2026, 123456), (2026, 0), (2026, None), (None, 5)],
    'percent_change': [(-100, -50), (-50, 50), (-200, -300), (0, 10), (3, 4), (100, 100), (None, 5)],
    'phone_digits': [('+44 20 7946 0958',), ('0044 20 7946 0958',), ('+1 (555) 123-4567',), ('001-555-123-4567',),
                     ('0201234567',), (5551234567,), (' 555-0100 ext. 22',), (None,)],
    'minutes_to_hhmm': [(0,), (59.9,), (1500,), (-15,), (-0.5,), (90.5,), (None,), ('75',)],
    'mask_card': [('4111 1111 1111 1111',), ('4111-1111-1111-1111',), ('12345678901',), ('123456789012',),
                  ('abcd11112222',), (4111111111111111,), (None,), ('',)],
    'fiscal_quarter': [('2026-04-01',), ('2026-03-31',), ('2026-05-10 14:30:00',), ('2026-05-10T09:00',),
                       (20260510,), (20261301,), ('2026-02-30',), (None,), ('10/05/2026',)],
    'split_bill': [(100, 3), (10, 3), (0.05, 2), (100, 0), (100, -2), (100, 1), (None, 2), (100, None)],
    'net_price': [(100, 90), (100, 80), (100, -10), (9.99, 15), (33.33, 33), (None, 10), (100, None), (0, 50)],
    'star_rating': [(20,), (40,), (79.5,), (79.4,), (100,), (0,), (101,), (-5,), (None,), (59.5,)],
    'business_days_add': [('2026-12-24', 1), ('2026-12-31', 1), ('2026-03-07', 1), ('2026-03-07', 0),
                          ('2026-03-04', -2), ('2026-03-06', 1), ('2026-02-30', 1), (None, 1), ('2026-03-02', 0)],
    'slugify_title': [('Salt & Pepper Grinder',), ("Men's Hiking Boots",),
                      ('Ultra Lightweight Waterproof Breathable Hiking Jacket for Women',),
                      ('A&B',), ("Rock 'n' Roll Tee",), ('  --Clearance!!  ',),
                      ('Supercalifragilisticexpialidociousproductname extra',), (None,)],
    'age_band': [('2010-01-01', '2026-01-01'), ('2008-02-29', '2026-02-28'), ('2008-02-29', '2026-03-01'),
                 ('2000-02-29', '2025-02-28'), ('2000-02-29', '2025-03-01'), ('1950-01-01', '2026-01-01'),
                 ('1951-06-01', '2026-06-01'), ('1951-06-02', '2026-06-01'), ('2030-01-01', '2026-01-01'),
                 ('1990-01-01', None)],
    'late_fee': [(2, 1000), (3, 1000), (5, 100), (70, 100), (100, 100), (7, -50), (7, 0), (7, 10), (None, 100)],
    'sku_check': [('abc-1234',), (' ABC-1234 ',), ('ABC-0000',), ('BOX-1234',), ('KIT-5000',),
                  ('abc-0000',), ('ABC 1234',), (1234,), (None,)],
    'loyalty_points': [(100, 'GOLD'), (100, 'Platinum'), (100, 'bronze'), (100, ''), (3000, 'gold'),
                       (5000, 'silver'), (-50, 'gold'), (-45.8, 'silver'), (100, None), (0.99, 'platinum')],
    'shipping_cost': [(0, 1), (-1, 1), (30, 1), (30.5, 1), (20, 1), (20.1, 1), (2, 4), (2, 0), (None, 1)],
}

AGG_TYPICAL = [[4, 5, 3], [5, 5, 4, 4], [2, 3, 4, 3], [1, 2, 3, 4, 5]]

AGG_EDGE = [
    [5, 4],
    [5, 4, None],
    [5, 4, 0, 6, 3],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 1],
    [4, 4, 5, 4],
    [3, 4, '5', 4],
    [],
]

DECISIONS = {
    'tier_discount': ['fractional quantity rounds up to whole unit'],
    'initials': ['hyphenated name parts each give an initial'],
    'grade_letter': ['above 100 gives A+'],
    'invoice_no': ['sequence above 99999 gives NULL'],
    'percent_change': ['negative old value uses absolute value as base'],
    'phone_digits': ['leading + kept', 'leading 00 converted to +'],
    'minutes_to_hhmm': ['negative duration gives NULL', 'fractional minutes truncated'],
    'mask_card': ['spaces and hyphens stripped', 'fewer than 12 digits gives NULL'],
    'fiscal_quarter': ['date with time part accepted', 'integer YYYYMMDD accepted'],
    'split_bill': ['share rounded up to the cent', 'people below 1 treated as 1'],
    'net_price': ['discount capped at 80', 'negative discount treated as 0', 'rounded up to the cent'],
    'star_rating': ['band boundaries belong to upper star', 'out of 0-100 gives NULL', 'score rounded half up first'],
    'business_days_add': ['Jan 1 and Dec 25 skipped', 'weekend/holiday start rolls to next business day',
                          'negative n treated as 0'],
    'slugify_title': ['& becomes and', 'apostrophes removed without split', 'max 40 chars cut at word boundary'],
    'age_band': ['under 18 gives minor', 'Feb 29 birthday on Mar 1 in non-leap years', '75 and over gives 75+'],
    'late_fee': ['grace period up to 2 days', 'minimum fee 5.00', 'fee capped at 20% of amount',
                 'non-positive amount gives 0'],
    'sku_check': ['lowercase accepted and uppercased', 'surrounding whitespace trimmed',
                  'digits 0000 invalid', 'letters I and O invalid'],
    'loyalty_points': ['tier case-insensitive', 'unknown tier earns x1', 'capped at 5000 per purchase',
                       'negative amount gives negative points'],
    'shipping_cost': ['over 30 kg gives NULL', 'non-positive weight gives NULL', 'unknown zone charged as zone 3',
                      'over 20 kg adds 10.00 surcharge'],
    'avg_rating': ['ratings outside 1-5 or non-numeric ignored', 'fewer than 3 valid ratings gives NULL',
                   '10 or more ratings drop one highest and one lowest', 'rounded half up to 1 decimal'],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, nargs) in SCALARS.items():
        con.create_function(name, nargs, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con
