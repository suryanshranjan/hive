"""His calendar, read-only (the owner, Nov 15 2026: Google Calendar). Google gives every calendar a private address in
iCal format (Settings, his calendar, "Integrate calendar", "Secret address in iCal format"); any calendar app that
publishes iCal works the same way (Outlook, Apple, Zoho). Hive reads his events from it and can never change them.

The address is a secret, kept on this computer only (~/.hive/calendar/<project>.json), never in his repository.
Named calendar_ so it does not hide Python's own calendar module."""
import datetime as dt, json, os, re, time, urllib.request

DIR = os.path.join(os.path.expanduser('~'), '.hive', 'calendar')
ICS = re.compile(r'https?://\S+?\.ics\b\S*|https://calendar\.google\.com/calendar/ical/\S+|webcal://\S+', re.I)

def _path(repo):
    from . import memory
    return os.path.join(DIR, memory.project_key(repo) + '.json')

def config(repo):
    try:
        return json.load(open(_path(repo), encoding='utf-8'))
    except (OSError, ValueError):
        return {}

def _fetch(url):
    url = re.sub(r'^webcal://', 'https://', url)
    req = urllib.request.Request(url, headers={'User-Agent': 'hive-calendar'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8', 'replace')

def setup(repo, url):
    """Keep his calendar's address once it reads. Returns (ok, what to tell him)."""
    try:
        evs = events_from(_fetch(url))
    except Exception as e:
        return False, f"I couldn't read that calendar address ({str(e)[:120]}). In Google Calendar it's under Settings, " \
                      "your calendar, Integrate calendar: \"Secret address in iCal format\"."
    os.makedirs(DIR, exist_ok=True)
    p = _path(repo)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump({'url': url, 'added': time.time()}, f)
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass
    soon = [e for e in evs if dt.datetime.now() <= e['start'] <= dt.datetime.now() + dt.timedelta(days=7)]
    return True, f"Connected to your calendar: {len(soon)} event{'s' if len(soon) != 1 else ''} in the next 7 days. " \
                 "I can only read it."

def _unfold(text):
    return re.sub(r'\r?\n[ \t]', '', text)

def _when(value, params=''):
    """An iCal date or time as a local naive datetime (all-day events at midnight)."""
    v = value.strip()
    if len(v) == 8:   # all day: 20261116
        return dt.datetime.strptime(v, '%Y%m%d'), True
    utc = v.endswith('Z')
    t = dt.datetime.strptime(v.rstrip('Z')[:15], '%Y%m%dT%H%M%S')
    if utc:
        t = t.replace(tzinfo=dt.timezone.utc).astimezone().replace(tzinfo=None)
    return t, False

def events_from(ics, horizon_days=60):
    """The events in an iCal text: [{'title', 'start', 'end', 'all_day', 'where', 'notes'}], weekly and daily repeats
    expanded up to horizon_days ahead (the common ones; others are shown once)."""
    out = []
    for block in re.findall(r'BEGIN:VEVENT(.*?)END:VEVENT', _unfold(ics), re.S):
        f = {}
        for line in block.strip().splitlines():
            if ':' not in line:
                continue
            k, v = line.split(':', 1)
            name, _, params = k.partition(';')
            f.setdefault(name.upper(), (v, params))
        if 'DTSTART' not in f or f.get('STATUS', ('',))[0].upper() == 'CANCELLED':
            continue
        start, all_day = _when(*f['DTSTART'])
        end = _when(*f['DTEND'])[0] if 'DTEND' in f else start + (dt.timedelta(days=1) if all_day else dt.timedelta(hours=1))
        unesc = lambda s: s.replace('\\n', '\n').replace('\\,', ',').replace('\\;', ';')
        ev = {'title': unesc(f.get('SUMMARY', ('(no title)',))[0]), 'start': start, 'end': end, 'all_day': all_day,
              'where': unesc(f.get('LOCATION', ('',))[0]), 'notes': unesc(f.get('DESCRIPTION', ('',))[0])[:300]}
        rule = f.get('RRULE', ('',))[0].upper()
        m = re.search(r'FREQ=(DAILY|WEEKLY)', rule)
        if m:
            step = dt.timedelta(days=1 if m.group(1) == 'DAILY' else 7)
            until = re.search(r'UNTIL=(\d{8}(T\d{6}Z?)?)', rule)
            stop = min(_when(until.group(1))[0] if until else dt.datetime.max,
                       dt.datetime.now() + dt.timedelta(days=horizon_days))
            count = int(re.search(r'COUNT=(\d+)', rule).group(1)) if 'COUNT=' in rule else 10 ** 6
            t, k = start, 0
            while t <= stop and k < count:
                if t >= dt.datetime.now() - dt.timedelta(days=1):
                    out.append(dict(ev, start=t, end=t + (end - start)))
                t += step; k += 1
        else:
            out.append(ev)
    return sorted(out, key=lambda e: e['start'])

def events(repo, days=7, back=0):
    """His events from `back` days ago to `days` ahead, or None if no calendar is connected."""
    cfg = config(repo)
    if not cfg:
        return None
    now = dt.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    lo, hi = now - dt.timedelta(days=back), now + dt.timedelta(days=days + 1)
    return [e for e in events_from(_fetch(cfg['url'])) if lo <= e['start'] < hi]

def _line(e):
    day = e['start'].strftime('%a %d %b')
    return f"{day}, {'all day' if e['all_day'] else e['start'].strftime('%H:%M') + '-' + e['end'].strftime('%H:%M')}: " \
           f"{e['title']}" + (f" ({e['where']})" if e['where'] else '')

ANSWER = """A business owner asked his assistant about his calendar: "{question}"
Today is {today}. His events:
{events}

Answer from these events only: what he has, when, and where; if he asks whether he is free, say yes or no first and
name what is in the way. Never invent an event.
Reply with JSON only: {{"answer": "..."}}"""

def answer(repo, question):
    from . import explain
    evs = events(repo, days=14, back=1)
    if evs is None:
        return {'ok': False, 'say': 'no calendar'}
    got = explain.ask_json(explain.plain(ANSWER.format(question=question, today=time.strftime('%A %d %B %Y, %H:%M'),
                                                       events='\n'.join(_line(e) for e in evs) or '(nothing)')))
    if not got or not got.get('answer'):
        return {'ok': False, 'say': "I couldn't read your calendar just now. Try again in a minute."}
    return {'ok': True, 'say': got['answer']}

def today_lines(repo):
    """Today's events, for the morning brief."""
    try:
        evs = events(repo, days=0)
    except Exception:
        return []
    return [_line(e) for e in evs or []]

def summary(repo):
    return 'His calendar (read-only)' if config(repo) else ''
