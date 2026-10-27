"""Gate 4 private intent: 20 business functions with invented rules (a fresh set; Gate 3's are public).
Workers see a one-line spec and 2 happy-path example tests per function.
connect() returns a SQLite connection with these functions registered; it is the referee and the product owner."""
import datetime, math, re, sqlite3

def _date(s):
    if s is None: return None
    try:
        return datetime.date.fromisoformat(str(s)[:10])
    except ValueError:
        return None

def _half_up(x):
    return math.floor(x + 0.5)

RATES = {'gold': 0.20, 'silver': 0.10, 'bronze': 0.05}
def discount(price, tier):
    if price is None or price < 0: return None
    if tier is None: return round(float(price), 2)
    off = min(price * RATES.get(str(tier).strip().lower(), 0.0), 50)
    return round(float(price - off), 2)

ZONES = {'local': 5, 'national': 10, 'intl': 25}
def shipping(w, zone):
    if w is None or zone is None: return None
    base = ZONES.get(str(zone).lower())
    if base is None: return None
    if w <= 0: return 0
    if w > 30: return None
    return base + 2 * max(0, math.ceil(w - 1))

def abbrev(s, n):
    if s is None: return None
    s = str(s)
    if n is None: return s
    if n < 2: return None
    n = int(n)
    return s if len(s) <= n else s[:n - 1] + '~'

DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'sat', 'sun']
def weekday(d):
    d = _date(d)
    return None if d is None else DAYS[d.weekday()]

def age(birth, on):
    b, o = _date(birth), _date(on)
    if b is None or o is None or b > o: return None
    y = o.year - b.year - ((o.month, o.day) < (b.month, b.day))
    return None if y >= 150 else y

def phone_fmt(s):
    if s is None: return None
    d = ''.join(c for c in str(s) if c.isdigit())
    if len(d) == 11 and d[0] == '1': return f'+1 ({d[1:4]}) {d[4:7]}-{d[7:]}'
    if len(d) == 10: return f'({d[:3]}) {d[3:6]}-{d[6:]}'
    return 'invalid'

def band(x):
    if x is None: return 'none'
    if x < 0: return 'neg'
    if x < 10: return 'low'
    if x <= 50: return 'mid'
    return 'high'

ROMAN = [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
         (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]
def roman(n):
    if n is None: return None
    n = _half_up(n)
    if n == 0: return 'N'
    if n < 0 or n > 3999: return None
    out = ''
    for v, sym in ROMAN:
        while n >= v: out += sym; n -= v
    return out

def ordinal(n):
    if n is None or n < 0 or n != int(n): return None
    n = int(n)
    suf = 'th' if 11 <= n % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f'{n}{suf}'

def split_part(s, sep, idx):
    if s is None or sep is None or idx is None: return None
    s, sep, idx = str(s), str(sep), int(idx)
    if sep == '': return None
    if idx == 0: return s
    parts = s.split(sep)
    if abs(idx) > len(parts): return None
    return parts[idx - 1] if idx > 0 else parts[idx]

def median3(a, b, c):
    v = sorted(x for x in (a, b, c) if x is not None)
    if not v: return None
    if len(v) == 3: return v[1]
    return v[0]

def stars(r):
    if r is None: return None
    r = min(max(math.floor(r * 2 + 0.5) / 2, 0), 5)
    full = int(r)
    return '*' * full + ('+' if r - full == 0.5 else '')

def elapsed(sec):
    if sec is None: return None
    sign = '-' if sec < 0 else ''
    s = math.floor(abs(sec))
    if s < 60: return f'{sign}{s}s'
    d, rem = divmod(s, 86400); h, rem = divmod(rem, 3600); m, x = divmod(rem, 60)
    core = f'{h}:{m:02d}:{x:02d}'
    return sign + (f'{d}d {core}' if d else core)

POINTS = {'A+': 4.0, 'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7, 'C+': 2.3, 'C': 2.0, 'C-': 1.7,
          'D+': 1.3, 'D': 1.0, 'E': 0.0, 'F': 0.0}
def grade_point(g):
    if g is None: return None
    return POINTS.get(str(g).strip().upper())

def credit_band(score):
    if score is None: return 'unknown'
    s = math.floor(score)
    if s < 300 or s > 850: return 'invalid'
    for hi, name in ((579, 'poor'), (669, 'fair'), (739, 'good'), (799, 'very good')):
        if s <= hi: return name
    return 'exceptional'

def color_hex(r, g, b):
    if r is None or g is None or b is None: return None
    c = [min(max(_half_up(v), 0), 255) for v in (r, g, b)]
    return '#%02x%02x%02x' % tuple(c)

def vowels(s):
    if s is None: return None
    s = str(s)
    n = sum(1 for c in s if c.lower() in 'aeiou')
    n += sum(1 for w in re.findall(r'[A-Za-z]+', s) if w[-1] in 'yY')
    return n

def next_bizday(d):
    d = _date(d)
    if d is None: return None
    d += datetime.timedelta(days=1)
    while d.weekday() >= 5 or (d.month, d.day) in ((1, 1), (12, 25)):
        d += datetime.timedelta(days=1)
    return d.isoformat()

def loyalty_pts(amount, years):
    if amount is None: return None
    years = 0 if years is None else years
    base = math.floor(amount)
    if base < 1: return 0
    mult = 2 if years >= 5 else 1.5 if years >= 2 else 1
    return min(math.floor(base * mult), 1000)

class ModeVal:
    def __init__(self): self.c = {}
    def step(self, v):
        if v is not None: self.c[v] = self.c.get(v, 0) + 1
    def finalize(self):
        if not self.c: return None
        top = max(self.c.values())
        return min(v for v, k in self.c.items() if k == top)

SCALARS = {'discount': (discount, 2), 'shipping': (shipping, 2), 'abbrev': (abbrev, 2), 'weekday': (weekday, 1),
           'age': (age, 2), 'phone_fmt': (phone_fmt, 1), 'band': (band, 1), 'roman': (roman, 1),
           'ordinal': (ordinal, 1), 'split_part': (split_part, 3), 'median3': (median3, 3), 'stars': (stars, 1),
           'elapsed': (elapsed, 1), 'grade_point': (grade_point, 1), 'credit_band': (credit_band, 1),
           'color_hex': (color_hex, 3), 'vowels': (vowels, 1), 'next_bizday': (next_bizday, 1),
           'loyalty_pts': (loyalty_pts, 2)}

def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, n) in SCALARS.items():
        con.create_function(name, n, fn, deterministic=True)
    con.create_aggregate('mode_val', 1, ModeVal)
    return con
