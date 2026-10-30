import math
import re
import sqlite3
import unicodedata
from datetime import date, timedelta
from fractions import Fraction


def _num(x):
    """Parse an SQL value to int/float, or None if missing or not numeric."""
    if x is None:
        return None
    if isinstance(x, (int, float)):
        if isinstance(x, float) and not math.isfinite(x):
            return None
        return x
    if isinstance(x, str):
        t = x.strip()
        try:
            return int(t)
        except ValueError:
            pass
        try:
            v = float(t)
        except ValueError:
            return None
        return v if math.isfinite(v) else None
    return None


def _frac(x):
    return Fraction(x) if isinstance(x, int) else Fraction(repr(x))


# ---------------------------------------------------------------- late_fee
def late_fee(amount_cents, days_late):
    a, d = _num(amount_cents), _num(days_late)
    if amount_cents is None or days_late is None or a is None or d is None:
        return None
    d = math.floor(d)
    if a <= 0 or d <= 5:
        return 0
    fee = math.floor(_frac(a) * d * 5 / 1000)
    fee = max(fee, 500)
    cap = math.floor(_frac(a) * 20 / 100)
    return int(min(fee, cap))


# ---------------------------------------------------------------- fmt_phone
_EXT = re.compile(r'\s*(?:ext\.?|extension|x|#)\s*(\d+)\s*$', re.I)


def fmt_phone(text):
    if text is None:
        return None
    s = str(text)
    ext = ''
    m = _EXT.search(s)
    if m:
        ext = ' x' + m.group(1)
        s = s[:m.start()]
    digits = re.sub(r'\D', '', s)
    if len(digits) == 11 and digits[0] == '1':
        digits = digits[1:]
    if len(digits) != 10:
        return ''
    return '(%s) %s-%s%s' % (digits[:3], digits[3:6], digits[6:], ext)


# ---------------------------------------------------------------- grade_letter
def grade_letter(score):
    s = _num(score)
    if score is None or s is None:
        return None
    if s < 0 or s > 100:
        return 'X'
    if s >= 92:
        return 'A'
    if s >= 83:
        return 'B'
    if s >= 71:
        return 'C'
    if s >= 60:
        return 'D'
    return 'F'


# ---------------------------------------------------------------- biz_days_between
_ISO = re.compile(r'^\s*(\d{4})-(\d{2})-(\d{2})\s*$')


def _parse_date(x):
    if not isinstance(x, str):
        return None
    m = _ISO.match(x)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def biz_days_between(start_date, end_date):
    if start_date is None or end_date is None:
        return None
    a, b = _parse_date(start_date), _parse_date(end_date)
    if a is None or b is None:
        return -1
    if b <= a:
        return 0
    n = (b - a).days
    count = n // 7 * 5
    for i in range(n % 7):
        if (a + timedelta(days=n // 7 * 7 + i)).weekday() < 5:
            count += 1
    for y in range(a.year, b.year + 1):
        for mo, dy in ((1, 1), (12, 25)):
            h = date(y, mo, dy)
            if a <= h < b and h.weekday() < 5:
                count -= 1
    return count


# ---------------------------------------------------------------- shipping_cost
def shipping_cost(weight_g, zone):
    if weight_g is None or zone is None:
        return None
    w = _num(weight_g)
    if w is None or w < 0:
        return None
    if w > 30000:
        return 9999
    z = _num(zone)
    if z is None or z != int(z) or not 1 <= z <= 3:
        z = 3
    return int(z) * (300 + 100 * math.ceil(w / 1000))


# ---------------------------------------------------------------- mask_card
def mask_card(number):
    if number is None:
        return None
    s = str(number).strip()
    if re.search(r'[^0-9 \-]', s):
        return 'INVALID'
    digits = re.sub(r'\D', '', s)
    if not 13 <= len(digits) <= 19:
        return 'INVALID'
    keep = 5 if len(digits) == 15 and digits[:2] in ('34', '37') else 4
    total = len(digits)
    out, seen = [], 0
    for ch in s:
        if ch.isdigit():
            out.append(ch if seen >= total - keep else '*')
            seen += 1
        else:
            out.append(ch)
    return ''.join(out)


# ---------------------------------------------------------------- slugify
def slugify(text):
    if text is None:
        return None
    s = str(text)
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    s = s.lower().replace('&', ' and ').replace("'", '')
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    s = s[:30].rstrip('-')
    return s or 'untitled'


# ---------------------------------------------------------------- tiered_price
def tiered_price(unit_cents, qty):
    u, q = _num(unit_cents), _num(qty)
    if unit_cents is None or qty is None or u is None or q is None:
        return None
    if q <= 0:
        return 0
    pct = 20 if q >= 50 else 10 if q >= 10 else 0
    total = _frac(u) * _frac(q) * (100 - pct) / 100
    return int(math.floor(total / 5 + Fraction(1, 2)) * 5)


# ---------------------------------------------------------------- weighted_rating
def weighted_rating(avg_rating, votes):
    a, v = _num(avg_rating), _num(votes)
    if avg_rating is None or votes is None or a is None or v is None:
        return None
    if v < 5:
        return None
    return float(round((a * v + 3.0 * 10) / (v + 10), 2))


# ---------------------------------------------------------------- aggregate
class GrossReceipts:
    def __init__(self):
        self.total = 0
        self.n = 0

    def step(self, value):
        v = _num(value)
        if v is None or v < 0:
            return
        self.total += v
        self.n += 1

    def finalize(self):
        return self.total if self.n else None


SPEC = {
    'late_fee': 'late_fee(amount_cents, days_late): penalty in cents charged on an overdue invoice of the given amount.',
    'fmt_phone': 'fmt_phone(text): normalizes a free-form North American phone number into a standard display format.',
    'grade_letter': 'grade_letter(score): converts a numeric course score into the letter grade shown on report cards.',
    'biz_days_between': 'biz_days_between(start_date, end_date): number of working days between two ISO dates (YYYY-MM-DD).',
    'shipping_cost': 'shipping_cost(weight_g, zone): shipping charge in cents for a parcel of the given weight to a delivery zone.',
    'mask_card': 'mask_card(number): hides a payment card number for display on receipts and screens.',
    'slugify': 'slugify(text): turns a title into a URL-friendly slug.',
    'tiered_price': 'tiered_price(unit_cents, qty): total order price in cents for a quantity, with volume discounts.',
    'weighted_rating': 'weighted_rating(avg_rating, votes): customer rating adjusted for how many votes it is based on.',
    'gross_receipts': 'gross_receipts(amount): total of payment amounts received in a group of rows.',
}

SCALARS = {
    'late_fee': (late_fee, 2),
    'fmt_phone': (fmt_phone, 1),
    'grade_letter': (grade_letter, 1),
    'biz_days_between': (biz_days_between, 2),
    'shipping_cost': (shipping_cost, 2),
    'mask_card': (mask_card, 1),
    'slugify': (slugify, 1),
    'tiered_price': (tiered_price, 2),
    'weighted_rating': (weighted_rating, 2),
}

AGGREGATE = ('gross_receipts', GrossReceipts)

TYPICAL = {
    'late_fee': [(200000, 10), (100000, 20), (400000, 12), (150000, 30), (80000, 15)],
    'fmt_phone': [('555-123-4567',), ('(555) 123 4567',), ('5551234567',), ('555.123.4567',)],
    'grade_letter': [(97,), (88,), (77,), (65,), (30,)],
    'biz_days_between': [('2024-03-04', '2024-03-11'), ('2024-05-06', '2024-05-10'),
                         ('2024-06-03', '2024-06-17'), ('2024-02-05', '2024-02-06'),
                         ('2024-07-10', '2024-08-10')],
    'shipping_cost': [(500, 1), (1500, 2), (2500, 3), (800, 2), (4000, 1), (12000, 3)],
    'mask_card': [('4111111111111111',), ('5500005555555559',), ('4012888888881881',),
                  ('6011000990139424',)],
    'slugify': [('Hello World',), ('Quarterly Sales Report 2024',), ('  Trim   me!  ',),
                ('Hello, World!',), ('Q3 Results (Final)',)],
    'tiered_price': [(1000, 12), (2500, 60), (1200, 5), (500, 10), (4000, 50), (800, 3)],
    'weighted_rating': [(5, 10), (4, 30), (2, 10), (4.6, 40), (3.5, 100)],
}

EDGE = {
    'late_fee': [(100000, 5), (100000, 6), (1000, 10), (50000, 100), (5000, 8),
                 (99999, 11), (0, 10), (-5000, 10), (None, 10), (100000, -3)],
    'fmt_phone': [('1-555-123-4567',), ('+1 (555) 123-4567',), ('555-123-4567 x89',),
                  ('555-123-4567 ext. 1234',), ('12345',), ('',), ('555-123-456789012',),
                  ('2-555-123-4567',), (None,), ('555-123-4567 x',)],
    'grade_letter': [(92,), (91.99,), (83,), (71,), (60,), (59.9,), (100,), (0,), (101,), (-1,)],
    'biz_days_between': [('2024-12-23', '2024-12-27'), ('2023-12-29', '2024-01-03'),
                         ('2024-03-11', '2024-03-04'), ('2024-02-30', '2024-03-04'),
                         ('hello', '2024-01-01'), ('2024-03-04', '2024-03-04'),
                         (None, '2024-03-04'), ('2024-12-25', '2024-12-26'),
                         ('2024-03-04T10:00', '2024-03-08'), ('2024-03-09', '2024-03-10')],
    'shipping_cost': [(30000, 1), (30001, 1), (0, 1), (500, 0), (500, 4), (2000, 'B'),
                      (-5, 1), (1000.5, 2), (None, 1)],
    'mask_card': [('4111 1111 1111 1111',), ('4111-1111-1111-1111',), ('378282246310005',),
                  ('371449635398431',), ('411111111111',), ('41111111111111111111',),
                  ('4111 1111 1111 111x',), ('',), (None,), ('4111111111111',)],
    'slugify': [('Tom & Jerry',), ("Don't Stop",),
                ('A very long title that keeps going and going on',),
                ('abcdefghijklmnopqrstuvwxyzabc def',), ('!!!',), ('',), (None,), ('   ',),
                ('CAFÉ au lait',)],
    'tiered_price': [(999, 3), (999, 12), (1002, 1), (1000, 0), (1000, -3), (1000, 49),
                     (1000, 50), (1000, 9), (1000, 10), (5, 0.5)],
    'weighted_rating': [(4.5, 4), (4.5, 5), (5, 0), (5, -3), (1, 1000), (3, 10), (5, 5),
                        (4.2, 7)],
}

AGG_TYPICAL = [[100, 250, 50], [19.5, 20.5], [5], [1000, 2000, 3000, 4000]]
AGG_EDGE = [[], [None, None], [100, None, 50], [100, -30, 20], [-5], [0, 0],
            ['abc', 7, '12']]

DECISIONS = {
    'late_fee': ['grace period of 5 days charges nothing', 'minimum fee of 500 cents once charged',
                 'fee capped at 20% of the amount', 'fee rounded down to whole cents'],
    'fmt_phone': ['leading country code 1 stripped', 'extension kept as " x<digits>"',
                  'wrong digit count returns empty string'],
    'grade_letter': ['cutoffs are A 92, B 83, C 71, D 60', 'scores outside 0-100 give X'],
    'biz_days_between': ['Jan 1 and Dec 25 are not working days', 'reversed range returns 0',
                         'invalid date text returns -1'],
    'shipping_cost': ['over 30000 g is flat 9999 regardless of zone',
                      'zone outside 1..3 or non-integer is billed as zone 3'],
    'mask_card': ['separators are kept in place', 'digit count outside 13-19 gives INVALID',
                  '15-digit 34/37 cards keep last 5 digits'],
    'slugify': ['ampersand becomes "and"', 'apostrophes removed rather than splitting',
                'truncated to 30 chars then trailing hyphen trimmed', 'empty result is "untitled"'],
    'tiered_price': ['total rounded half up to nearest 5 cents', 'qty <= 0 gives 0'],
    'weighted_rating': ['fewer than 5 votes gives NULL'],
    'gross_receipts': ['negative amounts (refunds) are skipped'],
}

DECISION_EXAMPLES = {
    'late_fee': [(250000, 2), (6000, 10), (30000, 90), (12345, 17)],
    'fmt_phone': [('1 (800) 555-0199',), ('212 555 0147 x302',), ('555-12',)],
    'grade_letter': [(70.9,), (250,)],
    'biz_days_between': [('2025-12-24', '2025-12-29'), ('2024-08-20', '2024-08-05'),
                         ('2024-13-01', '2024-12-01')],
    'shipping_cost': [(45000, 2), (3200, 7)],
    'mask_card': [('5500 0000 0000 0004',), ('123456789',), ('341111111111111',)],
    'slugify': [('AT&T Wireless',), ("It's Friday",),
                ('The quick brown fox jumps over the lazy dog',), ('--- ***',)],
    'tiered_price': [(1234, 7), (500, -8)],
    'weighted_rating': [(4.8, 3)],
    'gross_receipts': [[40, -5, -10, 15]],
}


def connect():
    conn = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, n) in SCALARS.items():
        conn.create_function(name, n, fn, deterministic=True)
    conn.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return conn
