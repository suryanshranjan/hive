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
    """His calendar: the secret iCal address, or {'kind': 'google'} when Google Calendar is connected through
    Google's API (hive/google.py), which can also add events on his yes."""
    from . import vault
    got = vault.load_json(_path(repo), {})
    if isinstance(got, dict) and got:
        return got
    try:
        from . import google
        if google.connected('calendar'):
            return {'kind': 'google'}
    except Exception:
        pass
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
    from . import vault
    vault.save_json(_path(repo), {'url': url, 'added': time.time()})   # the secret address, encrypted when Hive can
    soon = [e for e in evs if dt.datetime.now() <= e['start'] <= dt.datetime.now() + dt.timedelta(days=7)]
    return True, f"Connected to your calendar: {len(soon)} event{'s' if len(soon) != 1 else ''} in the next 7 days. " \
                 "I can only read it."

def _unfold(text):
    return re.sub(r'\r?\n[ \t]', '', text)

def _zone(params):
    """The time zone an iCal value names (TZID=Asia/Kolkata), or None."""
    m = re.search(r'TZID=("?)([^;:"]+)\1', params or '')
    if not m:
        return None
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(m.group(2).strip())
    except Exception:   # an unknown zone name (or no zone data on this machine): read as his own time, as before
        return None

def _when(value, params=''):
    """An iCal date or time as his local naive datetime (all-day events at midnight). A time in a named zone
    (TZID=...) or in UTC (...Z) is turned into his time (the audit, Nov 15: a 3 pm New York call showed as 3 pm here)."""
    v = value.strip()
    if len(v) == 8:   # all day: 20261116
        return dt.datetime.strptime(v, '%Y%m%d'), True
    utc = v.endswith('Z')
    t = dt.datetime.strptime(v.rstrip('Z')[:15], '%Y%m%dT%H%M%S')
    zone = dt.timezone.utc if utc else _zone(params)
    if zone is not None:
        t = t.replace(tzinfo=zone).astimezone().replace(tzinfo=None)
    return t, False

DAYS = {'MO': 0, 'TU': 1, 'WE': 2, 'TH': 3, 'FR': 4, 'SA': 5, 'SU': 6}

def _occurrences(start, rule, stop):
    """The start times of a repeating event up to stop: DAILY, WEEKLY (with BYDAY and INTERVAL), MONTHLY (same day of
    the month), YEARLY; COUNT and UNTIL honoured. Anything else: the first time only."""
    freq = re.search(r'FREQ=(\w+)', rule)
    if not freq or freq.group(1) not in ('DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY'):
        return [start]
    every = int(re.search(r'INTERVAL=(\d+)', rule).group(1)) if 'INTERVAL=' in rule else 1
    count = int(re.search(r'COUNT=(\d+)', rule).group(1)) if 'COUNT=' in rule else 10 ** 6
    until = re.search(r'UNTIL=(\d{8}(T\d{6}Z?)?)', rule)
    if until:
        stop = min(stop, _when(until.group(1))[0] if len(until.group(1)) > 8 else
                   _when(until.group(1))[0] + dt.timedelta(days=1, seconds=-1))
    by = re.search(r'BYDAY=([^;]+)', rule)
    byday = [DAYS[d] for d in re.findall(r'(MO|TU|WE|TH|FR|SA|SU)', by.group(1))] if by else []
    out, n, f = [], 0, freq.group(1)
    if f == 'WEEKLY' and byday:
        week = start - dt.timedelta(days=start.weekday())
        while week <= stop and n < count:
            for d in sorted(set(byday)):
                t = week + dt.timedelta(days=d)
                t = t.replace(hour=start.hour, minute=start.minute, second=start.second)
                if start <= t <= stop and n < count:
                    out.append(t); n += 1
            week += dt.timedelta(weeks=every)
        return out
    t, k = start, 0
    while t <= stop and n < count:
        out.append(t); n += 1; k += 1
        if f == 'DAILY':
            t = start + dt.timedelta(days=every * k)
        elif f == 'WEEKLY':
            t = start + dt.timedelta(weeks=every * k)
        else:   # the same day of the month (or year); a month without that day is skipped, as calendars do
            while True:
                months = (every * k) * (12 if f == 'YEARLY' else 1)
                y, m = divmod(start.month - 1 + months, 12)
                try:
                    t = start.replace(year=start.year + y, month=m + 1); break
                except ValueError:
                    k += 1
    return out

def events_from(ics, horizon_days=60):
    """The events in an iCal text: [{'title', 'start', 'end', 'all_day', 'where', 'notes'}], repeats expanded up to
    horizon_days ahead, dates he removed from a series (EXDATE) left out, and a moved occurrence (RECURRENCE-ID) shown
    at its new time instead of the old one."""
    out, moved = [], {}
    blocks = []
    for block in re.findall(r'BEGIN:VEVENT(.*?)END:VEVENT', _unfold(ics), re.S):
        f, exdates = {}, set()
        for line in block.strip().splitlines():
            if ':' not in line:
                continue
            k, v = line.split(':', 1)
            name, _, params = k.partition(';')
            if name.upper() == 'EXDATE':
                for x in v.split(','):
                    try:
                        exdates.add(_when(x, params)[0])
                    except ValueError:
                        pass
                continue
            f.setdefault(name.upper(), (v, params))
        blocks.append((f, exdates))
        if 'RECURRENCE-ID' in f:   # one occurrence of a series, changed or cancelled: replaces the original time
            try:
                moved.setdefault(f.get('UID', ('',))[0], set()).add(_when(*f['RECURRENCE-ID'])[0])
            except ValueError:
                pass
    now = dt.datetime.now()
    unesc = lambda s: s.replace('\\n', '\n').replace('\\,', ',').replace('\\;', ';')
    for f, exdates in blocks:
        if 'DTSTART' not in f or f.get('STATUS', ('',))[0].upper() == 'CANCELLED':
            continue
        try:
            start, all_day = _when(*f['DTSTART'])
            end = _when(*f['DTEND'])[0] if 'DTEND' in f else start + (dt.timedelta(days=1) if all_day else dt.timedelta(hours=1))
        except ValueError:
            continue
        ev = {'title': unesc(f.get('SUMMARY', ('(no title)',))[0]), 'start': start, 'end': end, 'all_day': all_day,
              'where': unesc(f.get('LOCATION', ('',))[0]), 'notes': unesc(f.get('DESCRIPTION', ('',))[0])[:300]}
        rule = f.get('RRULE', ('',))[0].upper()
        if rule and 'RECURRENCE-ID' not in f:
            skip = exdates | moved.get(f.get('UID', ('',))[0], set())
            for t in _occurrences(start, rule, now + dt.timedelta(days=horizon_days)):
                if t not in skip and t >= now - dt.timedelta(days=1):
                    out.append(dict(ev, start=t, end=t + (end - start)))
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
    if cfg.get('kind') == 'google':
        from . import google
        return [e for e in google.events(days=days, back=back) if lo <= e['start'] < hi]
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
    cfg = config(repo)
    return ('His Google Calendar (events added only on his yes)' if cfg.get('kind') == 'google' else
            'His calendar (read-only)' if cfg else '')
