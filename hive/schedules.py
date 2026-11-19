"""Civil-time occurrences and declarative predicates for owner-defined routines."""

import datetime as dt
import hmac
import hashlib
import json
import math
import os
import re
import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from . import store, tasks, tools

DAYS = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
CIVIL = re.compile(
    r'^(daily|weekdays|weekly(?: on)? ([a-z, ]+?)) at (\d\d?):(\d\d) ([A-Za-z0-9_+/.-]+)\s*:\s*(.+)$',
    re.I | re.S,
)
EVENT = re.compile(r'^on ((?:pulse|webhook)\.[a-z][a-z0-9_-]{0,31})(.*)$', re.I | re.S)
PULSE_FIELDS = {'title', 'body', 'priority', 'ref'}
NEVER = 253402300799


def occurrences(definition, after, count=3):
    zone = ZoneInfo(definition['zone'])
    date = dt.datetime.fromtimestamp(after, zone).date()
    hour, minute = map(int, definition['time'].split(':'))
    result = []
    while len(result) < count:
        if date.weekday() in definition['days']:
            stamp = dt.datetime.combine(date, dt.time(hour, minute), tzinfo=zone).replace(fold=0)
            ts = stamp.timestamp()
            if (
                dt.datetime.fromtimestamp(ts, zone).replace(tzinfo=None) == stamp.replace(tzinfo=None)
                and ts > after
            ):
                result.append(ts)
        date += dt.timedelta(days=1)
    return result


def next_run(definition, interval, now):
    if definition.get('kind') == 'calendar':
        return occurrences(definition, now, 1)[0]
    return NEVER if definition.get('kind') == 'event' else now + interval


def parse(text, repo):
    match = CIVIL.fullmatch(text.strip())
    if match:
        freq, days, hour, minute, zone, instruction = match.groups()
        try:
            ZoneInfo(zone)
            clock = dt.time(int(hour), int(minute)).strftime('%H:%M')
            weekdays = range(7) if freq.lower() == 'daily' else range(5)
            if days:
                weekdays = [
                    next(i for i, name in enumerate(DAYS) if value.strip().lower() in (name, name[:3]))
                    for value in days.split(',')
                ]
        except (StopIteration, ValueError, ZoneInfoNotFoundError):
            raise tools.Refused('Use a valid weekday, local 24-hour time and IANA time zone.') from None
        return {
            'kind': 'calendar',
            'days': sorted(set(weekdays)),
            'time': clock,
            'zone': zone,
        }, instruction.strip()
    match = EVENT.fullmatch(text.strip())
    if match:
        source, tail = match[1].lower(), match[2].strip()
        fields = fields_for(source, repo)
        filters = {}
        if tail.lower().startswith('where '):
            raw = tail[6:].lstrip()
            try:
                filters, n = json.JSONDecoder().raw_decode(raw)
            except ValueError:
                raise tools.Refused('Specify the event filter as a JSON object.') from None
            tail = raw[n:].strip()
        if not tail.startswith(':') or not tail[1:].strip():
            raise tools.Refused('Add a colon and the instruction to run for this event.')
        validate_filters(filters, fields)
        return {'kind': 'event', 'source': source, 'filters': filters}, tail[1:].strip()
    return None


def fields_for(source, repo):
    if source in ('pulse.mail', 'pulse.calendar', 'pulse.payments', 'pulse.deadlines'):
        return PULSE_FIELDS
    from . import gateway

    hook = gateway.config().get('webhooks', {}).get(source.removeprefix('webhook.'))
    if not source.startswith('webhook.') or not hook or hook['project'] != tasks._project(repo):
        raise tools.Refused('Register this webhook and its event fields for this project first.')
    return set(hook['fields'])


def validate_filters(filters, fields):
    if not isinstance(filters, dict) or not set(filters) <= fields:
        raise tools.Refused('Filters can use only declared event fields.')
    for predicate in filters.values():
        if isinstance(predicate, dict) and len(predicate) == 1:
            op, value = next(iter(predicate.items()))
        else:
            op, value = 'eq', predicate
        if op not in ('eq', 'gte', 'lte') or not isinstance(value, (str, int, float, bool)):
            raise tools.Refused('Use scalar equality or a numeric gte/lte filter.')
        if op in ('gte', 'lte') and (
            type(value) not in (int, float) or (type(value) is float and not math.isfinite(value))
        ):
            raise tools.Refused('Numeric filters require finite numbers.')


def matches(filters, data):
    for field, pred in filters.items():
        op, expected = next(iter(pred.items())) if isinstance(pred, dict) else ('eq', pred)
        actual = data.get(field)
        if op == 'eq':
            if actual != expected or isinstance(actual, bool) != isinstance(expected, bool):
                return False
        elif (
            type(actual) not in (int, float)
            or (op == 'gte' and actual < expected)
            or (op == 'lte' and actual > expected)
        ):
            return False
    return True


def event(repo, source, eid, data, now=None):
    now = time.time() if now is None else now
    if not eid or len(eid) > 512 or not isinstance(data, dict) or not set(data) <= fields_for(source, repo):
        raise ValueError('Undeclared event fields or invalid ID')
    if any(
        type(v) not in (int, float, str, bool) or (type(v) is float and not math.isfinite(v))
        for v in data.values()
    ):
        raise ValueError('Event fields must contain finite numbers, text or booleans')
    project = tasks._project(repo)
    with store.transaction() as con:
        from . import handoff

        handoff.available(repo)
        if not con.execute(
            'INSERT OR IGNORE INTO trigger_events VALUES(?,?,?,?,?)',
            (project, source, eid, json.dumps(data), now),
        ).rowcount:
            return False
        for row in con.execute(
            "SELECT id,definition FROM routines WHERE project=? AND owner_id=? AND enabled=1 "
            "AND json_extract(definition,'$.source')=?",
            (project, store.OWNER, source),
        ).fetchall():
            if matches(json.loads(row['definition'])['filters'], data):
                con.execute('INSERT INTO event_runs VALUES(?,?,?,NULL)', (row['id'], source, eid))
                con.execute('UPDATE routines SET next_run=min(next_run,?) WHERE id=?', (now, row['id']))
    return True


def webhook(name, headers, body, now=None):
    from . import gateway

    now = time.time() if now is None else now
    hook = gateway.config().get('webhooks', {}).get(name)
    if not hook:
        return False
    stamp, eid = headers.get('x-hive-timestamp', ''), headers.get('x-hive-event-id', '')
    key = os.environ.get(hook['key_env'])
    if (
        not key
        or not re.fullmatch(r'[0-9]{1,12}', stamp)
        or abs(now - int(stamp)) > 300
        or not re.fullmatch(r'[\w./:-]{1,128}', eid, re.ASCII)
    ):
        return False
    tag = hmac.new(
        key.encode(), stamp.encode() + b'.' + eid.encode() + b'.' + body, hashlib.sha256
    ).hexdigest()
    supplied = headers.get('x-hive-signature', '')
    if not re.fullmatch('[0-9a-f]{64}', supplied) or not hmac.compare_digest(tag, supplied):
        return False
    event(hook['project'], 'webhook.' + name, eid, json.loads(body), now)
    return True


def label(definition):
    if definition['kind'] == 'event':
        return definition['source'] + ' where ' + json.dumps(definition['filters'], sort_keys=True)
    return (
        ', '.join(DAYS[i].title()[:3] for i in definition['days'])
        + ' at '
        + definition['time']
        + ' '
        + definition['zone']
    )
