"""hive/google.py against a stand-in Google (a local HTTP server speaking the same REST): signing in from the phone
(link, pasted address, PKCE, state), token refresh, Gmail read and send (once, even when cut off), Calendar read and add
(once), Drive, and Hive's existing mail and calendar features running on it. No network.
usage: python3 tests/test_google.py"""
import base64, datetime as dt, http.server, json, os, subprocess, sys, tempfile, threading, time, urllib.parse
sys.path.insert(0, os.getcwd()); sys.stdout.reconfigure(encoding='utf-8')
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home; os.environ['HIVE_EMBED'] = '0'

STATE = {'tokens': 0, 'refreshes': 0, 'sent': [], 'events': [], 'fail_send_once': False, 'verifier_ok': None}
class Google(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass
    def _json(self, code, body):
        raw = json.dumps(body).encode(); self.send_response(code); self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def _authed(self):
        return self.headers.get('Authorization') == f"Bearer access-{STATE['refreshes']}"
    def do_POST(self):
        n = int(self.headers.get('Content-Length') or 0); body = self.rfile.read(n)
        u = urllib.parse.urlparse(self.path)
        if u.path == '/token':
            f = dict(urllib.parse.parse_qsl(body.decode()))
            if f['grant_type'] == 'authorization_code':
                import hashlib
                STATE['verifier_ok'] = (base64.urlsafe_b64encode(hashlib.sha256(f['code_verifier'].encode()).digest())
                                        .rstrip(b'=').decode() == STATE.get('challenge'))
                if f['code'] != 'GOOD':
                    return self._json(400, {'error': 'invalid_grant'})
                return self._json(200, {'access_token': 'access-0', 'refresh_token': 'refresh-1', 'expires_in': 3600,
                                        'scope': ' '.join(STATE['scopes'])})
            STATE['refreshes'] += 1
            return self._json(200, {'access_token': f"access-{STATE['refreshes']}", 'expires_in': 3600})
        if not self._authed():
            return self._json(401, {'error': {'message': 'expired'}})
        if u.path.endswith('/messages/send'):
            raw = base64.urlsafe_b64decode(json.loads(body)['raw']).decode()
            STATE['sent'].append(raw)
            if STATE['fail_send_once']:   # it went, but the answer was lost on the way back
                STATE['fail_send_once'] = False; return self._json(503, {'error': {'message': 'lost'}})
            return self._json(200, {'id': f"m{len(STATE['sent'])}"})
        if '/calendars/primary/events/' in u.path:
            item = next((e for e in STATE['events'] if e.get('id') == u.path.rsplit('/',1)[1]), None)
            return self._json(200 if item else 404, item or {})
        if u.path.endswith('/calendars/primary/events'):
            STATE['events'].append(json.loads(body)); return self._json(200, {'id': 'e1', 'htmlLink': 'https://cal/e1'})
        if u.path.startswith('/upload/drive'):
            return self._json(200, {'id': 'f1'})
        self._json(404, {})
    def do_GET(self):
        u = urllib.parse.urlparse(self.path); q = dict(urllib.parse.parse_qsl(u.query))
        if not self._authed():
            return self._json(401, {'error': {'message': 'expired'}})
        if u.path.endswith('/messages') and 'rfc822msgid' in q.get('q', ''):
            mid = q['q'].split('rfc822msgid:', 1)[1]
            return self._json(200, {'messages': [{'id': 'x'}]} if any(mid in s for s in STATE['sent']) else {})
        if u.path.endswith('/messages'):
            return self._json(200, {'messages': [{'id': 'g1'}]})
        if '/messages/sent' in u.path:
            return self._json(200, {'id': u.path.rsplit('/', 1)[1]})
        if '/messages/m' in u.path:
            import email
            mid = u.path.rsplit('/', 1)[1]
            message = email.message_from_string(STATE['sent'][int(mid[1:]) - 1])
            data = base64.urlsafe_b64encode(message.get_payload(decode=True)).decode()
            return self._json(200, {'id': mid, 'payload': {'mimeType': 'text/plain', 'body': {'data': data},
                'headers': [{'name': k, 'value': v} for k, v in message.items()]}})
        if '/messages/' in u.path:
            body = base64.urlsafe_b64encode(b'Can the tasting move to Friday?').decode()
            return self._json(200, {'id': 'g1', 'threadId': 't1', 'labelIds': ['UNREAD', 'INBOX'], 'payload': {
                'mimeType': 'text/plain', 'body': {'data': body}, 'headers': [
                    {'name': 'From', 'value': 'Asha <asha@mehta.example>'}, {'name': 'Subject', 'value': 'Tasting'},
                    {'name': 'Message-ID', 'value': '<a1@mehta.example>'}, {'name': 'Date', 'value': 'today'}]}})
        if '/calendars/primary/events/' in u.path:
            item = next((e for e in STATE['events'] if e.get('id') == u.path.rsplit('/',1)[1]), None)
            return self._json(200 if item else 404, item or {})
        if u.path.endswith('/calendars/primary/events'):
            t = (dt.datetime.now() + dt.timedelta(hours=2)).astimezone()
            return self._json(200, {'items': [{'id': 'e0', 'summary': 'Supplier call', 'start': {'dateTime': t.isoformat()},
                                               'end': {'dateTime': (t + dt.timedelta(hours=1)).isoformat()}}]})
        if u.path.endswith('/drive/v3/files'):
            return self._json(200, {'files': [{'id': 'f0', 'name': 'Menu.pdf'}]})
        self._json(404, {})

srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Google); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{srv.server_address[1]}'
os.environ.update(HIVE_GOOGLE_TOKEN=base + '/token', HIVE_GOOGLE_API=base, HIVE_GMAIL_API=base,
                  HIVE_GOOGLE_AUTH='https://accounts.example/auth')
from hive import calendar_, google, mail, memory, office, telegram
memory.DIR = os.path.join(home, '.hive', 'rules')
sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
from test_telegram_fake import FakeTelegram, ME, say, tap

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))

repo = os.path.join(home, 'shop'); subprocess.run(['git', 'init', '-q', '-b', 'main', repo])
subprocess.run(['git', '-C', repo, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'i'])
ch = lambda fake: telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake)

# 1. signing in from the phone: steps and client first, then a link, then the pasted address
fake = FakeTelegram([say('id 123-abc.apps.googleusercontent.com secret GOCSPX-abcdefghijklmnop')])
r = office.handle(ch(fake), repo, 'connect my google', 1)
link = fake.sent[-1]['text']
q = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(link).query))
STATE['challenge'] = q['code_challenge']; STATE['scopes'] = q['scope'].split()
check('connect google: the one-time steps, then his client kept and a sign-in link with the smallest scopes',
      (r, 'test user' in fake.sent[0]['text'], q['client_id'], 'gmail.send' in q['scope'] and 'drive.file' in q['scope'],
       'https://mail.google.com/' in q['scope'], q['code_challenge_method']),
      ('google_link_sent', True, '123-abc.apps.googleusercontent.com', True, False, 'S256'))
fake = FakeTelegram([])
r = office.handle(ch(fake), repo, f"http://127.0.0.1:8765/?state=WRONG&code=GOOD&scope=x", 1)
check('an address from another sign-in is refused', (r, google.connected()), ('google_failed', False))
r = office.handle(ch(fake), repo, f"http://127.0.0.1:8765/?state={q['state']}&code=GOOD&scope=x", 1)
check('the pasted address connects (PKCE checked); the message carrying it is deleted',
      (r, google.connected('gmail'), google.connected('calendar'), STATE['verifier_ok'], bool(getattr(fake, 'deleted', None))),
      ('google_connected', True, True, True, True))
raw = open(google._path()).read()
check('tokens and the client secret are encrypted on disk', ('refresh-1' in raw, 'GOCSPX' in raw), (False, False))

# 2. Gmail through Hive's own mail features; an expired token is refreshed by itself
STATE['refreshes'] = 1   # the stored token is now stale: the next call is refused once, then refreshed
msgs = mail.messages(repo, days=2)
check('his Gmail reads in mail.py\'s own shape (after refreshing the token)',
      (msgs[0]['from'], msgs[0]['subject'], 'Friday' in msgs[0]['text'], msgs[0]['unread'], STATE['refreshes'] >= 2),
      ('Asha <asha@mehta.example>', 'Tasting', True, True, True))
ok, why = mail.send(repo, 'asha@mehta.example', 'Re: Tasting', 'Friday works.', reply_to=msgs[0])
check('a reply goes from his Gmail, in the thread', (ok, 'In-Reply-To: <a1@mehta.example>' in STATE['sent'][-1]), (True, True))
mail.send(repo, 'asha@mehta.example', 'Re: Tasting', 'Friday works.', reply_to=msgs[0])
check('the same reply again is not sent twice', len(STATE['sent']), 1)
STATE['fail_send_once'] = True
ok, why = mail.send(repo, 'ravi@x.in', 'Rota', 'You are on Saturday.')
ok2, why2 = mail.send(repo, 'ravi@x.in', 'Rota', 'You are on Saturday.')
check('cut off mid-way: it is checked in Gmail before a retry, and not sent twice', (len(STATE['sent']), ok2, why2),
      (2, True, 'already sent'))

# 3. Calendar: read by Hive's calendar features; an event added on his yes, once
evs = calendar_.events(repo, days=1)
check('his Google Calendar reads in calendar_.py\'s own shape', [e['title'] for e in evs], ['Supplier call'])
from hive import explain
explain.ask_json = lambda prompt: {'title': 'Tasting with Asha', 'start': (dt.datetime.now() + dt.timedelta(days=1)).strftime('%Y-%m-%dT15:00'),
                                   'minutes': 60, 'where': 'Andheri', 'guests': ['asha@mehta.example']}
from test_telegram_fake import tap
fake = FakeTelegram([tap('evt|yes')])
r = office.handle(ch(fake), repo, 'put the tasting with Asha on my calendar tomorrow at 3', 1)
check('"put ... on my calendar": shown with its guests, added on his yes',
      (r, 'Invites go to asha@mehta.example' in fake.sent[0]['text'], STATE['events'][-1]['summary']),
      ('event_added', True, 'Tasting with Asha'))
# Replay the same persisted approval after completion: no second event is created.
from hive import actions, store
row = store.connect().execute('SELECT id,message_id FROM actions ORDER BY created DESC LIMIT 1').fetchone()
actions.resume(ch(FakeTelegram([])), f'act|{row[0]}|yes', row[1], repo)
check('a completed approval cannot create the event again', len(STATE['events']), 1)
# A fresh explicit approval is a new action, even if the content is identical.
fake = FakeTelegram([tap('evt|yes')]); office.handle(ch(fake), repo, 'put the tasting with Asha on my calendar tomorrow at 3', 1)
check('a separately approved identical event is a distinct action', len(STATE['events']), 2)
fake = FakeTelegram([tap('evt|no')]); r = office.handle(ch(fake), repo, 'put the tasting with Asha on my calendar tomorrow at 3', 1)
check('Cancel: nothing added', (r, len(STATE['events'])), ('add_event_no', 2))

# 4. Drive (only what Hive made or he picked), and disconnecting
check('Drive: the files Hive may see', [f['name'] for f in google.drive_files()], ['Menu.pdf'])
p = os.path.join(home, 'report.txt'); open(p, 'w').write('weekly report')
check('Drive: a file put in his Drive', google.drive_upload(p), 'f1')
fake = FakeTelegram([]); office.handle(ch(fake), repo, 'disconnect google', 1)
check('"disconnect google": tokens gone, mail and calendar no longer read from it',
      (google.connected(), mail.config(repo), calendar_.config(repo)), (False, {}, {}))
srv.shutdown()
sys.exit(fail)
