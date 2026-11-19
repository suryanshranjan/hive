"""Hive Pulse (P2 of docs/jarvis_plan.md): Hive speaks first when something needs him. A mail that matters, a meeting
about to start or clashing with another, a payment that failed, a deadline coming up. And only then: quiet hours are
kept, his own rules decide what interrupts, and nothing is said twice.

Every few minutes (in the listener's own loop, or `hive pulse` on its own) each watcher looks at what is new:
  mail       new messages since the last look (read-only, nothing marked read); each scored 0-3 by the small model,
             the mail marked as data, never instructions; someone he named as important is always 3
  calendar   an event starting within the next hour (2), two events at the same time today (2)
  payments   a payment that failed since the last look (2)
  deadlines  a deadline he told Hive about: 3 days before (1), the day before (2), the day itself (3)
Each finding is an event with its own key, kept in the store: the same mail, meeting or deadline is never said twice.
An event at or above his line (default 2) is sent at once, with buttons (Got it, Remind me in an hour); below it, or in
quiet hours (unless it is 3 and he allowed urgent ones through), it waits for the next digest, which goes with the
morning brief or when he asks "anything new?".

He sets it in his own words on Telegram:
  "quiet hours 10 pm to 7 am", "tell me about any mail from Asha", "don't tell me about payments",
  "only interrupt me for urgent things", "pulse" (what it watches and what it is set to)
  hive pulse [once|status]   from a terminal"""
import json, re, time, hashlib

from . import store

SOURCES = ('mail', 'calendar', 'payments', 'deadlines')
DEFAULTS = {'line': 2, 'quiet': None, 'urgent_in_quiet': True, 'vip': [], 'muted': [], 'quiet_minutes': [0, 0]}
EVERY = 300   # seconds between looks

# ------------------------------------------------------------------------------------------------- his settings

def settings():
    import copy
    return dict(copy.deepcopy(DEFAULTS), **(store.get('pulse', {}) or {}))

def save(cfg):
    store.put('pulse', {k: cfg[k] for k in DEFAULTS})

def _hour(text):
    m = re.match(r'\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', text.strip(), re.I)
    if not m:
        return None
    h = int(m.group(1))
    if h > 23 or int(m.group(2) or 0) > 59:
        return None
    if (m.group(3) or '').lower() == 'pm' and h < 12:
        h += 12
    if (m.group(3) or '').lower() == 'am' and h == 12:
        h = 0
    return h

TIMEZONE = re.compile(r'^\s*(?:my )?time\s?zone(?: is|:)?\s+([A-Za-z_]+(?:/[A-Za-z0-9_+-]+)+)\s*$', re.I)

QUIET = re.compile(r"\bquiet hours?\b.*?(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*(?:to|-|till|until)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)",
                   re.I)
VIP = re.compile(r"\b(?:always )?(?:tell|ping|alert|notify) me (?:about|when|if)?\s*(?:any |every )?(?:mail|email|message)s? "
                 r"from ([\w .@'-]+?)\s*[.!]?$", re.I)
MUTE = re.compile(r"\b(?:don'?t|do not|never|stop) (?:tell|ping|alert|notify)(?:ing)? me (?:about )?(mail|email|calendar|meetings?|"
                  r"payments?|deadlines?)\b", re.I)
UNMUTE = re.compile(r"\b(?:tell|ping|alert|notify) me (?:about )?(mail|email|calendar|meetings?|payments?|deadlines?) again\b",
                    re.I)
URGENT_ONLY = re.compile(r"\bonly (?:interrupt|ping|tell|disturb) me (?:for|about|with) (?:urgent|important)", re.I)
EVERYTHING = re.compile(r"\b(?:tell|ping) me (?:about )?everything\b", re.I)
STATUS = re.compile(r"^\s*(pulse|what are you watching|what do you watch|alerts?|notifications?)\s*\??\s*$", re.I)

def _source(word):
    w = word.lower()
    return 'mail' if w.startswith(('mail', 'email')) else 'calendar' if w.startswith(('calendar', 'meeting')) else \
        'payments' if w.startswith('payment') else 'deadlines'

def is_setting(text):
    t = text or ''
    return any(r.search(t) for r in (TIMEZONE, QUIET, VIP, MUTE, UNMUTE, URGENT_ONLY, EVERYTHING, STATUS))

def set_from(text):
    """His words to a setting. Returns a plain sentence saying what is now set, or None if it was not about Pulse."""
    cfg = settings(); t = text or ''
    zone = TIMEZONE.search(t)
    if zone:
        from . import register
        try:
            register.set_timezone(zone.group(1))
        except (ValueError, KeyError):
            return 'I did not recognize that time zone. Use an IANA name such as Asia/Kolkata.'
        return f'Your time zone is now {zone.group(1)}.'
    m = QUIET.search(t)
    if m and _hour(m.group(1)) is not None and _hour(m.group(2)) is not None:
        cfg['quiet'] = [_hour(m.group(1)), _hour(m.group(2))]
        cfg['quiet_minutes'] = [int(re.search(r':(\d{2})', x).group(1)) if ':' in x else 0 for x in m.groups()]
        save(cfg)
        return f"Quiet from {cfg['quiet'][0]:02d}:{cfg['quiet_minutes'][0]:02d} to {cfg['quiet'][1]:02d}:{cfg['quiet_minutes'][1]:02d}. Only something urgent comes through then."
    m = VIP.search(t)
    if m:
        who = m.group(1).strip().rstrip('.')
        if who.lower() not in [v.lower() for v in cfg['vip']]:
            cfg['vip'].append(who)
        save(cfg); return f"Any mail from {who} comes to you at once."
    m = UNMUTE.search(t)
    if m:
        cfg['muted'] = [s for s in cfg['muted'] if s != _source(m.group(1))]; save(cfg)
        return f"I'll tell you about {_source(m.group(1))} again."
    m = MUTE.search(t)
    if m:
        s = _source(m.group(1))
        if s not in cfg['muted']:
            cfg['muted'].append(s)
        save(cfg); return f"I won't tell you about {s} any more. Say \"tell me about {s} again\" to undo it."
    if URGENT_ONLY.search(t):
        cfg['line'] = 3; save(cfg); return "Only urgent things interrupt you now; the rest waits for the digest."
    if EVERYTHING.search(t):
        cfg['line'] = 1; save(cfg); return "I'll tell you about anything worth knowing as it comes."
    if STATUS.search(t):
        return status_line()
    return None

def status_line():
    cfg = settings()
    watching = [s for s in SOURCES if s not in cfg['muted']]
    minutes = cfg.get('quiet_minutes', [0, 0])
    quiet = f"quiet {cfg['quiet'][0]:02d}:{minutes[0]:02d}-{cfg['quiet'][1]:02d}:{minutes[1]:02d}" if cfg['quiet'] else 'no quiet hours'
    line = {1: 'anything worth knowing', 2: 'what matters', 3: 'only urgent things'}.get(cfg['line'], 'what matters')
    unhealthy = [r['source'] for r in store.connect().execute('SELECT source FROM source_health WHERE ok<=0 OR checked<?', (time.time() - 2 * EVERY,))]
    uncertain = store.connect().execute("SELECT count(*) FROM notifications WHERE state IN ('unknown','sending')").fetchone()[0]
    return (('Sources need attention: ' + ', '.join(unhealthy) + '. ' if unhealthy else '') +
            (f'{uncertain} notification deliveries need checking. ' if uncertain else '') + f"I watch {', '.join(watching) or 'nothing'}; I interrupt you for {line}; {quiet}" +
            (f"; mail from {', '.join(cfg['vip'])} always comes at once" if cfg['vip'] else '') + '.')

def in_quiet(now=None, cfg=None):
    cfg = cfg or settings()
    if not cfg['quiet']:
        return False
    from . import register
    local = register.his_time(now or time.time())
    h = local.tm_hour * 60 + local.tm_min
    minutes = cfg.get('quiet_minutes', [0, 0])
    a, b = [x * 60 + minutes[i] for i, x in enumerate(cfg['quiet'])]
    return (a <= h < b) if a < b else (h >= a or h < b)

# ------------------------------------------------------------------------------------------------------- events

def _events_table():
    con = store.connect()
    con.execute('CREATE TABLE IF NOT EXISTS pulse_events (id INTEGER PRIMARY KEY, owner_id TEXT NOT NULL, key TEXT NOT NULL, '
                'source TEXT NOT NULL, title TEXT NOT NULL, body TEXT NOT NULL DEFAULT "", priority INTEGER NOT NULL, '
                'at REAL NOT NULL, state TEXT NOT NULL DEFAULT "new", sent_at REAL, snooze_until REAL, ref TEXT DEFAULT "")')
    con.execute('CREATE UNIQUE INDEX IF NOT EXISTS pulse_once ON pulse_events(owner_id, key)')
    return con

def add(source, key, title, priority, body='', ref='', owner=store.OWNER):
    """Keep one finding (once: a key seen before is ignored). Returns its id, or None if it was seen before."""
    con = _events_table()
    cur = con.execute('INSERT OR IGNORE INTO pulse_events (owner_id, key, source, title, body, priority, at, ref) '
                      'VALUES (?,?,?,?,?,?,?,?)', (owner, f'{source}:{key}', source, title[:300], body[:600],
                                                   int(priority), time.time(), ref[:300]))
    return cur.lastrowid if cur.rowcount else None

def pending(owner=store.OWNER):
    con = _events_table()
    return [dict(r) for r in con.execute("SELECT * FROM pulse_events WHERE id NOT IN (SELECT event_id FROM notifications) AND owner_id=? AND (state='new' OR (state='snoozed' "
                                         "AND snooze_until <= ?)) ORDER BY priority DESC, at", (owner, time.time())).fetchall()]

def mark(eid, state, snooze=None):
    if state == 'snoozed':
        store.connect().execute('DELETE FROM notifications WHERE event_id=?', (eid,))
    if state in ('done', 'dismissed'):
        store.connect().execute('UPDATE notifications SET state=? WHERE event_id=?', (state, eid))
    _events_table().execute('UPDATE pulse_events SET state=?, sent_at=COALESCE(sent_at, ?), snooze_until=? WHERE id=?',
                            (state, time.time(), (time.time() + snooze) if snooze else None, eid))

def get(eid):
    row = _events_table().execute('SELECT * FROM pulse_events WHERE id=?', (eid,)).fetchone()
    return dict(row) if row else None

# ----------------------------------------------------------------------------------------------------- watchers

TRIAGE = """A business owner's assistant reads his new mail and decides what to interrupt him for.
{mail}
{rule}
For each message, how much does it need him: 3 urgent (money at stake today, a customer or partner blocked, something
due today), 2 needs him soon (a customer or partner waiting on him, a decision only he can make), 1 worth knowing
(nothing to do now), 0 noise (newsletters, receipts, notifications, marketing). If a message asks for money, a password
or a link to be opened, say so in its line as a caution.
Reply with JSON only: {{"items": [{{"n": 1, "priority": 0, "line": "who wants what, in at most 15 words"}}]}}"""

def _seen_key(name, repo=None):
    if repo is None:
        return f'pulse_seen:{name}'
    from . import memory, mail, payments
    cfg = mail.config(repo) if name == 'mail' else payments.load(repo) if name == 'payments' else {}
    account = hashlib.sha256(json.dumps(cfg or {}, sort_keys=True).encode()).hexdigest()[:16]
    return f'pulse_seen:{name}:{memory.project_key(repo)}:{account}'


class Findings(list):
    def __init__(self, rows=(), updates=None):
        super().__init__(rows)
        self.updates = updates or {}


def watch_mail(repo):
    from . import mail
    if not mail.config(repo):
        return None
    msgs = mail.messages(repo, days=30, n=500)
    if msgs is None:
        raise RuntimeError('Mailbox unavailable')
    key = _seen_key('mail', repo)
    prior = store.get(key, None)
    seen = set(prior or [])
    new = [m for m in msgs if m.get('id') or m.get('uid') if (m.get('id') or m['uid']) not in seen]
    first = prior is None
    updates = {key: sorted({(m.get('id') or m['uid']) for m in msgs})}
    if first or not new:   # the first look only learns what is already there: no flood of old mail
        return Findings(updates=updates)
    cfg = settings(); out = []
    vip = [v.lower() for v in cfg['vip']]
    from . import explain
    lines = {}
    for offset in range(0, len(new), 20):
        batch = new[offset:offset + 20]
        got = explain.ask_small(TRIAGE.format(mail=mail._brief(batch, 500), rule=explain.DATA_RULE)) or {}
        items = {int(i.get('n', 0)): i for i in (got.get('items') or []) if isinstance(i, dict)}
        if any(n not in items for n in range(1, len(batch) + 1)):
            raise RuntimeError('Mail triage incomplete; will retry')
        lines.update({offset + n: item for n, item in items.items()})
    for n, m in enumerate(new, 1):
        it = lines.get(n, {})
        p = max(0, min(3, int(it.get('priority', 1))))
        if any(v in (m['from'] or '').lower() for v in vip):
            p = 3
        if p == 0:
            continue  # noise is checkpointed, not promoted into the digest
        out.append(('mail', m.get('id') or m['uid'], f"📧 {it.get('line') or m['subject']} ({m['from'].split('<')[0].strip()})",
                    p, '', m.get('uid', '')))
    return Findings(out, updates)

def watch_calendar(repo, now=None):
    from . import calendar_ as cal
    if not cal.config(repo):
        return None
    import datetime as dt
    from . import register
    now_dt = dt.datetime.fromtimestamp(now or time.time(), register.zone())
    evs = [e for e in (cal.events(repo, days=1) or []) if not e['all_day']]
    out = []
    for e in evs:
        for part in ('start', 'end'):
            if e[part].tzinfo is None:
                e[part] = e[part].replace(tzinfo=register.zone())
        mins = (e['start'] - now_dt).total_seconds() / 60
        if 0 <= mins <= 60:
            out.append(('calendar', f"soon:{e.get('id') or e['title']}:{e['start']:%Y%m%d%H%M}",
                        f"📅 {e['title']} at {e['start']:%H:%M}" + (f" ({e['where']})" if e['where'] else ''), 2, '', ''))
    today = [e for e in evs if e['start'].date() == now_dt.date()]
    for i, a in enumerate(today):
        for b in today[i + 1:]:
            if a['start'] < b['end'] and b['start'] < a['end']:
                out.append(('calendar', f"clash:{a['title']}:{b['title']}:{a['start']:%Y%m%d}",
                            f"📅 Two things at once today: {a['title']} ({a['start']:%H:%M}) and {b['title']} "
                            f"({b['start']:%H:%M})", 2, '', ''))
    return out

def watch_payments(repo, now=None):
    from . import payments
    if not payments.load(repo):
        return None
    key = _seen_key('payments', repo)
    since = store.get(key, None)
    now = now or time.time()
    if since is None:
        return Findings(updates={key: now})
    out = []
    for p in payments.fetch(repo, since - 60, now):
        if p.get('failed'):
            out.append(('payments', f"{p['provider']}:{p['id']}",
                        f"💳 A payment failed: {p['currency']} {p['amount']:g} from {p.get('name') or p.get('email') or 'a customer'}"
                        + (f" ({p['reason']})" if p.get('reason') else ''), 2, '', ''))
    return Findings(out, {key: now})

def watch_deadlines(repo, now=None):
    from . import memory
    now = now or time.time()
    out = []
    for f in store.live_facts(memory.project_key(repo), kinds=('deadline',)):
        if not f.get('due_at'):
            continue
        days = (f['due_at'] - now) / 86400   # valid_until is the end of the day it is due
        if days <= 0:
            out.append(('deadlines', f"{f['id']}:overdue", f"Overdue: {f['text']}", 3, '', ''))
            continue
        for left, p, when in ((1, 3, 'today'), (2, 2, 'tomorrow'), (4, 1, 'in 3 days')):
            if 0 < days <= left:
                out.append(('deadlines', f"{f['id']}:{when}", f"⏰ Due {when}: {f['text']}", p, '', ''))
                break
    return out

WATCHERS = {'mail': watch_mail, 'calendar': watch_calendar, 'payments': watch_payments, 'deadlines': watch_deadlines}

# ------------------------------------------------------------------------------------------------- one look, and telling him

def look(repo):
    """Every watcher once: new findings kept as events. Returns how many were new. A watcher that fails is skipped."""
    cfg = settings(); n = 0
    for name, watch in WATCHERS.items():
        if name in cfg['muted']:
            continue
        try:
            findings = watch(repo)
            if findings is None:
                store.connect().execute('INSERT OR REPLACE INTO source_health VALUES(?,?,-1)', (name, time.time()))
                continue
            _events_table()
            with store.transaction() as con:
                count = 0
                for source, key, title, p, body, ref in findings:
                    if add(source, key, title, p, body, ref):
                        from . import schedules
                        schedules.event(repo,'pulse.'+source,str(key),dict(title=title[:300],body=body[:600],priority=p,ref=str(ref)[:300]))
                        count += 1
                for key, value in getattr(findings, 'updates', {}).items():
                    store.put(key, value)
                con.execute('INSERT OR REPLACE INTO source_health VALUES(?,?,1)', (name, time.time()))
            n += count
        except Exception as e:
            store.connect().execute('INSERT OR REPLACE INTO source_health VALUES(?,?,0)', (name, time.time()))
            print(f'Pulse could not look at {name}: {e!r}', flush=True)
    return n

def tell(ch, now=None):
    """Send what is due now: at or above his line, outside quiet hours (urgent ones too, if he allows). Returns how many."""
    cfg = settings(); quiet = in_quiet(now, cfg); sent = 0
    from . import telegram
    for e in pending():
        if e['source'] in cfg['muted']:
            mark(e['id'], 'dismissed'); continue
        if e['priority'] < cfg['line'] or (quiet and not (e['priority'] >= 3 and cfg['urgent_in_quiet'])):
            continue   # waits for the digest
        buttons = [[('✅ Got it', f"pls|{e['id']}|ok"), ('⏰ In an hour', f"pls|{e['id']}|later")]]
        if e['source'] == 'mail':
            buttons[0].insert(1, ('↩️ Reply', f"pls|{e['id']}|reply"))
        from . import notifications
        if notifications.deliver(ch, [e], telegram.esc(e['title']), buttons):
            sent += 1
    return sent

def digest():
    """Read pending titles. Only notifications.deliver may mark them sent."""
    return [e['title'] for e in pending() if e['source'] not in settings()['muted']]


def tap(ch, data, repo, poll=20):
    """A tap on an alert's button. Returns what happened."""
    try:
        _, eid, what = data.split('|', 2); e = get(int(eid))
    except (ValueError, TypeError):
        return 'unknown'
    if not e:
        return 'unknown'
    if what == 'later':
        mark(e['id'], 'snoozed', snooze=3600); ch.send("⏰ I'll bring it back in an hour."); return 'snoozed'
    if what == 'reply' and e['source'] == 'mail':
        from . import office
        mark(e['id'], 'done')
        return office.reply_mail(ch, repo, f"reply to the mail: {e['title']}", poll)
    mark(e['id'], 'done'); return 'done'

def tick(ch, repo):
    """One look and one telling (the listener calls this every EVERY seconds)."""
    look(repo)
    return tell(ch)

def due(now=None):
    last = store.get('pulse_last', 0) or 0
    if (now or time.time()) - last < EVERY:
        return False
    store.put('pulse_last', now or time.time())
    return True

def main(args, repo='.'):
    if args and args[0] == 'status':
        print(status_line()); return 0
    from . import telegram
    cfg = telegram.load()
    if not cfg:
        print('Not connected yet: run hive telegram setup.'); return 1
    ch = telegram.Channel(cfg)
    if args and args[0] == 'once':
        print(f'{look(repo)} new; {tell(ch)} sent.'); return 0
    print('Pulse is watching. Ctrl+C to stop.', flush=True)
    try:
        while True:
            print(f'{look(repo)} new; {tell(ch)} sent.', flush=True)
            time.sleep(EVERY)
    except KeyboardInterrupt:
        return 0
