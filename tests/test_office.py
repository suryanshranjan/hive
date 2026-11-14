"""The office on his phone (hive/office.py, mail.py, calendar_.py, payments.py), with stand-ins (no network, no tokens):
which messages go where, connecting each from the chat with the password or key taken back out of it, mail read without
marking it read, a reply sent only on his yes and in its thread, his calendar read from its iCal address, and payments
from Stripe and Razorpay summed exactly, by reads only.
usage: python3 tests/test_office.py   (run from the hive repo root)"""
import datetime as dt, email, http.server, json, os, subprocess, sys, tempfile, threading, time
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home
from hive import assistant, calendar_, explain, mail, memory, office, payments, telegram
from hive import logins as _logins; _logins.ensure = lambda ch, service, poll=20: True
explain.CMD = '"' + sys.executable.replace(chr(92), '/') + '" tests/fake_explain.py'
telegram.BUSY = os.path.join(home, 'busy'); telegram.CONVERSATION = os.path.join(home, 'conversation.json')
from test_telegram_fake import FakeTelegram, ME, tap, say

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))
ch = lambda fake: telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake)
repo = os.path.join(home, 'dabba'); os.makedirs(repo)
subprocess.run(['git', 'init', '-q', '-b', 'main', repo])
subprocess.run(['git', '-C', repo, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'office test'])

# ---- a stand-in mailbox -------------------------------------------------------------------------------------------
def raw(uid, frm, subject, body, mid):
    m = email.message.EmailMessage(); m['From'], m['To'], m['Subject'] = frm, 'me@dabbadays.in', subject
    m['Date'] = email.utils.formatdate(time.time() - uid * 3600); m['Message-ID'] = mid; m.set_content(body)
    return m.as_bytes()
INBOX = {b'1': (raw(3, 'Newsletter <news@x.com>', 'Weekly deals', 'Sale!', '<n1@x>'), b'\\Seen'),
         b'2': (raw(2, 'Asha Rao <asha@client.in>', 'Lunch order for 40 people', 'Can you do Thursday?', '<a2@client>'), b''),
         b'3': (raw(1, 'Ravi <ravi@cook.in>', 'Payout question', 'When is my bonus paid?', '<r3@cook>'), b'')}
seen = {'examine': [], 'flags_changed': False}
class Box:
    def __init__(self, cfg): self.cfg = cfg
    def list(self): return 'OK', [b'(\\HasNoChildren) "/" "INBOX"', b'(\\HasNoChildren) "/" "Sent"']
    def select(self, folder, readonly=False): seen['examine'].append(readonly); return 'OK', [b'3']
    def uid(self, cmd, *a):
        if cmd == 'SEARCH':
            return 'OK', [b' '.join(k for k in sorted(INBOX) if 'UNSEEN' not in a or not INBOX[k][1])]
        if cmd == 'FETCH':
            if 'PEEK' not in a[1]:
                seen['flags_changed'] = True
            body, flags = INBOX[a[0]]
            return 'OK', [(b'%s (UID %s FLAGS (%s) BODY[] {%d}' % (a[0], a[0], flags, len(body)), body), b')']
        raise AssertionError(cmd)
    def logout(self): pass
mail._imap = lambda cfg: Box(cfg)
sent_mail = []
class SMTP:
    def __init__(self, *a, **k): pass
    def login(self, u, p): self.u = u
    def send_message(self, m): sent_mail.append(m)
    def quit(self): pass
mail.smtplib.SMTP_SSL = SMTP

# 1. which messages go where (nothing connected yet: questions are not taken; connecting always is)
check('"connect my email" is the office, even before anything is connected', office.route('connect my email', repo), 'connect_mail')
check('a Stripe key or "connect Razorpay" is payments', (office.route('connect razorpay please', repo),
      office.route('here: rk_test_' + 'a' * 24, repo)), ('connect_pay', 'connect_pay'))
check('a calendar address is the calendar', office.route('https://calendar.google.com/calendar/ical/me%40x/private-abc/basic.ics', repo), 'connect_cal')
check('nothing connected: "any emails?" is not taken', office.route('any emails today?', repo), None)

# 2. connecting his mailbox in the chat: the address, then an app password, which is deleted from the chat and from
#    Hive's record of the conversation
made = []
real_setup = mail.setup
def fake_setup(repo_, address, pw, **k):
    made.append((address, pw)); return real_setup(repo_, address, pw, **k)
mail.setup = fake_setup
fake = FakeTelegram([say('me@dabbadays.in'), say('abcd efgh ijkl mnop')])
c = ch(fake); c.keep = False
r = assistant.handle(c, repo, 'connect my email', poll=1)
texts = [m['text'] for m in fake.sent]
check('connected with the address and the app password (Gmail-style spaces kept for others)', (r, made),
      ('mail_connected', [('me@dabbadays.in', 'abcd efgh ijkl mnop')]))
check('the message with the password was deleted from the chat', getattr(fake, 'deleted', []), [1002])
check("...and from Hive's record of the conversation", any('abcd efgh' in t for _, t in c.history), False)
check('he is told what Hive can do with it, plainly', 'nothing is sent without your yes' in texts[-1], True)
check('the password is kept on this computer only, never in his repository',
      (os.path.exists(mail._path(repo)), subprocess.run(['git', '-C', repo, 'status', '--porcelain'], capture_output=True, text=True).stdout), (True, ''))
mail.setup = real_setup
check('a known provider is filled in from the address', (mail.guess('x@gmail.com')[0], mail.guess('x@shop.in', 'godaddy')[0],
      mail.guess('owner@mystartup.in')[:2]), ('imap.gmail.com', 'imap.secureserver.net', ('imap.mystartup.in', 'smtp.mystartup.in')))

# 3. reading: answered from his mail, read-only (EXAMINE, BODY.PEEK): nothing he hasn't read is marked read
check('now "any emails?" is the mail; a build that mentions mail is still a build', (office.route('any emails from customers?', repo),
      office.route('add an email signup box', repo), office.route('why did the build fail', repo)), ('mail', None, None))
fake = FakeTelegram([])
r = assistant.handle(ch(fake), repo, 'Any important emails today?', poll=1)
check('his mail is read and answered, newest first', (r, 'Ravi <ravi@cook.in> wrote about Payout question.' in fake.sent[-1]['text']),
      ('mail_answered', True))
check('read-only: the mailbox is opened for reading, and no message is marked read', (set(seen['examine']), seen['flags_changed']),
      ({True}, False))

# 4. a reply: the right message, a draft in his words, sent only on his yes, in the same thread
fake = FakeTelegram([tap('mlr|no')])
r = assistant.handle(ch(fake), repo, 'reply to Asha saying Thursday works, 40 lunches at 120 each', poll=1)
check('the draft is shown; "don\'t send" sends nothing', (r, 'Thursday works' in fake.sent[-1 - 1]['text'], sent_mail),
      ('mail_not_sent', True, []))
fake = FakeTelegram([tap('mlr|send')])
r = assistant.handle(ch(fake), repo, 'reply to Asha saying Thursday works, 40 lunches at 120 each', poll=1)
m = sent_mail[-1] if sent_mail else {}
check('on his yes it goes to her, from his address, in her thread', (r, m.get('To'), m.get('From'), m.get('In-Reply-To'),
      m.get('Subject')), ('mail_sent', 'asha@client.in', 'me@dabbadays.in', '<a2@client>', 'Re: Lunch order for 40 people'))

# ---- his calendar, at a local iCal address --------------------------------------------------------------------------
tom = (dt.datetime.now() + dt.timedelta(days=1)).replace(hour=15, minute=0, second=0, microsecond=0)
mon = dt.datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) - dt.timedelta(days=7)
f = lambda t: t.strftime('%Y%m%dT%H%M%S')
ICS_TEXT = ("BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nDTSTART:" + f(tom) + "\r\nDTEND:" + f(tom + dt.timedelta(hours=1)) +
            "\r\nSUMMARY:Tasting with Asha\\, 40 lunches\r\nLOCATION:Koramangala\r\nEND:VEVENT\r\n"
            "BEGIN:VEVENT\r\nDTSTART:" + f(mon) + "\r\nDTEND:" + f(mon + dt.timedelta(minutes=30)) +
            "\r\nRRULE:FREQ=WEEKLY\r\nSUMMARY:Cooks stand-up\r\nEND:VEVENT\r\n"
            "BEGIN:VEVENT\r\nDTSTART:" + f(tom) + "\r\nSTATUS:CANCELLED\r\nSUMMARY:Dropped call\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n")
class Serve(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        STUB.append((self.command, self.path, self.headers.get('Authorization', '')))
        body, code = route_stub(self.path)
        self.send_response(code); self.end_headers(); self.wfile.write(body.encode())
    def do_POST(self):
        STUB.append(('POST', self.path, '')); self.send_response(405); self.end_headers()
STUB = []
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Serve); threading.Thread(target=srv.serve_forever, daemon=True).start()
local = f'http://127.0.0.1:{srv.server_address[1]}'

# ---- Stripe and Razorpay stand-ins, with payments planted this week ------------------------------------------------
now = int(time.time())
STRIPE = [{'id': 'ch_1', 'amount': 250000, 'currency': 'inr', 'status': 'succeeded', 'paid': True, 'amount_refunded': 0,
           'created': now - 3600, 'billing_details': {'name': 'Asha Rao', 'email': 'asha@client.in'}, 'description': 'Office lunches'},
          {'id': 'ch_2', 'amount': 120000, 'currency': 'inr', 'status': 'succeeded', 'paid': True, 'amount_refunded': 20000,
           'created': now - 7200, 'billing_details': {}, 'description': 'Monthly plan'},
          {'id': 'ch_3', 'amount': 50000, 'currency': 'inr', 'status': 'failed', 'paid': False, 'amount_refunded': 0,
           'created': now - 9000, 'billing_details': {'email': 'late@x.in'}, 'failure_message': 'Card declined'}]
RAZOR = [{'id': 'pay_1', 'amount': 300000, 'currency': 'INR', 'status': 'captured', 'amount_refunded': 0, 'created_at': now - 600,
          'email': 'b@x.in', 'description': 'Weekly plan'},
         {'id': 'pay_2', 'amount': 99900, 'currency': 'INR', 'status': 'failed', 'amount_refunded': 0, 'created_at': now - 900,
          'email': 'c@x.in', 'error_description': 'Payment was cancelled by the customer'}]
def route_stub(path):
    if path.startswith('/cal.ics'):
        return ICS_TEXT, 200
    if path.startswith('/v1/charges'):
        after = 'starting_after=ch_1' in path
        return json.dumps({'data': STRIPE[1:] if after else STRIPE[:1], 'has_more': not after}), 200   # two pages
    if path.startswith('/v1/payments'):
        return json.dumps({'items': RAZOR if 'skip=0' in path else []}), 200
    return '{}', 404
payments.BASE = {'stripe': local, 'razorpay': local}

# 5. the calendar: connected from the address he pastes (deleted from the chat), read, never changed
fake = FakeTelegram([])
r = assistant.handle(ch(fake), repo, f'here is my calendar {local}/cal.ics', poll=1)
check('the calendar connects from its address, and the address is taken out of the chat',
      (r, 'Connected to your calendar' in fake.sent[-1]['text'], len(getattr(fake, 'deleted', []))), ('cal_connected', True, 1))
evs = calendar_.events(repo, days=8, back=8)
check('events are read: the one-off with its place, the weekly one repeated, the cancelled one left out',
      (any(e['title'] == 'Tasting with Asha, 40 lunches' and e['where'] == 'Koramangala' for e in evs),
       sum(e['title'] == 'Cooks stand-up' for e in evs) >= 2, any(e['title'] == 'Dropped call' for e in evs)), (True, True, False))
fake = FakeTelegram([])
r = assistant.handle(ch(fake), repo, 'Am I free tomorrow at 3?', poll=1)
check('"am I free tomorrow at 3?" is answered from it', (r, 'Tasting with Asha' in fake.sent[-1]['text']), ('cal_answered', True))

# 6. payments: Stripe by a read-only key, Razorpay by its key ID and secret; both deleted from the chat; sums exact
fake = FakeTelegram([say('rk_test_' + 'k' * 24)])
r = assistant.handle(ch(fake), repo, 'connect stripe', poll=1)
check('Stripe connects with a read-only key, taken out of the chat', (r, 'read-only key' in fake.sent[-1]['text'],
      len(getattr(fake, 'deleted', []))), ('pay_connected', True, 1))
fake = FakeTelegram([say('rzp_test_ABCDEF123456 secretSECRETsecret99')])
r = assistant.handle(ch(fake), repo, 'connect razorpay', poll=1)
check("Razorpay connects; he's told its keys can't be limited, and that Hive only reads", (r,
      "can't be limited to reading" in fake.sent[-1]['text']), ('pay_connected', True))
fake = FakeTelegram([])
r = assistant.handle(ch(fake), repo, 'How much did we make this week?', poll=1)
check('this week, summed exactly: paid 2500 + 1200 + 3000 = 6700 from 3, 2 failed, 200 refunded, 6500 kept',
      (r, fake.sent[-1]['text']), ('pay_answered', '💳 INR: 6700.00 from 3 successful payments; 2 failed; 200.00 refunded; kept 6500.00'))
check('Stripe was read page by page, and nothing but reads was ever sent', (sum('starting_after=ch_1' in p for _, p, _ in STUB) >= 1,
      {m for m, _, _ in STUB}), (True, {'GET'}))
check('each provider got its own sign-in (a bearer key; Razorpay basic)',
      ({a.split()[0] for _, p, a in STUB if p.startswith('/v1/charges')}, {a.split()[0] for _, p, a in STUB if p.startswith('/v1/payments')}),
      ({'Bearer'}, {'Basic'}))
check('"add a payments page" is still a build', office.route('add a payments page with UPI', repo), None)
check('connecting is his own account; adding a feature is a build', (office.route('add stripe payments to checkout', repo),
      office.route('connect my gmail', repo), office.route('link our razorpay', repo), office.route('connect calendar', repo)),
      (None, 'connect_mail', 'connect_pay', 'connect_cal'))
check('what Hive tells the model about him names his office, read-only', office.summary(repo),
      ['His mailbox me@dabbadays.in (read-only; replies only on his yes)', 'His calendar (read-only)',
       'His payments: Stripe, Razorpay (read-only; never moves money)'])
srv.shutdown()
sys.exit(fail)
