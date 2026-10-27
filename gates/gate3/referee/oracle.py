"""The product owner's private intent: 20 business functions with invented rules.
Workers see only a one-line description per function and 2 small examples.
connect() returns a SQLite connection with these functions registered; it is the referee."""
import datetime, decimal, math, re, sqlite3

def _date(s):
    if s is None: return None
    try:
        return datetime.date.fromisoformat(str(s)[:10])
    except ValueError:
        return None

def clamp(x, lo, hi):
    if x is None: return None
    if lo is not None and hi is not None and lo > hi: lo, hi = hi, lo
    if lo is not None and x < lo: return lo
    if hi is not None and x > hi: return hi
    return x

def bucket(x, w):
    if x is None or w is None or w <= 0: return None
    r = math.floor(x / w) * w
    return int(r) if isinstance(x, int) and isinstance(w, int) else float(r)

def mask(s):
    if s is None: return None
    s = str(s)
    return '*' * len(s) if len(s) <= 2 else '*' * (len(s) - 2) + s[-2:]

def slug(s):
    if s is None: return None
    r = re.sub(r'[^a-z0-9]+', '-', str(s).lower()).strip('-')
    return r or 'n-a'

SMALL = {'of', 'and', 'the'}
def titlecase(s):
    if s is None: return None
    words = str(s).split(' ')
    out = []
    for i, w in enumerate(words):
        lw = w.lower()
        out.append(lw if (i > 0 and lw in SMALL) else lw[:1].upper() + lw[1:])
    return ' '.join(out)

def fiscal_q(d):
    d = _date(d)
    if d is None: return None
    fy = d.year + 1 if d.month >= 4 else d.year
    q = (d.month - 4) % 12 // 3 + 1
    return f'FY{fy % 100:02d}Q{q}'

def biz_days(a, b):
    a, b = _date(a), _date(b)
    if a is None or b is None: return None
    if b < a: return -biz_days(b.isoformat(), a.isoformat())
    n, d = 0, a
    while d < b:
        if d.weekday() < 5: n += 1
        d += datetime.timedelta(days=1)
    return n

def round_half_even(x, n=0):
    if x is None: return None
    n = int(n or 0)
    q = decimal.Decimal(1).scaleb(-n)
    r = decimal.Decimal(repr(x)).quantize(q, rounding=decimal.ROUND_HALF_EVEN)
    return float(r) if n > 0 else int(r)

def pct(a, b):
    if a is None or b is None: return None
    if b == 0: return 'n/a'
    return f'{round(a / b * 100, 1):.1f}%'

def initials(s):
    if s is None: return None
    words = [w for w in re.split(r'[\s\-]+', str(s)) if w]
    return ''.join(w[0].upper() + '.' for w in words if w[0].isalpha())

def score(x):
    if x is None or x < 0: return 0
    if x < 10: return x * 2
    if x < 100: return 20 + (x - 10)
    return 110 + round(math.log10(x / 100) * 10, 2)

def grade(s):
    if s is None: return 'I'
    if s >= 100: return 'A+'
    for cut, g in ((90, 'A'), (80, 'B'), (70, 'C'), (60, 'D')):
        if s >= cut: return g
    return 'F'

def safe_div(a, b, d=None):
    if a is None: return None
    if b is None or b == 0: return 0 if d is None else d
    return a / b

RATES = {'IN': 0.18, 'US': 0.0725, 'EU': 0.20, 'UK': 0.20}
def tax(amount, region):
    if amount is None: return None
    if amount <= 0 or region is None: return 0.0
    r = str(region).upper()
    if r == 'UK' and amount < 10: return 0.0
    return round(amount * RATES.get(r, 0.0), 2)

def checksum(s):
    if s is None: return None
    v = sum((i + 1) * ord(c) for i, c in enumerate(str(s))) % 97
    return v + 97 if v < 10 else v

def nth_word(s, n):
    if s is None or n is None: return None
    w = str(s).split(); n = int(n)
    if n == 0 or abs(n) > len(w): return ''
    return w[n - 1] if n > 0 else w[n]

def collapse(s):
    if s is None: return None
    out = []
    for c in str(s):
        if out and out[-1].lower() == c.lower(): continue
        out.append(c)
    return ''.join(out)

def _plural(n, unit): return f'{n} {unit}{"" if n == 1 else "s"} ago'
def ago(a, b):
    a, b = _date(a), _date(b)
    if a is None or b is None: return None
    d = (b - a).days
    if d < 0: return 'in the future'
    if d == 0: return 'today'
    if d == 1: return 'yesterday'
    if d < 7: return f'{d} days ago'
    if d < 30: return _plural(d // 7, 'week')
    if d < 365: return _plural(d // 30, 'month')
    return _plural(d // 365, 'year')

def luhn_ok(s):
    if s is None: return None
    s = str(s).replace(' ', '').replace('-', '')
    if not s.isdigit() or len(s) < 2: return 0
    total = 0
    for i, c in enumerate(reversed(s)):
        v = int(c)
        if i % 2: v = v * 2 - 9 if v * 2 > 9 else v * 2
        total += v
    return int(total % 10 == 0)

class WAvg:
    def __init__(self): self.sw = 0.0; self.swx = 0.0
    def step(self, v, w):
        if v is None or w is None or w <= 0: return
        self.sw += w; self.swx += v * w
    def finalize(self):
        return None if self.sw == 0 else round(self.swx / self.sw, 4)

SCALARS = {'clamp': (clamp, 3), 'bucket': (bucket, 2), 'mask': (mask, 1), 'slug': (slug, 1), 'titlecase': (titlecase, 1),
           'fiscal_q': (fiscal_q, 1), 'biz_days': (biz_days, 2), 'round_half_even': (round_half_even, -1), 'pct': (pct, 2),
           'initials': (initials, 1), 'score': (score, 1), 'grade': (grade, 1), 'safe_div': (safe_div, -1), 'tax': (tax, 2),
           'checksum': (checksum, 1), 'nth_word': (nth_word, 2), 'collapse': (collapse, 1), 'ago': (ago, 2), 'luhn_ok': (luhn_ok, 1)}

def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, n) in SCALARS.items():
        con.create_function(name, n, fn, deterministic=True)
    con.create_aggregate('wavg', 2, WAvg)
    return con
