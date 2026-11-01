import re
import math
import sqlite3
import datetime
import unicodedata
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN, ROUND_CEILING
from fractions import Fraction


# ---------------------------------------------------------------- helpers
def _d(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError('not numeric')
    if isinstance(x, float):
        if x != x or x in (float('inf'), float('-inf')):
            raise ValueError('not finite')
        return Decimal(repr(x))
    return Decimal(x)


def _r(x, places, mode=ROUND_HALF_UP):
    return x.quantize(Decimal(1).scaleb(-places), rounding=mode)


def _f(x):
    v = float(x)
    return 0.0 if v == 0 else v


def _date(s):
    if not isinstance(s, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', s):
        raise ValueError('bad date')
    return datetime.date(int(s[:4]), int(s[5:7]), int(s[8:10]))


def _safe(fn):
    def w(*args):
        if any(a is None for a in args):
            return None
        try:
            return fn(*args)
        except Exception:
            return None
    w.__name__ = fn.__name__
    return w


def _lh(prefix):
    total = 0
    for i, ch in enumerate(reversed(prefix)):
        n = int(ch)
        if i % 2 == 0:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return prefix + str((10 - total % 10) % 10)


# ---------------------------------------------------------------- functions
def tip_amount(bill, pct):
    b, p = _d(bill), _d(pct)
    if b <= 0 or p <= 0:
        return 0.0
    p = min(p, Decimal(30))
    return _f(_r(b * p / 100, 2))


def late_fee(amount, days):
    a, n = _d(amount), _d(days)
    if a <= 0 or n <= 3:
        return 0.0
    fee = a * n * Decimal('0.005')
    fee = min(fee, a * Decimal('0.25'))
    fee = _r(fee, 2)
    fee = max(fee, Decimal('5.00'))
    return _f(fee)


def volume_price(price, qty):
    p, q = _d(price), _d(qty)
    if q <= 0:
        return 0.0
    if q < 10:
        rate = Decimal('1')
    elif q < 50:
        rate = Decimal('0.95')
    elif q < 500:
        rate = Decimal('0.90')
    else:
        rate = Decimal('0.75')
    return _f(_r(p * q * rate, 2))


def luhn_flag(card):
    s = str(card)
    s = s.replace(' ', '').replace('-', '')
    if not re.fullmatch(r'[0-9]+', s) or not (12 <= len(s) <= 19):
        return 0
    total = 0
    for i, ch in enumerate(reversed(s)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return 1 if total % 10 == 0 else 0


def bday_age(birth, asof):
    b, a = _date(birth), _date(asof)
    if a < b:
        return 0
    bm, bd = b.month, b.day
    leap = a.year % 4 == 0 and (a.year % 100 != 0 or a.year % 400 == 0)
    if (bm, bd) == (2, 29) and not leap:
        bm, bd = 3, 1
    age = a.year - b.year
    if (a.month, a.day) < (bm, bd):
        age -= 1
    return min(age, 99)


def due_date(start, days):
    d = _date(start)
    n = int(_d(days))
    if abs(n) > 100000:
        return None

    def biz(x):
        return x.weekday() < 5 and (x.month, x.day) not in ((1, 1), (12, 25))
    one = datetime.timedelta(days=1)
    if n == 0:
        while not biz(d):
            d += one
    else:
        step = one if n > 0 else -one
        cnt = abs(n)
        while cnt:
            d += step
            if biz(d):
                cnt -= 1
    return d.isoformat()


def shipping_cost(weight, zone):
    w, z = _d(weight), _d(zone)
    base = {1: Decimal('5'), 2: Decimal('8'), 3: Decimal('12')}
    b = base[int(z)] if z in (1, 2, 3) else base[3]
    billed = (w * 2).to_integral_value(rounding=ROUND_CEILING) / 2
    cost = b
    if billed > 1:
        cost += Decimal('1.5') * (billed - 1)
    if billed > 30:
        cost += Decimal('25')
    return _f(cost)


def star_rating(up, down):
    u, d = max(_d(up), Decimal(0)), max(_d(down), Decimal(0))
    t = u + d
    if t < 5:
        r = u + Decimal('0.6') * (5 - t)
    else:
        r = 5 * u / t
    return _f(_r(r, 1))


def mask_email(email):
    s = str(email)
    if '@' not in s:
        return ''
    local, domain = s.rsplit('@', 1)
    if not local or not domain:
        return ''
    m = '*' if len(local) == 1 else local[0] + '***'
    return m + '@' + domain.lower()


def slugify(title):
    s = unicodedata.normalize('NFKD', str(title))
    s = s.encode('ascii', 'ignore').decode('ascii')
    s = s.replace('&', ' and ').lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    s = s[:40].rstrip('-')
    return s or 'n-a'


def initials(name):
    toks = str(name).split()
    while len(toks) > 1 and toks[-1].strip('.,').lower() in ('jr', 'sr', 'ii', 'iii', 'iv'):
        toks.pop()
    if not toks:
        return '?'
    if len(toks) == 1:
        return toks[0][:2].upper()
    return (toks[0][0] + toks[-1][0]).upper()


def risk_band(score):
    s = _r(_d(score), 0)
    if s >= 85:
        return 'CRITICAL'
    if s >= 65:
        return 'HIGH'
    if s >= 35:
        return 'MEDIUM'
    return 'LOW'


def slots_needed(minutes, slot):
    m, s = _d(minutes), _d(slot)
    if s <= 0:
        s = Decimal(30)
    if m <= 0:
        return 0
    n = int(((m - 5) / s).to_integral_value(rounding=ROUND_CEILING))
    return max(1, n)


def pct_change(old, new):
    o, n = _d(old), _d(new)
    if o == 0:
        if n == 0:
            return 0.0
        return 999.9 if n > 0 else -999.9
    ch = (n - o) / abs(o) * 100
    ch = max(min(ch, Decimal('999.9')), Decimal('-999.9'))
    return _f(_r(ch, 1))


def parse_money(text):
    if not isinstance(text, str):
        return _f(_d(text))
    s = text.strip()
    for c in '$€£¥ \t':
        s = s.replace(c, '')
    neg = False
    if s.startswith('(') and s.endswith(')'):
        neg = True
        s = s[1:-1]
    if s.startswith('-'):
        neg = True
        s = s[1:]
    elif s.startswith('+'):
        s = s[1:]
    mult = Decimal(1)
    if s and s[-1] in 'kK':
        mult = Decimal(1000)
        s = s[:-1]
    if '.' not in s and re.fullmatch(r'\d+,\d{1,2}', s):
        s = s.replace(',', '.')
    elif re.fullmatch(r'\d{1,3}(,\d{3})+(\.\d+)?', s):
        s = s.replace(',', '')
    if not re.fullmatch(r'\d+(\.\d+)?|\.\d+', s):
        return 0.0
    v = Decimal(s) * mult
    return _f(-v if neg else v)


def ean_check_digit(code):
    s = str(code)
    if not re.fullmatch(r'[0-9]+', s):
        return None
    if len(s) == 12:
        w = [1, 3] * 6
    elif len(s) == 7:
        w = [3, 1] * 3 + [3]
    else:
        return None
    total = sum(int(c) * k for c, k in zip(s, w))
    return (10 - total % 10) % 10


def grade_letter(score, max_score):
    s, m = _d(score), _d(max_score)
    if m <= 0:
        return None
    p = s * 100 / m
    if p >= 98:
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


def quarter_label(date):
    d = _date(date)
    y, m = d.year, d.month
    if m in (1, 4, 7, 10) and d.day <= 3:
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    fy = y + 1 if m >= 4 else y
    q = ((m - 4) % 12) // 3 + 1
    return 'FY%d-Q%d' % (fy, q)


def compact_num(n):
    x = _d(n)
    neg = x < 0
    v = abs(x)
    units = ['', 'K', 'M', 'B', 'T']
    i = 0
    while v >= 1000 and i < 4:
        v = v / 1000
        i += 1
    if i == 0:
        out = str(int(v.to_integral_value(rounding=ROUND_DOWN)))
    else:
        out = format(_r(v, 1, ROUND_DOWN), 'f')
        if out.endswith('.0'):
            out = out[:-2]
        out += units[i]
    if neg and out != '0':
        out = '-' + out
    return out


class TrimmedMean:
    def __init__(self):
        self.vals = []

    def step(self, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return
        try:
            self.vals.append(_d(value))
        except Exception:
            pass

    def finalize(self):
        v = sorted(self.vals)
        if not v:
            return None
        if len(v) >= 5:
            v = v[1:-1]
        return _f(_r(sum(v) / len(v), 2))


# ---------------------------------------------------------------- module API
SPEC = {
    'tip_amount': 'tip_amount(bill, pct): Suggested gratuity in dollars for a restaurant bill at a given tip percentage.',
    'late_fee': 'late_fee(amount_due, days_late): Penalty charged on an overdue invoice, based on the amount owed and how many days it is late.',
    'volume_price': 'volume_price(unit_price, qty): Total order price for a quantity of an item, with volume discounts applied.',
    'luhn_flag': 'luhn_flag(card_number): 1 if a payment card number looks valid, otherwise 0.',
    'bday_age': "bday_age(birth_date, as_of_date): Customer's age in whole years on a given date; dates are YYYY-MM-DD.",
    'due_date': 'due_date(start_date, business_days): Date that is the given number of business days after (or before, if negative) a start date, as YYYY-MM-DD.',
    'shipping_cost': 'shipping_cost(weight_kg, zone): Shipping charge in dollars for a parcel of a given weight sent to a delivery zone (1 to 3).',
    'star_rating': 'star_rating(up_votes, down_votes): Display rating from 0 to 5 stars, to one decimal, built from thumbs-up and thumbs-down counts.',
    'mask_email': 'mask_email(email): Obfuscated version of an email address that is safe to show on customer-support screens.',
    'slugify': 'slugify(title): URL-friendly slug for a page or product title.',
    'initials': "initials(full_name): Short uppercase initials for a person's name, used on avatars.",
    'risk_band': 'risk_band(score): Risk label for a numeric risk score between 0 and 100.',
    'slots_needed': 'slots_needed(minutes, slot_minutes): Number of calendar slots to book for a meeting of a given length.',
    'pct_change': 'pct_change(old_value, new_value): Percentage change from an old value to a new value, to one decimal place.',
    'parse_money': 'parse_money(text): Converts a currency amount typed as text into a number.',
    'ean_check_digit': 'ean_check_digit(code): Check digit to append to a retail barcode number.',
    'grade_letter': 'grade_letter(score, max_score): Letter grade for a score out of a maximum.',
    'quarter_label': 'quarter_label(date): Fiscal quarter label for a transaction date, for finance reports.',
    'compact_num': 'compact_num(n): Short human-readable form of a large number for dashboards.',
    'trimmed_mean': 'trimmed_mean(value): Aggregate giving the average of a column that is robust to extreme values.',
}

_FUNCS = [
    (tip_amount, 2), (late_fee, 2), (volume_price, 2), (luhn_flag, 1),
    (bday_age, 2), (due_date, 2), (shipping_cost, 2), (star_rating, 2),
    (mask_email, 1), (slugify, 1), (initials, 1), (risk_band, 1),
    (slots_needed, 2), (pct_change, 2), (parse_money, 1),
    (ean_check_digit, 1), (grade_letter, 2), (quarter_label, 1),
    (compact_num, 1),
]
SCALARS = {f.__name__: (_safe(f), n) for f, n in _FUNCS}
AGGREGATE = ('trimmed_mean', TrimmedMean)

TYPICAL = {
    'tip_amount': [(50, 20), (80.0, 15), (40, 10), (120, 18)],
    'late_fee': [(1000, 10), (400, 20), (2000, 8), (800, 12)],
    'volume_price': [(10, 5), (10, 20), (10, 60), (8, 2), (25, 100)],
    'luhn_flag': [('4111111111111111',), ('5500000000000004',), ('378282246310005',),
                  ('4111111111111112',), ('1234567812345678',)],
    'bday_age': [('1990-06-15', '2024-03-01'), ('2000-01-01', '2024-12-31'),
                 ('1985-11-30', '2020-02-02'), ('2010-08-08', '2024-08-08')],
    'due_date': [('2024-03-04', 3), ('2024-03-08', 1), ('2024-03-01', 10), ('2024-06-03', 5)],
    'shipping_cost': [(3, 1), (1, 2), (5, 3), (10, 2)],
    'star_rating': [(8, 2), (9, 1), (1, 9), (50, 50), (3, 7)],
    'mask_email': [('john.smith@acme.com',), ('Alice@mail.org',), ('bob@x.io',),
                   ('maria.garcia@company.co.uk',)],
    'slugify': [('Hello World',), ('Q3 Sales Report!',), ('  New   Product Launch  ',),
                ('Rock-n-Roll 101',)],
    'initials': [('John Smith',), ('ada lovelace',), ('Mary Ann Jones',),
                 ('Grace Brewster Murray Hopper',)],
    'risk_band': [(10,), (20,), (45,), (50,), (75,), (80,)],
    'slots_needed': [(60, 30), (90, 30), (45, 15), (120, 60), (100, 50)],
    'pct_change': [(100, 150), (200, 100), (80, 84), (50, 50), (40, 100)],
    'parse_money': [('$1,234.50',), ('12.99',), ('£ 500',), ('-45.10',), ('€2,000',)],
    'ean_check_digit': [('400638133393',), ('590123412345',), ('978020137962',), ('123456789012',)],
    'grade_letter': [(95, 100), (43, 50), (72, 100), (13, 20), (40, 100)],
    'quarter_label': [('2024-05-10',), ('2024-08-20',), ('2024-11-15',), ('2025-02-14',),
                      ('2024-03-20',), ('2024-06-30',)],
    'compact_num': [(1500,), (2300000,), (12000,), (450,), (7200000000,)],
}

EDGE = {
    'tip_amount': [(12.2, 12.5), (100, 45), (100, 30), (100, 0), (0, 20), (None, 20),
                   (50, None), (80, 29)],
    'late_fee': [(1000, 3), (1000, 4), (1000, 60), (100, 5), (557, 9), (0, 10),
                 (None, 10), (1000, None)],
    'volume_price': [(10, 9), (10, 10), (10, 49), (10, 50), (10, 499), (10, 500),
                     (0.99, 10), (None, 5)],
    'luhn_flag': [('79927398713',), (_lh('12345678901'),), (_lh('1' * 18),),
                  ('4111 1111 1111 1111',), ('4111-1111-1111-1111',), ('',),
                  ('4111x11111111111',), ('41111111111111 12',)],
    'bday_age': [('2000-02-29', '2023-02-28'), ('2000-02-29', '2023-03-01'),
                 ('2000-02-29', '2024-02-29'), ('2024-05-01', '2020-05-01'),
                 ('1925-01-01', '2024-01-01'), ('1924-01-01', '2024-01-01'),
                 ('2000-13-01', '2024-01-01'), ('1990-05-15', None)],
    'due_date': [('2024-12-23', 2), ('2024-12-31', 1), ('2024-03-09', 0), ('2024-03-10', 1),
                 ('2024-12-25', 0), ('2024-03-04', 0), ('2024-03-04', -1), ('2024-02-30', 1)],
    'shipping_cost': [(2.2, 1), (2.5, 1), (2, 1), (4, 0), (4, 7), (30, 1), (30.5, 1),
                      (0.4, 2), (None, 1)],
    'star_rating': [(1, 19), (0, 0), (4, 0), (0, 4), (1, 0), (2, 2), (5, 0), (0, 5), (None, 3)],
    'mask_email': [('a@b.com',), ('John@ACME.COM',), ('nodomain',), ('@x.com',), ('x@',),
                   ('ab@c.d',), ('',), (None,)],
    'slugify': [('Café Crème',), ('Tom & Jerry',), ('!!!',), ('',), ('a' * 39 + ' bcd',),
                ('x' * 60,), ('Hello   World --- Again',), ('Ünïcödé Tëst',)],
    'initials': [('Madonna',), ('X',), ('John Smith Jr.',), ('Martin Luther King III',),
                 ('   ',), ('',), ('  ada   lovelace ',), (None,)],
    'risk_band': [(34,), (35,), (64,), (65,), (85,), (34.5,), (100,), (-3,)],
    'slots_needed': [(61, 30), (65, 30), (66, 30), (3, 30), (0, 30), (60, 0), (60, -15),
                     (95, 15), (None, 30)],
    'pct_change': [(0, 5), (0, 0), (0, -3), (1, 100), (-50, -25), (400, 533), (400, 267),
                   (-100, -150), (-1, -100), (None, 5)],
    'parse_money': [('(250.00)',), ('12k',), ('1.5K',), ('$2.5k',), ('12,50',), ('1,234',),
                    ('abc',), ('',), ('-3.5k',), ('(1,200)',)],
    'ean_check_digit': [('7351353',), ('1234567',), ('4006381333931',), ('12345',),
                        ('abcdefghijkl',), ('',), ('000000000000',), ('12345678901234',),
                        ('73513a3',)],
    'grade_letter': [(98, 100), (97.9, 100), (90, 100), (80, 100), (70, 100), (60, 100),
                     (59, 100), (150, 100), (-5, 100), (50, 0)],
    'quarter_label': [('2024-04-01',), ('2024-04-03',), ('2024-04-04',), ('2025-01-01',),
                      ('2025-01-02',), ('2025-01-04',), ('2024-10-01',), ('2024-05-02',),
                      ('2024-02-30',), (None,)],
    'compact_num': [(1999,), (999999,), (450.7,), (1000,), (-1999,), (1050,), (0,),
                    (999.99,), (1000000000000,), (12345678,)],
}

AGG_TYPICAL = [
    [10, 20, 30, 40, 50],
    [1, 2, 3, 4, 100, 5],
    [100, 100, 100, 100, 100],
    [5, 7, 8, 6, 9, 100, 1],
]
AGG_EDGE = [
    [1, 2, 3],
    [1, 2, 3, 10],
    [1, 2, 3, 4, 5],
    ['10', '20', 5, 15, 25, 35, 45],
    [0, 0, 0.01, 0.01],
    [None, None, 4],
    [5, 5, 5, 5, 1, 100],
    ['a', 'b'],
]

DECISIONS = {
    'tip_amount': ['half-up rounding to cents', 'tip percentage capped at 30'],
    'late_fee': ['no fee for 3 days late or fewer', 'fee capped at 25% of amount',
                 'minimum fee 5.00 once a fee applies', 'half-up rounding to cents'],
    'volume_price': ['500+ units get a 25% discount tier', 'half-up rounding to cents'],
    'luhn_flag': ['spaces and dashes ignored', 'length outside 12-19 digits gives 0'],
    'bday_age': ['Feb 29 birthday counts on Mar 1 in non-leap years',
                 'as-of before birth gives 0', 'age capped at 99'],
    'due_date': ['Dec 25 and Jan 1 are not business days',
                 'zero days from a non-business day rolls forward'],
    'shipping_cost': ['weight billed in half-kg steps rounded up',
                      'unknown zone billed as zone 3', 'over 30 kg adds flat 25'],
    'star_rating': ['fewer than 5 votes blended toward 3 stars',
                    'half-up rounding to one decimal'],
    'mask_email': ['single-character local part shown as one star',
                   'domain lowercased', 'invalid address gives empty string'],
    'slugify': ['accents folded to base letters', '& becomes and',
                'max 40 chars, trailing hyphen trimmed', "empty result becomes 'n-a'"],
    'initials': ['generational suffixes ignored', 'single name gives first two letters',
                 'blank name gives ?'],
    'risk_band': ['CRITICAL from 85', 'band boundaries 35 and 65 inclusive',
                  'score rounded half-up before banding'],
    'slots_needed': ['5-minute overrun grace', 'non-positive slot length defaults to 30'],
    'pct_change': ['zero base gives 0 or +/-999.9', 'result capped at +/-999.9',
                   'negative base uses absolute value of old', 'half-up (away from zero) to one decimal'],
    'parse_money': ['parentheses mean negative', 'k suffix means thousands',
                    'comma followed by 1-2 digits is a decimal comma',
                    'unparseable text gives 0.0'],
    'ean_check_digit': ['7-digit input uses EAN-8 weights'],
    'grade_letter': ['98% and above is A+'],
    'quarter_label': ['first 3 days of a quarter belong to the previous quarter'],
    'compact_num': ['truncate rather than round to one decimal'],
    'trimmed_mean': ['trim one min and one max only with 5+ numeric values',
                     'text values ignored even if numeric-looking',
                     'half-up rounding to 2 decimals'],
}

DECISION_EXAMPLES = {
    'tip_amount': [(8.2, 12.5), (60, 50)],
    'late_fee': [(2000, 2), (400, 100), (60, 10), (131, 23)],
    'volume_price': [(4, 1000), (0.99, 30)],
    'luhn_flag': [('5500-0000 0000-0004',), (_lh('123456789'),)],
    'bday_age': [('1996-02-29', '2021-03-01'), ('2030-01-01', '2024-01-01'),
                 ('1800-01-01', '2024-06-01')],
    'due_date': [('2025-12-24', 1), ('2024-06-15', 0)],
    'shipping_cost': [(6.1, 3), (3, -1), (40, 2)],
    'star_rating': [(2, 1), (3, 17)],
    'mask_email': [('q@site.org',), ('tom@Example.ORG',), ('hello world',)],
    'slugify': [('Zürich Übung',), ('R&D Budget',),
                ('The quick brown fox jumps over the lazy dog again and again',), ('@#$',)],
    'initials': [('Anna Lee Sr',), ('Cher',), ('\t',)],
    'risk_band': [(92,), (35.4,), (64.5,)],
    'slots_needed': [(125, 60), (90, 0)],
    'pct_change': [(0, 7.5), (5, 1000), (-80, -20), (800, 1066)],
    'parse_money': [('($75.25)',), ('$4k',), ('99,99',), ('n/a',)],
    'ean_check_digit': [('9638507',)],
    'grade_letter': [(49.5, 50)],
    'quarter_label': [('2024-07-02',)],
    'compact_num': [(2999,)],
    'trimmed_mean': [[2, 4, 6, 100], [1, '50', 2, 3, '60', 4, 5], [0.03, 0.03, 0.02, 0.02]],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, n) in SCALARS.items():
        con.create_function(name, n, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con
