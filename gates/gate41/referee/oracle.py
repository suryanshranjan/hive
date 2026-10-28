import datetime
import math
import re
import sqlite3


def _num(x):
    if x is None or isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return x if math.isfinite(x) else None
    if isinstance(x, str):
        try:
            v = float(x.strip())
        except ValueError:
            return None
        return v if math.isfinite(v) else None
    return None


# ---------------------------------------------------------------- late_fee
def late_fee(amount, days):
    a, d = _num(amount), _num(days)
    if a is None or d is None:
        return None
    if a <= 0:
        return 0
    blocks = int(math.floor(d)) // 30
    if blocks <= 0:
        return 0
    fee = math.ceil(round(a * 5 * blocks / 100.0, 6))
    fee = max(fee, 500)
    cap = int(math.floor(a * 25 / 100.0))
    return int(min(fee, cap))


# --------------------------------------------------------------- card_mask
def card_mask(card):
    if card is None:
        return None
    if isinstance(card, float):
        if not math.isfinite(card):
            return None
        if card == int(card):
            card = int(card)
    s = str(card)
    digits = ''.join(c for c in s if c in '0123456789')
    n = len(digits)
    if n < 8:
        return '*' * n
    return '*' * (n - 4) + digits[-4:]


# --------------------------------------------------------------- bizday_add
_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def _is_bday(d):
    if d.weekday() >= 5:
        return False
    if (d.month, d.day) in ((1, 1), (12, 25)):
        return False
    return True


def bizday_add(start, n):
    if start is None or not isinstance(start, str):
        return None
    k = _num(n)
    if k is None:
        return None
    s = start.strip()
    if not _DATE_RE.match(s):
        return None
    try:
        d = datetime.date(int(s[:4]), int(s[5:7]), int(s[8:10]))
    except ValueError:
        return None
    k = int(k)
    k = max(-260, min(260, k))
    try:
        while not _is_bday(d):
            d += datetime.timedelta(days=1)
        step = 1 if k > 0 else -1
        for _ in range(abs(k)):
            d += datetime.timedelta(days=step)
            while not _is_bday(d):
                d += datetime.timedelta(days=step)
    except OverflowError:
        return None
    return d.isoformat()


# -------------------------------------------------------------- star_display
def star_display(avg, count):
    a, c = _num(avg), _num(count)
    if a is None or c is None:
        return None
    if c < 3:
        return None
    a = max(0.0, min(5.0, float(a)))
    return math.floor(a * 2 + 0.5) / 2.0


# --------------------------------------------------------------- phone_norm
def phone_norm(raw):
    if raw is None:
        return None
    if isinstance(raw, float):
        if not math.isfinite(raw):
            return None
        if raw == int(raw):
            raw = int(raw)
    s = re.split(r'(?i)ext|x|#', str(raw))[0]
    digits = ''.join(c for c in s if c in '0123456789')
    if len(digits) == 11 and digits[0] == '1':
        digits = digits[1:]
    if len(digits) != 10:
        return None
    return '+1' + digits


# ---------------------------------------------------------------- ship_cost
def ship_cost(weight, zone):
    w, z = _num(weight), _num(zone)
    if w is None or z is None:
        return None
    if w > 25000:
        return None
    zi = max(1, min(4, int(z)))
    steps = max(0, int(math.ceil(w / 500.0)) - 1)
    cost = 300 + 200 * zi + 150 * steps
    if w > 10000:
        cost += 1000
    return cost


# ------------------------------------------------------------ name_initials
_PARTICLES = {'de', 'van', 'von', 'la', 'di', 'da', 'del'}


def name_initials(name):
    if name is None:
        return None
    words = [w for w in str(name).split() if w not in _PARTICLES]
    out = []
    for w in words:
        letter = next((c for c in w if c.isalpha()), None)
        if letter is None:
            continue
        out.append(letter.upper())
        if len(out) == 3:
            break
    return ''.join(out)


# ---------------------------------------------------------------- pct_delta
def pct_delta(old, new):
    o, n = _num(old), _num(new)
    if o is None or n is None:
        return None
    if o == 0:
        return 0.0
    return float(round((n - o) / abs(o) * 100.0, 1))


# --------------------------------------------------------------- title_slug
def title_slug(title):
    if title is None:
        return None
    parts = re.findall(r'[a-z0-9]+', str(title).lower())
    return '-'.join(parts)[:40].rstrip('-')


# ---------------------------------------------------------------- nps_score
class NpsScore:
    def __init__(self):
        self.valid = 0
        self.prom = 0
        self.det = 0

    def step(self, value):
        v = value
        if v is None or isinstance(v, (str, bytes)):
            return
        if not (0 <= v <= 10):
            return
        self.valid += 1
        if v >= 9:
            self.prom += 1
        elif v <= 6:
            self.det += 1

    def finalize(self):
        if self.valid < 5:
            return None
        num = (self.prom - self.det) * 100
        q = (2 * abs(num) + self.valid) // (2 * self.valid)
        return q if num >= 0 else -q


SPEC = {
    'late_fee': 'late_fee(amount_cents, days_late): Late-payment fee, in cents, charged on an overdue invoice.',
    'card_mask': 'card_mask(card_number): Masks a payment card number for display on receipts.',
    'bizday_add': 'bizday_add(start_date, n): Adds a number of business days to an ISO date (YYYY-MM-DD).',
    'star_display': 'star_display(avg_rating, review_count): Star rating shown in the storefront, from the average score and the number of reviews.',
    'phone_norm': 'phone_norm(raw_phone): Normalizes a US phone number to E.164 for the contact database.',
    'ship_cost': 'ship_cost(weight_g, zone): Shipping charge in cents for a parcel of the given weight in grams sent to a delivery zone (1-4).',
    'name_initials': 'name_initials(full_name): Uppercase initials for avatar badges, from a full name.',
    'pct_delta': 'pct_delta(old_value, new_value): Percent change from old to new for dashboards, to one decimal place.',
    'title_slug': 'title_slug(title): URL slug for a page title.',
    'nps_score': 'nps_score(score): Net Promoter Score from a column of 0-10 survey answers.',
}

SCALARS = {
    'late_fee': (late_fee, 2),
    'card_mask': (card_mask, 1),
    'bizday_add': (bizday_add, 2),
    'star_display': (star_display, 2),
    'phone_norm': (phone_norm, 1),
    'ship_cost': (ship_cost, 2),
    'name_initials': (name_initials, 1),
    'pct_delta': (pct_delta, 2),
    'title_slug': (title_slug, 1),
}

AGGREGATE = ('nps_score', NpsScore)

TYPICAL = {
    'late_fee': [(20000, 30), (50000, 60), (100000, 90), (40000, 120)],
    'card_mask': [('4111111111111111',), ('378282246310005',), (5500005555555559,), ('6011000990139424',)],
    'bizday_add': [('2024-03-04', 1), ('2024-03-08', 1), ('2024-03-06', 5), ('2024-03-12', -2), ('2024-03-05', 0)],
    'star_display': [(4.3, 120), (3.8, 40), (2.1, 10), (4.9, 500), (1.6, 25)],
    'phone_norm': [('(415) 555-2671',), ('415-555-2671',), ('1 415 555 2671',), ('+1 (212) 555-0100',)],
    'ship_cost': [(500, 1), (1000, 1), (2500, 2), (5000, 3), (1500, 4)],
    'name_initials': [('john smith',), ('Mary Jane Watson',), ('ada lovelace',), ('grace brewster hopper',)],
    'pct_delta': [(100, 110), (200, 150), (80, 100), (50, 51), (3, 4)],
    'title_slug': [('Hello World',), ('Quarterly Report 2024',), ('Q3 Results: Revenue & Growth',), ('Spring   Sale!!!',)],
}

EDGE = {
    'late_fee': [(20000, 29), (20001, 30), (10000, 150), (10000, 300), (3000, 30),
                 (100, 60), (0, 90), (-5000, 60), (20000, -30), (20000, None)],
    'card_mask': [('4111 1111 1111 1111',), ('4111-1111-1111-1111',), ('12345678',), ('1234567',),
                  ('',), ('abc',), (4111111111111111,), (None,)],
    'bizday_add': [('2024-03-09', 0), ('2024-03-10', 1), ('2024-12-24', 1), ('2024-12-31', 1),
                   ('2025-01-01', 0), ('2024-03-04', 300), ('2024-03-04', -300), ('2024-02-30', 1),
                   ('2024-02-28', 1), ('hello', 1)],
    'star_display': [(4.25, 50), (4.75, 50), (3.0, 2), (3.0, 3), (5.7, 100),
                     (-1.0, 100), (0.2, 10), (4.3, None), (4.3, 2.5)],
    'phone_norm': [('415-555-2671 x123',), ('415.555.2671 ext. 55',), ('555-2671',), ('4155552671',),
                   (4155552671,), ('',), ('call me',), ('+44 20 7946 0958',), ('2 415 555 2671',),
                   ('415-555-2671#9',)],
    'ship_cost': [(501, 1), (10000, 1), (10001, 1), (25000, 2), (25001, 2),
                  (1000, 0), (1000, 9), (0, 2), (-100, 2), (1000, None)],
    'name_initials': [('Ludwig van Beethoven',), ('Jean Claude Van Damme',), ('a b c d e',), ('',),
                      ('   ',), ('madonna',), ("o'brien",), ('Anne-Marie Smith',), ('de la cruz',),
                      ('de la',)],
    'pct_delta': [(0, 50), (0, 0), (-100, -50), (100, 100), (7, 8), (3, 2),
                  (100, None), ('abc', 5), (1000000, 1000001), (-50, 50)],
    'title_slug': [('The Complete Guide to Choosing a Reliable Business Laptop',),
                   ('abcdefghijklmnopqrstuvwxyz0123456789abcd',), ('abcdefghijklmnopqrstuvwxyz0123456789abc de',),
                   ('',), ('!!!',), ('  Leading and trailing  ',), (2024,), ('Tabs\tand\nnewlines',)],
}

AGG_TYPICAL = [
    [10, 9, 9, 8, 7, 6, 3, 10, 9, 5, None],
    [9, 10, 9, 9, 10, 10],
    [3, 4, 5, 6, 7, 8, 9, 2, 10, 1],
]

AGG_EDGE = [
    [9, 9, 9, 9],
    [9, 8, 8, 8, 8, 8, 8, 8],
    [6, 8, 8, 8, 8, 8, 8, 8],
    [11, 9, 9, 9, 9, 9, -1, 10.5],
    [9.5, 9, 10, 8.5, 6.5, 7, 7],
    [None, None, None],
    [10, 9, 'x', 0, 3, None, 7, 9],
    [0, 10, 5, 5, 5],
]

DECISIONS = {
    'late_fee': ['only full 30-day blocks count', 'fractional cents round up', 'fee capped at 25% of amount', 'minimum fee 500 once any fee applies'],
    'card_mask': ['separators removed from output', 'fewer than 8 digits fully masked'],
    'bizday_add': ['weekend start rolls forward to next business day before counting', 'Jan 1 and Dec 25 are not business days', 'n clamped to +/-260'],
    'star_display': ['half-star ties round up', 'fewer than 3 reviews gives NULL', 'average clamped to 0..5'],
    'phone_norm': ['extension discarded', 'wrong digit count gives NULL'],
    'ship_cost': ['partial 500g steps charged in full', 'over 10000g adds 1000 surcharge', 'over 25000g gives NULL', 'zone clamped into 1..4'],
    'name_initials': ['at most 3 initials', 'lowercase particles skipped'],
    'pct_delta': ['zero base gives 0.0'],
    'title_slug': ['slug cut at 40 chars, trailing hyphen stripped'],
    'nps_score': ['out-of-range scores ignored', 'fewer than 5 valid answers gives NULL', 'rounding half away from zero'],
}

DECISION_EXAMPLES = {
    'late_fee': [(30000, 45), (20010, 30), (20000, 180), (4000, 30)],
    'card_mask': [('5500-0055-5555-5559',), ('123456',)],
    'bizday_add': [('2024-06-15', 2), ('2024-12-23', 3), ('2024-01-15', 1000)],
    'star_display': [(3.75, 80), (4.5, 1), (7.2, 40)],
    'phone_norm': [('212-555-0100 x9',), ('12345',)],
    'ship_cost': [(1200, 2), (12000, 3), (30000, 3), (500, 6)],
    'name_initials': [('Leonardo da Vinci',), ('Mary Ann Elizabeth Jones',)],
    'pct_delta': [(0, -12)],
    'title_slug': [('The Complete Guide to Choosing a Reliable Business Laptop for Your Team',)],
    'nps_score': [[10, 10, 10, 10, 10, 15, -3], [10, 10, 10], [9, 9, 9, 8, 8, 8, 8, 8]],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, nargs) in SCALARS.items():
        con.create_function(name, nargs, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con
