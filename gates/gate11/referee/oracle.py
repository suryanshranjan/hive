"""Business-function policy oracle: 19 scalar SQL functions and 1 aggregate.

Each function's exact behaviour is company policy. Standard library only.
"""

import datetime
import math
import re
import sqlite3
import unicodedata
from decimal import Decimal, ROUND_CEILING, ROUND_DOWN, ROUND_FLOOR, ROUND_HALF_UP, InvalidOperation

CENT = Decimal('0.01')


# ---------------------------------------------------------------- helpers

def _num(v):
    """SQL value -> finite Decimal, or None."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, int):
        return Decimal(v)
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return None
        return Decimal(repr(v))
    if isinstance(v, str):
        try:
            d = Decimal(v.strip())
        except (InvalidOperation, ValueError):
            return None
        return d if d.is_finite() else None
    return None


def _money(d, rounding=ROUND_HALF_UP):
    return float(d.quantize(CENT, rounding=rounding))


def _date(v):
    """'YYYY-MM-DD' or 'YYYY/MM/DD' (optional time suffix) or int YYYYMMDD -> date."""
    try:
        if isinstance(v, int) and not isinstance(v, bool):
            if not 10000101 <= v <= 99991231:
                return None
            return datetime.date(v // 10000, v // 100 % 100, v % 100)
        if isinstance(v, str):
            m = re.fullmatch(r'\s*(\d{4})[-/](\d{2})[-/](\d{2})(?:[ T].*)?\s*', v)
            if not m:
                return None
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except (ValueError, OverflowError):
        return None
    return None


HOLIDAYS = {(1, 1), (12, 25), (12, 26)}


def _is_business_day(d):
    return d.weekday() < 5 and (d.month, d.day) not in HOLIDAYS


def _count_business(a, b):
    """Business days in [a, b), a <= b."""
    days = (b - a).days
    weeks, rem = divmod(days, 7)
    count = weeks * 5
    for i in range(rem):
        if (a + datetime.timedelta(days=weeks * 7 + i)).weekday() < 5:
            count += 1
    for year in range(a.year, b.year + 1):
        for (mo, dy) in HOLIDAYS:
            h = datetime.date(year, mo, dy)
            if a <= h < b and h.weekday() < 5:
                count -= 1
    return count


def _safe(fn):
    def wrapper(*args):
        try:
            return fn(*args)
        except Exception:
            return None
    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    return wrapper


# ---------------------------------------------------------------- scalars

@_safe
def net_price(gross, discount_pct):
    g = _num(gross)
    if g is None or g < 0:
        return None
    p = _num(discount_pct)
    if p is None or p < 0:
        p = Decimal(0)
    if p > 70:
        p = Decimal(70)
    return _money(g * (100 - p) / 100)


VAT_RATES = {'DE': Decimal('0.19'), 'FR': Decimal('0.20'), 'GB': Decimal('0.20'),
             'NL': Decimal('0.21'), 'IT': Decimal('0.22'), 'ES': Decimal('0.21')}


@_safe
def vat_amount(net, country):
    n = _num(net)
    if n is None or not isinstance(country, str):
        return None
    code = country.strip().upper()
    if code == 'UK':
        code = 'GB'
    rate = VAT_RATES.get(code)
    if rate is None:
        return None
    if abs(n) < 1:
        return 0.0
    return _money(n * rate, ROUND_DOWN)


@_safe
def late_fee(days_late, invoice_amount):
    d = _num(days_late)
    a = _num(invoice_amount)
    if d is None or a is None or a < 0:
        return None
    days = int(d.to_integral_value(rounding=ROUND_FLOOR))
    if days <= 2:
        return 0.0
    fee = a * Decimal('0.005') * days
    fee = max(fee, Decimal(5))
    fee = min(fee, a * Decimal('0.25'))
    return _money(fee)


@_safe
def business_days(start_date, end_date):
    a, b = _date(start_date), _date(end_date)
    if a is None or b is None:
        return None
    if a <= b:
        return _count_business(a, b)
    return -_count_business(b, a)


@_safe
def add_business_days(date, n):
    d = _date(date)
    k = _num(n)
    if d is None or k is None:
        return None
    k = int(k.to_integral_value(rounding=ROUND_FLOOR))
    if abs(k) > 100000:
        return None
    step = datetime.timedelta(days=1 if k >= 0 else -1)
    while not _is_business_day(d):
        d += step
    for _ in range(abs(k)):
        d += step
        while not _is_business_day(d):
            d += step
    return d.isoformat()


@_safe
def fiscal_quarter(date):
    d = _date(date)
    if d is None:
        return None
    if d.month == 3 and d.day >= 25:  # year-end close cutoff
        return 'FY%d-Q1' % (d.year + 1)
    fy = d.year + 1 if d.month >= 4 else d.year
    q = ((d.month - 4) % 12) // 3 + 1
    return 'FY%d-Q%d' % (fy, q)


KEYPAD = {}
for _digit, _letters in {'2': 'ABC', '3': 'DEF', '4': 'GHI', '5': 'JKL',
                         '6': 'MNO', '7': 'PQRS', '8': 'TUV', '9': 'WXYZ'}.items():
    for _ch in _letters:
        KEYPAD[_ch] = _digit


@_safe
def normalize_phone(text):
    if isinstance(text, int) and not isinstance(text, bool):
        text = str(text)
    if not isinstance(text, str):
        return None
    s = re.sub(r'\s*(?:x|ext\.?|#)\s*\d+\s*$', '', text.strip(), flags=re.I)
    s = ''.join(KEYPAD.get(c, c) for c in s.upper())
    intl = False
    if s.startswith('+'):
        intl, s = True, s[1:]
    elif s.startswith('00'):
        intl, s = True, s[2:]
    if re.search(r'[^0-9 ().\-]', s):
        return None
    digits = re.sub(r'\D', '', s)
    if intl:
        return '+' + digits if 8 <= len(digits) <= 15 else None
    if len(digits) == 10:
        return '+1' + digits
    if len(digits) == 11 and digits[0] == '1':
        return '+' + digits
    return None


@_safe
def slugify_title(text):
    if isinstance(text, (int, float)) and not isinstance(text, bool):
        text = str(text)
    if not isinstance(text, str):
        return None
    s = unicodedata.normalize('NFKD', text)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.replace('&', ' and ').replace("'", '').replace('’', '').lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    if len(s) > 40:
        cut = s[:40]
        if s[40] != '-' and '-' in cut:
            cut = cut[:cut.rfind('-')]
        s = cut.strip('-')
    return s or 'untitled'


def _luhn_ok(digits):
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


@_safe
def mask_card(text):
    if isinstance(text, int) and not isinstance(text, bool):
        text = str(text)
    if not isinstance(text, str):
        return None
    digits = re.sub(r'[ \-]', '', text.strip())
    if not digits.isdigit() or not 12 <= len(digits) <= 19:
        return None
    if not _luhn_ok(digits):
        return 'INVALID'
    masked = '*' * (len(digits) - 4) + digits[-4:]
    if len(digits) == 15 and digits[:2] in ('34', '37'):
        return ' '.join([masked[:4], masked[4:10], masked[10:]])
    return ' '.join(masked[i:i + 4] for i in range(0, len(masked), 4))


@_safe
def credit_grade(score):
    n = _num(score)
    if n is None or n < 300 or n > 850:
        return None
    s = int(n.to_integral_value(rounding=ROUND_FLOOR))
    for floor_, grade in ((760, 'A'), (700, 'B'), (640, 'C'), (560, 'D')):
        if s >= floor_:
            return grade
    return 'E'


SHIP_ZONES = {1: (Decimal(5), Decimal('1.2')), 2: (Decimal(8), Decimal('1.8')),
              3: (Decimal(12), Decimal('2.5'))}


@_safe
def shipping_cost(weight_kg, zone):
    w = _num(weight_kg)
    z = _num(zone)
    if w is None or z is None or w <= 0 or z != z.to_integral_value():
        return None
    rates = SHIP_ZONES.get(int(z))
    if rates is None:
        return None
    if w > 30:
        return 'FREIGHT'
    billable = (w * 2).to_integral_value(rounding=ROUND_CEILING) / 2
    return _money(rates[0] + rates[1] * billable)


TIERS = {'silver': Decimal(1), 'gold': Decimal('1.5'), 'platinum': Decimal(2)}


@_safe
def loyalty_points(amount, tier):
    a = _num(amount)
    if a is None:
        return None
    if a < 10:
        return 0
    mult = Decimal(1)
    if isinstance(tier, str):
        mult = TIERS.get(tier.strip().lower(), Decimal(1))
    pts = int((a * mult).to_integral_value(rounding=ROUND_FLOOR))
    return min(pts, 5000)


@_safe
def normalize_sku(text):
    if not isinstance(text, str):
        return None
    m = re.fullmatch(r'([A-Z]{3})[\s\-_]*([0-9OIL]{1,5})', text.strip().upper())
    if not m:
        return None
    num = int(m.group(2).replace('O', '0').replace('I', '1').replace('L', '1'))
    if num == 0:
        return None
    return '%s-%05d' % (m.group(1), num)


@_safe
def age_band(age):
    n = _num(age)
    if n is None or n < 0 or n > 120:
        return None
    a = int(n.to_integral_value(rounding=ROUND_FLOOR))
    if a < 18:
        return 'MINOR'
    if a < 25:
        return '18-24'
    if a >= 65:
        return '65+'
    lo = 25 + (a - 25) // 10 * 10
    return '%d-%d' % (lo, lo + 9)


@_safe
def split_bill(total, people):
    t = _num(total)
    p = _num(people)
    if t is None or p is None or t < 0:
        return None
    n = int(p.to_integral_value(rounding=ROUND_FLOOR))
    if n < 1:
        return None
    return _money(t / n, ROUND_CEILING)


PARTICLES = {'van', 'von', 'de', 'der', 'da', 'di', 'du', 'la', 'le', 'del', 'den'}


@_safe
def initials(name):
    if not isinstance(name, str):
        return None
    words = name.split()
    out = []
    for i, w in enumerate(words):
        if i > 0 and w in PARTICLES:
            continue
        for part in w.split('-'):
            letters = [c for c in part if c.isalpha()]
            if letters:
                out.append(letters[0].upper())
    if not out:
        return None
    if len(out) > 3:
        out = out[:2] + out[-1:]
    return ''.join(out)


@_safe
def rating_stars(score):
    n = _num(score)
    if n is None or n < 0:
        return None
    if n > 100:
        n = Decimal(100)
    stars = (n / 10).to_integral_value(rounding=ROUND_FLOOR) / 2
    if n > 0 and stars == 0:
        stars = Decimal('0.5')
    return float(stars)


@_safe
def meeting_end(start_time, duration_minutes):
    if not isinstance(start_time, str):
        return None
    m = re.fullmatch(r'\s*(\d{1,2}):(\d{2})\s*', start_time)
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    if h > 23 or mi > 59:
        return None
    start = h * 60 + mi
    if start < 8 * 60 or start >= 18 * 60:
        return None
    d = _num(duration_minutes)
    if d is None:
        return None
    if d <= 0:
        end = start
    else:
        blocks = (d / 15).to_integral_value(rounding=ROUND_CEILING)
        end = start + int(blocks) * 15
    if end > 18 * 60:
        return 'OVERTIME'
    return '%02d:%02d' % divmod(end, 60)


CURRENCY = {'USD': ('$', 2), 'GBP': ('£', 2), 'EUR': ('€', 2), 'JPY': ('¥', 0)}


@_safe
def money_format(amount, currency):
    a = _num(amount)
    if a is None or not isinstance(currency, str):
        return None
    code = currency.strip().upper()
    if not re.fullmatch(r'[A-Z]{3}', code):
        return None
    symbol, places = CURRENCY.get(code, (None, 2))
    q = a.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    neg = q < 0
    body = '{:,.{p}f}'.format(abs(q), p=places)
    body = symbol + body if symbol else body + ' ' + code
    return '(' + body + ')' if neg else body


# ---------------------------------------------------------------- aggregate

class PanelScore:
    def __init__(self):
        self.vals = []

    def step(self, value):
        try:
            n = _num(value)
            if n is not None and 0 <= n <= 10:
                self.vals.append(n)
        except Exception:
            pass

    def finalize(self):
        try:
            vals = sorted(self.vals)
            if not vals:
                return None
            if len(vals) >= 5:
                vals = vals[1:-1]
            mean = sum(vals) / len(vals)
            return float(mean.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
        except Exception:
            return None


# ---------------------------------------------------------------- registry

SPEC = {
    'net_price': 'net_price(gross, discount_pct): price a customer pays after a percentage discount, in currency units',
    'vat_amount': 'vat_amount(net, country): VAT owed on a net invoice amount for a two-letter country code',
    'late_fee': 'late_fee(days_late, invoice_amount): penalty charged on an invoice paid late, at 0.5% of the amount per day late',
    'business_days': 'business_days(start_date, end_date): number of working days between two ISO dates, for SLA tracking',
    'add_business_days': 'add_business_days(date, n): ISO date that is n working days after a given ISO date, for due dates',
    'fiscal_quarter': 'fiscal_quarter(date): fiscal quarter label for a date, used on finance reports',
    'normalize_phone': 'normalize_phone(text): customer phone number in E.164 form, defaulting to North American numbers',
    'slugify_title': 'slugify_title(text): URL slug for an article or product title',
    'mask_card': 'mask_card(text): payment card number masked for display on receipts, showing only the last four digits',
    'credit_grade': 'credit_grade(score): letter grade A to E for a customer credit score',
    'shipping_cost': 'shipping_cost(weight_kg, zone): parcel shipping charge for a weight and delivery zone 1, 2 or 3',
    'loyalty_points': 'loyalty_points(amount, tier): loyalty points earned on a purchase by a member of a tier (silver, gold, platinum)',
    'normalize_sku': 'normalize_sku(text): canonical stock-keeping-unit code of three letters and a five-digit number',
    'age_band': 'age_band(age): marketing age band for a customer age in years',
    'split_bill': 'split_bill(total, people): amount each person pays when a bill is split evenly',
    'initials': 'initials(name): uppercase initials of a person\'s full name, for avatars and badges',
    'rating_stars': 'rating_stars(score): star rating out of 5 for a review score out of 100',
    'meeting_end': 'meeting_end(start_time, duration_minutes): end time HH:MM of a meeting booked in a meeting room',
    'money_format': 'money_format(amount, currency): display string for a money amount in a three-letter currency',
    'panel_score': 'panel_score(score): overall score of a judging panel from the judges\' individual 0 to 10 scores',
}

SCALARS = {
    'net_price': (net_price, 2),
    'vat_amount': (vat_amount, 2),
    'late_fee': (late_fee, 2),
    'business_days': (business_days, 2),
    'add_business_days': (add_business_days, 2),
    'fiscal_quarter': (fiscal_quarter, 1),
    'normalize_phone': (normalize_phone, 1),
    'slugify_title': (slugify_title, 1),
    'mask_card': (mask_card, 1),
    'credit_grade': (credit_grade, 1),
    'shipping_cost': (shipping_cost, 2),
    'loyalty_points': (loyalty_points, 2),
    'normalize_sku': (normalize_sku, 1),
    'age_band': (age_band, 1),
    'split_bill': (split_bill, 2),
    'initials': (initials, 1),
    'rating_stars': (rating_stars, 1),
    'meeting_end': (meeting_end, 2),
    'money_format': (money_format, 2),
}

AGGREGATE = ('panel_score', PanelScore)

TYPICAL = {
    'net_price': [(100, 10), (80, 25), (50, 20), (200, 15), (19.99, 0)],
    'vat_amount': [(100, 'DE'), (250, 'FR'), (80, 'NL'), (10, 'GB'), (50, 'IT')],
    'late_fee': [(10, 1000), (20, 500), (4, 1000), (30, 200)],
    'business_days': [('2025-03-03', '2025-03-10'), ('2025-03-04', '2025-03-06'),
                      ('2025-06-02', '2025-06-30'), ('2025-09-01', '2025-09-05')],
    'add_business_days': [('2025-03-03', 5), ('2025-03-04', 2), ('2025-06-02', 10), ('2025-09-03', 1)],
    'fiscal_quarter': [('2025-05-10',), ('2025-08-20',), ('2025-11-03',), ('2026-02-14',)],
    'normalize_phone': [('(415) 555-2671',), ('415.555.2671',), ('212-555-0187',), ('+1 415 555 2671',)],
    'slugify_title': [('Hello World',), ('Q3 Results Are In',), ('New Product Launch 2025',), ('Annual Report',)],
    'mask_card': [('4111111111111111',), ('5555555555554444',), ('4012888888881881',), ('6011111111111117',)],
    'credit_grade': [(800,), (730,), (670,), (600,)],
    'shipping_cost': [(2, 1), (5, 2), (1.5, 3), (10, 1), (3, 2)],
    'loyalty_points': [(100, 'silver'), (40, 'gold'), (25, 'platinum'), (60, 'silver'), (200, 'gold')],
    'normalize_sku': [('abc-1234',), ('ABC1234',), ('xyz 99',), ('KLN-50210',)],
    'age_band': [(30,), (40,), (52,), (27,)],
    'split_bill': [(100, 4), (90, 3), (60, 2), (50, 5)],
    'initials': [('John Smith',), ('mary jane watson',), ('Ada Lovelace',), ('Alan Turing',)],
    'rating_stars': [(100,), (80,), (60,), (40,), (90,)],
    'meeting_end': [('09:00', 30), ('14:15', 45), ('10:00', 90), ('13:30', 60)],
    'money_format': [(1234.5, 'USD'), (12, 'GBP'), (1000000, 'USD'), (5.25, 'GBP'), (99.99, 'EUR')],
}

EDGE = {
    'net_price': [(100, 80), (100, 70), (100, -5), (100, None), (10.005, 0),
                  (-50, 10), (None, 10), (0.125, 0), (33.33, 33.3)],
    'vat_amount': [(10.99, 'DE'), (0.5, 'DE'), (100, 'UK'), (100, 'de'), (100, 'US'),
                   (-100, 'FR'), (None, 'DE'), (100, None), (1, 'NL')],
    'late_fee': [(2, 1000), (3, 1000), (3, 100), (100, 1000), (3, 10),
                 (-5, 100), (10, -100), (10.9, 1000), (None, 100)],
    'business_days': [('2025-03-01', '2025-03-10'), ('2025-03-03', '2025-03-08'),
                      ('2025-12-22', '2025-12-29'), ('2025-03-10', '2025-03-03'),
                      ('2025-03-03', '2025-03-03'), ('2025-02-30', '2025-03-03'),
                      (None, '2025-03-03'), ('2025-12-31', '2026-01-05')],
    'add_business_days': [('2025-03-01', 0), ('2025-03-01', 1), ('2025-12-24', 1), ('2025-03-10', -5),
                          ('2025-03-02', -1), (None, 3), ('bad', 3), ('2025-03-03', None),
                          ('2025-03-03', 2.7)],
    'fiscal_quarter': [('2026-03-24',), ('2026-03-25',), ('2025-04-01',), (20250815,),
                       ('2025/08/15',), ('2025-13-01',), (None,), ('2025-03-31 23:59',)],
    'normalize_phone': [('1-800-FLOWERS',), ('415-555-2671 x204',), ('0044 20 7946 0958',),
                        ('555-2671',), ('',), (None,), ('14155552671',),
                        ('+44 20 7946 0958',), (4155552671,)],
    'slugify_title': [('Café Crème',), ('Salt & Pepper',), ("Don't Stop",), ('!!!',),
                      ('The Quarterly Business Review For Northern Region Sales',),
                      ('  Multiple   Spaces -- here ',), (None,), (12345,)],
    'mask_card': [('378282246310005',), ('4111111111111112',), ('4111-1111-1111-1111',),
                  ('4111',), ('4111a11111111111',), (None,), (4111111111111111,),
                  ('4222222222222',)],
    'credit_grade': [(760,), (759,), (700,), (640,), (560,), (559,), (300,), (299,),
                     (851,), (759.9,)],
    'shipping_cost': [(2.1, 1), (0.1, 1), (30, 1), (30.01, 1), (0, 1), (2, 4),
                      (2, None), (None, 1), (-1, 2), (2, 1.5)],
    'loyalty_points': [(9.99, 'gold'), (10, 'gold'), (99.99, 'silver'), (33.5, 'gold'),
                       (100, 'GOLD'), (100, None), (100, 'diamond'), (10000, 'platinum'),
                       (-50, 'silver'), (None, 'gold')],
    'normalize_sku': [('ABC-12O4',), ('abc-l23',), ('ABC-00000',), ('ABC-123456',),
                      ('AB-123',), ('ABCD-123',), (' abc_77 ',), (None,), ('ABC-',)],
    'age_band': [(17,), (18,), (24,), (25,), (64.9,), (65,), (120,), (121,), (-1,), (None,)],
    'split_bill': [(100, 3), (10, 3), (0, 4), (100, 0), (100, 2.9), (-20, 2),
                   (100, None), (0.01, 3), (100, -2)],
    'initials': [('Ludwig van Beethoven',), ('Jean-Luc Picard',), ('John Ronald Reuel Tolkien',),
                 ('Vincent Van Gogh',), ('   ',), (None,), ('madonna',), ("Conan O'Brien",),
                 ('Mary-Kate Ashley Olsen',)],
    'rating_stars': [(79,), (75,), (3,), (0,), (120,), (-5,), (None,), (99.9,), (50.5,)],
    'meeting_end': [('09:00', 20), ('09:00', 1), ('17:00', 60), ('17:00', 61), ('07:45', 30),
                    ('9:00', 30), ('09:00', 0), ('25:00', 30), (None, 30), ('18:00', 15)],
    'money_format': [(-5, 'USD'), (1234.5, 'JPY'), (1234.5, 'chf'), (0.005, 'USD'),
                     (2.675, 'USD'), (100, 'usd'), (None, 'USD'), (100, None),
                     (-0.001, 'USD'), (-1234.5, 'EUR')],
}

AGG_TYPICAL = [[7, 8, 9], [6, 8], [5, 6, 7, 8], [9.0, 9.5, 8.5]]

AGG_EDGE = [
    [1, 8, 8, 8, 10],
    [None, 7, 9],
    [12, 7, 8, -1],
    [],
    [None, None],
    [7, 8, 8],
    [7.2, 7.3],
    [10, 10, 10, 10, 0],
]


def connect():
    conn = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, nargs) in SCALARS.items():
        conn.create_function(name, nargs, fn, deterministic=True)
    conn.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return conn
