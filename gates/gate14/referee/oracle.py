"""Company policy for 20 business SQL functions (19 scalars + 1 aggregate).

Standard library only. Every function returns a value (never raises) for any
int, float, str or None argument.
"""
import datetime
import math
import re
import sqlite3
from decimal import Decimal, ROUND_FLOOR, ROUND_CEILING, ROUND_HALF_UP


# ---------------------------------------------------------------- helpers

def _num(x):
    if x is None or isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
            return None
        return x
    if isinstance(x, str):
        try:
            v = float(x.strip())
        except ValueError:
            return None
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    return None


def _dec(x):
    return Decimal(repr(x)) if isinstance(x, float) else Decimal(x)


def _cents(d, mode):
    return float(d.quantize(Decimal('0.01'), rounding=mode))


def _date(s):
    if not isinstance(s, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', s.strip()):
        return None
    try:
        return datetime.date.fromisoformat(s.strip())
    except ValueError:
        return None


def _int_like(x):
    v = _num(x)
    if v is None or v != int(v):
        return None
    return int(v)


# ---------------------------------------------------------------- scalars

def net_price(gross, discount_pct):
    try:
        g, d = _num(gross), _num(discount_pct)
        if g is None or d is None:
            return None
        if g < 0:
            return None
        d = max(d, 0)
        d = min(d, 40)
        val = _dec(g) * (Decimal(100) - _dec(d)) / Decimal(100)
        return _cents(val, ROUND_FLOOR)
    except Exception:
        return None


_HOLIDAYS = {(12, 25), (1, 1)}


def delivery_date(order_date, business_days):
    try:
        start, n = _date(order_date), _num(business_days)
        if start is None or n is None:
            return None
        if n > 60:
            return None
        n = math.ceil(n)
        if n < 1:
            n = 1
        d, count = start, 0
        while count < n:
            d += datetime.timedelta(days=1)
            if d.weekday() >= 5 or (d.month, d.day) in _HOLIDAYS:
                continue
            count += 1
        return d.isoformat()
    except Exception:
        return None


_TIERS = ['Bronze', 'Silver', 'Gold', 'Platinum']


def loyalty_tier(points, years):
    try:
        p = _num(points)
        if p is None:
            return None
        if p < 0:
            return 'Suspended'
        if p > 1_000_000:
            return 'Review'
        if p < 1000:
            t = 0
        elif p < 5000:
            t = 1
        elif p < 20000:
            t = 2
        else:
            t = 3
        y = _num(years)
        if y is None:
            y = 0
        if y >= 10:
            t = min(t + 1, 3)
        return _TIERS[t]
    except Exception:
        return None


def sku_normalize(code):
    try:
        if not isinstance(code, str):
            return None
        s = code.strip().upper()
        m = re.fullmatch(r'([A-Z]{3})[-_]?([0-9O]{1,4})', s)
        if not m:
            return None
        prefix, digits = m.group(1), m.group(2).replace('O', '0')
        if prefix == 'TMP':
            return None
        return '%s-%s' % (prefix, digits.zfill(4))
    except Exception:
        return None


def late_fee(days_late, invoice_amount):
    try:
        d, a = _num(days_late), _num(invoice_amount)
        if d is None or a is None:
            return None
        if a < 0:
            return 0.0
        if d <= 3:
            return 0.0
        fee = _dec(a) * _dec(d) / Decimal(100)
        if fee > 0 and fee < 2:
            fee = Decimal(2)
        if fee > 25:
            fee = Decimal(25)
        return _cents(fee, ROUND_HALF_UP)
    except Exception:
        return None


def invoice_number(year, seq):
    try:
        y, s = _int_like(year), _int_like(seq)
        if y is None or s is None:
            return None
        if 0 <= y <= 99:
            y += 2000
        if y < 0 or y > 9999:
            return None
        if s <= 0 or s >= 1_000_000:
            return None
        prefix = 'OLD' if y < 2000 else 'INV'
        return '%s-%04d-%06d' % (prefix, y, s)
    except Exception:
        return None


def mask_card(card_number):
    try:
        if isinstance(card_number, int) and not isinstance(card_number, bool):
            card_number = str(card_number)
        if not isinstance(card_number, str):
            return None
        digits = re.sub(r'[ \-]', '', card_number.strip())
        if not digits.isdigit() or not digits.isascii():
            return None
        if len(digits) < 12 or len(digits) > 19:
            return None
        if len(set(digits)) == 1:
            return 'INVALID'
        keep = 5 if (len(digits) == 15 and digits[:2] in ('34', '37')) else 4
        return '*' * (len(digits) - keep) + digits[-keep:]
    except Exception:
        return None


_LABELS = ['Unrated', 'Poor', 'Fair', 'Good', 'Very Good', 'Excellent']


def rating_label(stars):
    try:
        s = _num(stars)
        if s is None or s < 0 or s > 10:
            return None
        if s > 5:
            s = s / 2
        if s - math.floor(s) == 0.5:
            r = math.floor(s)
        else:
            r = math.floor(s + 0.5)
        return _LABELS[int(r)]
    except Exception:
        return None


_TAX = {'EU': Decimal('0.20'), 'US': Decimal('0.07'), 'JP': Decimal('0.10')}


def tax_amount(amount, region):
    try:
        a = _num(amount)
        if a is None or not isinstance(region, str):
            return None
        rate = _TAX.get(region.strip().upper())
        if rate is None:
            return 0.0
        if a < 1:
            return 0.0
        return _cents(_dec(a) * rate, ROUND_CEILING)
    except Exception:
        return None


def meeting_slot(start_time, duration_min):
    try:
        if not isinstance(start_time, str):
            return None
        m = re.fullmatch(r'(\d{1,2}):(\d{2})', start_time.strip())
        dur = _num(duration_min)
        if not m or dur is None or dur <= 0:
            return None
        h, mi = int(m.group(1)), int(m.group(2))
        if h > 23 or mi > 59:
            return None
        start = max(h * 60 + mi, 8 * 60)
        dur = math.ceil(dur / 15) * 15
        end = start + dur
        if end > 18 * 60:
            return None
        return '%02d:%02d' % (end // 60, end % 60)
    except Exception:
        return None


def phone_e164(phone):
    try:
        if not isinstance(phone, str):
            return None
        s = re.sub(r'\s*(?:x|ext\.?)\s*\d+\s*$', '', phone.strip(), flags=re.I)
        s = re.sub(r'[ \-().]', '', s)
        if s.startswith('+'):
            s = s[1:]
        if not s.isdigit() or not s.isascii():
            return None
        if len(s) == 11 and s[0] == '1':
            s = s[1:]
        elif len(s) == 7:
            s = '555' + s
        if len(s) != 10:
            return None
        return '+1' + s
    except Exception:
        return None


def age_band(age):
    try:
        a = _num(age)
        if a is None or a < 0 or a > 120:
            return None
        if a < 18:
            return 'Minor'
        a = math.floor(a)
        for lo, hi in ((18, 24), (25, 34), (35, 44), (45, 54), (55, 64)):
            if lo <= a <= hi:
                return '%d-%d' % (lo, hi)
        return '65+'
    except Exception:
        return None


def slugify_title(title):
    try:
        if not isinstance(title, str):
            return None
        words = re.findall(r'[a-z0-9]+', title.lower().replace('&', ' and '))
        slug = ''
        for w in words:
            cand = w if not slug else slug + '-' + w
            if len(cand) > 40:
                if not slug:
                    slug = w[:40]
                break
            slug = cand
        return slug
    except Exception:
        return None


def percent_change(old_value, new_value):
    try:
        o, n = _num(old_value), _num(new_value)
        if o is None or n is None or o == 0:
            return None
        r = (n - o) / abs(o) * 100
        r = max(-999.9, min(999.9, r))
        return round(r, 1)
    except Exception:
        return None


def parcel_class(weight_kg):
    try:
        w = _num(weight_kg)
        if w is None or w <= 0:
            return None
        if w > 70:
            return 'Refused'
        if w <= 2:
            return 'Small'
        if w <= 10:
            return 'Medium'
        if w <= 30:
            return 'Large'
        return 'Freight'
    except Exception:
        return None


_PARTICLES = {'van', 'von', 'de', 'der', 'da', 'del', 'la', 'le', 'di', 'du'}


def initials(full_name):
    try:
        if not isinstance(full_name, str):
            return None
        words = [w for w in full_name.split() if w.lower() not in _PARTICLES]
        letters = [w[0].upper() for w in words if w[0].isalpha()]
        if not letters:
            return None
        return ''.join(c + '.' for c in letters)
    except Exception:
        return None


def fiscal_quarter(date_text):
    try:
        if not isinstance(date_text, str):
            return None
        m = re.fullmatch(r'(\d{4}-\d{2}-\d{2})(?: \d{2}:\d{2}(?::\d{2})?)?',
                         date_text.strip())
        if not m:
            return None
        d = _date(m.group(1))
        if d is None:
            return None
        fy = d.year if d.month >= 4 else d.year - 1
        q = ((d.month - 4) % 12) // 3 + 1
        return 'FY%d-Q%d' % (fy, q)
    except Exception:
        return None


def word_tally(text):
    try:
        if not isinstance(text, str):
            return None
        return sum(len([p for p in tok.split('-') if p]) for tok in text.split())
    except Exception:
        return None


def days_overdue(due_date, paid_date):
    try:
        due, paid = _date(due_date), _date(paid_date)
        if due is None or paid is None:
            return None
        if due.weekday() == 5:
            due += datetime.timedelta(days=2)
        elif due.weekday() == 6:
            due += datetime.timedelta(days=1)
        return max(0, (paid - due).days)
    except Exception:
        return None


# ---------------------------------------------------------------- aggregate

class AvgBasket:
    def __init__(self):
        self.total = 0.0
        self.n = 0

    def step(self, value):
        try:
            v = _num(value)
            if v is None or v < 0:
                return
            self.total += v
            self.n += 1
        except Exception:
            pass

    def finalize(self):
        try:
            if self.n == 0:
                return None
            return round(self.total / self.n, 2)
        except Exception:
            return None


# ---------------------------------------------------------------- registry

SPEC = {
    'net_price': 'net_price(gross, discount_pct): price the customer pays after a percentage discount is applied to the gross price.',
    'delivery_date': 'delivery_date(order_date, business_days): ISO date an order arrives, counting the promised number of business days (Mon-Fri) after the order date.',
    'loyalty_tier': 'loyalty_tier(points, years): customer loyalty tier (Bronze, Silver, Gold, Platinum) from lifetime points and years of membership.',
    'sku_normalize': 'sku_normalize(code): canonical product code in the form AAA-9999 (three letters, dash, four digits) from a code typed by staff.',
    'late_fee': 'late_fee(days_late, invoice_amount): late-payment fee in currency units, charged at 1% of the invoice amount per day late.',
    'invoice_number': 'invoice_number(year, seq): printed invoice number such as INV-2026-000123 from the invoice year and its sequence number.',
    'mask_card': 'mask_card(card_number): card number safe to show on receipts, with all but the last digits replaced by asterisks.',
    'rating_label': 'rating_label(stars): word label (Poor, Fair, Good, Very Good, Excellent) for a customer review score of 1 to 5 stars.',
    'tax_amount': 'tax_amount(amount, region): sales tax due on an amount for a region code (EU 20%, US 7%, JP 10%).',
    'meeting_slot': 'meeting_slot(start_time, duration_min): end time HH:MM of a meeting room booking that starts at HH:MM and lasts the given minutes.',
    'phone_e164': 'phone_e164(phone): North American phone number in E.164 form (+1 and ten digits) from a number typed in any common layout.',
    'age_band': 'age_band(age): marketing age band (18-24, 25-34, 35-44, 45-54, 55-64, 65+) for a customer age in years.',
    'slugify_title': 'slugify_title(title): URL slug for an article title: lowercase words joined by dashes.',
    'percent_change': 'percent_change(old_value, new_value): percentage change from the old value to the new value, to one decimal place.',
    'parcel_class': 'parcel_class(weight_kg): shipping size class (Small, Medium, Large, Freight) for a parcel weight; Small up to about 2 kg, Medium to 10, Large to 30.',
    'initials': 'initials(full_name): initials of a person\'s name for badges, each letter followed by a dot.',
    'fiscal_quarter': 'fiscal_quarter(date_text): fiscal quarter label such as FY2026-Q1 for a date; the fiscal year starts on 1 April and is named for the year it starts in.',
    'word_tally': 'word_tally(text): number of words in a piece of text, used for translation billing.',
    'days_overdue': 'days_overdue(due_date, paid_date): days a payment was late (0 if paid on or before the due date).',
    'avg_basket': 'avg_basket(order_value): average order value across a group of orders, to two decimals.',
}

SCALARS = {
    'net_price': (net_price, 2),
    'delivery_date': (delivery_date, 2),
    'loyalty_tier': (loyalty_tier, 2),
    'sku_normalize': (sku_normalize, 1),
    'late_fee': (late_fee, 2),
    'invoice_number': (invoice_number, 2),
    'mask_card': (mask_card, 1),
    'rating_label': (rating_label, 1),
    'tax_amount': (tax_amount, 2),
    'meeting_slot': (meeting_slot, 2),
    'phone_e164': (phone_e164, 1),
    'age_band': (age_band, 1),
    'slugify_title': (slugify_title, 1),
    'percent_change': (percent_change, 2),
    'parcel_class': (parcel_class, 1),
    'initials': (initials, 1),
    'fiscal_quarter': (fiscal_quarter, 1),
    'word_tally': (word_tally, 1),
    'days_overdue': (days_overdue, 2),
}

AGGREGATE = ('avg_basket', AvgBasket)

TYPICAL = {
    'net_price': [(100, 10), (80, 25), (250, 20), (12.5, 20)],
    'delivery_date': [('2026-03-09', 3), ('2026-03-13', 1), ('2026-03-11', 5), ('2026-06-01', 10)],
    'loyalty_tier': [(500, 1), (2500, 3), (8000, 5), (25000, 2)],
    'sku_normalize': [('abc-1234',), ('XYZ9876',), (' KLM-0042 ',), ('Def-5555',)],
    'late_fee': [(10, 100), (5, 200), (20, 50), (7, 300)],
    'invoice_number': [(2026, 123), (2025, 1), (2024, 45678), (2030, 999)],
    'mask_card': [('4111 1111 1111 1234',), ('5500-0000-0000-0004',), ('6011000990139424',), ('4012888888881881',)],
    'rating_label': [(1,), (2,), (3,), (5,)],
    'tax_amount': [(100, 'EU'), (200, 'US'), (80, 'JP'), (250, 'EU')],
    'meeting_slot': [('09:00', 30), ('13:15', 60), ('10:30', 90), ('14:00', 15)],
    'phone_e164': [('(415) 555-0101',), ('212.555.0199',), ('+1 646 555 0123',), ('3125550142',)],
    'age_band': [(20,), (30,), (41,), (70,)],
    'slugify_title': [('Hello World',), ('Q3 Sales Report',), ('  Top 10 Tips!  ',), ('Pricing: Basics',)],
    'percent_change': [(100, 110), (200, 150), (80, 100), (50, 75)],
    'parcel_class': [(1,), (5,), (20,), (50,)],
    'initials': [('John Smith',), ('mary ann lee',), ('Ada Lovelace',), ('Grace Brewster Hopper',)],
    'fiscal_quarter': [('2026-04-15',), ('2026-08-01',), ('2026-11-30',), ('2027-02-10',)],
    'word_tally': [('hello world',), ('The quick brown fox',), ('one',), ('Ship it today please',)],
    'days_overdue': [('2026-03-02', '2026-03-05'), ('2026-03-10', '2026-03-09'), ('2026-04-01', '2026-04-15'), ('2026-05-04', '2026-05-04')],
}

EDGE = {
    'net_price': [(300, 45), (300, 40), (9.94, 10), (75, -5), (-10, 5), (None, 10), (100, 100), (0, 0)],
    'delivery_date': [('2026-12-31', 1), ('2026-03-10', -3), ('2026-03-10', 1.5), ('2026-03-10', 100),
                      ('2026-03-14', 1), ('not a date', 2), ('2026-02-30', 1), ('2026-03-10', None)],
    'loyalty_tier': [(1000, 0), (5000, 4), (25000, 15), (4999, 10), (-1, 20), (2500, None),
                     (2000000, 0), (None, 5), (1000000, 0)],
    'sku_normalize': [('ab-1234',), ('abcd-1234',), ('qrs-1O0O',), ('qrs-7',), ('TMP-0001',),
                      ('qrs_0099',), ('qrs 1234',), ('',), (None,), ('abc-12345',)],
    'late_fee': [(0, 100), (1, 1000), (100, 1000), (4, 10), (10, -50), (None, 100), (8, 0), (-2, 100)],
    'invoice_number': [(2026, 0), (2026, -3), (2026, 1500000), (99, 7), (0, 7), (1999, 7), (None, 5), (2026, 12.5)],
    'mask_card': [('4111111111111',), ('12345678901',), ('3782 822463 10005',), ('0000-0000-0000-0000',),
                  ('4111-1111-1111-111a',), ('',), (None,), (4111111111111111,)],
    'rating_label': [(2.5,), (4.6,), (0.2,), (10,), (6,), (12,), (-0.5,), (None,)],
    'tax_amount': [(10.01, 'EU'), (0.99, 'US'), (1, 'US'), (100, 'CA'), (100, ''), (None, 'EU'),
                   (100, None), (33.33, 'JP')],
    'meeting_slot': [('09:10', 20), ('17:00', 60), ('17:30', 45), ('06:00', 60), ('08:00', 1),
                     ('25:00', 30), ('09:00', 0), ('09:00', None), ('9:05', 15)],
    'phone_e164': [('1-800-555-0100',), ('415 555 0101 ext 7',), ('867-5309',), ('12345',),
                   ('415-555-01O1',), ('',), (None,), ('44 20 7946 0958',)],
    'age_band': [(17.9,), (0,), (24.5,), (25,), (120,), (121,), (-3,), (None,)],
    'slugify_title': [('R&D Budget',), ('A very long title that goes on and on beyond every sensible limit',),
                      ('Forty characters exactly in this slug ok',), ('!!!',), (None,),
                      ('multiple   spaces -- here',)],
    'percent_change': [(10, 0), (0, 5), (2, 100), (-100, -50), (-20, 10), (3, 4), (1, -20), (None, 5)],
    'parcel_class': [(10,), (30,), (70,), (70.5,), (0,), (-1,), (0.01,), (None,)],
    'initials': [('Vincent van Gogh',), ('Cher',), ('  alan   turing ',), ('',), (None,), ('Maria de la Cruz',)],
    'fiscal_quarter': [('2026-03-31',), ('2026-04-01',), ('2026-12-31 23:59:59',), ('2026-13-01',),
                       ('2026/05/01',), ('',), (None,)],
    'word_tally': [('',), ('   ',), ('a  b   c',), ('state-of-the-art design',), (None,), ('end. Start',), ('x - y',)],
    'days_overdue': [('2026-03-08', '2026-03-10'), ('2026-03-07', '2026-03-08'), ('2026-03-07', '2026-03-12'),
                     ('bad', '2026-03-01'), ('2026-03-02', None), ('2026-12-31', '2027-01-04'),
                     ('2026-02-28', '2026-03-03')],
}

AGG_TYPICAL = [[10, 20, 30], [12.5, 7.5], [100], [40, 60, 80, 20]]
AGG_EDGE = [[None, 10, 20], [], [-5, -10], [1, 2, 2], [15, -15, 30], [0, 0], [None]]

DECISIONS = {
    'net_price': ['discount capped at 40%', 'negative discount treated as no discount',
                  'result truncated (floored) to cents', 'negative gross price returns NULL'],
    'delivery_date': ['Dec 25 and Jan 1 are not business days', 'fewer than 1 business day counts as 1',
                      'more than 60 business days returns NULL', 'fractional business days rounded up'],
    'loyalty_tier': ['10+ years of membership bumps one tier (max Platinum)', 'negative points give Suspended',
                     'NULL years treated as 0 years', 'points above 1,000,000 give Review'],
    'sku_normalize': ['letter O in the digit part read as zero', 'digit part shorter than 4 is zero-padded',
                      'TMP prefix codes rejected (NULL)', 'underscore accepted as separator'],
    'late_fee': ['grace period: 3 days or fewer late cost nothing', 'fee capped at 25.00',
                 'minimum fee 2.00 when any fee is due', 'negative invoice amount (credit note) gives 0.0'],
    'invoice_number': ['sequence of 1,000,000 or more returns NULL', 'two-digit years mean 20xx',
                       'years before 2000 use the OLD prefix'],
    'mask_card': ['fewer than 12 digits returns NULL', 'Amex (15 digits, 34/37) shows last 5 digits',
                  'all-identical digits return INVALID'],
    'rating_label': ['exact half stars round down', 'scores below 1 (0 included) give Unrated',
                     'scores above 5 up to 10 are a 10-point scale and are halved'],
    'tax_amount': ['unknown region pays 0 tax', 'amounts below 1.00 are exempt', 'tax rounded up to cents'],
    'meeting_slot': ['duration rounded up to a multiple of 15 minutes', 'ending after 18:00 returns NULL',
                     'start before 08:00 moved to 08:00'],
    'phone_e164': ['extension (x/ext) dropped', '7-digit local numbers get area code 555'],
    'age_band': ['under 18 gives Minor', 'over 120 returns NULL'],
    'slugify_title': ['& becomes the word and', 'slug cut to at most 40 characters at a word boundary'],
    'percent_change': ['result clamped to +/-999.9', 'negative old value uses its absolute value as the base'],
    'parcel_class': ['weight exactly on a boundary goes to the lower class', 'over 70 kg gives Refused'],
    'initials': ['name particles (van, de, la, ...) skipped'],
    'fiscal_quarter': ['date with a space-separated time of day accepted'],
    'word_tally': ['hyphenated parts count as separate words'],
    'days_overdue': ['due date on a weekend moves to the following Monday'],
    'avg_basket': ['negative values (refunds) excluded'],
}

DECISION_EXAMPLES = {
    'net_price': [(200, 60), (50, -10), (1.97, 25), (-20, 10)],
    'delivery_date': [('2026-12-24', 1), ('2026-03-10', 0), ('2026-03-10', 61), ('2026-03-10', 2.2)],
    'loyalty_tier': [(1500, 12), (-5, 2), (6000, None), (1500000, 1)],
    'sku_normalize': [('abc-12O4',), ('abc-42',), ('tmp-1234',), ('abc_1234',)],
    'late_fee': [(3, 400), (30, 200), (5, 20), (10, -100)],
    'invoice_number': [(2026, 1000000), (26, 5), (1998, 42)],
    'mask_card': [('123456789',), ('371449635398431',), ('4444 4444 4444 4444',)],
    'rating_label': [(3.5,), (0,), (8,)],
    'tax_amount': [(50, 'BR'), (0.5, 'EU'), (10.01, 'US')],
    'meeting_slot': [('09:00', 50), ('16:30', 120), ('07:30', 30)],
    'phone_e164': [('415-555-0101 x22',), ('555-0199',)],
    'age_band': [(16,), (130,)],
    'slugify_title': [('Salt & Pepper',), ('The Complete Guide to Quarterly Revenue Planning Methods',)],
    'percent_change': [(1, 50), (-50, -25)],
    'parcel_class': [(2,), (75,)],
    'initials': [('Ludwig van Beethoven',)],
    'fiscal_quarter': [('2026-05-10 14:00',)],
    'word_tally': [('well-known fact',)],
    'days_overdue': [('2026-03-07', '2026-03-09')],
    'avg_basket': [[10, 20, -5]],
}

CONTRAST_EXAMPLES = {
    'net_price': [(200, 35), (50, 10), (1.96, 25), (0, 10)],
    'delivery_date': [('2026-12-22', 1), ('2026-03-10', 2), ('2026-03-10', 60), ('2026-03-10', 2.0)],
    'loyalty_tier': [(1500, 9), (0, 2), (None, 3), (999999, 1)],
    'sku_normalize': [('abc-12X4',), ('abc-42345',), ('tmq-1234',), ('abc.1234',)],
    'late_fee': [(4, 400), (12, 200), (5, 50), (10, 150)],
    'invoice_number': [(2026, 999999), (2005, 5), (2000, 42)],
    'mask_card': [('123456789012',), ('361449635398431',), ('4444 4444 4444 4445',)],
    'rating_label': [(3.7,), (-1,), (11,)],
    'tax_amount': [(50, 'JP'), (1.5, 'EU'), (10.0, 'US')],
    'meeting_slot': [('09:00', 45), ('16:00', 120), ('08:00', 30)],
    'phone_e164': [('415-555-0101 #22',), ('5555-0199',)],
    'age_band': [(18,), (110,)],
    'slugify_title': [('Salt + Pepper',), ('Quarterly Revenue Planning Guide',)],
    'percent_change': [(10, 50), (50, 25)],
    'parcel_class': [(2.5,), (65,)],
    'initials': [('Ludwig Vann Beethoven',)],
    'fiscal_quarter': [('2026-05-10T14:00',)],
    'word_tally': [("it's fine",)],
    'days_overdue': [('2026-03-06', '2026-03-09')],
    'avg_basket': [[10, 20, 0]],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, nargs) in SCALARS.items():
        con.create_function(name, nargs, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con
