"""Business function policy for the SQL engine (private oracle, gate 24).

Tacit conventions shared by every function (not counted as policy decisions):
NULL in any argument gives NULL; a value of the wrong SQL type gives NULL
(numbers are not parsed from text and text is not taken from numbers, unless a
function's own policy says otherwise); malformed or impossible input gives NULL.
"""
import datetime
import math
import re
import sqlite3
import unicodedata
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP

CENT = Decimal('0.01')


def _num(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return None
    return x


def _dec(x):
    return Decimal(str(x))


def _txt(x):
    return x if isinstance(x, str) else None


def _date(x):
    if not isinstance(x, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', x):
        return None
    try:
        return datetime.date.fromisoformat(x)
    except ValueError:
        return None


def _money(d, rounding=ROUND_HALF_UP):
    return float(d.quantize(CENT, rounding=rounding))


# 1 decision each ------------------------------------------------------------

def vat_cents(net):
    net = _num(net)
    if net is None:
        return None
    if net < 0:  # D: refunds/negative net carry no VAT
        return 0
    return int((_dec(net) / 5).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def fiscal_quarter(value):
    value = _txt(value)
    if value is None:
        return None
    m = re.fullmatch(r'(\d{4}-\d{2}-\d{2})(?:[ T]\d{2}:\d{2}(?::\d{2})?)?', value)
    if not m:  # D: a date-time is accepted, its date part is used
        return None
    d = _date(m.group(1))
    if d is None:
        return None
    fy = d.year if d.month >= 4 else d.year - 1
    q = (d.month - 4) % 12 // 3 + 1
    return 'FY%d-Q%d' % (fy, q)


def sku_normalize(code):
    code = _txt(code)
    if code is None:
        return None
    m = re.fullmatch(r'([A-Za-z]+)[\s-]*(\d+)', code.strip())
    if not m:
        return None
    n = int(m.group(2))
    if n > 99999:  # D: numbers beyond 5 digits are rejected, not kept
        return None
    return '%s-%05d' % (m.group(1).upper(), n)


def initials(name):
    name = _txt(name)
    if name is None:
        return None
    out = []
    for word in name.split():
        for part in word.split('-'):  # D: each hyphenated part gives a letter
            if part:
                out.append(part[0].upper())
    return ''.join(out)


def mask_card(card):
    card = _txt(card)
    if card is None:
        return None
    if not re.fullmatch(r'[\d \-]+', card):
        return None
    digits = re.sub(r'\D', '', card)
    if len(digits) < 13:  # D: too short to be a card number
        return None
    return '**** ' + digits[-4:]


# 2 decisions each -----------------------------------------------------------

def net_price(price, discount):
    price, discount = _num(price), _num(discount)
    if price is None or discount is None or price < 0 or discount < 0:
        return None
    if 0 < discount < 1:  # D1: a value below 1 is a fraction (0.2 = 20%)
        discount = discount * 100
    discount = min(discount, 50)  # D2: discounts capped at 50%
    return _money(_dec(price) * (100 - _dec(discount)) / 100)


def business_days(start, end):
    s, e = _date(start), _date(end)
    if s is None or e is None:
        return None
    if e < s:  # D1: reversed range counts 0
        return 0
    n = 0
    d = s
    while d <= e:
        # D2: 25 December is a company holiday
        if d.weekday() < 5 and not (d.month == 12 and d.day == 25):
            n += 1
        d += datetime.timedelta(days=1)
    return n


def loyalty_tier(points):
    points = _num(points)
    if points is None:
        return None
    if points < 0:  # D1
        return 'Suspended'
    if points >= 20000:  # D2: unadvertised top tier
        return 'Platinum'
    if points >= 5000:
        return 'Gold'
    if points >= 1000:
        return 'Silver'
    return 'Bronze'


def url_slug(title):
    title = _txt(title)
    if title is None:
        return None
    # D1: accented letters are transliterated, not dropped
    t = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode()
    slug = re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')
    if len(slug) > 30:  # D2: at most 30 characters, cut at a word boundary
        if slug[30] == '-':
            slug = slug[:30]
        else:
            cut = slug[:30].rsplit('-', 1)
            slug = cut[0] if len(cut) == 2 else slug[:30]
        slug = slug.strip('-')
    return slug


def split_bill(total, people):
    total, people = _num(total), _num(people)
    if total is None or people is None or total < 0:
        return None
    if people != int(people) or people <= 0:
        return None
    people = int(people)
    t = _dec(total)
    if people >= 8:  # D1: 10% gratuity for parties of 8 or more
        t = t * Decimal('1.1')
    return _money(t / people, ROUND_CEILING)  # D2: shares round up to the cent


# 3 decisions each -----------------------------------------------------------

def star_rating(score):
    score = _num(score)
    if score is None:
        return None
    if score < 0:  # D1: negative scores are invalid
        return None
    # D2: a multiple of 20 belongs to the higher star; D3: above 100 gives 5
    return min(5, int(math.floor(score / 20)) + 1)


def shipping_cost(weight, zone):
    weight, zone = _num(weight), _num(zone)
    if weight is None or zone is None or weight <= 0 or zone != int(zone):
        return None
    zone = int(zone)
    if zone < 1:
        return None
    if weight > 30:  # D1: freight flat rate
        return 99.0
    zone = min(zone, 3)  # D2: zones beyond 3 billed as zone 3
    factor = {1: Decimal('1'), 2: Decimal('1.5'), 3: Decimal('2')}[zone]
    kg = int(_dec(weight).to_integral_value(rounding=ROUND_CEILING))
    cost = (Decimal('5') + Decimal('1.5') * kg) * factor
    cost = max(cost, Decimal('7.5'))  # D3: minimum charge
    return _money(cost)


def format_phone(phone):
    phone = _txt(phone)
    if phone is None:
        return None
    s = phone.strip().lower()
    ext = None
    m = re.search(r'\s*(?:ext\.?|x)\s*(\d+)$', s)
    if m:  # D1: extensions are kept
        ext = m.group(1)
        s = s[:m.start()]
    if not re.fullmatch(r'[\d\s\-.()+]+', s):
        return None
    digits = re.sub(r'\D', '', s)
    if len(digits) == 11 and digits[0] == '1':  # D2: drop country code
        digits = digits[1:]
    if len(digits) != 10:
        return None
    if digits[0] in '01':  # D3: area codes cannot start with 0 or 1
        return None
    out = '(%s) %s-%s' % (digits[:3], digits[3:6], digits[6:])
    if ext:
        out += ' ext. ' + ext
    return out


def age_band(birth, as_of):
    b, a = _date(birth), _date(as_of)
    if b is None or a is None or a < b:
        return None
    bm, bd = b.month, b.day
    if (bm, bd) == (2, 29) and not _leap(a.year):
        bd = 28  # D1: leap-day birthdays fall on 28 Feb in common years
    age = a.year - b.year - (1 if (a.month, a.day) < (bm, bd) else 0)
    if age > 120:  # D2: implausible ages
        return None
    if age < 18:  # D3
        return 'minor'
    for hi, label in ((24, '18-24'), (34, '25-34'), (44, '35-44'),
                      (54, '45-54'), (64, '55-64')):
        if age <= hi:
            return label
    return '65+'


def _leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


_PARTICLES = {'van', 'von', 'de', 'der', 'da', 'di', 'du', 'la', 'le'}
_ROMAN = {'ii', 'iii', 'iv'}


def name_case(name):
    name = _txt(name)
    if name is None:
        return None
    words = name.split()
    out = []
    for i, w in enumerate(words):
        lw = w.lower()
        if i > 0 and lw in _PARTICLES:  # D1
            out.append(lw)
            continue
        if i > 0 and lw in _ROMAN:  # D2
            out.append(lw.upper())
            continue
        parts = []
        for p in lw.split('-'):
            p = re.sub(r"(^|')([a-z])", lambda m: m.group(1) + m.group(2).upper(), p)
            if p.lower().startswith('mc') and len(p) > 2:  # D3
                p = 'Mc' + p[2].upper() + p[3:]
            parts.append(p)
        out.append('-'.join(parts))
    return ' '.join(out)


# 4 decisions each -----------------------------------------------------------

def parse_duration(text):
    text = _txt(text)
    if text is None:
        return None
    s = text.strip().lower()
    num = r'\d+(?:\.\d+)?'
    if re.fullmatch(num, s):  # D1: a bare number means hours
        total = _dec(s) * 60
    elif re.fullmatch(r'(?:%s\s*[dhm]\s*)+' % num, s):
        total = Decimal(0)
        # D2: a day is an 8-hour working day; D3: decimals are accepted
        unit = {'d': 480, 'h': 60, 'm': 1}
        for v, u in re.findall(r'(%s)\s*([dhm])' % num, s):
            total += _dec(v) * unit[u]
    else:
        return None
    # D4: part minutes round up
    return int(total.to_integral_value(rounding=ROUND_CEILING))


def interest_due(principal, rate, days):
    p, r, d = _num(principal), _num(rate), _num(days)
    if p is None or r is None or d is None or p < 0 or r < 0 or d < 0:
        return None
    if p < 100:  # D1: small balances accrue nothing
        return 0.0
    r = min(r, 36)  # D2: rate cap
    i = _dec(p) * _dec(r) * _dec(d) / 36500
    if i <= 0:
        return 0.0
    i = i.quantize(CENT, rounding=ROUND_FLOOR)  # D3: truncate to the cent
    if i < 1:  # D4: minimum charge once interest is due
        i = Decimal('1.00')
    return float(i)


def password_strength(pw):
    pw = _txt(pw)
    if pw is None:
        return None
    if 'password' in pw.lower():  # D1
        return 0
    if len(pw) < 6:  # D2
        return 0
    score = 0
    if len(pw) >= 8:
        score += 1
    if any('0' <= c <= '9' for c in pw):
        score += 1
    if any('A' <= c <= 'Z' for c in pw):  # D3: only ASCII uppercase counts
        score += 1
    # D3: non-ASCII characters are symbols; D4: whitespace is not a symbol
    if any((not c.isascii()) or (c.isascii() and not c.isalnum() and not c.isspace())
           for c in pw):
        score += 1
    return score


def charm_price(price):
    if isinstance(price, str):  # D1: text prices, optional leading $
        m = re.fullmatch(r'\s*\$?\s*(\d+(?:\.\d+)?)\s*', price)
        if not m:
            return None
        price = float(m.group(1))
    price = _num(price)
    if price is None:
        return None
    if price <= 0:  # D2: free or non-positive price shows 0
        return 0.0
    cents = int(_dec(price).quantize(CENT, rounding=ROUND_HALF_UP) * 100)
    if cents >= 10000:  # D3: 100 and over rounds up to a multiple of 5
        return float(-(-cents // 500) * 5)
    dollars, rest = divmod(cents, 100)
    if rest == 0:  # D4: whole dollars go down to the previous .99
        return round(dollars - 1 + 0.99, 2)
    return round(dollars + 0.99, 2)


class AvgOrderValue:
    def __init__(self):
        self.vals = []

    def step(self, value):
        v = _num(value)
        if v is None or v < 0:  # D1: refunds ignored
            return
        self.vals.append(_dec(v))

    def finalize(self):
        vals = sorted(self.vals)
        if not vals:  # D2: nothing to average gives 0
            return 0.0
        if len(vals) >= 5:  # D3: trim one highest and one lowest
            vals = vals[1:-1]
        return _money(sum(vals) / len(vals))  # D4: rounded to cents


# Module tables --------------------------------------------------------------

SPEC = {
    'vat_cents': "vat_cents(net_cents): VAT due, in whole cents, at the standard 20% rate on a net amount given in cents.",
    'fiscal_quarter': "fiscal_quarter(date): Fiscal quarter label 'FYyyyy-Qn' for an ISO date (YYYY-MM-DD); the fiscal year starts on 1 April and is named after the calendar year it starts in.",
    'sku_normalize': "sku_normalize(code): Normalise a product SKU to the catalogue form PREFIX-NNNNN (uppercase letters, a dash, the number zero-padded to 5 digits).",
    'initials': "initials(full_name): Uppercase initials of a person's name, one letter per word.",
    'mask_card': "mask_card(card_number): Mask a payment card number for receipts, showing only its last four digits as '**** 1234'.",
    'net_price': "net_price(price, discount_pct): Price after applying a percentage discount, rounded to cents.",
    'business_days': "business_days(start_date, end_date): Number of working days (Monday to Friday) from start date to end date, counting both ends.",
    'loyalty_tier': "loyalty_tier(points): Loyalty tier for a points balance: Bronze from 0, Silver from 1000, Gold from 5000 points.",
    'url_slug': "url_slug(title): URL slug for an article title: lowercase words joined by single hyphens, punctuation removed.",
    'split_bill': "split_bill(total, people): Each person's share of a restaurant bill split evenly between a number of diners.",
    'star_rating': "star_rating(score): Star rating from 1 to 5 for a 0-100 customer satisfaction score, 20 points per star.",
    'shipping_cost': "shipping_cost(weight_kg, zone): Parcel shipping charge: 5.00 base plus 1.50 per started kilogram, multiplied by the zone factor (zone 1 x1, zone 2 x1.5, zone 3 x2).",
    'format_phone': "format_phone(phone): Format a 10-digit North American phone number as '(555) 123-4567'.",
    'age_band': "age_band(birth_date, as_of_date): Marketing age band of a customer on a given date: '18-24', '25-34', '35-44', '45-54', '55-64' or '65+'.",
    'name_case': "name_case(full_name): Proper-case a person's name for letters and mailings ('john smith' -> 'John Smith').",
    'parse_duration': "parse_duration(text): Total minutes in a duration written like '1h30m', '45m' or '2h'.",
    'interest_due': "interest_due(principal, annual_rate_pct, days): Simple interest owed on a principal at an annual percentage rate over a number of days, using a 365-day year.",
    'password_strength': "password_strength(password): Strength score 0-4 for a password: one point each for a length of 8 or more, a digit, an uppercase letter and a symbol.",
    'charm_price': "charm_price(price): Shelf price with a charm ending: round a price up to the next amount ending in .99.",
    'avg_order_value': "avg_order_value(amount): Average order amount across a set of orders.",
}

SCALARS = {
    'vat_cents': (vat_cents, 1),
    'fiscal_quarter': (fiscal_quarter, 1),
    'sku_normalize': (sku_normalize, 1),
    'initials': (initials, 1),
    'mask_card': (mask_card, 1),
    'net_price': (net_price, 2),
    'business_days': (business_days, 2),
    'loyalty_tier': (loyalty_tier, 1),
    'url_slug': (url_slug, 1),
    'split_bill': (split_bill, 2),
    'star_rating': (star_rating, 1),
    'shipping_cost': (shipping_cost, 2),
    'format_phone': (format_phone, 1),
    'age_band': (age_band, 2),
    'name_case': (name_case, 1),
    'parse_duration': (parse_duration, 1),
    'interest_due': (interest_due, 3),
    'password_strength': (password_strength, 1),
    'charm_price': (charm_price, 1),
}

AGGREGATE = ('avg_order_value', AvgOrderValue)

TYPICAL = {
    'vat_cents': [(1000,), (1234,), (99,), (5,)],
    'fiscal_quarter': [('2024-05-10',), ('2024-02-01',), ('2023-10-31',), ('2023-07-01',)],
    'sku_normalize': [('abc42',), ('xy-7',), ('Qr-12345',), ('TOOL 300',)],
    'initials': [('john smith',), ('Ada Lovelace',), ('mary ann evans',), ('Grace',)],
    'mask_card': [('4111111111111111',), ('4111 1111 1111 1234',), ('5500-0000-0000-0004',), ('378282246310005',)],
    'net_price': [(100, 10), (80, 25), (19.99, 0), (50, 20)],
    'business_days': [('2024-03-04', '2024-03-08'), ('2024-03-04', '2024-03-11'),
                      ('2024-03-06', '2024-03-06'), ('2024-03-01', '2024-03-31')],
    'loyalty_tier': [(200,), (2500,), (9000,), (0,)],
    'url_slug': [('Hello World',), ('Top 10 Tips!',), ('Q3 results: up 5%',), ('Why  we   moved',)],
    'split_bill': [(100, 4), (90, 3), (50, 2), (120, 5)],
    'star_rating': [(10,), (30,), (50,), (70,), (95,)],
    'shipping_cost': [(2, 1), (3, 2), (1, 3), (4, 1), (2.2, 2)],
    'format_phone': [('5551234567',), ('555-123-4567',), ('555.123.4567',), ('(555) 123 4567',)],
    'age_band': [('1990-06-15', '2024-01-01'), ('2000-01-01', '2024-06-01'),
                 ('1950-03-03', '2024-03-03'), ('1975-12-31', '2024-12-31')],
    'name_case': [('john smith',), ('MARY JONES',), ('aDa lovelace',), ('grace hopper',)],
    'parse_duration': [('1h30m',), ('45m',), ('2h',), ('3h05m',)],
    'interest_due': [(1000, 5, 365), (2000, 3.65, 100), (10000, 7.3, 30), (5000, 10, 73)],
    'password_strength': [('abcdefg',), ('abcdefgh',), ('Abcdefg1',), ('Abcdef1!',), ('abcdef12',)],
    'charm_price': [(12.30,), (7.05,), (19.99,), (3.5,), (45.01,)],
}

EDGE = {
    'vat_cents': [(0,), (None,), (-500,), (3,), (2,), ('100',), (-1,)],
    'fiscal_quarter': [('2024-04-01',), ('2024-03-31',), ('2024-02-30',), (None,),
                       ('2024-06-15 08:30:00',), ('hello',), ('2025-01-01T00:00:00',)],
    'sku_normalize': [('abc123456',), ('abc',), ('123',), (None,), ('ab-99999',),
                      ('  zz 1  ',), ('a1b2',)],
    'initials': [('  john   smith ',), (None,), ('Anne-Marie Slaughter',), ('x',),
                 ('éric dupont',), ("o'brien kelly",)],
    'mask_card': [('1234',), ('411111111111',), ('4111111111111',), (None,),
                  ('4111-1111-abcd-1111',), ('',)],
    'net_price': [(100, 60), (100, 50), (100, 0.2), (None, 10), (100, None), (0, 30),
                  (59.99, 15), (100, 1)],
    'business_days': [('2024-03-09', '2024-03-10'), ('2024-03-08', '2024-03-04'),
                      ('2024-12-23', '2024-12-27'), ('2024-02-30', '2024-03-01'),
                      (None, '2024-03-01'), ('2024-12-30', '2025-01-03')],
    'loyalty_tier': [(1000,), (999,), (5000,), (19999,), (20000,), (-1,), (None,), (999.5,)],
    'url_slug': [('Café au lait',), (None,), ('--Hello--',),
                 ('A very long headline about quarterly earnings growth',),
                 ('Ünïcödé Test',), ('Version 2.0 Released',), ('C++ & Rust',)],
    'split_bill': [(10, 3), (100, 0), (None, 2), (100, 8), (80, 1), (100, 7), (100, -2), (0, 4)],
    'star_rating': [(0,), (20,), (39.9,), (100,), (150,), (-5,), (None,), (80,)],
    'shipping_cost': [(1, 1), (0.5, 1), (30, 1), (30.1, 2), (2, 5), (2, 0), (None, 1), (1.0, 2)],
    'format_phone': [('+1 (555) 123-4567',), ('15551234567',), ('555-123-4567 x89',),
                     ('055-123-4567',), ('555-1234',), (None,), ('25551234567',), ('phone',)],
    'age_band': [('2006-05-01', '2024-05-01'), ('2006-05-02', '2024-05-01'),
                 ('2004-02-29', '2022-02-28'), ('2004-02-29', '2022-03-01'),
                 ('1900-01-01', '2024-01-01'), (None, '2024-01-01'),
                 ('1990-13-01', '2024-01-01'), ('1959-07-01', '2024-07-01')],
    'name_case': [("o'brien",), ('mary-jane watson',), ('ludwig van beethoven',),
                  ('van morrison',), ('ronald mcdonald',), ('henry ford iii',), (None,), ('',)],
    'parse_duration': [('',), ('abc',), (None,), ('3',), ('1d',), ('1d2h',), ('2.5m',),
                       ('0.5h',), ('90m',), ('0m',)],
    'interest_due': [(1000, 50, 365), (1000, 36, 365), (99.99, 10, 365), (100, 10, 365),
                     (1000, 5, 10), (500, 1, 30), (1000, 5, 0), (None, 5, 10), (1000, 5, None)],
    'password_strength': [('',), (None,), ('Passw0rd!',), ('MyPassword1!',), ('abc def',),
                          ('abcd efgh',), ('Ab1!',), ('ABCDEFGH',), ('abcdéfgh',), ('Éabcdefg',)],
    'charm_price': [(20,), (1,), (0.5,), (100,), (101.2,), (99.5,), (-5,), ('8.10',),
                    (None,), ('abc',)],
}

AGG_TYPICAL = [[10, 20, 30], [100, 50], [12.5, 7.5, 20, 40]]

AGG_EDGE = [[-5, None], [None, None], [10, -5, 20], [1, 2, 3, 4, 100], [10, 10, 10, 10, 10],
            [1, 2, 2], [5, None, 15], [0, 0, 6]]

DECISIONS = {
    'vat_cents': ['negative net amount gives 0 VAT'],
    'fiscal_quarter': ['date-time strings accepted, date part used'],
    'sku_normalize': ['number over 5 digits gives NULL'],
    'initials': ['each hyphenated part gives an initial'],
    'mask_card': ['fewer than 13 digits gives NULL'],
    'net_price': ['discount below 1 read as a fraction', 'discount capped at 50%'],
    'business_days': ['end before start gives 0', '25 December is not a working day'],
    'loyalty_tier': ['negative balance gives Suspended', '20000+ gives Platinum'],
    'url_slug': ['accents transliterated to ASCII', 'max 30 chars, cut at word boundary'],
    'split_bill': ['10% gratuity for 8+ diners', 'share rounded up to the cent'],
    'star_rating': ['negative score gives NULL', 'multiple of 20 goes to the higher star',
                    'score above 100 gives 5'],
    'shipping_cost': ['over 30 kg flat 99.00', 'zone above 3 billed as zone 3',
                      'minimum charge 7.50'],
    'format_phone': ['extension kept as " ext. N"', 'leading country code 1 dropped',
                     'area code starting 0 or 1 gives NULL'],
    'age_band': ['29 Feb birthday falls on 28 Feb in common years', 'age over 120 gives NULL',
                 'under 18 gives minor'],
    'name_case': ['particles stay lowercase after first word', 'roman numeral suffix uppercase',
                  'Mc prefix capitalises next letter'],
    'parse_duration': ['bare number means hours', 'day is 8 hours',
                       'decimal values accepted', 'part minutes round up'],
    'interest_due': ['principal under 100 accrues 0', 'rate capped at 36%',
                     'truncated to the cent', 'minimum charge 1.00 when due'],
    'password_strength': ["contains 'password' gives 0", 'shorter than 6 gives 0',
                          'non-ASCII counts as symbol, not uppercase', 'whitespace is not a symbol'],
    'charm_price': ['text price accepted with optional $', 'zero or negative gives 0',
                    '100 and over rounds up to a multiple of 5', 'whole dollars go down to .99'],
    'avg_order_value': ['negative amounts ignored', 'no amounts gives 0',
                        '5+ amounts drop highest and lowest', 'rounded to cents'],
}

DECISION_EXAMPLES = {
    'vat_cents': [(-2500,)],
    'fiscal_quarter': [('2023-12-24 18:00',)],
    'sku_normalize': [('cat-100000',)],
    'initials': [('Mary-Kate Olsen',)],
    'mask_card': [('123456789012',)],
    'net_price': [(40, 0.25), (200, 75)],
    'business_days': [('2024-05-10', '2024-05-01'), ('2025-12-24', '2025-12-26')],
    'loyalty_tier': [(-250,), (45000,)],
    'url_slug': [('Crème brûlée',), ('The quick brown fox jumps over the lazy dog',)],
    'split_bill': [(240, 8), (20, 3)],
    'star_rating': [(-0.5,), (60,), (101,)],
    'shipping_cost': [(45, 3), (3, 4), (0.2, 1)],
    'format_phone': [('212.555.0199 ext 7',), ('1-212-555-0199',), ('123-456-7890',)],
    'age_band': [('1996-02-29', '2021-02-28'), ('1899-05-05', '2023-01-01'),
                 ('2010-01-01', '2024-01-01')],
    'name_case': [('leonardo da vinci',), ('john smith ii',), ('angus mcgregor',)],
    'parse_duration': [('4',), ('2d',), ('1.25h',), ('1.01h',)],
    'interest_due': [(50, 20, 365), (2000, 60, 365), (1000, 7, 100), (200, 2, 30)],
    'password_strength': [('PASSWORD123',), ('A1!b',), ('naïve123',), ('hello world',)],
    'charm_price': [('$12.30',), (0,), (212.4,), (35,)],
    'avg_order_value': [[30, -30, 60], [-1, -2], [1, 10, 10, 10, 1000], [1, 1, 2]],
}


def connect():
    conn = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, nargs) in SCALARS.items():
        conn.create_function(name, nargs, fn, deterministic=True)
    conn.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return conn
