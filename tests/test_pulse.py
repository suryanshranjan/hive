"""Hive Pulse (hive/pulse.py): Hive speaks first when something needs him, and only then. Stand-in mail, calendar and
payments; a stand-in small model; fake Telegram. No network.   usage: python3 tests/test_pulse.py"""
import datetime as dt, os, subprocess, sys, tempfile, time
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.getcwd())
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home; os.environ['HIVE_EMBED'] = '0'
from hive import assistant, explain, memory, pulse, register, store, telegram
memory.DIR = os.path.join(home, '.hive', 'rules'); telegram.BUSY = os.path.join(home, '.hive', 'telegram.busy')
register.PATH = os.path.join(home, '.hive', 'profile.json')
sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
from test_telegram_fake import FakeTelegram, ME, tap

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))

repo = os.path.join(home, 'shop'); subprocess.run(['git', 'init', '-q', '-b', 'main', repo])
subprocess.run(['git', '-C', repo, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'i'])
ch = lambda fake: telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake)

# stand-ins for what Pulse watches
from hive import mail, calendar_, payments
INBOX = []
mail.config = lambda repo: {'user': 'me@x.in'}
mail.messages = lambda repo, **k: list(INBOX)
now_dt = dt.datetime.now().replace(second=0, microsecond=0)
EVENTS = [{'title': 'Tasting with Asha', 'start': now_dt + dt.timedelta(minutes=30), 'end': now_dt + dt.timedelta(minutes=90),
           'all_day': False, 'where': 'Andheri', 'notes': ''}]
calendar_.config = lambda repo: {'url': 'x'}
calendar_.events = lambda repo, days=7, back=0: list(EVENTS)
PAYS = []
payments.load = lambda repo: {'stripe': 'rk'}
payments.fetch = lambda repo, since, until=None: list(PAYS)
explain.ask_small = lambda prompt: {'items': [{'n': i + 1, 'priority': 2 if 'refund' in l.lower() else 0,
                                               'line': l.split('Subject: ')[1][:40] if 'Subject: ' in l else 'x'}
                                              for i, l in enumerate(prompt.split('\n[')[1:])]}
msg = lambda i, frm, subj: {'uid': str(i), 'id': f'<{i}@x>', 'from': frm, 'subject': subj, 'date': '', 'unread': True,
                            'text': subj, 'to': 'me@x.in', 'refs': ''}

# 1. the first look only learns what is there; new mail after it is scored, and only what matters interrupts
INBOX[:] = [msg(1, 'Old <o@x.in>', 'An old thread')]
pulse.look(repo)
check('the first look learns what is already there: no flood of old mail', [e['source'] for e in pulse.pending()].count('mail'), 0)
INBOX[:] = [msg(2, 'Asha <asha@mehta.example>', 'Refund for the cold lunch?'), msg(3, 'Deals <news@shop.example>', 'Big sale'),
            msg(1, 'Old <o@x.in>', 'An old thread')]
check('new mail is found, the calendar too', pulse.look(repo) >= 2, True)
fake = FakeTelegram([])
n = pulse.tell(ch(fake))
sent = [m['text'] for m in fake.sent]
check('what matters interrupts (the refund, the meeting in 30 minutes); the newsletter waits',
      (any('Refund' in t for t in sent), any('Tasting with Asha' in t for t in sent), any('Big sale' in t for t in sent)),
      (True, True, False))
m0 = next(m for m in fake.sent if 'Refund' in m['text'])
check('a mail alert has Got it, Reply and In an hour', [b['callback_data'].split('|')[2] for row in m0['reply_markup']
      ['inline_keyboard'] for b in row], ['ok', 'reply', 'later'])
pulse.look(repo); fake2 = FakeTelegram([]); pulse.tell(ch(fake2))
check('nothing is said twice', fake2.sent, [])
check('the newsletter waits for the digest, then is seen', (any('Big sale' in t for t in pulse.digest()), pulse.digest()), (True, []))

# 2. his rules, in his words
check('"tell me about any mail from Ravi": always at once', pulse.set_from('always tell me about any mail from Ravi'),
      'Any mail from Ravi comes to you at once.')
INBOX.insert(0, msg(4, 'Ravi Kumar <ravi@x.in>', 'Lunch?'))
pulse.look(repo); fake = FakeTelegram([]); pulse.tell(ch(fake))
check('... mail from him interrupts though the model scored it 0', any('Ravi' in m['text'] for m in fake.sent), True)
said_q = pulse.set_from('quiet hours 10 pm to 7 am')
check('"quiet hours 10 pm to 7 am"', (pulse.settings()['quiet'], said_q.startswith('Quiet from 22:00')), ([22, 7], True))
check('a time in quiet hours is quiet, one outside is not',
      (pulse.in_quiet(time.mktime(now_dt.replace(hour=23).timetuple())), pulse.in_quiet(time.mktime(now_dt.replace(hour=12).timetuple()))),
      (True, False))
print('  ' + pulse.set_from("don't tell me about payments"))
PAYS[:] = [{'provider': 'stripe', 'id': 'ch_1', 'failed': True, 'amount': 999, 'currency': 'INR', 'name': 'Late', 'email': '',
            'reason': 'card declined', 'paid': False}]
store.put('pulse_seen:payments', time.time() - 600)
pulse.look(repo)
check('a muted kind is not watched', [e for e in pulse.pending() if e['source'] == 'payments'], [])
pulse.set_from('tell me about payments again'); pulse.look(repo)
check('... and is again when he says so; a failed payment is found', [e['title'].startswith('💳 A payment failed') and e['title'][:18] for e in pulse.pending()
      if e['source'] == 'payments'], ['💳 A payment failed'])
check('his settings in one line', pulse.status_line().startswith('I watch mail, calendar, payments, deadlines'), True)

# 3. deadlines from what he told Hive: three days before, the day before, the day itself
store.add_fact('The FSSAI licence renewal is due.', 'deadline', memory.project_key(repo), valid_until=time.time() + 20 * 3600)
pulse.look(repo)
check('a deadline due today is found as urgent', [(e['priority'], e['title'][:9]) for e in pulse.pending() if e['source'] == 'deadlines'],
      [(3, '⏰ Due tod')])

# 4. quiet hours: only the urgent comes through (when he allows it)
store.put('pulse', dict(pulse.settings(), quiet=[0, 24] if False else [(now_dt.hour) % 24, (now_dt.hour + 2) % 24]))
fake = FakeTelegram([]); pulse.tell(ch(fake))
check('in quiet hours: the urgent deadline comes through, the failed payment waits',
      (any('FSSAI' in m['text'] for m in fake.sent), any('payment failed' in m['text'] for m in fake.sent)), (True, False))
store.put('pulse', dict(pulse.settings(), quiet=None))

# 5. his taps: in an hour brings it back, got it is done; set from the chat
fake = FakeTelegram([]); pulse.tell(ch(fake))
pid = next(int(b['callback_data'].split('|')[1]) for m in fake.sent for row in m.get('reply_markup', {}).get('inline_keyboard', [])
           for b in row if 'payment' in m['text'] and b['callback_data'].endswith('|later'))
check('"In an hour": snoozed', pulse.tap(ch(FakeTelegram([])), f'pls|{pid}|later', repo), 'snoozed')
check('... and not before the hour', [e['id'] for e in pulse.pending()].count(pid), 0)
store.connect().execute('UPDATE pulse_events SET snooze_until=? WHERE id=?', (time.time() - 1, pid))
check('... and back after it', [e['id'] for e in pulse.pending()].count(pid), 1)
fake = FakeTelegram([])
r = assistant.handle(ch(fake), repo, 'quiet hours 11pm to 6am', poll=1)
check('his words on the chat set it', (r, pulse.settings()['quiet'], 'Quiet from 23:00' in fake.sent[-1]['text']),
      ('pulse_set', [23, 6], True))
sys.exit(fail)
