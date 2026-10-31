import math
import re
import sqlite3
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN


def _num(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    if isinstance(x, float) and not math.isfinite(x):
        return None
    return x


def _dec(x):
    return Decimal(repr(x)) if isinstance(x, float) else Decimal(x)


def _cents(d, mode=ROUND_HALF_UP):
    return d.quantize(Decimal('0.01'), rounding=mode)


# 1. late_fee -------------------------------------------------------------
def late_fee(amount, days_late):
    amount, days_late = _num(amount), _num(days_late)
    if amount is None or days_late is None:
        return None
    if amount <= 0 or days_late <= 3:
        return 0.0
    a = _dec(amount)
    fee = a * Decimal('0.005') * _dec(days_late)
    fee = min(fee, a * Decimal('0.25'))
    fee = _cents(fee)
    if fee < Decimal('2.50'):
        fee = Decimal('2.50')
    return float(fee)


# 2. ship_cost ------------------------------------------------------------
_ZONES = {'A': Decimal('1.0'), 'B': Decimal('1.5'), 'C': Decimal('2.2')}


def ship_cost(weight_kg, zone):
    w = _num(weight_kg)
    if w is None or not isinstance(zone, str) or w <= 0:
        return None
    kg = math.ceil(w)
    mult = _ZONES.get(zone.strip().upper(), _ZONES['C'])
    cost = (Decimal('4.90') + Decimal('1.20') * kg) * mult
    if kg > 30:
        cost += Decimal('15')
    return float(_cents(cost))


# 3. bayes_rating ---------------------------------------------------------
def bayes_rating(avg, votes):
    avg, votes = _num(avg), _num(votes)
    if avg is None or votes is None:
        return None
    avg = min(max(avg, 1), 5)
    votes = max(votes, 0)
    r = (votes * avg + 10 * 3.5) / (votes + 10)
    return float(_cents(Decimal(repr(float(r)))))


# 4. sku_check ------------------------------------------------------------
def sku_check(code):
    if isinstance(code, bool) or code is None:
        return None
    if isinstance(code, int):
        if code < 0:
            return None
        code = str(code)
    if not isinstance(code, str):
        return None
    s = code.replace(' ', '').replace('-', '')
    if not s or not re.fullmatch(r'[0-9]+', s) or len(s) > 12:
        return None
    total = 0
    for i, ch in enumerate(reversed(s)):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return s + str((10 - total % 10) % 10)


# 5. workdays_between -----------------------------------------------------
def _parse(s):
    if not isinstance(s, str):
        return None
    m = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})', s.strip())
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def workdays_between(start, end):
    a, b = _parse(start), _parse(end)
    if a is None or b is None:
        return None
    if b <= a:
        return 0
    n = (b - a).days
    count = (n // 7) * 5
    d = a + timedelta(days=(n // 7) * 7)
    while d < b:
        if d.weekday() < 5:
            count += 1
        d += timedelta(days=1)
    for y in range(a.year, b.year + 1):
        for h in (date(y, 1, 1), date(y, 12, 25)):
            if a <= h < b and h.weekday() < 5:
                count -= 1
    return count


# 6. mask_email -----------------------------------------------------------
def mask_email(email):
    if not isinstance(email, str) or email.count('@') != 1:
        return None
    local, domain = email.split('@')
    if not local or not domain:
        return None
    if len(local) <= 2:
        return '*' * len(local) + '@' + domain
    return local[0] + '*' * (len(local) - 2) + local[-1] + '@' + domain


# 7. pro_rata -------------------------------------------------------------
def pro_rata(amount, days_used, days_in_period):
    amount, du, p = _num(amount), _num(days_used), _num(days_in_period)
    if amount is None or du is None or p is None:
        return None
    if p <= 0:
        return 0.0
    du = min(max(du, 0), p)
    v = _dec(amount) * _dec(du) / _dec(p)
    return float(_cents(v, ROUND_DOWN))


# 8. time_slot ------------------------------------------------------------
def time_slot(minutes):
    m = _num(minutes)
    if m is None:
        return None
    if m <= 0:
        return 0
    return min(math.ceil(m / 15) * 15, 480)


# 9. initials -------------------------------------------------------------
def initials(name):
    if not isinstance(name, str):
        return None
    words = name.split()
    if not words:
        return None
    return ''.join(w[0].upper() for w in words[:3])


# Aggregate ---------------------------------------------------------------
class CleanAvg:
    def __init__(self):
        self.total = Decimal(0)
        self.n = 0

    def step(self, value):
        v = _num(value)
        if v is None or v < 0 or v > 10000:
            return
        self.total += _dec(v)
        self.n += 1

    def finalize(self):
        if self.n == 0:
            return 0.0
        return float(_cents(self.total / self.n))


SPEC = {
    'late_fee': 'late_fee(amount, days_late): penalty charged on an overdue invoice amount, based on how many days it is late.',
    'ship_cost': 'ship_cost(weight_kg, zone): shipping charge for a parcel of the given weight sent to a delivery zone (A, B or C).',
    'bayes_rating': 'bayes_rating(avg, votes): star rating for a product that is adjusted for how many votes back the average.',
    'sku_check': 'sku_check(code): returns a numeric product code with its mod-10 (Luhn) check digit appended.',
    'workdays_between': 'workdays_between(start, end): number of working days between two ISO dates (YYYY-MM-DD).',
    'mask_email': 'mask_email(email): hides most of an email address\'s name part so it can be shown in reports.',
    'pro_rata': 'pro_rata(amount, days_used, days_in_period): share of a periodic charge owed for the days a service was used.',
    'time_slot': 'time_slot(minutes): billable length of a meeting or booking, in minutes, rounded to the scheduling grid.',
    'initials': 'initials(name): uppercase initials of a person\'s full name for avatars and badges.',
    'clean_avg': 'clean_avg(amount): average order amount over a set of rows, for dashboards.',
}

SCALARS = {
    'late_fee': (late_fee, 2),
    'ship_cost': (ship_cost, 2),
    'bayes_rating': (bayes_rating, 2),
    'sku_check': (sku_check, 1),
    'workdays_between': (workdays_between, 2),
    'mask_email': (mask_email, 1),
    'pro_rata': (pro_rata, 3),
    'time_slot': (time_slot, 1),
    'initials': (initials, 1),
}

AGGREGATE = ('clean_avg', CleanAvg)

TYPICAL = {
    'late_fee': [(1000, 10), (400, 20), (2000, 30), (850.5, 12), (1200, 8)],
    'ship_cost': [(2, 'A'), (5, 'B'), (10, 'C'), (1, 'A'), (4, 'B')],
    'bayes_rating': [(4.5, 90), (5, 10), (2, 40), (4.0, 15)],
    'sku_check': [('7992739871',), ('4539',), ('123456',), ('0123',), (555,)],
    'workdays_between': [('2024-03-04', '2024-03-11'), ('2024-03-01', '2024-03-04'),
                         ('2024-05-06', '2024-05-10'), ('2024-06-03', '2024-06-28')],
    'mask_email': [('john.smith@example.com',), ('anna@x.org',), ('bob@mail.net',), ('christopher@corp.io',)],
    'pro_rata': [(300, 10, 30), (1200, 15, 30), (90, 1, 3), (500, 20, 25)],
    'time_slot': [(20,), (45,), (50,), (100,), (7,)],
    'initials': [('john smith',), ('Mary Jane Watson',), ('ada lovelace',), ('Plato',)],
}

EDGE = {
    'late_fee': [(1001, 5), (1000, 100), (100, 4), (1000, 3), (1000, 0), (-500, 20), (None, 10), (1000, None), (10, 50)],
    'ship_cost': [(0.5, 'A'), (30, 'A'), (30.5, 'B'), (50, 'C'), (3, 'X'), (3, 'b'), (0, 'A'), (3, None), (-2, 'A')],
    'bayes_rating': [(7, 50), (0, 50), (4, -5), (4, 0), (None, 5), (3, None), (5, 1000000), (3.5, 10)],
    'sku_check': [('1234-5678',), ('12 34 56',), ('12ab34',), ('1234567890123',), ('123456789012',), ('',), (None,), (-5,), (1.5,)],
    'workdays_between': [('2024-12-23', '2024-12-27'), ('2024-12-31', '2025-01-02'), ('2024-03-11', '2024-03-04'),
                         ('2024-03-04', '2024-03-04'), ('2024-02-30', '2024-03-04'), (None, '2024-03-04'),
                         ('2022-12-24', '2022-12-27'), ('2024-01-01', '2024-01-03'), ('garbage', '2024-01-01')],
    'mask_email': [('ab@x.com',), ('a@x.com',), ('plainstring',), ('a@b@c.com',), ('@x.com',), ('x@',), (None,), ('abc@x.com',)],
    'pro_rata': [(100, 2, 3), (300, 45, 30), (300, -5, 30), (300, 5, 0), (None, 5, 30), (300, 30, 30),
                 (300, 0, 30), (300, 5, -30), (-100, 1, 3)],
    'time_slot': [(480,), (481,), (1000,), (0,), (-5,), (14.5,), (465.1,), (None,), (15,)],
    'initials': [('one two three four',), ('  lee   wong ',), ('',), (None,), (123,), ('élan vital',), ("o'brien",), ('Jean-Luc Picard',)],
}

AGG_TYPICAL = [[100, 200, 300], [10.5, 20.5], [50, None, 150], [80, 120, 100, 100]]
AGG_EDGE = [[-50, 100, 300], [10000, 10001, 50], [0.02, 0.03], [-5, -10], [None, None], [0, 0, 3]]

DECISIONS = {
    'late_fee': ['no fee within 3-day grace', 'fee capped at 25% of amount', 'fee floored at 2.50 minimum', 'half-up cent rounding'],
    'ship_cost': ['weight rounded up to whole kg', 'unknown zone billed as C', 'surcharge 15 above 30 kg'],
    'bayes_rating': ['avg clamped to 1..5', 'negative votes treated as 0'],
    'sku_check': ['spaces and dashes ignored', 'other characters give NULL', 'more than 12 digits give NULL'],
    'workdays_between': ['Jan 1 and Dec 25 are holidays', 'reversed range gives 0'],
    'mask_email': ['name part of 2 chars or fewer fully masked', 'not exactly one @ with both sides gives NULL'],
    'pro_rata': ['days clamped to 0..period', 'non-positive period gives 0.0', 'rounded down to cents'],
    'time_slot': ['capped at 480 minutes'],
    'initials': ['at most 3 initials'],
    'clean_avg': ['negative values excluded', 'values above 10000 excluded', 'no qualifying values gives 0.0', 'half-up 2 decimal rounding'],
}

DECISION_EXAMPLES = {
    'late_fee': [(500, 2), (1000, 120), (80, 5), (3003, 5)],
    'ship_cost': [(4.2, 'A'), (3, 'Z'), (40, 'A')],
    'bayes_rating': [(9.5, 20), (4, -20)],
    'sku_check': [('98-76 54',), ('98x76',), ('98765432109876',)],
    'workdays_between': [('2025-12-24', '2025-12-26'), ('2024-04-12', '2024-04-05')],
    'mask_email': [('jo@mail.net',), ('a@@b.com',)],
    'pro_rata': [(200, 40, 30), (50, 5, 0), (10, 2, 3)],
    'time_slot': [(700,)],
    'initials': [('Ludwig van Beethoven Jr Esq',)],
    'clean_avg': [[-20, 80, 100], [9999.99, 10000.01, 1], [], [0.04, 0.05]],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, n) in SCALARS.items():
        con.create_function(name, n, fn, deterministic=True)
    con.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return con


def _selfcheck():
    ok = (int, float, str, type(None))

    def run():
        con = connect()
        out = []
        for src in (TYPICAL, EDGE, DECISION_EXAMPLES):
            for name in SCALARS:
                for args in src[name]:
                    q = 'SELECT %s(%s)' % (name, ','.join('?' * len(args)))
                    r = con.execute(q, args).fetchone()[0]
                    assert isinstance(r, ok), (name, args, r)
                    out.append((name, args, r))
        lists = AGG_TYPICAL + AGG_EDGE + DECISION_EXAMPLES[AGGREGATE[0]]
        for vals in lists:
            con.execute('DROP TABLE IF EXISTS m')
            con.execute('CREATE TABLE m (id INTEGER, v)')
            for i, v in enumerate(vals):
                con.execute('INSERT INTO m VALUES (?,?)', (i, v))
            r = con.execute('SELECT %s(v) FROM m' % AGGREGATE[0]).fetchone()[0]
            assert isinstance(r, ok)
            out.append((AGGREGATE[0], tuple(vals), r))
        return out

    a, b = run(), run()
    assert a == b
    for name in SCALARS:
        for ex in DECISION_EXAMPLES[name]:
            assert ex not in TYPICAL[name] and ex not in EDGE[name], (name, ex)
        assert len(DECISIONS[name]) == len(DECISION_EXAMPLES[name])
        assert 6 <= len(EDGE[name]) <= 10 and len(TYPICAL[name]) >= 4
    n = AGGREGATE[0]
    for ex in DECISION_EXAMPLES[n]:
        assert ex not in AGG_TYPICAL and ex not in AGG_EDGE
    assert len(DECISIONS[n]) == len(DECISION_EXAMPLES[n])
    assert sum(len(v) for v in DECISIONS.values()) == 25
    return a


if __name__ == '__main__':
    for row in _selfcheck():
        print(row)
    print('SELF-CHECK OK')
