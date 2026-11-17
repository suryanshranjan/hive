"""hive/calendar_.py, the parts the audit found wrong (Nov 15): time zones, removed dates, every-N repeats, weekly on
chosen days, monthly, a moved occurrence. No network.   usage: python3 tests/test_calendar.py"""
import datetime as dt, os, sys
sys.path.insert(0, os.getcwd())
os.environ['TZ'] = 'Asia/Kolkata'
if hasattr(__import__('time'), 'tzset'):
    __import__('time').tzset()
from hive import calendar_ as cal

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))

local = lambda y, mo, d, h, mi, zone: dt.datetime(y, mo, d, h, mi, tzinfo=__import__('zoneinfo').ZoneInfo(zone)).astimezone(__import__('hive.register', fromlist=['zone']).zone()).replace(tzinfo=None)
soon = dt.datetime.now() + dt.timedelta(days=3)
day = soon.strftime('%Y%m%d')
ics = lambda body: 'BEGIN:VCALENDAR\r\n' + body + 'END:VCALENDAR\r\n'
ev = lambda uid, start, extra='', title='Call': (f'BEGIN:VEVENT\r\nUID:{uid}\r\nSUMMARY:{title}\r\nDTSTART{start}\r\n{extra}'
                                               'END:VEVENT\r\n')

# 1. a time in a named zone is his time
e = cal.events_from(ics(ev('a', f';TZID=America/New_York:{day}T150000', title='NY call')))
check('a 3 pm New York call is shown at his time', e[0]['start'], local(soon.year, soon.month, soon.day, 15, 0, 'America/New_York'))
e = cal.events_from(ics(ev('b', f':{day}T093000Z', title='UTC call')))
check('a UTC time is shown at his time', e[0]['start'], local(soon.year, soon.month, soon.day, 9, 30, 'UTC'))
e = cal.events_from(ics(ev('c', f';TZID=Nowhere/Fake:{day}T150000')))
check('an unknown zone is read as his own time, not dropped', e[0]['start'].hour, 15)

# 2. weekly on chosen days, every other week, a count, and a removed date
mon = soon + dt.timedelta(days=(7 - soon.weekday()) % 7)   # a Monday ahead, whatever today is
start = mon.strftime('%Y%m%d') + 'T100000'
e = cal.events_from(ics(ev('d', f':{start}', 'RRULE:FREQ=WEEKLY;BYDAY=MO,WE;COUNT=4\r\n', 'Standup')))
check('weekly on Monday and Wednesday, 4 times', [x['start'].strftime('%a') for x in e], ['Mon', 'Wed', 'Mon', 'Wed'])
e = cal.events_from(ics(ev('e', f':{start}', 'RRULE:FREQ=WEEKLY;INTERVAL=2;COUNT=3\r\n', 'Review')))
check('every other week', [(x['start'] - e[0]['start']).days for x in e], [0, 14, 28])
gone = (mon + dt.timedelta(days=7)).strftime('%Y%m%d') + 'T100000'
e = cal.events_from(ics(ev('f', f':{start}', f'RRULE:FREQ=WEEKLY;COUNT=3\r\nEXDATE:{gone}\r\n', 'Sync')))
check('a date he removed from the series is left out', [(x['start'] - e[0]['start']).days for x in e], [0, 14])

# 3. monthly on the same day, and a moved occurrence shows once, at its new time
e = cal.events_from(ics(ev('g', f':{start}', 'RRULE:FREQ=MONTHLY;COUNT=2\r\n', 'Rent')))
check('monthly on the same day', [x['start'].day for x in e], [mon.day, mon.day] if mon.day <= 28 else [mon.day, e[1]['start'].day])
moved_from = (mon + dt.timedelta(days=7)).strftime('%Y%m%d') + 'T100000'
moved_to = (mon + dt.timedelta(days=8)).strftime('%Y%m%d') + 'T120000'
e = cal.events_from(ics(ev('h', f':{start}', 'RRULE:FREQ=WEEKLY;COUNT=3\r\n', 'Class') +
                        ev('h', f':{moved_to}', f'RECURRENCE-ID:{moved_from}\r\n', 'Class (moved)')))
check('a moved occurrence: once, at its new time, the old time gone',
      [(x['title'], x['start'].strftime('%a %H:%M')) for x in e if (x['start'] - e[0]['start']).days in (7, 8)],
      [('Class (moved)', (mon + dt.timedelta(days=8)).strftime('%a') + ' 12:00')])
sys.exit(fail)
