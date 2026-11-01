import sqlite3
import math

SPEC = {
    'late_fee': 'late_fee(balance_cents, days_late): late-payment fee in cents charged on an overdue invoice balance.',
    'short_name': 'short_name(full_name): compact display name such as "Maria G." for tight UI lists.',
    'rating_label': 'rating_label(avg_rating, num_reviews): storefront badge text for a product given its average star rating and review count.',
    'nps_score': 'nps_score(rating): net promoter score (integer, -100 to 100) over a column of 0-10 survey ratings.',
}


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and not (isinstance(x, float) and math.isnan(x))


def late_fee(balance, days):
    if not _num(balance) or not _num(days):
        return None
    if balance <= 0:
        return 0
    if days <= 3:          # decision: grace period
        return 0
    fee = int(balance * 2 // 100)
    return min(fee, 5000)  # decision: cap


_SUFFIX = {'jr', 'sr', 'ii', 'iii', 'iv', 'phd', 'md'}


def short_name(name):
    if not isinstance(name, str):
        return None
    toks = name.split()
    # decision: trailing suffixes ignored
    while len(toks) > 1 and toks[-1].strip('.,').lower() in _SUFFIX:
        toks.pop()
    if not toks:
        return ''
    first = toks[0].strip(',')
    first = first[:1].upper() + first[1:].lower()
    if len(toks) == 1:
        return first
    last = toks[-1].strip('.,')
    if not last:
        return first
    return first + ' ' + last[0].upper() + '.'


def rating_label(avg, n):
    if not _num(avg) or not _num(n):
        return None
    if avg < 0 or avg > 5:      # decision: out of range -> NULL
        return None
    if n < 5:                   # decision: too few reviews
        return 'New'
    if avg >= 4.5:
        return 'Excellent'
    if avg >= 4.0:
        return 'Great'
    if avg >= 3.0:
        return 'Good'
    return 'Poor'


class NpsScore:
    def __init__(self):
        self.p = 0
        self.d = 0
        self.n = 0

    def step(self, v):
        if not _num(v) or v < 0 or v > 10:   # decision: out-of-range/non-numeric ignored
            return
        self.n += 1
        if v >= 9:
            self.p += 1
        elif v <= 6:
            self.d += 1

    def finalize(self):
        if self.n < 3:                        # decision: too few responses
            return None
        diff = 100 * (self.p - self.d)
        q, r = divmod(abs(diff) * 2 + self.n, 2 * self.n)  # round half away from zero
        return q if diff >= 0 else -q


SCALARS = {'late_fee': (late_fee, 2), 'short_name': (short_name, 1), 'rating_label': (rating_label, 2)}
AGGREGATE = ('nps_score', NpsScore)

TYPICAL = {
    'late_fee': [(10000, 10), (25000, 30), (50000, 45), (7500, 60), (0, 20)],
    'short_name': [('Maria Garcia',), ('john smith',), ('Priya Raman',), ('Wei Chen',), ('Cher',)],
    'rating_label': [(4.8, 120), (4.2, 60), (3.5, 200), (2.1, 80), (4.6, 30)],
}
EDGE = {
    'late_fee': [(400000, 30), (10000, 3), (10000, 4), (10000, 1), (-500, 10), (None, 5), (10000, None), (12345, 10), (10000, 0)],
    'short_name': [('  ana   lopez ',), ('',), ('Dan Brown Jr.',), ('Jr',), ('Mary Jane Watson',), (None,), ('Li Wu, III',)],
    'rating_label': [(4.5, 10), (4.0, 5), (4.9, 4), (4.9, 0), (5.5, 50), (-1, 50), (None, 20), (3.0, 100), (2.9, 5)],
}
AGG_TYPICAL = [
    [10, 9, 8, 7, 3, 10, 9, 5],
    [9, 9, 10, 8],
    [0, 3, 6, 5, 9, 2, 1, 4],
    [7, 8, 7, 8, 9, 10],
]
AGG_EDGE = [
    [10, 9, 8, 7, 3, 2, 9, 10, 10, 1, 8, 7, 9],
    [10, 9],
    [],
    [None, 10, 9, 11, -2, 3, 'x', 9],
    [10, 9, 9, 8, 7, 7, 6, 3],
    [10, 10, 10, 10],
    [6.9, 7.0, 8.9, 9.0, 10.0],
    [0, 0, 10],
]

DECISIONS = {
    'late_fee': ['grace period of 3 days charges nothing', 'fee capped at 5000 cents'],
    'short_name': ['trailing suffixes (Jr, Sr, II, III, IV, PhD, MD) ignored for the initial'],
    'rating_label': ['fewer than 5 reviews gives New regardless of rating', 'average outside 0-5 gives NULL'],
    'nps_score': ['out-of-range or non-numeric ratings ignored', 'fewer than 3 valid ratings gives NULL', 'result rounded half away from zero'],
}
DECISION_EXAMPLES = {
    'late_fee': [(20000, 2), (300000, 90)],
    'short_name': [('Will Smith Sr',), ],
    'rating_label': [(4.9, 3), (7, 50)],
    'nps_score': [[5, 8, 'abc', 10, 99, 9, 12], [9, 4], [1, 2, 3, 4, 5, 6, 7, 10]],
}


def connect():
    c = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, n) in SCALARS.items():
        c.create_function(name, n, fn, deterministic=True)
    c.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return c
