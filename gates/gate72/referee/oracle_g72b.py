import sqlite3, math, re, datetime, unicodedata


def _num(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        v = float(x)
    elif isinstance(x, str):
        s = x.strip()
        if '_' in s:
            return None
        try:
            v = float(s)
        except ValueError:
            return None
    else:
        return None
    return v if math.isfinite(v) else None


def late_fee(balance, days_overdue):
    b, d = _num(balance), _num(days_overdue)
    if b is None or d is None:
        return None
    if b <= 0 or d <= 5:
        return 0.0
    fee = b * math.ceil(d / 30) / 100.0
    fee = max(fee, 5.0)
    fee = min(fee, 250.0)
    return round(fee, 2)


def ship_cost(weight_kg, zone):
    w = _num(weight_kg)
    if w is None or zone is None:
        return None
    mult = {'A': 1.0, 'B': 1.5}.get(str(zone), 2.5)
    wr = math.ceil(max(w, 0.0) * 2) / 2.0
    cost = (4.0 + 2.0 * wr) * mult
    if w > 30:
        cost += 15.0
    return round(cost, 2)


def mask_card(card_number):
    if card_number is None:
        return None
    s = str(card_number)
    total = sum(c.isdigit() for c in s)
    if total < 12:
        return None
    out, seen = [], 0
    for c in s:
        if c.isdigit():
            seen += 1
            out.append(c if seen > total - 4 else '*')
        else:
            out.append(c)
    return ''.join(out)


def age_band(age):
    if age is None:
        return None
    n = _num(age)
    if n is None or n < 0 or n > 120:
        return 'invalid'
    if n < 18:
        return 'minor'
    if n < 67:
        return 'adult'
    return 'senior'


def slug(title):
    if title is None:
        return None
    s = unicodedata.normalize('NFKD', str(title))
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    s = s[:40].rstrip('-')
    return s if s else 'untitled'


_HOLIDAYS = {(12, 25), (1, 1)}


def add_workdays(start_date, days):
    if not isinstance(start_date, str):
        return None
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', start_date):
        return None
    n = _num(days)
    if n is None:
        return None
    try:
        cur = datetime.date.fromisoformat(start_date)
        n = max(-250, min(250, int(n)))
        while cur.weekday() >= 5:
            cur += datetime.timedelta(days=1)
        step = datetime.timedelta(days=1 if n >= 0 else -1)
        for _ in range(abs(n)):
            cur += step
            while cur.weekday() >= 5 or (cur.month, cur.day) in _HOLIDAYS:
                cur += step
        return cur.isoformat()
    except (ValueError, OverflowError):
        return None


def blended_rating(avg_stars, votes):
    a, v = _num(avg_stars), _num(votes)
    if a is None or v is None:
        return None
    v = int(v)
    if v < 5:
        return None
    v = min(v, 500)
    a = min(max(a, 1.0), 5.0)
    return round((v * a + 35.0) / (v + 10.0), 2)


def initials(full_name):
    if full_name is None:
        return None
    return ''.join(w[0].upper() for w in str(full_name).split()[:3])


def meeting_slots(minutes):
    n = _num(minutes)
    if n is None:
        return None
    if n <= 5:
        return 0
    return min(int(math.ceil(n / 30)), 16)


class AvgOrderValue:
    def __init__(self):
        self.total = 0.0
        self.count = 0

    def step(self, value):
        n = _num(value)
        if n is None or n <= 0:
            return
        self.total += n
        self.count += 1

    def finalize(self):
        if self.count == 0:
            return None
        return round(self.total / self.count, 2)


SPEC = {
    'late_fee': 'late_fee(balance, days_overdue): Late fee charged on an overdue invoice balance, in currency units.',
    'ship_cost': 'ship_cost(weight_kg, zone): Shipping charge for a parcel of the given weight to a delivery zone (A, B or C).',
    'mask_card': 'mask_card(card_number): Masks a payment card number for display on receipts.',
    'age_band': "age_band(age): Classifies a customer's age in years into a marketing band.",
    'slug': 'slug(title): Turns a page or product title into a URL-friendly slug.',
    'add_workdays': 'add_workdays(start_date, days): Adds working days to an ISO date (YYYY-MM-DD) for delivery and SLA due dates.',
    'blended_rating': "blended_rating(avg_stars, votes): Combines a product's average star rating and vote count into a fair ranking score.",
    'initials': "initials(full_name): Builds an initials badge from a person's full name.",
    'meeting_slots': 'meeting_slots(minutes): Number of half-hour calendar slots to reserve for a meeting of the given length.',
    'avg_order_value': 'avg_order_value(amount): Aggregate giving the average order value for a group of orders.',
}

SCALARS = {
    'late_fee': (late_fee, 2),
    'ship_cost': (ship_cost, 2),
    'mask_card': (mask_card, 1),
    'age_band': (age_band, 1),
    'slug': (slug, 1),
    'add_workdays': (add_workdays, 2),
    'blended_rating': (blended_rating, 2),
    'initials': (initials, 1),
    'meeting_slots': (meeting_slots, 1),
}

AGGREGATE = ('avg_order_value', AvgOrderValue)

TYPICAL = {
    'late_fee': [(1000, 10), (2000, 45), (1500, 75), (800, 95), (1200.5, 20)],
    'ship_cost': [(2, 'A'), (1, 'B'), (4, 'C'), (6, 'A'), (2.5, 'B')],
    'mask_card': [('4111111111111111',), ('378282246310005',), ('5500000000000004',), (6011111111111117,)],
    'age_band': [(5,), (12,), (30,), (50,), (90,)],
    'slug': [('Hello World',), ('Q3 Sales Report!',), ('  Summer -- Sale 2024  ',), ('New_Product Launch',)],
    'add_workdays': [('2024-03-04', 3), ('2024-03-06', 5), ('2024-05-10', 1), ('2024-03-13', -2), ('2024-02-26', 10)],
    'blended_rating': [(4.5, 90), (3.0, 40), (4.0, 200), (2.5, 15)],
    'initials': [('ada lovelace',), ('John Ronald Tolkien',), ('Cher',), ('maria garcia',)],
    'meeting_slots': [(25,), (45,), (60,), (90,), (100,)],
}

EDGE = {
    'late_fee': [(1000, 5), (1000, 6), (100, 10), (30000, 10), (-500, 40), (0, 20), (1000, 30), (1000, 31), (1000, 0), (None, 10)],
    'ship_cost': [(0.3, 'A'), (30, 'A'), (30.2, 'A'), (1, 'a'), (2, 'Z'), (0, 'B'), (-3, 'B'), (45, 'C'), (1.1, 'B'), (None, 'A')],
    'mask_card': [('4111-1111-1111-1111',), ('4111 1111 1111 1111',), ('12345678901',), ('123456789012',), ('',), ('abcd',), (None,), (4111111111111111,), ('1234 5678 9012 3456 7890',)],
    'age_band': [(17,), (18,), (66,), (67,), (-1,), (121,), (120,), (0,), ('abc',), (17.9,)],
    'slug': [('Café Crème Brûlée',), ('Ünïcödé',), ('!!!',), ('',), ('   ',), ('a' * 50,), ('word ' * 12,), ('Straße 日本語',), ('C++ & C# --- Tips',), (None,)],
    'add_workdays': [('2024-03-02', 1), ('2024-03-03', 0), ('2024-12-24', 1), ('2024-12-31', 1), ('2024-03-04', 1000), ('2024-03-04', -1000), ('2024-13-45', 1), ('not a date', 2), ('2024-03-08', 1), (None, 1)],
    'blended_rating': [(4.0, 4), (4.0, 5), (4.0, 5.9), (5.0, 500), (5.0, 1000), (7, 50), (0.5, 40), (-2, 100), (4.5, None), (3.5, 0)],
    'initials': [('a b c d e',), ('Jean-Luc Picard',), ('',), ('   ',), ('élan vital',), ('J. R. R. Tolkien',), (42,), (None,), ('ADA  LOVELACE',), ('  mary jane watson ',)],
    'meeting_slots': [(0,), (5,), (6,), (-10,), (480,), (481,), (600,), (5.5,), (30,), (None,)],
}

AGG_TYPICAL = [[10, 20, 30], [99.5, 100.5, 200], [15, None, 25, 35]]
AGG_EDGE = [[10, -10, 20], [0, 0, 0], [], [None, None], [-5], [1, 2, 2], [100, '50', 0]]

DECISIONS = {
    'late_fee': ['grace period of days before any fee', 'minimum fee', 'maximum fee cap', 'non-positive balance charges nothing'],
    'ship_cost': ['weight rounded up to half kilo', 'heavy parcel surcharge', 'unknown zone priced as zone C'],
    'mask_card': ['separators kept in place', 'too few digits gives NULL'],
    'age_band': ['senior band starts at 67', 'out-of-range or non-numeric age is invalid'],
    'slug': ['accents transliterated to ASCII', 'length cut at 40 without trailing hyphen', 'empty result becomes untitled'],
    'add_workdays': ['weekend start rolls forward to Monday', 'Dec 25 and Jan 1 are non-working', 'day count clamped to +-250'],
    'blended_rating': ['fewer than 5 votes gives NULL', 'average clamped to 1..5', 'votes capped at 500', 'fractional votes truncated'],
    'initials': ['at most 3 initials'],
    'meeting_slots': ['5 minutes or less needs no slot', 'at most 16 slots'],
    'avg_order_value': ['zero and negative amounts excluded'],
}

DECISION_EXAMPLES = {
    'late_fee': [(1000, 2), (60, 40), (50000, 100), (-20, 15)],
    'ship_cost': [(3.2, 'A'), (31, 'B'), (2, 'X')],
    'mask_card': [('5500-0000-0000-0004',), ('1234567',)],
    'age_band': [(66.9,), (150,)],
    'slug': [('Crème Fraîche',), ('the quick brown fox jumps over the lazy dog again and again',), ('@#$%',)],
    'add_workdays': [('2024-06-09', 2), ('2023-12-22', 2), ('2024-01-02', 300)],
    'blended_rating': [(3.0, 2), (0, 30), (1.0, 100000), (4.0, 10.9)],
    'initials': [('Anna Maria Louise Smith',)],
    'meeting_slots': [(3,), (900,)],
    'avg_order_value': [[40, 0, -20, 60]],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, n) in SCALARS.items():
        con.create_function(name, n, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con
