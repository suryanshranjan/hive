"""Company policy oracle: 20 business functions for the SQL engine.

19 scalar functions and 1 aggregate. The comment block above each function
lists the policy decisions that the one-line SPEC and the TYPICAL examples
do not reveal. Standard library only; fully deterministic.
"""

import functools
import math
import re
import sqlite3
from datetime import date
from decimal import (Context, Decimal, ROUND_FLOOR, ROUND_HALF_DOWN,
                     ROUND_HALF_UP, localcontext)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_CTX = Context(prec=1000)
_NUM_RE = re.compile(r'[+-]?([0-9]+(\.[0-9]*)?|\.[0-9]+)([eE][+-]?[0-9]+)?')
_DATE_RE = re.compile(r'([0-9]{4})-([0-9]{2})-([0-9]{2})')
_CENT = Decimal('0.01')


def _num(x):
    """SQL value -> finite int or float; numeric text is parsed; else None."""
    if x is None or isinstance(x, bool):
        return None
    if isinstance(x, int):
        return x
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    if isinstance(x, str):
        s = x.strip()
        if not _NUM_RE.fullmatch(s):
            return None
        if any(c in s for c in '.eE'):
            v = float(s)
            return v if math.isfinite(v) else None
        return int(s)
    return None


def _dec(n):
    """int/float -> Decimal of the value as written (repr for floats)."""
    return Decimal(n) if isinstance(n, int) else Decimal(repr(n))


def _to_float(d):
    f = float(d)
    if not math.isfinite(f):
        return None
    return 0.0 if f == 0 else f


def _cents(d, rounding=ROUND_HALF_UP):
    with localcontext(_CTX):
        return _to_float(d.quantize(_CENT, rounding=rounding))


def _iso_date(x):
    if not isinstance(x, str):
        return None
    m = _DATE_RE.fullmatch(x.strip())
    if not m:
        return None
    try:
        return date(int(m[1]), int(m[2]), int(m[3]))
    except ValueError:
        return None


def _safe(fn):
    """Never let an exception reach SQLite; only SQL-storable results."""
    @functools.wraps(fn)
    def wrapper(*args):
        try:
            r = fn(*args)
        except Exception:
            return None
        if r is None or isinstance(r, str):
            return r
        if isinstance(r, float):
            return r if math.isfinite(r) else None
        if isinstance(r, int) and not isinstance(r, bool):
            return r if -2 ** 63 <= r < 2 ** 63 else None
        return None
    return wrapper


# ---------------------------------------------------------------------------
# 1. late_fee
# Policy: (a) grace period: 5 days late or fewer -> 0.0;
#         (b) at most 3 periods are charged (fee capped at 6% of balance);
#         (c) minimum fee $5.00 whenever a fee applies;
#         (d) zero or negative (credit) balance -> 0.0. Cents rounded half up.
# ---------------------------------------------------------------------------
@_safe
def late_fee(days_late, balance):
    d, b = _num(days_late), _num(balance)
    if d is None or b is None:
        return None
    if b <= 0 or d <= 5:
        return 0.0
    with localcontext(_CTX):
        periods = min(3, math.ceil(_dec(d) / 30))
        fee = _dec(b) * Decimal('0.02') * periods
        fee = max(fee, Decimal('5.00'))
    return _cents(fee)


# ---------------------------------------------------------------------------
# 2. loyalty_tier
# Policy: (a) 'Platinum' from 20000 points; (b) negative balance ->
#         'Suspended'; (c) NULL (no points record yet) -> 'Bronze';
#         non-numeric text -> NULL.
# ---------------------------------------------------------------------------
@_safe
def loyalty_tier(points):
    if points is None:
        return 'Bronze'
    p = _num(points)
    if p is None:
        return None
    if p < 0:
        return 'Suspended'
    if p < 1000:
        return 'Bronze'
    if p < 5000:
        return 'Silver'
    if p < 20000:
        return 'Gold'
    return 'Platinum'


# ---------------------------------------------------------------------------
# 3. business_days
# Policy: (a) company holidays 1 Jan, 4 Jul, 25 Dec and 26 Dec are not
#         working days (fixed dates, no shift when they fall on a weekend);
#         (b) end before start -> negative count of the reversed range;
#         malformed or impossible dates -> NULL.
# ---------------------------------------------------------------------------
_HOLIDAYS = ((1, 1), (7, 4), (12, 25), (12, 26))


def _workdays_after(a, b):
    """Working days d with a < d <= b (a <= b)."""
    n = (b - a).days
    full, rem = divmod(n, 7)
    count = 5 * full
    wd = a.weekday()
    for i in range(1, rem + 1):
        if (wd + i) % 7 < 5:
            count += 1
    for y in range(a.year, b.year + 1):
        for m, dd in _HOLIDAYS:
            h = date(y, m, dd)
            if a < h <= b and h.weekday() < 5:
                count -= 1
    return count


@_safe
def business_days(start_date, end_date):
    a, b = _iso_date(start_date), _iso_date(end_date)
    if a is None or b is None:
        return None
    if b >= a:
        return _workdays_after(a, b)
    return -_workdays_after(b, a)


# ---------------------------------------------------------------------------
# 4. sku_check_digit
# Policy: (a) 11 minus remainder 0 (i.e. 11) -> '0';
#         (b) 11 minus remainder 1 (i.e. 10) -> 'X';
#         (c) spaces and hyphens in the code are ignored; any other
#         non-digit, an empty code, a negative or real number -> NULL.
# ---------------------------------------------------------------------------
@_safe
def sku_check_digit(code):
    if isinstance(code, bool):
        return None
    if isinstance(code, int):
        if code < 0:
            return None
        code = str(code)
    if not isinstance(code, str):
        return None
    digits = re.sub(r'[ \-]', '', code)
    if not re.fullmatch(r'[0-9]+', digits):
        return None
    total = 0
    for i, ch in enumerate(reversed(digits)):
        total += int(ch) * (2 + i % 6)
    c = 11 - total % 11
    if c == 11:
        return '0'
    if c == 10:
        return 'X'
    return str(c)


# ---------------------------------------------------------------------------
# 5. shipping_cost
# Policy: (a) weight is first rounded to the nearest 0.1 kg (half up), so
#         2.04 kg bills as 2 kg; (b) parcels over 30 kg (after rounding) pay
#         a $25.00 oversize surcharge; (c) weight <= 0 or a zone other than
#         1, 2, 3 -> NULL. At least 1 kg is always billed.
# ---------------------------------------------------------------------------
_ZONE_BASE = {1: Decimal('4.00'), 2: Decimal('6.00'), 3: Decimal('9.00')}


@_safe
def shipping_cost(weight_kg, zone):
    w, z = _num(weight_kg), _num(zone)
    if w is None or z is None or w <= 0:
        return None
    if z != int(z) or int(z) not in _ZONE_BASE:
        return None
    with localcontext(_CTX):
        rw = _dec(w).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
        kg = max(1, math.ceil(rw))
        cost = _ZONE_BASE[int(z)] + Decimal('2.00') * kg
        if rw > 30:
            cost += Decimal('25.00')
    return _cents(cost)


# ---------------------------------------------------------------------------
# 6. star_rating
# Policy: (a) an exact quarter-star midpoint rounds DOWN (4.25 -> 4.0,
#         4.75 -> 4.5): we never overstate a rating; (b) averages below 1.0
#         (including 0, meaning no reviews) -> NULL; (c) above 5 -> 5.0.
# ---------------------------------------------------------------------------
@_safe
def star_rating(avg_score):
    s = _num(avg_score)
    if s is None or s < 1:
        return None
    if s > 5:
        return 5.0
    with localcontext(_CTX):
        halves = (_dec(s) * 2).quantize(Decimal(1), rounding=ROUND_HALF_DOWN)
        return _to_float(halves / 2)


# ---------------------------------------------------------------------------
# 7. format_phone
# Policy: (a) 11 digits starting with country code 1 -> the 1 is dropped;
#         (b) 7-digit local numbers -> '123-4567' without area code;
#         (c) an area code starting with 0 or 1 -> NULL; any letter
#         (vanity numbers, extensions) or other digit count -> NULL.
#         Integer input is read as its digits.
# ---------------------------------------------------------------------------
@_safe
def format_phone(number):
    if isinstance(number, bool):
        return None
    if isinstance(number, int):
        number = str(number)
    if not isinstance(number, str):
        return None
    if re.search(r'[^\W\d_]', number):
        return None
    d = re.sub(r'[^0-9]', '', number)
    if len(d) == 11 and d[0] == '1':
        d = d[1:]
    if len(d) == 10:
        if d[0] in '01':
            return None
        return '(%s) %s-%s' % (d[:3], d[3:6], d[6:])
    if len(d) == 7:
        return '%s-%s' % (d[:3], d[3:])
    return None


# ---------------------------------------------------------------------------
# 8. mask_card
# Policy: (a) fewer than 12 digits -> every digit masked (nothing shown);
#         (b) any character other than digits, spaces and hyphens -> NULL;
#         (c) more than 19 digits, or no digits at all -> NULL.
#         Surrounding whitespace is trimmed; integer input is read as digits.
# ---------------------------------------------------------------------------
@_safe
def mask_card(card_number):
    if isinstance(card_number, bool):
        return None
    if isinstance(card_number, int):
        card_number = str(card_number)
    if not isinstance(card_number, str):
        return None
    s = card_number.strip()
    if not re.fullmatch(r'[0-9 \-]*', s):
        return None
    n = sum(ch.isdigit() for ch in s)
    if n == 0 or n > 19:
        return None
    keep = 0 if n < 12 else 4
    out, seen = [], 0
    for ch in s:
        if ch.isdigit():
            seen += 1
            out.append(ch if seen > n - keep else '*')
        else:
            out.append(ch)
    return ''.join(out)


# ---------------------------------------------------------------------------
# 9. fiscal_quarter
# Policy: (a) year-end close cut-off: 28-31 March are booked into Q1 of the
#         next fiscal year; (b) a timestamp ('YYYY-MM-DD HH:MM[:SS]' or with
#         'T') is accepted and only its date part used; other formats or
#         impossible dates -> NULL.
# ---------------------------------------------------------------------------
_TS_RE = re.compile(r'([0-9]{4}-[0-9]{2}-[0-9]{2})(?:[ T][0-9]{2}:[0-9]{2}(?::[0-9]{2}(?:\.[0-9]+)?)?)?')


@_safe
def fiscal_quarter(d):
    if not isinstance(d, str):
        return None
    m = _TS_RE.fullmatch(d.strip())
    if not m:
        return None
    dt = _iso_date(m[1])
    if dt is None:
        return None
    y, mo = dt.year, dt.month
    if mo == 3 and dt.day >= 28:
        y, mo = y, 4
    fy = y + 1 if mo >= 4 else y
    q = {4: 1, 5: 1, 6: 1, 7: 2, 8: 2, 9: 2, 10: 3, 11: 3, 12: 3,
         1: 4, 2: 4, 3: 4}[mo]
    return 'FY%d-Q%d' % (fy, q)


# ---------------------------------------------------------------------------
# 10. sales_tax
# Policy: (a) half a cent rounds up (away from zero), on the amount as
#         written, not binary floating point; (b) the state code is
#         case-insensitive and surrounding spaces are ignored; (c) a state
#         not in the table -> 0.0 (no tax collected), not NULL.
#         NULL amount or NULL state -> NULL. Refunds give negative tax.
# ---------------------------------------------------------------------------
_TAX = {'CA': Decimal('0.0725'), 'NY': Decimal('0.04'),
        'TX': Decimal('0.0625'), 'WA': Decimal('0.065')}


@_safe
def sales_tax(net_amount, state):
    a = _num(net_amount)
    if a is None or state is None:
        return None
    rate = _TAX.get(str(state).strip().upper())
    if rate is None:
        return 0.0
    with localcontext(_CTX):
        return _cents(_dec(a) * rate)


# ---------------------------------------------------------------------------
# 11. name_initials
# Policy: (a) only first and last name count: middle names are dropped;
#         (b) honorifics (Mr, Mrs, Ms, Miss, Dr, Prof, Sir) and suffixes
#         (Jr, Sr, II, III, IV, PhD, MD) are skipped; (c) 'Last, First'
#         (comma form) is read as 'First Last'; a single name gives one
#         letter; blank or non-text -> NULL.
# ---------------------------------------------------------------------------
_HONORIFICS = {'mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'sir'}
_SUFFIXES = {'jr', 'sr', 'ii', 'iii', 'iv', 'phd', 'md'}


@_safe
def name_initials(full_name):
    if not isinstance(full_name, str):
        return None
    s = full_name.strip()
    if ',' in s:
        last, _, first = s.partition(',')
        s = first + ' ' + last
    words = []
    for w in s.split():
        key = w.strip('.,').lower()
        if key in _HONORIFICS or key in _SUFFIXES:
            continue
        letters = [ch for ch in w if ch.isalpha()]
        if letters:
            words.append(letters[0].upper())
    if not words:
        return None
    if len(words) == 1:
        return words[0]
    return words[0] + words[-1]


# ---------------------------------------------------------------------------
# 12. uk_postcode
# Policy: (a) a letter 'O' typed where the inward code's digit belongs is
#         read as zero ('SW1A OAA' -> 'SW1A 0AA'); (b) only 5 to 7 letters and
#         digits are a postcode, else NULL; inward code must be digit + two
#         letters and outward code must start with a letter, else NULL;
#         (c) spaces, hyphens and dots anywhere are ignored, other symbols
#         -> NULL.
# ---------------------------------------------------------------------------
@_safe
def uk_postcode(code):
    if not isinstance(code, str):
        return None
    s = re.sub(r'[\s.\-]', '', code.upper())
    if not re.fullmatch(r'[A-Z0-9]{5,7}', s):
        return None
    outward, inward = s[:-3], s[-3:]
    if inward[0] == 'O':
        inward = '0' + inward[1:]
    if not re.fullmatch(r'[0-9][A-Z]{2}', inward):
        return None
    if not re.fullmatch(r'[A-Z][A-Z0-9]{1,3}', outward):
        return None
    return outward + ' ' + inward


# ---------------------------------------------------------------------------
# 13. volume_unit_price
# Policy: (a) 15% off from 250 units (top tier); (b) the discounted price is
#         rounded DOWN to the cent; (c) a fractional quantity is truncated
#         (9.9 units -> 9); quantity below 1 after truncation or a negative
#         list price -> NULL.
# ---------------------------------------------------------------------------
@_safe
def volume_unit_price(list_price, quantity):
    p, q = _num(list_price), _num(quantity)
    if p is None or q is None or p < 0:
        return None
    qi = math.floor(q)
    if qi < 1:
        return None
    if qi >= 250:
        pct = 15
    elif qi >= 50:
        pct = 10
    elif qi >= 10:
        pct = 5
    else:
        pct = 0
    with localcontext(_CTX):
        price = _dec(p) * (100 - pct) / 100
    return _cents(price, ROUND_FLOOR)


# ---------------------------------------------------------------------------
# 14. age_bracket
# Policy: (a) under 18 -> 'minor'; (b) the bands stop at '55-64': 65 and
#         over -> '65+'; (c) a 29 February birthday falls on 28 February in
#         non-leap years; as_of before birth or invalid dates -> NULL.
# ---------------------------------------------------------------------------
def _is_leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


@_safe
def age_bracket(birth_date, as_of_date):
    b, a = _iso_date(birth_date), _iso_date(as_of_date)
    if b is None or a is None or a < b:
        return None
    bm, bd = b.month, b.day
    if bm == 2 and bd == 29 and not _is_leap(a.year):
        bd = 28
    age = a.year - b.year - (1 if (a.month, a.day) < (bm, bd) else 0)
    if age < 18:
        return 'minor'
    if age < 25:
        return '18-24'
    if age >= 65:
        return '65+'
    lo = 25 + 10 * ((age - 25) // 10)
    return '%d-%d' % (lo, lo + 9)


# ---------------------------------------------------------------------------
# 15. prorated_refund
# Policy: (a) rounded DOWN to the cent (never over-refund); (b) refunds
#         under $1.00 are not paid -> 0.0; (c) a started day counts as used
#         (2.5 days used -> 3). Used >= period -> 0.0; negative amount,
#         negative days used or period <= 0 -> NULL.
# ---------------------------------------------------------------------------
@_safe
def prorated_refund(amount, days_used, days_in_period):
    a, u, p = _num(amount), _num(days_used), _num(days_in_period)
    if a is None or u is None or p is None:
        return None
    if a < 0 or u < 0 or p <= 0:
        return None
    used = math.ceil(u)
    with localcontext(_CTX):
        pd = _dec(p)
        if used >= pd:
            return 0.0
        refund = _dec(a) * (pd - used) / pd
        refund = refund.quantize(_CENT, rounding=ROUND_FLOOR)
        if refund < 1:
            return 0.0
        return _to_float(refund)


# ---------------------------------------------------------------------------
# 16. meeting_end
# Policy: (a) bookings are whole 15-minute blocks: the duration is rounded
#         UP to a multiple of 15; (b) rooms are bookable 08:00-18:00 only: a
#         start before 08:00 or an end after 18:00 -> NULL; (c) minutes <= 0
#         -> NULL. A one-digit hour ('9:00') is accepted.
# ---------------------------------------------------------------------------
@_safe
def meeting_end(start_time, minutes):
    if not isinstance(start_time, str):
        return None
    m = re.fullmatch(r'([0-9]{1,2}):([0-9]{2})', start_time.strip())
    n = _num(minutes)
    if not m or n is None or n <= 0:
        return None
    h, mi = int(m[1]), int(m[2])
    if h > 23 or mi > 59:
        return None
    start = h * 60 + mi
    if start < 8 * 60:
        return None
    end = start + 15 * math.ceil(n / 15)
    if end > 18 * 60:
        return None
    return '%02d:%02d' % divmod(end, 60)


# ---------------------------------------------------------------------------
# 17. money_text
# Policy: (a) negative amounts in accounting parentheses '($12.00)'; an
#         amount that rounds to zero is shown unsigned; (b) JPY is shown with
#         no decimals as '¥1,235'; (c) any other 3-letter code -> US style
#         number followed by the code ('1,234.50 CHF'); codes are
#         case-insensitive; not 3 letters -> NULL. Rounding is half up.
# ---------------------------------------------------------------------------
_CUR = {'USD': ('$', ',', '.', 2), 'EUR': ('€', '.', ',', 2),
        'GBP': ('£', ',', '.', 2), 'JPY': ('¥', ',', '.', 0)}


def _group(ip, sep):
    parts = []
    while len(ip) > 3:
        parts.insert(0, ip[-3:])
        ip = ip[:-3]
    parts.insert(0, ip)
    return sep.join(parts)


@_safe
def money_text(amount, currency):
    a = _num(amount)
    if a is None or not isinstance(currency, str):
        return None
    code = currency.strip().upper()
    if not re.fullmatch(r'[A-Z]{3}', code):
        return None
    sym, gsep, dsep, places = _CUR.get(code, ('', ',', '.', 2))
    with localcontext(_CTX):
        q = _dec(a).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
        neg = q < 0
        s = '{:f}'.format(abs(q))
    if places:
        ip, fp = s.split('.')
        body = sym + _group(ip, gsep) + dsep + fp
    else:
        body = sym + _group(s, gsep)
    if code not in _CUR:
        body += ' ' + code
    return '(' + body + ')' if neg else body


# ---------------------------------------------------------------------------
# 18. canonical_email
# Policy: (a) a '+tag' in the local part is removed for every domain;
#         (b) gmail.com and googlemail.com: dots in the local part are removed
#         and the domain becomes gmail.com; (c) invalid address (not exactly
#         one '@', empty local part, inner whitespace, domain without an
#         inner dot) -> NULL.
# ---------------------------------------------------------------------------
@_safe
def canonical_email(email):
    if not isinstance(email, str):
        return None
    s = email.strip().lower()
    if not s or re.search(r'\s', s) or s.count('@') != 1:
        return None
    local, domain = s.split('@')
    local = local.split('+', 1)[0]
    if domain in ('gmail.com', 'googlemail.com'):
        local = local.replace('.', '')
        domain = 'gmail.com'
    if not local:
        return None
    if '.' not in domain or domain.startswith('.') or domain.endswith('.'):
        return None
    return local + '@' + domain


# ---------------------------------------------------------------------------
# 19. overtime_pay
# Policy: (a) hours beyond 60 are paid at double time; (b) hours are first
#         rounded to the nearest quarter hour (half up); (c) an hourly rate
#         below the $7.25 minimum wage is raised to $7.25. Negative hours or
#         negative rate -> NULL. Cents rounded half up.
# ---------------------------------------------------------------------------
@_safe
def overtime_pay(hours, hourly_rate):
    h, r = _num(hours), _num(hourly_rate)
    if h is None or r is None or h < 0 or r < 0:
        return None
    with localcontext(_CTX):
        rate = max(_dec(r), Decimal('7.25'))
        hq = (_dec(h) * 4).quantize(Decimal(1), rounding=ROUND_HALF_UP) / 4
        regular = min(hq, Decimal(40))
        overtime = min(max(hq - 40, Decimal(0)), Decimal(20))
        double = max(hq - 60, Decimal(0))
        pay = rate * (regular + Decimal('1.5') * overtime + 2 * double)
    return _cents(pay)


# ---------------------------------------------------------------------------
# 20. median_price (aggregate)
# Policy: (a) an even count gives the LOWER of the two middle prices (an
#         actually observed price), not their average; (b) zero and negative
#         prices (free samples, refunds) are ignored; (c) NULL and text values
#         are ignored, even numeric-looking text; no valid price -> NULL.
#         Result is a real.
# ---------------------------------------------------------------------------
class MedianPrice:
    def __init__(self):
        self.values = []

    def step(self, value):
        try:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return
            if isinstance(value, float) and not math.isfinite(value):
                return
            if value > 0:
                self.values.append(value)
        except Exception:
            pass

    def finalize(self):
        try:
            if not self.values:
                return None
            v = sorted(self.values)
            return float(v[(len(v) - 1) // 2])
        except Exception:
            return None


# ---------------------------------------------------------------------------
# Module interface
# ---------------------------------------------------------------------------

SPEC = {
    'late_fee': 'late_fee(days_late, balance): late-payment fee in dollars on '
                'an overdue invoice: 2% of the balance for each started '
                '30-day period past the due date.',
    'loyalty_tier': "loyalty_tier(points): loyalty programme tier for a "
                    "customer's points balance: 'Bronze' below 1000 points, "
                    "'Silver' from 1000, 'Gold' from 5000.",
    'business_days': "business_days(start_date, end_date): number of working "
                     "days (Monday to Friday) after start_date up to and "
                     "including end_date, for ISO dates 'YYYY-MM-DD'; used "
                     "for SLA and delivery-time reports.",
    'sku_check_digit': 'sku_check_digit(code): check character for a numeric '
                       'product code: weight the digits 2,3,4,5,6,7 '
                       '(repeating) starting from the rightmost digit, and '
                       'take 11 minus the weighted sum mod 11.',
    'shipping_cost': 'shipping_cost(weight_kg, zone): parcel shipping charge '
                     'in dollars: the zone base fee (zone 1 $4.00, zone 2 '
                     '$6.00, zone 3 $9.00) plus $2.00 per started kilogram.',
    'star_rating': 'star_rating(avg_score): star rating displayed on product '
                   'pages for an average review score on the 1-5 scale, to '
                   'the nearest half star.',
    'format_phone': "format_phone(number): North American phone number in our "
                    "display format '(555) 123-4567', from any common way of "
                    "writing it.",
    'mask_card': "mask_card(card_number): payment card number for receipts and "
                 "support screens, with every digit except the last four "
                 "replaced by '*' and separators kept as typed.",
    'fiscal_quarter': "fiscal_quarter(date): fiscal quarter label such as "
                      "'FY2027-Q1' for an ISO date; the fiscal year starts on "
                      "1 April and is named after the calendar year in which "
                      "it ends.",
    'sales_tax': 'sales_tax(net_amount, state): sales tax in dollars and cents '
                 'on a net amount for a US state code, at the company rates '
                 'CA 7.25%, NY 4%, TX 6.25%, WA 6.5%.',
    'name_initials': "name_initials(full_name): upper-case initials of a "
                     "person's name for avatar badges, e.g. 'Ada Lovelace' "
                     "gives 'AL'.",
    'uk_postcode': "uk_postcode(code): UK postcode in standard display form, "
                   "upper case with a single space before the last three "
                   "characters, e.g. 'sw1a1aa' gives 'SW1A 1AA'.",
    'volume_unit_price': 'volume_unit_price(list_price, quantity): unit price '
                         'in dollars and cents after the volume discount on '
                         'an order line: 5% off from 10 units, 10% off from '
                         '50 units.',
    'age_bracket': "age_bracket(birth_date, as_of_date): marketing age bracket "
                   "of a customer on a given date, for ISO dates: '18-24', "
                   "then ten-year bands '25-34', '35-44', '45-54' and so on.",
    'prorated_refund': 'prorated_refund(amount, days_used, days_in_period): '
                       'refund in dollars for the unused part of a prepaid '
                       'subscription period, proportional to the unused days.',
    'meeting_end': "meeting_end(start_time, minutes): end time 'HH:MM' of a "
                   "meeting-room booking that starts at start_time ('HH:MM') "
                   "and lasts the given number of minutes.",
    'money_text': "money_text(amount, currency): amount formatted for invoices "
                  "in an ISO currency: USD as '$1,234.50', EUR as "
                  "'€1.234,50', GBP as '£1,234.50'.",
    'canonical_email': 'canonical_email(email): canonical form of a customer '
                       'email address, used to detect duplicate accounts.',
    'overtime_pay': 'overtime_pay(hours, hourly_rate): gross weekly pay in '
                    'dollars for hourly staff: hours up to 40 at the hourly '
                    'rate, hours beyond 40 at time and a half.',
    'median_price': 'median_price(price): median of the prices in a group, '
                    'for price-benchmark reports (aggregate).',
}

SCALARS = {
    'late_fee': (late_fee, 2),
    'loyalty_tier': (loyalty_tier, 1),
    'business_days': (business_days, 2),
    'sku_check_digit': (sku_check_digit, 1),
    'shipping_cost': (shipping_cost, 2),
    'star_rating': (star_rating, 1),
    'format_phone': (format_phone, 1),
    'mask_card': (mask_card, 1),
    'fiscal_quarter': (fiscal_quarter, 1),
    'sales_tax': (sales_tax, 2),
    'name_initials': (name_initials, 1),
    'uk_postcode': (uk_postcode, 1),
    'volume_unit_price': (volume_unit_price, 2),
    'age_bracket': (age_bracket, 2),
    'prorated_refund': (prorated_refund, 3),
    'meeting_end': (meeting_end, 2),
    'money_text': (money_text, 2),
    'canonical_email': (canonical_email, 1),
    'overtime_pay': (overtime_pay, 2),
}

AGGREGATE = ('median_price', MedianPrice)

TYPICAL = {
    'late_fee': [(10, 500.0), (45, 1000), (75, 250.0), (20, 1234.5)],
    'loyalty_tier': [(250,), (1500,), (7200,), (3000,), (12000,)],
    'business_days': [('2026-03-02', '2026-03-06'), ('2026-03-06', '2026-03-09'),
                      ('2026-03-02', '2026-03-16'), ('2026-03-02', '2026-03-31'),
                      ('2026-05-13', '2026-05-13')],
    'sku_check_digit': [('7351353',), ('5012345',), ('9780306',),
                        ('4012888',), ('6020000',)],
    'shipping_cost': [(2.5, 1), (0.8, 2), (10, 3), (4.3, 2), (15.5, 1)],
    'star_rating': [(4.3,), (3.1,), (3.8,), (2.6,), (4.9,)],
    'format_phone': [('555-123-4567',), ('212.555.0188',),
                     ('(415) 5550199',), ('617 555 0123',)],
    'mask_card': [('4111 1111 1111 1111',), ('5500-0000-0000-0004',),
                  ('378282246310005',), ('6011000990139424',)],
    'fiscal_quarter': [('2026-05-10',), ('2026-12-01',), ('2027-02-14',),
                       ('2026-08-31',), ('2025-04-01',)],
    'sales_tax': [(100, 'CA'), (19.99, 'NY'), (240, 'TX'), (50, 'WA'),
                  (12.4, 'CA')],
    'name_initials': [('Ada Lovelace',), ('grace hopper',), ('Alan Turing',),
                      ('Linus Torvalds',)],
    'uk_postcode': [('sw1a1aa',), ('EC1A 1BB',), ('m1 1ae',), ('b33 8th',),
                    ('cr2 6xh',)],
    'volume_unit_price': [(20.0, 12), (8.0, 60), (12.5, 3), (4.99, 15),
                          (100, 75)],
    'age_bracket': [('1990-06-15', '2026-01-01'), ('2000-03-10', '2026-10-01'),
                    ('1980-01-20', '2026-05-05'), ('2005-09-01', '2026-02-01')],
    'prorated_refund': [(30.0, 10, 30), (100, 25, 100), (12.0, 1, 4),
                        (60, 15, 30), (365, 65, 365)],
    'meeting_end': [('09:00', 30), ('13:15', 45), ('10:30', 60),
                    ('14:00', 90)],
    'money_text': [(1234.5, 'USD'), (1234.5, 'EUR'), (99.99, 'GBP'),
                   (1000000, 'USD'), (0.5, 'EUR')],
    'canonical_email': [('Alice@Example.com',), ('  bob.smith@shop.co.uk ',),
                        ('CAROL@MAIL.COM',), ('dave_99@acme.io',)],
    'overtime_pay': [(40, 20), (45, 20), (30, 15.5), (50, 10), (37.5, 18)],
}

EDGE = {
    'late_fee': [(5, 1000), (6, 1000), (91, 1000), (400, 1000), (10, 100),
                 (10, 0), (40, -500), (-3, 100), (None, 100), (30, 1000)],
    'loyalty_tier': [(20000,), (19999,), (-5,), (None,), (1000,), (5000,),
                     (999.5,), ('abc',), ('1500',), (0,)],
    'business_days': [('2026-12-24', '2026-12-28'), ('2026-12-31', '2027-01-05'),
                      ('2026-07-03', '2026-07-06'), ('2025-07-03', '2025-07-07'),
                      ('2026-03-06', '2026-03-02'), ('2026-03-07', '2026-03-08'),
                      ('2026-02-30', '2026-03-02'), (None, '2026-03-02'),
                      ('2026/03/02', '2026-03-06'), ('2025-12-19', '2026-01-09')],
    'sku_check_digit': [('5550001',), ('123456',), ('2718281',),
                        ('8675309',), ('735-135 3',), ('73A1353',), ('',),
                        (None,), (7351353,), ('4006381',)],
    'shipping_cost': [(2.04, 1), (2.05, 1), (30, 1), (30.04, 1), (30.06, 1),
                      (0, 2), (-1, 2), (3, 4), (3, None), (0.04, 3)],
    'star_rating': [(4.25,), (4.75,), (1.25,), (0.0,), (0.9,), (5.6,),
                    (1.0,), (None,), ('4.3',), (4.2500001,)],
    'format_phone': [('1-555-123-4567',), ('+1 (212) 555-0188',),
                     ('555-0199',), ('055-123-4567',), ('155-123-4567',),
                     ('2-555-123-4567',), ('1-800-FLOWERS',),
                     ('555-123-4567 x22',), (2125550188,), (None,)],
    'mask_card': [('12345678901',), ('123456789012',),
                  ('4111-1111-1111-111X',), ('  4111111111111111  ',),
                  (4111111111111111,), ('',), (None,),
                  ('41111111111111111111',), ('4111.1111.1111.1111',)],
    'fiscal_quarter': [('2026-03-28',), ('2026-03-27',), ('2026-03-31',),
                       ('2026-05-10 14:30:00',), ('2026-05-10T09:00',),
                       ('2026-02-30',), ('10/05/2026',), (None,),
                       (20260510,), ('2026-06-30',)],
    'sales_tax': [(2, 'TX'), (10, 'CA'), (25, ' ny '), (100, 'OR'),
                  (100, None), (None, 'CA'), (-2, 'TX'), (0.2, 'CA'),
                  (100, ''), (18, 'tx')],
    'name_initials': [('John Ronald Reuel Tolkien',), ('Dr. Grace Hopper',),
                      ('Martin Luther King Jr.',), ('Lovelace, Ada',),
                      ('Cher',), ('   ',), (None,), ('Mr',),
                      ('Jean-Luc Picard',), (42,)],
    'uk_postcode': [('SW1A OAA',), ('W1A',), ('SW1A1AAX',), ('sw1a-1aa',),
                    ('SW1A 1A1',), ('1SW 1AA',), ('',), (None,),
                    ('  ec1a   1bb ',), ('SW1A#1AA',)],
    'volume_unit_price': [(100, 250), (100, 249), (2.5, 10), (100, 9.9),
                          (100, 0), (100, -5), (-10, 5), (None, 10),
                          (100, 10), (100, 50)],
    'age_bracket': [('2010-05-05', '2026-05-05'), ('2008-05-05', '2026-05-05'),
                    ('1960-01-01', '2026-01-01'), ('1962-01-01', '2026-12-31'),
                    ('2000-02-29', '2018-02-28'), ('2000-02-29', '2025-02-28'),
                    ('2030-01-01', '2026-01-01'), ('1990-13-01', '2026-01-01'),
                    (None, '2026-01-01'), ('2001-07-01', '2026-06-30')],
    'prorated_refund': [(10.0, 1, 3), (29.99, 29, 30), (30, 30, 30),
                        (30, 31, 30), (30, -1, 30), (30, 5, 0),
                        (30, 2.5, 30), (None, 1, 30), (30, 0, 30),
                        (-30, 10, 30)],
    'meeting_end': [('09:00', 20), ('09:00', 1), ('17:30', 30),
                    ('17:30', 31), ('07:45', 30), ('9:00', 30), ('09:00', 0),
                    ('25:00', 30), (None, 30), ('08:00', 600)],
    'money_text': [(-12, 'USD'), (-1234.5, 'EUR'), (1234.5, 'JPY'),
                   (1234.5, 'CHF'), (10, 'usd'), (2.675, 'USD'),
                   (-0.001, 'USD'), (None, 'USD'), (5, None), (5, 'US')],
    'canonical_email': [('alice+news@example.com',), ('J.Doe@gmail.com',),
                        ('j.doe+x@googlemail.com',), ('no-at-sign.com',),
                        ('a@@b.com',), ('a@b',), ('+tag@example.com',),
                        ('john doe@example.com',), (None,),
                        ('first.last@Sub.Gmail.com',)],
    'overtime_pay': [(65, 10), (60, 10), (40.1, 20), (40.125, 20),
                     (40, 5), (40, 0), (-1, 20), (40, -10), (None, 20),
                     (0, 20)],
}

AGG_TYPICAL = [
    [10, 20, 30],
    [5.5, 3.25, 9.0, 7.0, 1.5],
    [100],
    [12, 15, 11, 19, 14],
]

AGG_EDGE = [
    [10, 20, 30, 40],
    [0, 10, 20, -5, 30],
    [None, 10, None, 30, 20],
    [],
    [None, 0, -1],
    ['15', 10, 20, 30],
    [7, 7, 7, 1],
    [2.5, 1],
]


def connect():
    conn = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, nargs) in SCALARS.items():
        conn.create_function(name, nargs, fn, deterministic=True)
    conn.create_aggregate(AGGREGATE[0], 1, AGGREGATE[1])
    return conn
