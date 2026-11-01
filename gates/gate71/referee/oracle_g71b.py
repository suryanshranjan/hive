import re
import math
import sqlite3
import calendar
import datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext


# ---------------------------------------------------------------- helpers
def _num(x):
    if x is None or isinstance(x, bool):
        return None
    if isinstance(x, int):
        return x
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    if isinstance(x, str):
        t = x.strip()
        if '_' in t:
            return None
        try:
            return int(t)
        except ValueError:
            pass
        try:
            f = float(t)
        except ValueError:
            return None
        return f if math.isfinite(f) else None
    return None


def _dec(x):
    return Decimal(x) if isinstance(x, int) else Decimal(repr(x))


def _round(d, nd):
    with localcontext() as c:
        c.prec = 200
        return d.quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)


def _date(x):
    if x is None:
        return None
    m = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})', str(x).strip())
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _safe(fn):
    def w(*a):
        try:
            r = fn(*a)
        except Exception:
            return None
        if isinstance(r, bool):
            r = int(r)
        if isinstance(r, int) and not (-2 ** 63 <= r < 2 ** 63):
            return None
        if isinstance(r, float) and not math.isfinite(r):
            return None
        return r
    w.__name__ = fn.__name__
    return w


# ---------------------------------------------------------------- scalars
@_safe
def vat_amount(net, rate):
    n, r = _num(net), _num(rate)
    if n is None or r is None:
        return None
    with localcontext() as c:
        c.prec = 200
        v = _dec(n) * _dec(r) / Decimal(100)
    return float(_round(v, 2))


_PARTICLES = {'de', 'da', 'di', 'van', 'von', 'der', 'del', 'la', 'le'}


@_safe
def initials(name):
    if name is None:
        return None
    words = str(name).split()
    out = []
    for i, w in enumerate(words):
        if i > 0 and w in _PARTICLES:
            continue
        out.append(w[0].upper())
    return ''.join(out)


@_safe
def quarter_label(d):
    if d is None:
        return None
    dt = _date(d)
    if dt is None:
        return 'Q?-????'
    return 'Q%d-%04d' % ((dt.month - 1) // 3 + 1, dt.year)


@_safe
def mask_card(num):
    if num is None:
        return None
    digits = re.sub(r'\D', '', str(num))
    return '*' * max(len(digits) - 4, 0) + digits[-4:]


@_safe
def cents_to_money(cents):
    n = _num(cents)
    if n is None:
        return None
    c = int(_round(_dec(n), 0))
    if c == 0:
        return '-'
    whole, frac = divmod(abs(c), 100)
    s = '$%s.%02d' % (format(whole, ','), frac)
    return '(' + s + ')' if c < 0 else s


def _wd(d):
    n = d.toordinal() - 1
    return (n // 7) * 5 + min(n % 7, 5)


def _bdays(a, b):
    cnt = _wd(b) - _wd(a)
    for y in range(a.year, b.year + 1):
        for m, dd in ((1, 1), (12, 25)):
            h = datetime.date(y, m, dd)
            if a <= h < b and h.weekday() < 5:
                cnt -= 1
    return cnt


@_safe
def business_days_between(d1, d2):
    a, b = _date(d1), _date(d2)
    if a is None or b is None:
        return None
    if a <= b:
        return _bdays(a, b)
    return -_bdays(b, a)


@_safe
def slugify(text):
    if text is None:
        return None
    s = re.sub(r'[^a-z0-9]+', '-', str(text).lower()).strip('-')
    if len(s) > 30:
        s = s[:30].rstrip('-')
    return s or 'untitled'


@_safe
def late_fee(amount, days_late):
    a, d = _num(amount), _num(days_late)
    if a is None or d is None:
        return None
    weeks = math.floor(d / 7)
    if a <= 0 or weeks <= 0:
        return 0.0
    amt = _dec(a)
    with localcontext() as c:
        c.prec = 200
        raw = amt * Decimal('0.005') * weeks
        fee = min(raw, amt * Decimal('0.2'))
        fee = max(fee, Decimal(2))
    return float(_round(fee, 2))


@_safe
def bmi_band(weight_kg, height_cm):
    w, h = _num(weight_kg), _num(height_cm)
    if w is None or h is None:
        return None
    if h < 100 or h > 250 or w <= 0:
        return None
    with localcontext() as c:
        c.prec = 200
        m = _dec(h) / Decimal(100)
        bmi = _round(_dec(w) / (m * m), 1)
    if bmi < Decimal('18.5'):
        return 'underweight'
    if bmi < Decimal('25'):
        return 'normal'
    if bmi < Decimal('30'):
        return 'overweight'
    return 'obese'


@_safe
def shift_label(hour):
    n = _num(hour)
    if n is None:
        return None
    h = math.floor(n) % 24
    if 6 <= h < 12:
        return 'morning'
    if 12 <= h < 18:
        return 'afternoon'
    if 18 <= h < 22:
        return 'evening'
    return 'night'


_EXT = re.compile(r'(?:x|ext\.?)\s*(\d+)\s*$', re.I)


@_safe
def fmt_phone(text):
    if text is None:
        return None
    t = str(text)
    ext = None
    m = _EXT.search(t)
    if m:
        ext = m.group(1)
        t = t[:m.start()]
    digits = re.sub(r'\D', '', t)
    if len(digits) == 11 and digits[0] == '1':
        digits = digits[1:]
    if len(digits) != 10:
        return None
    out = '(%s) %s-%s' % (digits[:3], digits[3:6], digits[6:])
    if ext:
        out += ' x' + ext
    return out


@_safe
def tier_discount(qty, unit_price):
    q, p = _num(qty), _num(unit_price)
    if q is None or p is None:
        return None
    q = math.floor(q)
    if q <= 0 or p < 0:
        return 0.0
    if q >= 500:
        pct = Decimal('0.20')
    elif q >= 100:
        pct = Decimal('0.15')
    elif q >= 50:
        pct = Decimal('0.10')
    elif q >= 10:
        pct = Decimal('0.05')
    else:
        pct = Decimal(0)
    with localcontext() as c:
        c.prec = 200
        tot = Decimal(q) * _dec(p) * (Decimal(1) - pct)
    return float(_round(tot, 2))


@_safe
def age_years(birth, asof):
    b, a = _date(birth), _date(asof)
    if b is None or a is None or b > a:
        return None
    bm, bd = b.month, b.day
    if bm == 2 and bd == 29 and not calendar.isleap(a.year):
        bm, bd = 3, 1
    yrs = a.year - b.year - (1 if (a.month, a.day) < (bm, bd) else 0)
    return min(yrs, 99)


@_safe
def grade_letter(pct):
    n = _num(pct)
    if n is None or n < 0:
        return 'I'
    r = int(_round(_dec(n), 0))
    if r > 100:
        return 'A+'
    if r >= 90:
        return 'A'
    if r >= 80:
        return 'B'
    if r >= 70:
        return 'C'
    if r >= 60:
        return 'D'
    return 'F'


_SMALL = {'a', 'an', 'and', 'at', 'by', 'for', 'in', 'of', 'on', 'or', 'the', 'to'}


@_safe
def title_case(text):
    if text is None:
        return None
    out = []
    for i, w in enumerate(str(text).split(' ')):
        if w.isalpha() and w.isupper() and 2 <= len(w) <= 4:
            out.append(w)
        elif i > 0 and w.lower() in _SMALL:
            out.append(w.lower())
        else:
            out.append('-'.join(p[:1].upper() + p[1:].lower() for p in w.split('-')))
    return ' '.join(out)


@_safe
def ticket_priority(severity, age_hours, is_vip):
    s = _num(severity)
    if s is None or s != int(s) or not (1 <= s <= 4):
        return 'P4'
    level = int(s)
    v = _num(is_vip)
    if v is not None and v != 0:
        level -= 1
    a = _num(age_hours)
    if a is not None and a > 72:
        level -= 1
    return 'P%d' % max(level, 1)


@_safe
def shipping_fee(weight_g, zone):
    w = _num(weight_g)
    if w is None or zone is None:
        return None
    if w > 30000:
        return None
    if w <= 0:
        return 0.0
    base = {'A': Decimal(4), 'B': Decimal(6), 'C': Decimal(9)}.get(str(zone), Decimal(9))
    blocks = math.ceil(w / 500)
    fee = base + Decimal('1.5') * (blocks - 1)
    if w > 10000:
        fee = fee * Decimal('1.1')
    return float(_round(fee, 2))


_UNITS = {}
for _names, _secs in ((('d', 'day', 'days'), 480 * 60),
                      (('h', 'hr', 'hrs', 'hour', 'hours'), 3600),
                      (('m', 'min', 'mins', 'minute', 'minutes', ''), 60),
                      (('s', 'sec', 'secs', 'second', 'seconds'), 1)):
    for _n in _names:
        _UNITS[_n] = _secs


@_safe
def parse_duration(text):
    if text is None:
        return None
    t = str(text).strip().lower()
    if not re.fullmatch(r'(?:\s*\d+(?:\.\d+)?\s*[a-z]*)+', t):
        return None
    total = Decimal(0)
    for num, unit in re.findall(r'(\d+(?:\.\d+)?)\s*([a-z]*)', t):
        if unit not in _UNITS:
            return None
        total += Decimal(num) * _UNITS[unit]
    return int((total / 60).to_integral_value(rounding='ROUND_CEILING'))


@_safe
def invoice_number(prefix, seq, year):
    if prefix is None or seq is None or year is None:
        return None
    s, y = _num(seq), _num(year)
    if s is None or y is None or s != int(s) or y != int(y):
        return None
    s, y = int(s), int(y)
    if not (1 <= s <= 999999):
        return None
    if 0 <= y < 100:
        y += 2000
    if not (0 <= y <= 9999):
        return None
    p = re.sub(r'[^A-Za-z0-9]', '', str(prefix))[:4]
    return '%s-%04d-%06d' % (p, y, s)


# ---------------------------------------------------------------- aggregate
class score_avg:
    def __init__(self):
        self.vals = []

    def step(self, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return
        if isinstance(value, float) and not math.isfinite(value):
            return
        if 0 <= value <= 10:
            self.vals.append(value)

    def finalize(self):
        if len(self.vals) < 3:
            return None
        with localcontext() as c:
            c.prec = 200
            tot = sum((_dec(v) for v in self.vals), Decimal(0))
            avg = tot / len(self.vals)
        return float(_round(avg, 1))


# ---------------------------------------------------------------- module tables
SPEC = {
    'vat_amount': 'vat_amount(net, rate_pct): VAT owed on a net amount at a percentage rate, in currency units.',
    'initials': "initials(name): Upper-case initials of a person's full name, for avatars and sign-offs.",
    'quarter_label': "quarter_label(date): Reporting label of the calendar quarter an ISO date (YYYY-MM-DD) falls in.",
    'mask_card': 'mask_card(card_number): Display-safe version of a payment card number that hides all but the last digits.',
    'cents_to_money': 'cents_to_money(cents): Formats an amount held in cents as a currency string for statements.',
    'business_days_between': 'business_days_between(start_date, end_date): Number of working days between two ISO dates, for SLA clocks.',
    'slugify': 'slugify(title): Turns a title into a URL-safe lowercase slug.',
    'late_fee': 'late_fee(amount, days_late): Penalty charged on an overdue invoice, growing with each week late.',
    'bmi_band': 'bmi_band(weight_kg, height_cm): Wellness-programme category (underweight/normal/overweight/obese) from body measurements.',
    'shift_label': 'shift_label(hour): Names the part of the working day (morning, afternoon, evening, night) for an hour of the clock.',
    'fmt_phone': 'fmt_phone(text): Normalises a North American phone number into the standard display format.',
    'tier_discount': 'tier_discount(qty, unit_price): Order total after the volume discount for the quantity bought.',
    'age_years': 'age_years(birth_date, as_of_date): Completed years of age between two ISO dates.',
    'grade_letter': 'grade_letter(percent): Letter grade for a course score given as a percentage.',
    'title_case': 'title_case(text): Capitalises a heading in publication style.',
    'ticket_priority': 'ticket_priority(severity, age_hours, is_vip): Support-queue priority (P1 most urgent to P4) for a ticket.',
    'shipping_fee': 'shipping_fee(weight_g, zone): Delivery charge for a parcel of a given weight to a pricing zone (A, B or C).',
    'parse_duration': 'parse_duration(text): Converts a human-written duration such as "1h 30m" into whole minutes for timesheets.',
    'invoice_number': 'invoice_number(prefix, seq, year): Builds the printed invoice number from a document prefix, sequence and year.',
    'score_avg': 'score_avg(value): Average customer rating across a group of responses, to one decimal place.',
}

SCALARS = {
    'vat_amount': (vat_amount, 2),
    'initials': (initials, 1),
    'quarter_label': (quarter_label, 1),
    'mask_card': (mask_card, 1),
    'cents_to_money': (cents_to_money, 1),
    'business_days_between': (business_days_between, 2),
    'slugify': (slugify, 1),
    'late_fee': (late_fee, 2),
    'bmi_band': (bmi_band, 2),
    'shift_label': (shift_label, 1),
    'fmt_phone': (fmt_phone, 1),
    'tier_discount': (tier_discount, 2),
    'age_years': (age_years, 2),
    'grade_letter': (grade_letter, 1),
    'title_case': (title_case, 1),
    'ticket_priority': (ticket_priority, 3),
    'shipping_fee': (shipping_fee, 2),
    'parse_duration': (parse_duration, 1),
    'invoice_number': (invoice_number, 3),
}

AGGREGATE = ('score_avg', score_avg)

TYPICAL = {
    'vat_amount': [(100, 20), (250.0, 8), (19.99, 10), (1000, 5), (80, 12.5)],
    'initials': [('John Smith',), ('mary jane watson',), ('Ada Lovelace',), ('Grace Brewster Hopper',)],
    'quarter_label': [('2026-05-17',), ('2025-01-01',), ('2024-12-31',), ('2023-08-09',)],
    'mask_card': [('4111111111111111',), ('5500005555555559',), ('378282246310005',), ('6011111111111117',)],
    'cents_to_money': [(123456,), (99,), (5000,), (100000000,), (250,)],
    'business_days_between': [('2026-03-02', '2026-03-06'), ('2026-03-02', '2026-03-09'),
                              ('2026-03-06', '2026-03-09'), ('2026-02-01', '2026-03-01')],
    'slugify': [('Hello World',), ('Quarterly Report 2026',), ('  Spring Sale! 50% off ',), ('Rock & Roll',)],
    'late_fee': [(1000, 14), (500, 35), (2400, 21), (800, 70)],
    'bmi_band': [(50, 175), (70, 175), (85, 175), (110, 175), (60, 165)],
    'shift_label': [(3,), (6,), (9,), (12,), (14,), (18,), (20,), (22,)],
    'fmt_phone': [('4155550134',), ('415-555-0134',), ('(415) 555 0134',), ('415.555.0134',)],
    'tier_discount': [(5, 10.0), (10, 10), (20, 12.5), (50, 8), (60, 3), (100, 2), (150, 4)],
    'age_years': [('1990-06-15', '2026-11-01'), ('2000-12-25', '2026-11-01'),
                  ('1985-03-10', '2020-03-10'), ('2010-01-01', '2026-11-01')],
    'grade_letter': [(95,), (85,), (72,), (64,), (30,), (90,), (80,), (70,), (60,)],
    'title_case': [('hello world',), ('annual sales review',), ('monthly budget report',), ('customer support team',)],
    'ticket_priority': [(3, 5, 0), (2, 10, 0), (4, 1, 0), (1, 20, 0)],
    'shipping_fee': [(400, 'A'), (500, 'B'), (1200, 'C'), (2000, 'A'), (501, 'B')],
    'parse_duration': [('2h',), ('45m',), ('1h 30m',), ('90m',), ('1.5h',), ('2 hours',)],
    'invoice_number': [('INV', 42, 2026), ('CRN', 7, 2025), ('PO', 123456, 2024), ('REF', 1000, 2023)],
}

EDGE = {
    'vat_amount': [(0.25, 10), (0.15, 10), (-0.25, 10), (None, 10), (100, None), (1e12, 20), (0, 20),
                   ('abc', 10), (-100, 20)],
    'initials': [('Ludwig van Beethoven',), ('van Gogh',), ('   ',), ('',), (None,), ('Jean-Luc Picard',),
                 ('Leonardo da Vinci',), ('Van Halen',)],
    'quarter_label': [('2026-13-01',), ('not a date',), (None,), ('',), ('2026-02-30',), ('2026-07-01',),
                      ('2026-04-01',), (20260517,)],
    'mask_card': [('4111 1111 1111 1111',), ('4111-1111-1111-1111',), ('1234',), ('12',), (None,), ('',),
                  ('abcd',), (4111111111111111,)],
    'cents_to_money': [(-123456,), (0,), (-1,), (None,), ('abc',), (1,), (-99999999999,), (10 ** 15,)],
    'business_days_between': [('2026-03-06', '2026-03-02'), ('2026-12-24', '2026-12-28'),
                              ('2025-12-31', '2026-01-02'), ('2026-03-02', '2026-03-02'),
                              ('bad', '2026-01-01'), (None, '2026-01-01'), ('2026-01-01', '2026-01-02'),
                              ('2026-03-02', '2026-02-30')],
    'slugify': [('The quick brown fox jumps over the lazy dog and more',), ('!!!',), ('',), (None,),
                ('a' * 50,), ('x' * 29 + ' yy',), ('Ünïcode Café',), ('  --Hi--  ',)],
    'late_fee': [(100, 400), (10, 14), (1000, 6), (1000, -5), (None, 5), (0, 100), (1000, None), (1000, 7.9)],
    'bmi_band': [(76.5, 175), (53.35, 170), (70, 50), (70, 300), (None, 170), (70, None), (-5, 170), (0, 170)],
    'shift_label': [(24,), (30,), (-1,), (13.9,), (5.9,), (None,), ('x',), (11.99,)],
    'fmt_phone': [('1-415-555-0134',), ('+1 415 555 0134',), ('555-0134',), ('415-555-0134 x22',),
                  ('415-555-0134 ext. 7',), ('24155550134',), (None,), ('',), ('44 20 7946 0958',)],
    'tier_discount': [(500, 2), (0, 10), (-5, 10), (10, -3), (12.9, 10), (0.9, 10), (None, 5), (10, None),
                      (499, 1)],
    'age_years': [('2000-02-29', '2026-02-28'), ('2000-02-29', '2026-03-01'), ('2000-02-29', '2028-02-28'),
                  ('2030-01-01', '2026-01-01'), ('1900-01-01', '2026-01-01'), ('2026-01-01', '2026-01-01'),
                  (None, '2026-01-01'), ('bad', '2026-01-01'), ('2000-02-29', '2028-02-29')],
    'grade_letter': [(89.5,), (89.4,), (100,), (100.5,), (100.4,), (-1,), (None,), ('abc',), (59.5,), (0,)],
    'title_case': [('lord of the rings',), ('the end of the road',), ('well-known facts',), ('NASA launch day',),
                   ('IBM and SAP',), ('',), (None,), ('a tale of two cities',), ('hello  world',)],
    'ticket_priority': [(3, 5, 1), (3, 100, 0), (3, 100, 1), (1, 100, 1), (7, 5, 1), (None, 5, 0),
                        (2.5, 5, 0), (4, 72, 0), (4, 73, 0), (2, None, None)],
    'shipping_fee': [(30001, 'A'), (30000, 'A'), (10000, 'B'), (10001, 'B'), (800, 'Z'), (800, 'a'),
                     (0, 'A'), (-50, 'A'), (None, 'A'), (800, None)],
    'parse_duration': [('1d',), ('45',), ('1h 15',), ('90s',), ('1m 1s',), ('abc',), ('1h 5x',), ('-5m',),
                       ('0.5d',), (None,)],
    'invoice_number': [('INVOICE', 5, 2026), ('in-v', 5, 2026), ('INV', 5, 26), ('INV', 999999, 2026),
                       ('INV', 1000000, 2026), ('INV', 0, 2026), ('INV', 2.5, 2026), ('INV', 5, None),
                       (None, 5, 2026), ('INV', 5, 0)],
}

AGG_TYPICAL = [[8, 9, 7, 6], [7, 8, 8], [10, 9, 8, 9], [8, None, 9, 7]]

AGG_EDGE = [[8, '9', 7, 6], [8, 9, 11, -1, 7], [8, 9], [8, 8, 9, 8], [None, None], [], [0, 10, 5]]

DECISIONS = {
    'vat_amount': ['ties round half up (away from zero)'],
    'initials': ['lowercase name particles skipped unless first word'],
    'quarter_label': ["unparseable non-NULL date gives 'Q?-????'"],
    'mask_card': ['non-digit characters removed before masking'],
    'cents_to_money': ['negative amounts in parentheses', "zero shown as '-'"],
    'business_days_between': ['reversed range gives negative count', 'Jan 1 and Dec 25 weekdays are not working days'],
    'slugify': ['slug capped at 30 chars, trailing hyphen trimmed', "empty slug becomes 'untitled'"],
    'late_fee': ['fee capped at 20% of amount', 'minimum fee 2.00 once any fee applies'],
    'bmi_band': ['BMI rounded to 1 decimal before banding', 'height outside 100-250 (or weight<=0) gives NULL'],
    'shift_label': ['hours outside 0-23 wrap modulo 24', 'fractional hours truncated down'],
    'fmt_phone': ['leading country code 1 on 11 digits dropped', 'other digit counts give NULL',
                  "extension kept as ' xNN'"],
    'tier_discount': ['500+ units get 20%', 'qty<=0 or negative price gives 0.0', 'fractional qty floored'],
    'age_years': ['Feb 29 birthday counts as Mar 1 in non-leap years', 'birth after as-of gives NULL',
                  'age capped at 99'],
    'grade_letter': ['percent rounded half up before banding', "above 100 after rounding gives 'A+'",
                     "negative/missing/non-numeric gives 'I'"],
    'title_case': ['small words lowercase unless first', 'all-caps words of 2-4 letters preserved',
                   'hyphenated parts each capitalised'],
    'ticket_priority': ['VIP raises priority one level', 'age over 72h raises priority one level',
                        "invalid severity gives 'P4' with no raises"],
    'shipping_fee': ['over 30000 g not shippable (NULL)', 'unknown zone priced as zone C',
                     'weight<=0 costs 0.0', '10% surcharge above 10000 g'],
    'parse_duration': ['a day is 480 minutes', 'bare number means minutes', 'leftover seconds round up to a minute',
                       'any unrecognised token gives NULL'],
    'invoice_number': ['prefix stripped to alphanumerics (up to 4 chars)',
                       'two-digit year means 20YY', 'seq outside 1..999999 gives NULL',
                       'prefix truncated to 4 characters'],
    'score_avg': ['text values ignored even if numeric-looking', 'values outside 0..10 ignored',
                  'fewer than 3 valid values gives NULL', 'average ties round half up to 1 decimal'],
}
# fix labels to match one-per-decision precisely
DECISIONS['invoice_number'] = ['prefix non-alphanumerics removed', 'two-digit year means 20YY',
                               'seq outside 1..999999 gives NULL', 'prefix truncated to 4 characters']

DECISION_EXAMPLES = {
    'vat_amount': [(0.45, 10)],
    'initials': [('Charles de Gaulle',)],
    'quarter_label': [('31-12-2026',)],
    'mask_card': [('3782 822463 10005',)],
    'cents_to_money': [(-5000,), ('0',)],
    'business_days_between': [('2026-04-30', '2026-04-27'), ('2028-12-22', '2028-12-27')],
    'slugify': [('The quick brown fox jumps over the lazy dog',), ('---',)],
    'late_fee': [(250, 500), (100, 7)],
    'bmi_band': [(97.1, 180), (70, 99)],
    'shift_label': [(36,), (17.99,)],
    'fmt_phone': [('1 (212) 555-0100',), ('2125550100123',), ('(212) 555-0100 x 9',)],
    'tier_discount': [(750, 2), (-1, -1), (59.99, 2)],
    'age_years': [('2004-02-29', '2027-02-28'), ('2027-05-05', '2026-11-01'), ('1910-05-05', '2026-11-01')],
    'grade_letter': [(79.5,), (250,), (-20.0,)],
    'title_case': [('state of the art tools',), ('USA today',), ('long-term PLAN',)],
    'ticket_priority': [(4, 2, 1), (3, 200, 0), (9, 500, 1)],
    'shipping_fee': [(45000, 'C'), (700, 'X'), (-1, 'B'), (15000, 'A')],
    'parse_duration': [('2 days',), ('3h 20',), ('30s',), ('10 parsecs',)],
    'invoice_number': [('A/B', 3, 2026), ('INV', 5, 7), ('INV', -3, 2026), ('SALES', 9, 2026)],
    'score_avg': [[4, 'x', '5', 6, 6], [10.5, 3, 3, 3], [5, 6], [7, 7, 7, 8]],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, n) in SCALARS.items():
        con.create_function(name, n, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con
