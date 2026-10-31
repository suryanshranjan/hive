import math
import re
import sqlite3
import unicodedata
import datetime
from fractions import Fraction


def _num(x):
    if x is None or isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        v = x
    elif isinstance(x, str):
        try:
            v = float(x.strip())
        except ValueError:
            return None
    else:
        return None
    if isinstance(v, float) and not math.isfinite(v):
        return None
    return v


def _fr(v):
    return Fraction(str(v))


# 1. late_fee --------------------------------------------------------------
def late_fee(balance, days_late):
    b, d = _num(balance), _num(days_late)
    if b is None or d is None:
        return None
    if b <= 0 or d <= 3:
        return 0.0
    B = _fr(b)
    weeks = math.ceil(_fr(d) / 7)
    fee = B * Fraction(3, 200) * weeks
    fee = max(fee, Fraction(5))
    fee = min(fee, B / 4)
    return math.floor(fee * 100) / 100


# 2. loyalty_tier ----------------------------------------------------------
def loyalty_tier(points):
    p = _num(points)
    if p is None:
        return None
    if p < 0:
        return 'Closed'
    if p < 1000:
        return 'Bronze'
    if p < 5000:
        return 'Silver'
    if p < 20000:
        return 'Gold'
    return 'Platinum'


# 3. mask_card -------------------------------------------------------------
def mask_card(number):
    if number is None:
        return None
    digits = re.sub(r'\D', '', str(number))
    if len(digits) <= 4:
        return '*' * len(digits)
    return '*' * (len(digits) - 4) + digits[-4:]


# 4. biz_days --------------------------------------------------------------
def _parse_date(s):
    if not isinstance(s, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', s.strip()):
        return None
    y, m, d = (int(t) for t in s.strip().split('-'))
    try:
        return datetime.date(y, m, d)
    except ValueError:
        return None


def biz_days(start, end):
    if start is None or end is None:
        return None
    a, b = _parse_date(start), _parse_date(end)
    if a is None or b is None:
        return -1
    if b < a:
        return 0
    n = 0
    one = datetime.timedelta(days=1)
    cur = a
    while cur < b:
        cur += one
        if cur.weekday() < 5 and (cur.month, cur.day) not in ((12, 25), (1, 1)):
            n += 1
    return n


# 5. split_bill ------------------------------------------------------------
def split_bill(total, people, tip_pct):
    t, p, tip = _num(total), _num(people), _num(tip_pct)
    if t is None or p is None or tip is None:
        return None
    if p <= 0:
        return None
    tip = min(_fr(tip), Fraction(30))
    per = _fr(t) * (1 + tip / 100) / _fr(p)
    return math.ceil(per * 100) / 100


# 6. review_stars ----------------------------------------------------------
def review_stars(avg, votes):
    a, n = _num(avg), _num(votes)
    if a is None or n is None:
        return None
    if n < 5:
        return 'n/a'
    A = min(max(_fr(a), Fraction(0)), Fraction(5))
    return math.floor(A * 2 + Fraction(1, 2)) / 2


# 7. make_slug -------------------------------------------------------------
def make_slug(text):
    if text is None:
        return None
    s = str(text).replace('&', ' and ')
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    s = s[:40].rstrip('-')
    return s if s else 'untitled'


# 8. overtime_pay ----------------------------------------------------------
def overtime_pay(hours, rate):
    h, r = _num(hours), _num(rate)
    if h is None or r is None:
        return None
    if h < 0:
        return 0.0
    H, R = _fr(h), _fr(r)
    pay = min(H, 40) * R
    if H > 40:
        pay += (min(H, 60) - 40) * R * Fraction(3, 2)
    if H > 60:
        pay += (H - 60) * R * 2
    return math.floor(pay * 100 + Fraction(1, 2)) / 100


# 9. norm_phone ------------------------------------------------------------
def norm_phone(text):
    if text is None:
        return None
    s = str(text)
    m = re.search(r'(?i)ext|x', s)
    if m:
        s = s[:m.start()]
    d = re.sub(r'\D', '', s)
    if len(d) == 10:
        return '+1' + d
    if len(d) == 11 and d[0] == '1':
        return '+' + d
    return 'INVALID'


# aggregate ----------------------------------------------------------------
class MidValue:
    def __init__(self):
        self.vals = []

    def step(self, value):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if isinstance(value, float) and not math.isfinite(value):
                return
            self.vals.append(value)

    def finalize(self):
        if not self.vals:
            return None
        v = sorted(self.vals)
        return v[(len(v) - 1) // 2]


SPEC = {
    'late_fee': 'late_fee(balance, days_late): Late-payment fee in dollars charged on an overdue invoice balance.',
    'loyalty_tier': 'loyalty_tier(points): Name of the customer loyalty tier for a points balance.',
    'mask_card': 'mask_card(number): Masks a payment card number for display on receipts and support screens.',
    'biz_days': "biz_days(start, end): Number of business days elapsed between two 'YYYY-MM-DD' dates, for delivery estimates.",
    'split_bill': 'split_bill(total, people, tip_pct): Amount each person pays when a restaurant bill plus tip is shared equally.',
    'review_stars': 'review_stars(avg, votes): Star rating shown in the storefront for an average review score and its vote count.',
    'make_slug': 'make_slug(text): Turns a product or article title into a URL slug.',
    'overtime_pay': 'overtime_pay(hours, rate): Gross weekly pay in dollars for hours worked at an hourly rate, including overtime.',
    'norm_phone': 'norm_phone(text): Normalizes a free-form phone number into a canonical dialable form.',
    'mid_value': 'mid_value(x): Aggregate giving the typical (median) value of a column of numbers.',
}

SCALARS = {
    'late_fee': (late_fee, 2),
    'loyalty_tier': (loyalty_tier, 1),
    'mask_card': (mask_card, 1),
    'biz_days': (biz_days, 2),
    'split_bill': (split_bill, 3),
    'review_stars': (review_stars, 2),
    'make_slug': (make_slug, 1),
    'overtime_pay': (overtime_pay, 2),
    'norm_phone': (norm_phone, 1),
}

AGGREGATE = ('mid_value', MidValue)

TYPICAL = {
    'late_fee': [(200, 10), (1000, 8), (500, 30), (400, 14), (800, 21)],
    'loyalty_tier': [(250,), (2500,), (12000,), (50000,)],
    'mask_card': [('4111111111111111',), ('378282246310005',), ('5500000000000004',), ('6011111111111117',)],
    'biz_days': [('2024-05-06', '2024-05-10'), ('2024-05-03', '2024-05-06'),
                 ('2024-06-03', '2024-06-17'), ('2024-03-01', '2024-03-08')],
    'split_bill': [(100, 4, 20), (60, 3, 15), (90, 2, 10), (200, 5, 0), (120, 6, 25)],
    'review_stars': [(4.6, 120), (3.9, 50), (4.8, 10), (2.2, 30), (3.6, 8)],
    'make_slug': [('Hello World',), ('Q3 Sales Report!',), ('  Spring  Sale 2024 ',), ('New-Arrivals: Shoes',)],
    'overtime_pay': [(40, 20), (45, 20), (50, 18.5), (30, 15), (44, 25)],
    'norm_phone': [('(415) 555-2671',), ('415-555-2671',), ('1-415-555-2671',), ('+1 415 555 2671',), ('4155552671',)],
}

EDGE = {
    'late_fee': [(200, 3), (200, 4), (100, 0), (-50, 20), (10, 10), (100, 400),
                 (50, 5), (333.33, 8), (None, 5)],
    'loyalty_tier': [(-1,), (0,), (999,), (1000,), (4999.5,), (5000,), (20000,), (None,), ('3000',)],
    'mask_card': [('4111 1111 1111 1111',), ('4111-1111-1111-1111',), ('1234',), ('123',), ('12345',),
                  ('',), ('abcd',), (None,), (4111111111111111,), ('ab12cd345678',)],
    'biz_days': [('2024-03-08', '2024-03-04'), ('2024-02-30', '2024-03-04'), ('hello', '2024-03-04'),
                 ('2024-12-20', '2024-12-27'), ('2023-12-29', '2024-01-02'), ('2024-03-04', None),
                 ('2024-03-04', '2024-03-04'), ('2024-03-09', '2024-03-10'), ('2022-12-23', '2022-12-27')],
    'split_bill': [(100, 3, 0), (100, 0, 10), (100, -2, 10), (100, 2, 50), (100, 2, 30),
                   (50, None, 10), (0, 3, 10), (100, 3, 10), (10, 3, 0)],
    'review_stars': [(4.5, 4), (4.5, 5), (4.25, 100), (4.75, 100), (3.25, 100), (6.2, 100),
                     (-1, 100), (None, 10), (4.0, None)],
    'make_slug': [('Café Müller',), ('Salt & Pepper',), ('Tom&Jerry',), ('!!!',), ('',),
                  ('The quick brown fox jumps over the lazy dog again and again',), ('Résumé',), (None,)],
    'overtime_pay': [(60, 20), (61, 20), (70, 20), (-5, 20), (0, 20), (40.5, 20), (None, 20), (100, 15.5)],
    'norm_phone': [('415-555-2671 x123',), ('415 555 2671 ext. 45',), ('555-2671',), ('',),
                   ('2-415-555-2671',), ('+44 20 7946 0958',), (None,), ('call me',), (4155552671,)],
}

AGG_TYPICAL = [[1, 3, 2], [5, 1, 9, 7, 3], [10.5, 20.5, 30.5]]
AGG_EDGE = [[], [None, None], [4, 1], [1, 2, 3, 4], [7], [1, None, 3], ['a', 5, 3], [2.5, 1, 2.5, 9]]

DECISIONS = {
    'late_fee': ['grace period of 3 days', 'fee capped at 25% of balance', 'minimum fee of 5.00',
                 'result floored to whole cents'],
    'loyalty_tier': ['negative points give Closed'],
    'mask_card': ['separators dropped from output', 'numbers of 4 or fewer digits fully masked'],
    'biz_days': ['reversed range gives 0', 'invalid date gives -1', 'Dec 25 and Jan 1 are not business days'],
    'split_bill': ['per-person share rounded up to the cent', 'people <= 0 gives NULL', 'tip capped at 30%'],
    'review_stars': ['fewer than 5 votes gives n/a', 'ties round half up to the next half star',
                     'average clamped to 0..5'],
    'make_slug': ['& becomes and', 'accents transliterated', 'truncated to 40 chars without trailing hyphen',
                  'empty result becomes untitled'],
    'overtime_pay': ['double time beyond 60 hours', 'negative hours pay 0'],
    'norm_phone': ['extension dropped', 'unusable numbers give INVALID'],
    'mid_value': ['even count returns the lower middle value'],
}

DECISION_EXAMPLES = {
    'late_fee': [(300, 2), (100, 200), (60, 6), (1234.57, 8)],
    'loyalty_tier': [(-250,)],
    'mask_card': [('5500 0000 0000 0004',), ('0042',)],
    'biz_days': [('2024-05-10', '2024-05-06'), ('2024-13-01', '2024-05-06'), ('2025-12-22', '2025-12-26')],
    'split_bill': [(70, 3, 0), (80, 0, 5), (200, 4, 45)],
    'review_stars': [(4.0, 3), (2.75, 40), (7.5, 60)],
    'make_slug': [('Crème Brûlée Recipe',), ('Fish & Chips',),
                  ('Annual Report for Fiscal Year Twenty Twenty Four Final',), ('***',)],
    'overtime_pay': [(65, 22), (-12, 30)],
    'norm_phone': [('(212) 555-0147 x9',), ('12345',)],
    'mid_value': [[10, 20, 30, 40, 50, 60]],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, n) in SCALARS.items():
        con.create_function(name, n, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con
