"""Policy oracle: a veterinary clinic's SQL functions."""
import math
import re
import sqlite3
from datetime import date, timedelta
from fractions import Fraction

# ---------------------------------------------------------------- helpers
EPOCH = date(1970, 1, 1)


def _num(x):
    """Numeric value as Fraction; missing/unreadable -> 0 (convention)."""
    if x is None or isinstance(x, bool):
        return Fraction(0)
    try:
        if isinstance(x, int):
            return Fraction(x)
        if isinstance(x, float):
            return Fraction(str(x)) if math.isfinite(x) else Fraction(0)
        s = str(x).strip()
        if not math.isfinite(float(s)):
            return Fraction(0)
        return Fraction(s)
    except (ValueError, TypeError, ZeroDivisionError):
        return Fraction(0)


def _txt(x):
    if x is None:
        return ''
    return x if isinstance(x, str) else str(x)


def _date(x):
    """Date value; missing/unreadable -> 1970-01-01 (convention)."""
    if isinstance(x, str):
        s = x.strip()
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', s):
            try:
                return date(int(s[:4]), int(s[5:7]), int(s[8:]))
            except ValueError:
                pass
    return EPOCH


def _money(fr):
    """Round up to the cent (convention)."""
    return math.ceil(fr * 100) / 100


def _add_months(d, n):
    """Month arithmetic; a missing day spills into the next month."""
    try:
        total = d.year * 12 + (d.month - 1) + n
        y, m = divmod(total, 12)
        return date(y, m + 1, 1) + timedelta(days=d.day - 1)
    except (ValueError, OverflowError):
        return None


def _iso(d):
    return None if d is None else d.isoformat()


def _cut(s):
    """Text results are cut to 12 characters (convention)."""
    return s[:12]


# -------------------------------------------------------------- functions
def dose_mg(weight_kg, mg_per_kg):
    d = math.ceil(max(_num(weight_kg), 0) * max(_num(mg_per_kg), 0))
    return int(min(d, 500))


def visit_fee(minutes, hourly_rate):
    m = _num(minutes)
    r = _num(hourly_rate)
    if m <= 0:
        return 0.0
    blocks = math.ceil(m / 15)
    fee = max(Fraction(blocks) * r / 4, Fraction(30))
    return _money(fee)


def size_class(weight_kg):
    w = _num(weight_kg)
    if w <= 1:
        return 'micro'
    if w <= 6:
        return 'small'
    if w <= 25:
        return 'medium'
    if w <= 45:
        return 'large'
    return 'giant'


def vaccine_next_due(last_date, interval_months):
    m = int(_num(interval_months))
    if m <= 0:
        m = 12
    return _iso(_add_months(_date(last_date), m))


def _alnum_part(x):
    s = ''.join(c for c in _txt(x) if c.isascii() and c.isalnum()).upper()
    return s if s else 'STRAY'


def pet_tag(pet_name, owner_surname):
    return _cut(_alnum_part(pet_name) + '-' + _alnum_part(owner_surname))


def boarding_cost(days, daily_rate):
    d = _num(days)
    r = max(_num(daily_rate), 0)
    if d <= 0:
        return 0.0
    dd = math.ceil(d)
    full = min(dd, 7)
    extra = max(dd - 7, 0)
    return _money(r * full + r * extra * Fraction(4, 5))


def loyalty_tier(visits, total_spent):
    v = min(max(math.floor(_num(visits)), 0), 30)
    s = max(_num(total_spent), 0)
    score = v * 10 + math.floor(s / 10)
    if score <= 100:
        return 'bronze'
    if score <= 300:
        return 'silver'
    if score <= 600:
        return 'gold'
    return 'platinum'


def membership_expiry(start_date, months):
    m = min(max(int(_num(months)), 0), 60)
    d = _add_months(_date(start_date), m)
    if d is not None and d.weekday() == 6:
        d = d + timedelta(days=1)
    return _iso(d)


def adoption_anniversary(adopt_date, years):
    y = math.floor(_num(years) + Fraction(1, 2))
    if y < 0:
        return None
    return _iso(_add_months(_date(adopt_date), y * 12))


def owner_label(first_name, last_name):
    f = _txt(first_name).strip()
    l = _txt(last_name).strip()
    l = l.capitalize() if l else 'Unknown'
    label = (l + ', ' + f[0].upper() + '.') if f else l
    return _cut(label)


def late_fee(days_late, invoice_amount):
    d = _num(days_late)
    a = _num(invoice_amount)
    if d <= 5 or a <= 0:
        return 0.0
    fee = min(a * d * Fraction(5, 1000), a / 4)
    return _money(fee)


def insurance_payout(claim_amount, deductible):
    c = _num(claim_amount)
    ded = max(_num(deductible), 0)
    rate = Fraction(4, 5) if c <= 1000 else Fraction(1, 2)
    return _money(max(c - ded, 0) * rate)


def installment_date(first_due_date, installment_no):
    n = min(max(math.floor(_num(installment_no)), 1), 12)
    return _iso(_add_months(_date(first_due_date), n - 1))


def invoice_code(prefix, number, year):
    p = ''.join(c for c in _txt(prefix) if c.isascii() and c.isalpha()).upper()
    p = p[:3].ljust(3, 'X')
    n = max(math.floor(_num(number)), 0)
    y = math.floor(_num(year)) % 100
    return _cut('%s%02d-%04d' % (p, y, n))


def reminder_text(pet_name, days_until):
    name = _txt(pet_name).strip()
    n = math.floor(_num(days_until))
    if n < 0:
        tail = 'overdue'
    elif n == 0:
        tail = 'today'
    elif n == 1:
        tail = 'tomorrow'
    else:
        tail = 'in %dd' % n
    return _cut((name + ' ' + tail).strip())


# ------------------------------------------------------------------- meta
SPEC = {
    'dose_mg': 'dose_mg(weight_kg, mg_per_kg): medication dose in mg for a patient of the given weight.',
    'visit_fee': 'visit_fee(minutes, hourly_rate): consultation fee for a visit of the given length.',
    'size_class': 'size_class(weight_kg): size category of a pet from its weight.',
    'vaccine_next_due': 'vaccine_next_due(last_date, interval_months): date the next vaccination is due (dates as YYYY-MM-DD).',
    'pet_tag': 'pet_tag(pet_name, owner_surname): short identification code printed on a pet tag.',
    'boarding_cost': 'boarding_cost(days, daily_rate): total price of a boarding stay.',
    'loyalty_tier': 'loyalty_tier(visits, total_spent): loyalty programme tier of a client.',
    'membership_expiry': 'membership_expiry(start_date, months): date a care-plan membership expires (dates as YYYY-MM-DD).',
    'adoption_anniversary': 'adoption_anniversary(adopt_date, years): date of a pet\'s adoption anniversary (dates as YYYY-MM-DD).',
    'owner_label': 'owner_label(first_name, last_name): owner name as shown on appointment sheets.',
    'late_fee': 'late_fee(days_late, invoice_amount): penalty charged on an overdue invoice.',
    'insurance_payout': 'insurance_payout(claim_amount, deductible): amount the pet insurer pays on a claim.',
    'installment_date': 'installment_date(first_due_date, installment_no): due date of the n-th instalment of a payment plan (dates as YYYY-MM-DD).',
    'invoice_code': 'invoice_code(prefix, number, year): printed invoice reference.',
    'reminder_text': 'reminder_text(pet_name, days_until): short SMS reminder for an upcoming appointment.',
}

_FUNCS = [dose_mg, visit_fee, size_class, vaccine_next_due, pet_tag,
          boarding_cost, loyalty_tier, membership_expiry, adoption_anniversary, owner_label,
          late_fee, insurance_payout, installment_date, invoice_code, reminder_text]
SCALARS = {f.__name__: (f, f.__code__.co_argcount) for f in _FUNCS}

FEATURES = {
    'f1': ['dose_mg', 'visit_fee', 'size_class', 'vaccine_next_due', 'pet_tag'],
    'f2': ['boarding_cost', 'loyalty_tier', 'membership_expiry', 'adoption_anniversary', 'owner_label'],
    'f3': ['late_fee', 'insurance_payout', 'installment_date', 'invoice_code', 'reminder_text'],
}

CONVENTIONS = [
    'money rounds up to the cent',
    'missing or unreadable input becomes zero value',
    'value equal to a threshold falls in the lower tier',
    'text results cut to 12 characters',
    'nonexistent day in target month spills into next month',
]
_M, _Z, _T, _C, _S = ['convention: ' + c for c in CONVENTIONS]

TYPICAL = {
    'dose_mg': [(10, 5), (20, 10), (4, 2), (30, 4), (8, 3)],
    'visit_fee': [(60, 120), (90, 100), (45, 80), (30, 90), (120, 75)],
    'size_class': [(3,), (12,), (30,), (60,)],
    'vaccine_next_due': [('2024-03-10', 12), ('2024-01-15', 6), ('2023-05-01', 3), ('2024-11-20', 1), ('2024-02-05', 24)],
    'pet_tag': [('Rex', 'Smith'), ('Bella', 'Jones'), ('Max', 'Li'), ('Luna', 'Cho')],
    'boarding_cost': [(3, 50), (5, 40), (1, 65), (7, 30)],
    'loyalty_tier': [(1, 50), (6, 300), (10, 500), (20, 800), (25, 1500), (28, 4000)],
    'membership_expiry': [('2024-01-15', 12), ('2024-03-05', 6), ('2023-10-10', 24), ('2024-06-20', 3), ('2024-02-12', 1)],
    'adoption_anniversary': [('2022-06-15', 1), ('2020-03-01', 3), ('2019-09-30', 2), ('2021-12-05', 5), ('2018-01-20', 10)],
    'owner_label': [('Anna', 'Smith'), ('Carlos', 'Ruiz'), ('Dana', 'Lee'), ('Eve', 'Walker')],
    'late_fee': [(10, 200), (20, 500), (8, 100), (30, 1000), (12, 250)],
    'insurance_payout': [(500, 100), (300, 50), (800, 200), (120, 20), (600, 0)],
    'installment_date': [('2024-01-10', 1), ('2024-01-10', 3), ('2024-05-15', 6), ('2023-11-01', 4), ('2024-02-05', 12)],
    'invoice_code': [('VET', 42, 2024), ('PET', 7, 2023), ('DOG', 1234, 2025), ('CAT', 99, 2022)],
    'reminder_text': [('Rex', 3), ('Bo', 5), ('Luna', 10), ('Max', 14), ('Zoe', 30)],
}

EDGE = {
    'dose_mg': [(3.3, 2.5), (100, 10), (50, 10), (None, 5), ('abc', 5), ('12', 5), (5, None), (0, 5)],
    'visit_fee': [(20, 100), (5, 40), (0, 100), (None, 100), (60, None), (75, 99.99), (50, 100), ('abc', 100)],
    'size_class': [(1,), (0.5,), (6,), (25,), (6.01,), (None,), ('abc',), (100,)],
    'vaccine_next_due': [('2024-01-31', 1), ('2023-01-31', 1), ('2024-03-10', 0), ('2024-03-10', -5),
                         (None, 6), ('garbage', 3), ('2024-03-10', None), ('2024-08-31', 6)],
    'pet_tag': [('Mr. Whiskers', 'Brown'), ('Rex', None), ('Rex', '  '), ('Sir Barks-a-lot', 'Wu'),
                ('d.o.g', 'x'), ('', 'Lee'), ('Rex', "O'Neil"), ('Buddy', 'Hansen'), ('Buddy', 'Hansens')],
    'boarding_cost': [(10, 50), (7.5, 50), (2.2, 50), (8, 33.33), (None, 50), (3, 'x'), (7, 50), (14, 20)],
    'loyalty_tier': [(10, 0), (5, 509.9), (40, 0), (30, 3000), (30, 3010), (None, None), ('x', 650), (30, 300)],
    'membership_expiry': [('2024-03-01', 6), ('2024-01-31', 1), ('2023-01-31', 1), ('2024-01-31', 2),
                          ('2024-01-15', 120), ('2024-01-15', 61), (None, 12), ('bad', 6), ('2024-01-15', None)],
    'adoption_anniversary': [('2020-02-29', 1), ('2020-02-29', 4), ('2022-06-15', 2.5), ('2022-06-15', 2.4),
                             ('2022-06-15', -1), ('2022-06-15', 0), (None, 2), ('bad', None)],
    'owner_label': [('Anna', 'McDONALD'), ('anna', 'smith'), ('', 'Smith'), (None, 'Smith'), ('Anna', ''),
                    ('Anna', None), ('Bartholomew', 'Featherstone'), ('Al', 'Smith-Jones')],
    'late_fee': [(5, 200), (6, 200), (7, 33.33), (60, 100), (50, 100), (None, 100), ('x', 100), (10, None), ('7', 200)],
    'insurance_payout': [(1000, 100), (1001, 100), (1500, 200), (50, 100), (100, 100), (None, 100), (500, None),
                         (333.33, 0), ('x', 'y')],
    'installment_date': [('2024-01-31', 2), ('2024-01-10', 13), ('2024-01-10', 0), ('2024-01-10', -3), (None, 3),
                         ('bad', 1), ('2024-01-10', None), ('2023-08-31', 7), ('2024-01-10', 50)],
    'invoice_code': [('Clinic', 5, 2024), ('ab', 5, 2024), ('', 5, 2024), ('VET', 123456, 2024), ('VET', 1234567, 2024),
                     (None, None, None), ('V3t!', 12, 2024), ('VET', 42, 'x'), ('VET', 5, 1999)],
    'reminder_text': [('Rex', 0), ('Rex', 1), ('Bella', 1), ('Rex', -2), ('Princess', -1), (None, 3), ('Rex', None),
                      ('Rex', 'abc'), ('Maximilian', 20)],
}

DECISIONS = {
    'dose_mg': [_Z, 'dose rounds up to a whole mg', 'dose capped at 500 mg'],
    'visit_fee': [_M, _Z, 'time billed in 15-minute blocks', 'minimum fee of 30 for any visit'],
    'size_class': [_Z, _T, 'extra micro class for pets of 1 kg or less'],
    'vaccine_next_due': [_Z, _S, 'interval of zero or less means 12 months'],
    'pet_tag': [_C, 'non-alphanumerics dropped and upper-cased', 'blank part becomes STRAY'],
    'boarding_cost': [_M, _Z, 'days beyond the 7th at 80 percent', 'partial days round up to whole days'],
    'loyalty_tier': [_Z, _T, 'spend counts one point per whole 10', 'visits counted up to 30'],
    'membership_expiry': [_Z, _S, 'expiry on a Sunday moves to Monday', 'membership length limited to 60 months'],
    'adoption_anniversary': [_Z, _S, 'fractional years round half up', 'negative years give NULL'],
    'owner_label': [_C, 'surname capitalised first letter only', 'blank first name gives surname alone', 'blank surname becomes Unknown'],
    'late_fee': [_M, _Z, _T, 'fee capped at 25 percent of invoice'],
    'insurance_payout': [_M, _Z, _T, 'claims over 1000 reimbursed at 50 percent of whole claim'],
    'installment_date': [_Z, _S, 'installment number limited to 12', 'installment number below 1 counts as 1'],
    'invoice_code': [_Z, _C, 'prefix cut to first 3 letters', 'short prefix padded with X'],
    'reminder_text': [_Z, _C, 'special words for today and tomorrow', 'past days say overdue'],
}

DECISION_EXAMPLES = {
    'dose_mg': [(12, 'x'), (7.3, 2), (90, 7)],
    'visit_fee': [(60, 100.001), ('x', 100), (16, 120), (15, 40)],
    'size_class': [('n/a',), (45,), (0.8,)],
    'vaccine_next_due': [('xx', 12), ('2023-12-31', 2), ('2024-05-05', -1)],
    'pet_tag': [('Charlemagne', 'Roberts'), ('T-Rex!', 'Ng'), (' ', 'Kim')],
    'boarding_cost': [(3, 12.341), ('n/a', 10), (9, 20), (1.1, 100)],
    'loyalty_tier': [(None, 1500), (10, 2000), (9, 109.99), (50, 0)],
    'membership_expiry': [('??', 3), ('2023-12-31', 2), ('2024-06-01', 3), ('2020-05-05', 200)],
    'adoption_anniversary': [('??', 1), ('2024-02-29', 1), ('2021-04-10', 3.5), ('2021-04-10', -2)],
    'owner_label': [('Ian', 'Wolfeschlegel'), ('Ian', 'vAN'), ('  ', 'Ito'), ('Zoe', ' ')],
    'late_fee': [(7, 77.77), ('?', 300), (5.0, 999), (90, 400)],
    'insurance_payout': [(777.77, 10), ('?', 5), (1000, 0), (3000, 500)],
    'installment_date': [('??', 2), ('2023-12-31', 3), ('2024-01-10', 99), ('2024-01-10', -9)],
    'invoice_code': [('DOG', 'n/a', 2020), ('VET', 98765432, 2024), ('Sunrise', 3, 2021), ('Z', 8, 2021)],
    'reminder_text': [('Ed', 'n/a'), ('Wolfgang', 99), ('Bo', 1), ('Ed', -9)],
}


def connect():
    con = sqlite3.connect(':memory:', isolation_level=None)
    for name, (fn, n) in SCALARS.items():
        con.create_function(name, n, fn, deterministic=True)
    return con
