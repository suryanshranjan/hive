"""Company policy for 20 business SQL functions (19 scalars, 1 aggregate)."""
import datetime
import math
import re
import sqlite3
import unicodedata
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR

# ---------------------------------------------------------------- helpers

def _num(x):
    if x is None or isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        v = float(x)
    elif isinstance(x, str):
        try:
            v = float(x.strip())
        except ValueError:
            return None
    else:
        return None
    if math.isnan(v) or math.isinf(v):
        return None
    return v


def _dec(x):
    return Decimal(repr(x)) if isinstance(x, float) else Decimal(str(x))


def _cents(d):
    return float(Decimal(d).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def _date(x):
    if not isinstance(x, str):
        return None
    s = x.strip()
    if len(s) > 10 and s[10] in ' T':
        s = s[:10]
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', s):
        return None
    try:
        return datetime.date(int(s[:4]), int(s[5:7]), int(s[8:10]))
    except ValueError:
        return None


# ---------------------------------------------------------------- scalars

def invoice_total(subtotal, tax_rate_pct, discount_pct):
    s = _num(subtotal)
    if s is None:
        return None
    if s < 0:
        return 0.0
    t = _num(tax_rate_pct)
    if t is None:
        t = 8.0
    d = _num(discount_pct)
    if d is None or d < 0:
        d = 0.0
    d = min(d, 50.0)
    total = _dec(s) * (1 - _dec(d) / 100) * (1 + _dec(t) / 100)
    return _cents(total)


def late_fee(days_late, amount):
    a = _num(amount)
    if a is None:
        return None
    d = _num(days_late)
    if d is None or a <= 0:
        return 0.0
    days = math.floor(d)
    if days <= 3:
        return 0.0
    fee = _dec(a) * days / 100
    fee = min(fee, _dec(a) / 4)
    fee = max(fee, Decimal(5))
    return _cents(fee)


def fiscal_quarter(date_text):
    if date_text is None:
        return None
    d = _date(date_text)
    if d is None:
        return 'INVALID'
    if d.month == 1:
        return 'FY%d-Q4' % (d.year - 1)
    return 'FY%d-Q%d' % (d.year, (d.month - 2) // 3 + 1)


def _is_bday(d):
    return d.weekday() < 5 and (d.month, d.day) not in ((12, 25), (1, 1))


def business_days_between(start_date, end_date):
    a, b = _date(start_date), _date(end_date)
    if a is None or b is None:
        return None
    sign = 1
    if b < a:
        a, b, sign = b, a, -1
    n = 0
    d = a + datetime.timedelta(days=1)
    while d <= b:
        if _is_bday(d):
            n += 1
        d += datetime.timedelta(days=1)
    return sign * n


def normalize_phone(text):
    if not isinstance(text, str):
        return None
    s = re.sub(r'(?i)\s*(x|ext\.?)\s*\d+\s*$', '', text.strip())
    digits = re.sub(r'\D', '', s)
    if s.startswith('+'):
        return '+' + digits if 8 <= len(digits) <= 15 else None
    if len(digits) == 11 and digits[0] == '1':
        digits = digits[1:]
    if len(digits) != 10 or digits[0] in '01':
        return None
    return '+1' + digits


def mask_card(text):
    if text is None:
        return None
    s = re.sub(r'[ \-]', '', str(text).strip())
    if not s or not s.isdigit() or not s.isascii():
        return None
    if len(s) < 13:
        return '****'
    return '*' * (len(s) - 4) + s[-4:]


def slugify_title(text):
    if text is None:
        return None
    s = unicodedata.normalize('NFKD', str(text))
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace('&', ' and ').replace("'", '')
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    if len(s) > 40:
        cut = s[:41]
        if cut.endswith('-'):
            s = cut[:-1]
        elif '-' in s[:40]:
            s = s[:40].rsplit('-', 1)[0]
        else:
            s = s[:40]
    return s or 'untitled'


def loyalty_tier(points):
    p = _num(points)
    if p is None:
        return None
    p = math.floor(p)
    if p < 0:
        return 'Suspended'
    if p >= 20000:
        return 'Platinum'
    if p >= 5000:
        return 'Gold'
    if p >= 1000:
        return 'Silver'
    return 'Bronze'


def shipping_cost(weight_kg, zone):
    w, z = _num(weight_kg), _num(zone)
    if w is None or z is None or w <= 0:
        return None
    if z not in (1.0, 2.0, 3.0):
        return None
    base = {1: 5.0, 2: 8.0, 3: 12.0}[int(z)]
    cost = base + 1.5 * math.ceil(w)
    if w > 30:
        cost += 25.0
    return _cents(_dec(cost))


def age_band(birth_date, as_of_date):
    b, t = _date(birth_date), _date(as_of_date)
    if b is None or t is None or t < b:
        return None
    age = t.year - b.year - ((t.month, t.day) < (b.month, b.day))
    if age < 18:
        return 'MINOR'
    if age >= 65:
        return '65+'
    for lo, hi in ((18, 24), (25, 34), (35, 44), (45, 54), (55, 64)):
        if lo <= age <= hi:
            return '%d-%d' % (lo, hi)


_SUFFIXES = {'jr', 'jr.', 'sr', 'sr.', 'ii', 'iii', 'iv', 'phd', 'md'}
_PARTICLES = {'van', 'von', 'de', 'da', 'di', 'del', 'der', 'la', 'le', 'du', 'ter', 'den'}


def surname_of(full_name):
    if not isinstance(full_name, str):
        return None
    s = full_name.strip()
    if ',' in s:
        head = s.split(',', 1)[0].strip()
        tail = s.split(',', 1)[1].strip().lower().rstrip('.')
        if head and tail not in {x.rstrip('.') for x in _SUFFIXES}:
            return ' '.join(head.split())
        s = head if head else s.replace(',', ' ')
    toks = [t.strip(',') for t in s.split()]
    toks = [t for t in toks if t]
    while len(toks) > 1 and toks[-1].lower() in _SUFFIXES:
        toks.pop()
    if not toks:
        return None
    i = len(toks) - 1
    while i > 1 and toks[i - 1].lower() in _PARTICLES:
        i -= 1
    return ' '.join(toks[i:])


_GRADES = [(93, 'A'), (90, 'A-'), (87, 'B+'), (83, 'B'), (80, 'B-'), (77, 'C+'),
           (73, 'C'), (70, 'C-'), (67, 'D+'), (63, 'D'), (60, 'D-')]


def letter_grade(score):
    s = _num(score)
    if s is None:
        return None
    if s < 0 or s > 100:
        return 'INVALID'
    r = int(_dec(s).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    for lo, g in _GRADES:
        if r >= lo:
            return g
    return 'F'


def sku_normalize(text):
    if not isinstance(text, str):
        return None
    s = re.sub(r'[\s\-_]', '', text).upper()
    if len(s) < 4 or not re.fullmatch(r'[A-Z]{3}', s[:3]):
        return None
    rest = s[3:].replace('O', '0')
    if not re.fullmatch(r'[0-9]{1,5}', rest):
        return None
    return s[:3] + '-' + rest.zfill(5)


def meeting_end(start_time, duration_min):
    if not isinstance(start_time, str):
        return None
    m = re.fullmatch(r'(\d{1,2}):(\d{2})', start_time.strip())
    if not m or int(m.group(1)) > 23 or int(m.group(2)) > 59:
        return None
    start = int(m.group(1)) * 60 + int(m.group(2))
    d = _num(duration_min)
    if d is None:
        return None
    dur = 0 if d <= 0 else math.ceil(d / 15) * 15
    end = start + dur
    days, mins = divmod(end, 1440)
    out = '%02d:%02d' % divmod(mins, 60)
    return out + ('+%d' % days if days else '')


_CURRENCIES = {'USD': ('$', 2), 'EUR': ('€', 2), 'GBP': ('£', 2), 'JPY': ('¥', 0)}


def format_money(amount, currency_code):
    a = _num(amount)
    if a is None:
        return None
    code = 'USD' if currency_code is None else str(currency_code).strip().upper()
    sym, places = _CURRENCIES.get(code, (code + ' ', 2))
    q = Decimal(1) if places == 0 else Decimal('0.01')
    v = _dec(a).quantize(q, rounding=ROUND_HALF_UP)
    neg = v < 0
    body = sym + format(abs(v), ',.%df' % places)
    return '(' + body + ')' if neg else body


_DOMAIN_ALIASES = {'googlemail.com': 'gmail.com'}


def email_domain(email):
    if not isinstance(email, str):
        return None
    s = email.strip()
    if s.count('@') != 1:
        return None
    local, dom = s.split('@')
    dom = dom.lower().rstrip('.')
    if not local or '.' not in dom or any(not p for p in dom.split('.')):
        return None
    if not re.fullmatch(r'[a-z0-9.\-]+', dom):
        return None
    return _DOMAIN_ALIASES.get(dom, dom)


def prorate_charge(monthly_price, start_day, days_in_month):
    p, s, n = _num(monthly_price), _num(start_day), _num(days_in_month)
    if p is None or s is None or n is None:
        return None
    if n not in (28.0, 29.0, 30.0, 31.0) or s != math.floor(s) or not 1 <= s <= n:
        return None
    s, n = int(s), int(n)
    if p <= 0:
        return 0.0
    if s == 1:
        return _cents(_dec(p))
    if s >= n - 2:
        return 0.0
    v = _dec(p) * (n - s + 1) / n
    return float(v.quantize(Decimal('0.01'), rounding=ROUND_FLOOR))


def overtime_pay(hours, rate):
    h, r = _num(hours), _num(rate)
    if h is None or r is None or r < 0:
        return None
    if h <= 0:
        return 0.0
    h = (_dec(h) * 4).quantize(Decimal('1'), rounding=ROUND_HALF_UP) / 4
    R = _dec(r)
    pay = (R * min(h, 40)
           + R * Decimal('1.5') * max(Decimal(0), min(h, 60) - 40)
           + R * 2 * max(Decimal(0), h - 60))
    return _cents(pay)


def name_initials(full_name):
    if not isinstance(full_name, str):
        return None
    parts = []
    for tok in full_name.split():
        if tok.islower() and tok in _PARTICLES:
            continue
        for piece in tok.split('-'):
            letters = [c for c in piece if c.isalpha()]
            if letters:
                parts.append(letters[0].upper())
    if not parts:
        return None
    if len(parts) > 3:
        parts = parts[:2] + parts[-1:]
    return ''.join(parts)


# ---------------------------------------------------------------- aggregate

class review_score:
    def __init__(self):
        self.vals = []

    def step(self, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return
        if isinstance(value, float) and math.isnan(value):
            return
        if 1 <= value <= 5:
            self.vals.append(_dec(value))

    def finalize(self):
        if len(self.vals) < 3:
            return None
        avg = sum(self.vals) / len(self.vals)
        return float(avg.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))


# ---------------------------------------------------------------- registry

SPEC = {
    'invoice_total': 'invoice_total(subtotal, tax_rate_pct, discount_pct): final amount due on an invoice after applying a percentage discount and sales tax, in currency units with cents.',
    'late_fee': 'late_fee(days_late, amount): fee charged on an overdue invoice amount, at 1% of the amount per day late.',
    'fiscal_quarter': "fiscal_quarter(date_text): the company fiscal year and quarter label (e.g. 'FY2026-Q2') for a 'YYYY-MM-DD' date.",
    'business_days_between': "business_days_between(start_date, end_date): number of company working days from start_date to end_date ('YYYY-MM-DD'), used for SLA tracking.",
    'normalize_phone': 'normalize_phone(text): normalizes a customer-entered phone number to E.164 format for the CRM.',
    'mask_card': 'mask_card(text): masks a payment card number for display on receipts, keeping only the last four digits visible.',
    'slugify_title': 'slugify_title(text): turns an article or product title into a URL slug for the website.',
    'loyalty_tier': 'loyalty_tier(points): the loyalty program tier name (Bronze, Silver, Gold, Platinum) for a customer point balance.',
    'shipping_cost': 'shipping_cost(weight_kg, zone): shipping charge for a parcel: a per-zone base fee plus 1.50 per kg, for delivery zones 1 to 3.',
    'age_band': "age_band(birth_date, as_of_date): marketing age band (e.g. '25-34') of a customer on a given date, both 'YYYY-MM-DD'.",
    'surname_of': 'surname_of(full_name): extracts the family name from a customer full name for formal salutations.',
    'letter_grade': 'letter_grade(score): converts a 0-100 training assessment score into the letter grade shown on employee certificates.',
    'sku_normalize': "sku_normalize(text): normalizes a product SKU typed by staff into the canonical 'ABC-12345' form.",
    'meeting_end': "meeting_end(start_time, duration_min): end time ('HH:MM') of a room booking that starts at start_time and lasts duration_min minutes.",
    'format_money': 'format_money(amount, currency_code): formats an amount for display in invoices and emails with the currency symbol and thousands separators.',
    'email_domain': 'email_domain(email): the domain part of a customer email address, used to group accounts by organisation.',
    'prorate_charge': 'prorate_charge(monthly_price, start_day, days_in_month): first-month subscription charge for a customer who starts on start_day, pro-rated by the days remaining in the month.',
    'overtime_pay': 'overtime_pay(hours, rate): weekly gross pay for hourly staff given hours worked and hourly rate, with time-and-a-half over 40 hours.',
    'name_initials': 'name_initials(full_name): uppercase initials of a person name, shown in avatars and document sign-offs.',
    'review_score': 'review_score(rating): aggregate; the published average star rating (1 to 5) of a product from its customer reviews.',
}

SCALARS = {
    'invoice_total': (invoice_total, 3),
    'late_fee': (late_fee, 2),
    'fiscal_quarter': (fiscal_quarter, 1),
    'business_days_between': (business_days_between, 2),
    'normalize_phone': (normalize_phone, 1),
    'mask_card': (mask_card, 1),
    'slugify_title': (slugify_title, 1),
    'loyalty_tier': (loyalty_tier, 1),
    'shipping_cost': (shipping_cost, 2),
    'age_band': (age_band, 2),
    'surname_of': (surname_of, 1),
    'letter_grade': (letter_grade, 1),
    'sku_normalize': (sku_normalize, 1),
    'meeting_end': (meeting_end, 2),
    'format_money': (format_money, 2),
    'email_domain': (email_domain, 1),
    'prorate_charge': (prorate_charge, 3),
    'overtime_pay': (overtime_pay, 2),
    'name_initials': (name_initials, 1),
}

AGGREGATE = ('review_score', review_score)

TYPICAL = {
    'invoice_total': [(100.0, 10, 0), (200.0, 5, 10), (50.0, 0, 20), (80.0, 25, 0)],
    'late_fee': [(10, 1000.0), (20, 500.0), (5, 2000.0), (15, 800.0)],
    'fiscal_quarter': [('2026-03-15',), ('2026-06-10',), ('2026-09-01',), ('2026-12-05',)],
    'business_days_between': [('2026-03-02', '2026-03-06'), ('2026-03-02', '2026-03-09'),
                              ('2026-06-01', '2026-06-12'), ('2026-09-07', '2026-09-30')],
    'normalize_phone': [('(415) 555-0123',), ('415-555-0199',), ('415.555.0142',), ('4155550100',)],
    'mask_card': [('4111111111111111',), ('5500000000000004',), ('6011000990139424',), ('4012888888881881',)],
    'slugify_title': [('Hello World',), ('Quarterly Sales Report 2026',), ('New Product Launch',), ('Summer Sale',)],
    'loyalty_tier': [(100,), (2500,), (8000,), (50000,)],
    'shipping_cost': [(2, 1), (4, 2), (10, 3), (1, 1)],
    'age_band': [('1990-05-10', '2026-10-27'), ('2000-01-15', '2026-10-27'),
                 ('1970-03-03', '2026-10-27'), ('2005-06-01', '2026-10-27')],
    'surname_of': [('John Smith',), ('Mary Ann Lee',), ('Robert Brown',), ('Alice Walker',)],
    'letter_grade': [(95,), (85,), (75,), (65,), (40,)],
    'sku_normalize': [('abc12345',), ('XYZ-00042',), ('Qrs 55555',), ('def-10203',)],
    'meeting_end': [('09:00', 30), ('13:15', 60), ('10:00', 45), ('08:30', 90)],
    'format_money': [(1234.5, 'USD'), (99, 'USD'), (2500, 'EUR'), (10.25, 'GBP')],
    'email_domain': [('Ann@Example.com',), ('bob@company.org',), ('carol.smith@mail.example.co.uk',), ('dave+news@shop.io',)],
    'prorate_charge': [(30.0, 16, 30), (60.0, 21, 30), (31.0, 11, 31), (90.0, 11, 30)],
    'overtime_pay': [(40, 20.0), (30, 15.0), (45, 20.0), (50, 10.0)],
    'name_initials': [('John Smith',), ('mary ann lee',), ('Alice Brown',), ('Peter Parker',)],
}

EDGE = {
    'invoice_total': [(100.0, 10, 60), (100.0, 10, 50), (-50.0, 10, 0), (100.0, None, 0),
                      (100.0, 10, None), (100.0, 10, -5), (1.005, 0, 0), (None, 10, 0), (0.0, 10, 10)],
    'late_fee': [(3, 1000.0), (4, 1000.0), (30, 1000.0), (4, 100.0), (2.9, 1000.0),
                 (None, 500.0), (10, None), (10, -100.0), (26, 1000.0)],
    'fiscal_quarter': [('2026-01-15',), ('2026-02-01',), ('2026-04-30',), ('2026-05-01',),
                       ('2026-02-30',), ('2026-07-04 10:30',), (None,), ('15/03/2026',)],
    'business_days_between': [('2026-12-24', '2026-12-28'), ('2026-12-31', '2027-01-04'),
                              ('2026-03-06', '2026-03-02'), ('2026-03-04', '2026-03-04'),
                              ('2026-03-07', '2026-03-08'), ('2026-03-06', '2026-03-09'),
                              ('2026-13-01', '2026-03-02'), (None, '2026-03-02')],
    'normalize_phone': [('1-415-555-0123',), ('+44 20 7946 0958',), ('415-555-0123 x204',),
                        ('415-555-0123 ext. 7',), ('555-0123',), ('015-555-0123',),
                        ('+1234567',), ('',), (None,)],
    'mask_card': [('4111 1111 1111 1111',), ('4111-1111-1111-1111',), ('378282246310005',),
                  ('411111111111',), ('4111a11111111111',), ('',), (None,), (4111111111111111,)],
    'slugify_title': [('Café Crème',), ('Salt & Pepper',), ("Don't Stop",), ('!!!',),
                      ('The Quick Brown Fox Jumps Over The Lazy Dog Again',), ('  --Hello--  ',),
                      ('a' * 50,), (None,)],
    'loyalty_tier': [(999.9,), (1000,), (4999,), (5000,), (20000,), (-10,), (None,), (0,)],
    'shipping_cost': [(2.1, 1), (0.2, 2), (30, 1), (30.5, 1), (0, 1), (5, 4), (5, 1.5), (5, None), ('3', '2')],
    'age_band': [('2008-10-28', '2026-10-27'), ('2008-10-27', '2026-10-27'), ('1961-10-27', '2026-10-27'),
                 ('2008-02-29', '2026-02-28'), ('2008-02-29', '2026-03-01'), ('2026-10-27', '2020-01-01'),
                 ('1990-02-30', '2026-10-27'), (None, '2026-10-27')],
    'surname_of': [('Ludwig van Beethoven',), ('Martin Luther King Jr.',), ('Smith, John',),
                   ('Cher',), ('Maria de la Cruz',), ('John Smith III',), ('  ',), (None,), ('Van Morrison',)],
    'letter_grade': [(93,), (92.5,), (89.4,), (80,), (59.5,), (100,), (101,), (-1,), (None,)],
    'sku_normalize': [('abc42',), ('ABC123456',), ('ABCO0O42',), ('AB-12345',), ('ABCD-1234',),
                      ('abc_123',), ('',), (None,)],
    'meeting_end': [('09:00', 20), ('09:00', 1), ('23:30', 60), ('09:00', 0), ('09:00', -30),
                    ('9:05', 15), ('24:00', 30), ('09:00', None), ('22:00', 1500)],
    'format_money': [(-12.0, 'USD'), (1234.567, 'JPY'), (1234.5, 'CHF'), (10.005, 'usd'),
                     (5, None), (-0.001, 'USD'), (1234567.891, 'EUR'), (None, 'USD')],
    'email_domain': [('a@googlemail.com',), ('a@b@c.com',), ('noatsign.com',), ('  Bob@Shop.IO.  ',),
                     ('@example.com',), ('a@localhost',), ('a@exa..mple.com',), (None,)],
    'prorate_charge': [(100.0, 2, 30), (50.0, 28, 30), (50.0, 27, 30), (50.0, 1, 30),
                       (50.0, 31, 30), (50.0, 15, 27), (-50.0, 10, 30), (50.0, 29, 31), (50.0, 2.5, 30)],
    'overtime_pay': [(40.13, 20.0), (65, 10.0), (60, 10.0), (-5, 20.0), (40, -1.0),
                     (None, 20.0), (40.1, 20.0), (0, 20.0)],
    'name_initials': [('Jean-Luc Picard',), ('Ludwig van Beethoven',), ('Ludwig Van Beethoven',),
                      ('John Paul George Ringo',), ('Cher',), ('',), (None,), ("o'Brien",)],
}

AGG_TYPICAL = [[4, 5, 3], [5, 5, 4, 4], [2, 3, 4, 3], [5, 4, 4, 5, 5]]

AGG_EDGE = [
    [5, 5],
    [4, 5, 0, 6, 3],
    [4, None, '5', 5, 3],
    [5, 4, 4, 4],
    [],
    [1, 1, 2, 2, 2, 2, 2, 2],
    [4.5, 3.5, 5],
]


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, n) in SCALARS.items():
        con.create_function(name, n, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con
