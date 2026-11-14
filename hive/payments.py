"""His payments, read-only (the owner, Nov 15 2026: Razorpay and Stripe). Hive answers "how much did we make this week?",
"any failed payments?", "who paid the most?" from his payment provider's own records, and never moves money: it only
ever reads (GET), never creates, refunds or captures anything.

- Stripe: a restricted key with read-only access (Dashboard, Developers, API keys, "Create restricted key", Read on
  Charges, Customers, Refunds), so even the key cannot move money.
- Razorpay: its keys cannot be limited to reading, so Hive says so plainly; its code only reads with them.

Keys stay on this computer (~/.hive/payments/<project>.json, readable by him only), never in his repository, and never
shown to him again or to builders."""
import base64, datetime as dt, json, os, time, urllib.parse, urllib.request

DIR = os.path.join(os.path.expanduser('~'), '.hive', 'payments')
BASE = {'stripe': 'https://api.stripe.com', 'razorpay': 'https://api.razorpay.com'}   # tests point these at stand-ins
ZERO_DECIMAL = {'jpy', 'krw', 'vnd', 'clp', 'pyg', 'ugx', 'xaf', 'xof'}

def _path(repo):
    from . import memory
    return os.path.join(DIR, memory.project_key(repo) + '.json')

def load(repo):
    try:
        return json.load(open(_path(repo), encoding='utf-8'))
    except (OSError, ValueError):
        return {}

def _save(repo, d):
    os.makedirs(DIR, exist_ok=True)
    p = _path(repo)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=1)
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass

def _get(provider, key, path, params):
    """One read. Only GET is ever sent."""
    url = BASE[provider] + path + '?' + urllib.parse.urlencode(params, doseq=True)
    if provider == 'stripe':
        auth = 'Bearer ' + key['secret']
    else:
        auth = 'Basic ' + base64.b64encode(f"{key['id']}:{key['secret']}".encode()).decode()
    req = urllib.request.Request(url, headers={'Authorization': auth, 'User-Agent': 'hive-payments'}, method='GET')
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))

def add(repo, provider, secret, key_id=None):
    """Keep one provider's key once a read works. Returns (ok, what to tell him)."""
    key = {'secret': secret.strip(), 'id': (key_id or '').strip()}
    try:
        if provider == 'stripe':
            _get('stripe', key, '/v1/charges', {'limit': 1})
            kind = ('a read-only key' if key['secret'].startswith('rk_') else
                    'a full key: please make a restricted, read-only one when you can (Dashboard, Developers, API keys)')
        else:
            _get('razorpay', key, '/v1/payments', {'count': 1})
            kind = "Razorpay keys can't be limited to reading, so know that I only ever read with it"
    except Exception as e:
        return False, f"I couldn't read your {provider.title()} payments with that key ({str(e)[:120]})."
    d = load(repo); d[provider] = dict(key, added=time.time()); _save(repo, d)
    return True, f"Connected to {provider.title()} ({kind}). I never move money."

def _money(amount, currency):
    return amount / (1 if currency.lower() in ZERO_DECIMAL else 100)

def fetch(repo, since, until=None, cap=2000):
    """Every payment between two times (epoch seconds), from each connected provider, in one shape:
    [{'provider', 'id', 'amount', 'currency', 'status', 'paid', 'failed', 'refunded', 'email', 'name', 'what',
    'created', 'reason'}]. Amounts in his currency's main unit (rupees, dollars)."""
    until = until or time.time()
    out = []
    keys = load(repo)
    if 'stripe' in keys:
        params, n = {'limit': 100, 'created[gte]': int(since), 'created[lte]': int(until)}, 0
        while n < cap:
            page = _get('stripe', keys['stripe'], '/v1/charges', params)
            for c in page.get('data', []):
                bd = c.get('billing_details') or {}
                out.append({'provider': 'stripe', 'id': c['id'], 'amount': _money(c.get('amount', 0), c.get('currency', 'usd')),
                            'currency': c.get('currency', '').upper(), 'status': c.get('status'),
                            'paid': c.get('status') == 'succeeded' and c.get('paid', True),
                            'failed': c.get('status') == 'failed', 'refunded': _money(c.get('amount_refunded', 0), c.get('currency', 'usd')),
                            'email': bd.get('email') or c.get('receipt_email') or '', 'name': bd.get('name') or '',
                            'what': c.get('description') or '', 'created': c.get('created', 0),
                            'reason': c.get('failure_message') or ''})
                n += 1
            if not page.get('has_more') or not page.get('data'):
                break
            params['starting_after'] = page['data'][-1]['id']
    if 'razorpay' in keys:
        skip = 0
        while skip < cap:
            page = _get('razorpay', keys['razorpay'], '/v1/payments', {'from': int(since), 'to': int(until), 'count': 100,
                                                                       'skip': skip})
            items = page.get('items', [])
            for p in items:
                out.append({'provider': 'razorpay', 'id': p['id'], 'amount': _money(p.get('amount', 0), p.get('currency', 'inr')),
                            'currency': p.get('currency', '').upper(), 'status': p.get('status'),
                            'paid': p.get('status') == 'captured', 'failed': p.get('status') == 'failed',
                            'refunded': _money(p.get('amount_refunded', 0), p.get('currency', 'inr')),
                            'email': p.get('email') or '', 'name': (p.get('notes') or {}).get('name', '') if isinstance(p.get('notes'), dict) else '',
                            'what': p.get('description') or '', 'created': p.get('created_at', 0),
                            'reason': p.get('error_description') or ''})
            if len(items) < 100:
                break
            skip += 100
    # only what falls in the dates asked about, whatever a provider sends back (stripe-mock ignores the filter; a real
    # API's paging could too), so an old payment is never counted as this week's
    return sorted((p for p in out if since <= p['created'] <= until), key=lambda p: -p['created'])

def totals(pays):
    """What came in, by currency: {'INR': {'paid': n, 'count': k, 'failed': f, 'refunded': r}}."""
    t = {}
    for p in pays:
        c = t.setdefault(p['currency'] or '?', {'paid': 0.0, 'count': 0, 'failed': 0, 'refunded': 0.0})
        if p['paid']:
            c['paid'] += p['amount']; c['count'] += 1
        if p['failed']:
            c['failed'] += 1
        c['refunded'] += p['refunded']
    return t

def _table(pays, rows=150):
    return '\n'.join(f"{dt.datetime.fromtimestamp(p['created']).strftime('%a %d %b %H:%M')} | {p['provider']} | "
                     f"{p['currency']} {p['amount']:.2f} | {p['status']}" + (f" (refunded {p['refunded']:.2f})" if p['refunded'] else '') +
                     f" | {p['name'] or p['email'] or '-'} | {p['what'][:40]}" + (f" | why: {p['reason'][:60]}" if p['reason'] else '')
                     for p in pays[:rows])

ANSWER = """A business owner asked his assistant about his payments: "{question}"
Today is {today}. His payments from {since} to now, newest first ({n} in all; sums worked out exactly below):
{sums}

The payments:
{table}

Answer from these records only. Money that came in means successful payments (succeeded or captured), less refunds if
he asks what he kept. Use the exact sums above rather than adding up yourself. Name failed payments and who they were
from if he asks. If what he asks is outside these dates, say so.
Reply with JSON only: {{"answer": "..."}}"""

def _range(question):
    """How far back his question reaches (days)."""
    q = question.lower()
    for words, days in ((('today',), 1), (('yesterday',), 2), (('this week', 'week', '7 days'), 7),
                        (('this month', 'month', '30 days'), 31), (('quarter', '90 days'), 92), (('year',), 366)):
        if any(w in q for w in words):
            return days
    return 31

def answer(repo, question):
    from . import explain
    if not load(repo):
        return {'ok': False, 'say': 'no payments'}
    days = _range(question)
    now = dt.datetime.now()
    start = (now.replace(hour=0, minute=0, second=0, microsecond=0) - dt.timedelta(days=days - 1))
    if days in (7,) and 'this week' in question.lower():
        start = (now - dt.timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    if days == 31 and 'this month' in question.lower():
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    try:
        pays = fetch(repo, start.timestamp())
    except Exception as e:
        return {'ok': False, 'say': f"I couldn't reach your payments just now ({str(e)[:100]})."}
    sums = '\n'.join(f"{c}: {v['paid']:.2f} from {v['count']} successful payments; {v['failed']} failed; "
                     f"{v['refunded']:.2f} refunded; kept {v['paid'] - v['refunded']:.2f}" for c, v in totals(pays).items()) or '(none)'
    got = explain.ask_json(explain.plain(ANSWER.format(question=question, today=now.strftime('%A %d %B %Y'),
                                                       since=start.strftime('%a %d %b'), n=len(pays), sums=sums,
                                                       table=_table(pays) or '(none)')))
    if not got or not got.get('answer'):
        return {'ok': False, 'say': "I couldn't work that out just now. Try again in a minute."}
    return {'ok': True, 'say': got['answer'], 'totals': totals(pays)}

def summary(repo):
    k = load(repo)
    return f"His payments: {', '.join(p.title() for p in k)} (read-only; never moves money)" if k else ''
