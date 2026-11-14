"""Gate 112: the office on real protocols, with the real model (PREDICTIONS.md). Needs Docker (GreenMail, stripe-mock)
and Claude on this computer:   python gates/gate112/flight112.py"""
import datetime as dt, email.message, email.utils, http.server, imaplib, json, os, re, shutil, smtplib, stat, subprocess
import sys, tempfile, threading, time

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'tests'))
from hive import assistant, calendar_, mail, memory, payments, telegram
from test_telegram_fake import FakeTelegram, ME, tap

OUT = os.path.join(HERE, 'results'); os.makedirs(OUT, exist_ok=True)
log, t0 = {'steps': []}, time.time()
def note(step, **kw):
    kw.update(step=step, minute=round((time.time() - t0) / 60, 1))
    log['steps'].append(kw); print(json.dumps(kw, ensure_ascii=False)[:900], flush=True)
    json.dump(log, open(os.path.join(OUT, 'flight.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

ME_ADDR, ME_PW, ASHA, ASHA_PW = 'me@dabbadays.in', 'mepw', 'asha@client.in', 'ashapw'
SEED = [   # (from, subject, body): his inbox, oldest first
    ('Lunchbox Weekly <news@lunchboxweekly.com>', 'This week: 10 tiffin trends', 'Our top picks for the season...'),
    (f'Asha Rao <{ASHA}>', 'Lunch order for 40 people', 'Hi, can you do 40 veg lunches for our office on Thursday? What would it cost?'),
    ('Ravi Kumar <ravi@cooks.in>', 'My bonus', 'Hello, I had no complaints in October. When is my 500 rupee bonus paid?'),
    ('Fresh Veg Co <billing@freshveg.in>', 'Invoice 2211 due Friday', 'Please find invoice 2211 for Rs 18,400, due this Friday.'),
    ('Meera Iyer <meera@gmail.com>', 'Cold lunch again', 'Second time this week my lunch arrived cold. I am thinking of cancelling.'),
    ('Security <no-reply@accounts.example.com>', 'Password reset requested', 'If this was not you, ignore this email.')]

def sh(*a):
    return subprocess.run(a, capture_output=True, text=True)

def imap(user, pw):
    b = imaplib.IMAP4('127.0.0.1', 3143); b.login(user, pw); return b

def unread(user, pw):
    b = imap(user, pw); b.select('INBOX'); n = len((b.search(None, 'UNSEEN')[1][0] or b'').split()); b.logout(); return n

def inbox(user, pw):
    b = imap(user, pw); b.select('INBOX', readonly=True)
    out = []
    for i in (b.search(None, 'ALL')[1][0] or b'').split():
        out.append(email.message_from_bytes(b.fetch(i, '(BODY.PEEK[])')[1][0][1]))
    b.logout(); return out

# ---- stand-ins ----------------------------------------------------------------------------------------------------
now = int(time.time())
RAZOR = [{'id': 'pay_A', 'amount': 300000, 'currency': 'INR', 'status': 'captured', 'amount_refunded': 0, 'created_at': now - 86400,
          'email': 'asha@client.in', 'description': 'Office lunches'},
         {'id': 'pay_B', 'amount': 150000, 'currency': 'INR', 'status': 'captured', 'amount_refunded': 0, 'created_at': now - 3 * 3600,
          'email': 'meera@gmail.com', 'description': 'Monthly plan'},
         {'id': 'pay_C', 'amount': 99900, 'currency': 'INR', 'status': 'failed', 'amount_refunded': 0, 'created_at': now - 2 * 3600,
          'email': 'late@x.in', 'error_description': 'Payment was cancelled by the customer'}]
tom = (dt.datetime.now() + dt.timedelta(days=1)).replace(hour=15, minute=0, second=0, microsecond=0)
mon = (dt.datetime.now() - dt.timedelta(days=dt.datetime.now().weekday())).replace(hour=10, minute=0, second=0, microsecond=0)
fmt = lambda t: t.strftime('%Y%m%dT%H%M%S')
ICS = ("BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nDTSTART:" + fmt(tom) + "\r\nDTEND:" + fmt(tom + dt.timedelta(hours=1)) +
       "\r\nSUMMARY:Tasting with Asha (40 lunches)\r\nLOCATION:Koramangala office\r\nEND:VEVENT\r\nBEGIN:VEVENT\r\nDTSTART:" +
       fmt(mon) + "\r\nDTEND:" + fmt(mon + dt.timedelta(minutes=30)) + "\r\nRRULE:FREQ=WEEKLY\r\nSUMMARY:Cooks stand-up\r\n"
       "END:VEVENT\r\nEND:VCALENDAR\r\n")
REQ = []
class Serve(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        REQ.append(('GET', self.path))
        if self.path.startswith('/cal.ics'):
            body = ICS
        elif self.path.startswith('/v1/payments'):
            body = json.dumps({'items': RAZOR if 'skip=0' in self.path else []})
        else:
            self.send_response(404); self.end_headers(); return
        self.send_response(200); self.end_headers(); self.wfile.write(body.encode())
    def do_POST(self):
        REQ.append(('POST', self.path)); self.send_response(405); self.end_headers()

def say(repo, script, words):
    fake = FakeTelegram(script)
    c = telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake); c.keep = False
    t = time.time(); r = assistant.handle(c, repo, words, poll=1)
    return r, [m['text'] for m in fake.sent], round(time.time() - t, 1)

def words(t):
    return len(re.sub(r'^\W+', '', t).split())

def main():
    sh('docker', 'rm', '-f', 'hive-mail', 'hive-stripe')
    opts = (f'-Dgreenmail.setup.test.smtp -Dgreenmail.setup.test.imap -Dgreenmail.hostname=0.0.0.0 '
            f'-Dgreenmail.users=me:{ME_PW}@dabbadays.in,asha:{ASHA_PW}@client.in -Dgreenmail.users.login=email')
    sh('docker', 'run', '-d', '--name', 'hive-mail', '-p', '3025:3025', '-p', '3143:3143', '-e', f'GREENMAIL_OPTS={opts}',
       'greenmail/standalone:2.1.2')
    sh('docker', 'run', '-d', '--name', 'hive-stripe', '-p', '12111:12111', 'stripe/stripe-mock:v0.194.0')
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Serve); threading.Thread(target=srv.serve_forever, daemon=True).start()
    local = f'http://127.0.0.1:{srv.server_address[1]}'
    work = tempfile.mkdtemp(prefix='hive112_'); repo = os.path.join(work, 'dabba-days')
    subprocess.run(['git', 'init', '-q', '-b', 'main', repo])
    subprocess.run(['git', '-C', repo, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m',
                    f'Gate 112 office {time.time()}'])
    memory.add_note(repo, 'Dabba Days delivers home-cooked veg lunchboxes in Bengaluru; the owner is Suresh.')
    try:
        for _ in range(60):   # the mail server takes a few seconds to start
            try:
                imap(ME_ADDR, ME_PW).logout(); break
            except Exception:
                time.sleep(2)
        ids = []
        for i, (frm, sub, body) in enumerate(SEED):
            m = email.message.EmailMessage(); m['From'], m['To'], m['Subject'] = frm, ME_ADDR, sub
            m['Date'] = email.utils.formatdate(time.time() - (len(SEED) - i) * 1800, localtime=True)
            m['Message-ID'] = email.utils.make_msgid(domain='seed.test'); ids.append(m['Message-ID']); m.set_content(body)
            s = smtplib.SMTP('127.0.0.1', 3025); s.send_message(m); s.quit()
        time.sleep(2)
        ok, said = mail.setup(repo, ME_ADDR, ME_PW, imap='127.0.0.1', smtp='127.0.0.1', smtp_port=3025, imap_port=3143,
                              use_ssl=False)
        note('setup', mail=(ok, said), unread=unread(ME_ADDR, ME_PW))
        r, told, secs = say(repo, [], 'Any important emails today?')
        ans = told[-1]
        note('O1_mail', result=r, answer=ans, seconds=secs, words=words(ans),
             names_asha='Asha' in ans, names_complaint=bool(re.search(r'cold|complain|Meera', ans, re.I)),
             leads_with_noise=bool(re.match(r'^\W*(Lunchbox Weekly|newsletter|password)', ans, re.I)),
             unread_after=unread(ME_ADDR, ME_PW))
        r, told, secs = say(repo, [tap('mlr|no')], "reply to Asha saying Thursday works, 40 lunches at ₹120 each")
        draft = next((t for t in told if 'Your reply to' in t), '')
        body = draft.split('\n\n', 1)[-1].rsplit('\n\n', 1)[0]
        note('O4_not_sent', result=r, draft=draft, asha_inbox=len(inbox(ASHA, ASHA_PW)),
             numbers=sorted(set(re.findall(r'\d[\d,]*', body))), days=sorted(set(re.findall(
                 r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|tomorrow|today)\b', body, re.I))))
        r, told, secs = say(repo, [tap('mlr|send')], "reply to Asha saying Thursday works, 40 lunches at ₹120 each")
        got = inbox(ASHA, ASHA_PW)
        m = got[-1] if got else {}
        note('O3_sent', result=r, told=told[-1], asha_inbox=len(got), sent_from=m.get('From') if got else None,
             in_reply_to=m.get('In-Reply-To') if got else None, asha_message_id=ids[1], subject=m.get('Subject') if got else None,
             body=(m.get_payload() if got else '')[:400], unread_after=unread(ME_ADDR, ME_PW))
        # payments: Stripe's official mock, and a Razorpay stand-in
        payments.BASE = {'stripe': 'http://127.0.0.1:12111', 'razorpay': local}
        seen = []
        real_get = payments._get
        def logged(provider, key, path, params):
            try:
                out = real_get(provider, key, path, params); seen.append((provider, path, 200)); return out
            except Exception as e:
                seen.append((provider, path, getattr(e, 'code', repr(e)[:80]))); raise
        payments._get = logged
        st = payments.add(repo, 'stripe', 'sk_test_123'); rz = payments.add(repo, 'razorpay', 'secretSECRETsecret99', 'rzp_test_ABC123')
        pays = payments.fetch(repo, time.time() - 7 * 86400)
        r, told, secs = say(repo, [], 'How much did we make this week?')
        ans = told[-1]
        note('O5_payments', stripe=st, razorpay=rz, requests=seen, methods_to_stand_in=sorted({x for x, _ in REQ}),
             hive_totals=payments.totals(pays), result=r, answer=ans, seconds=secs, words=words(ans),
             says_4500=bool(re.search(r'4,500|4500', ans)), says_failed=bool(re.search(r'fail|cancel', ans, re.I)))
        # the calendar
        okc, saidc = calendar_.setup(repo, local + '/cal.ics')
        r, told, secs = say(repo, [], 'Am I free tomorrow at 3?')
        ans = told[-1]
        note('O6_calendar', setup=(okc, saidc), result=r, answer=ans, seconds=secs, words=words(ans),
             says_no=bool(re.match(r'^\W*(no\b|nope|you\'re not|you are not|not free)', ans, re.I)),
             names_tasting=bool(re.search(r'tasting|Asha', ans, re.I)))
    finally:
        for f in (mail._path(repo), calendar_._path(repo), payments._path(repo), memory._notes_path(repo),
                  os.path.join(memory.DIR, memory.project_key(repo) + '.json')):
            try:
                os.remove(f)
            except OSError:
                pass
        sh('docker', 'rm', '-f', 'hive-mail', 'hive-stripe'); srv.shutdown()
        shutil.rmtree(work, onerror=lambda f, p, e: (os.chmod(p, stat.S_IWRITE), f(p)))
        note('cleanup', containers_left=sh('docker', 'ps', '-aq', '--filter', 'name=hive-mail', '--filter', 'name=hive-stripe').stdout.strip(),
             total_minutes=round((time.time() - t0) / 60, 1))

if __name__ == '__main__':
    main()
