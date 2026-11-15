"""His Google account over Google's own REST APIs (P5 of docs/jarvis_plan.md; the owner chose plain REST, no Google
client libraries): Gmail (read, and send on his yes), Calendar (read, and add or move events on his yes), Drive (only
the files Hive made or he picked: the drive.file scope, never his whole Drive).

Signing in, from his phone:
  1. Once, his own Google OAuth client (Google Cloud console > APIs & Services: enable the Gmail, Calendar and Drive
     APIs; OAuth consent screen with himself as a test user; Credentials > Create OAuth client > Desktop app). Gmail's
     scopes are restricted for public apps, so each owner's Hive signs in through his own client. He pastes its client
     ID and secret into the chat once; the message is deleted and they are kept encrypted (hive/vault.py).
  2. Hive sends a sign-in link. He signs in and allows; Google then opens a page on 127.0.0.1 that his phone cannot
     show. He copies that page's address and sends it: it carries the one-time code. (Google's device flow, which needs
     no copy, does not allow Gmail.)
The tokens are kept encrypted, refreshed when they expire, and `hive google forget` (or "disconnect google") removes them.

Sending is never done twice: each send has an action id, kept in the store's outbox before it goes; a send whose id
is already marked sent is not sent again, and one cut off mid-way is checked against Gmail (by its Message-ID) before
any retry."""
import base64, hashlib, json, os, secrets, time, urllib.error, urllib.parse, urllib.request
from email.message import EmailMessage

AUTH = os.environ.get('HIVE_GOOGLE_AUTH', 'https://accounts.google.com/o/oauth2/v2/auth')
TOKEN = os.environ.get('HIVE_GOOGLE_TOKEN', 'https://oauth2.googleapis.com/token')
API = os.environ.get('HIVE_GOOGLE_API', 'https://www.googleapis.com')
GMAIL = os.environ.get('HIVE_GMAIL_API', 'https://gmail.googleapis.com')
REDIRECT = 'http://127.0.0.1:8765/'
SCOPES = {   # the smallest that do the job
    'gmail': ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send'],
    'calendar': ['https://www.googleapis.com/auth/calendar.events'],
    'drive': ['https://www.googleapis.com/auth/drive.file'],
}

def _path():
    return os.path.join(os.path.expanduser('~'), '.hive', 'google.json')

def _load():
    from . import vault
    got = vault.load_json(_path(), {})
    return got if isinstance(got, dict) else {}

def _save(d):
    from . import vault
    vault.save_json(_path(), d)

def connected(what=None):
    d = _load()
    return bool(d.get('refresh_token')) and (what is None or what in d.get('allowed', []))

def set_client(client_id, client_secret):
    d = _load(); d.update(client_id=client_id.strip(), client_secret=client_secret.strip()); _save(d)

def has_client():
    d = _load()
    return bool(d.get('client_id') and d.get('client_secret'))

def sign_in_link(parts=('gmail', 'calendar', 'drive')):
    """The link he opens on his phone; the state and PKCE verifier are kept until he sends the code back."""
    d = _load()
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    state = secrets.token_urlsafe(16)
    d.update(pending={'state': state, 'verifier': verifier, 'parts': list(parts), 'at': time.time()}); _save(d)
    q = {'client_id': d['client_id'], 'redirect_uri': REDIRECT, 'response_type': 'code', 'access_type': 'offline',
         'prompt': 'consent', 'scope': ' '.join(s for p in parts for s in SCOPES[p]), 'state': state,
         'code_challenge': challenge, 'code_challenge_method': 'S256'}
    return AUTH + '?' + urllib.parse.urlencode(q)

def _post(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(),
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try:
            return json.load(e)
        except Exception:
            return {'error': f'HTTP {e.code}'}

def finish(pasted):
    """The address he sent back (or just the code). Returns (ok, a plain sentence)."""
    d = _load(); pend = d.get('pending') or {}
    q = urllib.parse.parse_qs(urllib.parse.urlparse(pasted.strip()).query) if '://' in pasted else {'code': [pasted.strip()]}
    if q.get('error'):
        return False, "Google says you didn't allow it, so nothing is connected."
    code = (q.get('code') or [''])[0]
    if not code or not pend:
        return False, "That isn't the address Google sent you to. Say \"connect google\" to start again."
    if q.get('state') and q['state'][0] != pend.get('state'):
        return False, "That address is from another sign-in. Say \"connect google\" to start again."
    got = _post(TOKEN, {'code': code, 'client_id': d['client_id'], 'client_secret': d['client_secret'],
                        'redirect_uri': REDIRECT, 'grant_type': 'authorization_code', 'code_verifier': pend['verifier']})
    if not got.get('refresh_token'):
        return False, f"Google didn't accept it ({got.get('error_description') or got.get('error') or 'no token'})."
    granted = got.get('scope', '')
    d.update(refresh_token=got['refresh_token'], access_token=got.get('access_token'),
             expires=time.time() + int(got.get('expires_in', 3600)) - 60,
             allowed=[p for p in pend.get('parts', []) if all(s in granted for s in SCOPES[p])] if granted else pend.get('parts', []))
    d.pop('pending', None); _save(d)
    return True, f"Connected to Google: {', '.join(d['allowed']) or 'nothing'} (I only read, and send or add only on your yes)."

def forget():
    d = _load()
    for k in ('refresh_token', 'access_token', 'expires', 'allowed', 'pending'):
        d.pop(k, None)
    _save(d)

def _token():
    d = _load()
    if not d.get('refresh_token'):
        raise RuntimeError('Google is not connected')
    if d.get('access_token') and d.get('expires', 0) > time.time():
        return d['access_token']
    got = _post(TOKEN, {'refresh_token': d['refresh_token'], 'client_id': d['client_id'],
                        'client_secret': d['client_secret'], 'grant_type': 'refresh_token'})
    if not got.get('access_token'):
        raise RuntimeError(f"Google sign-in has expired ({got.get('error', '?')}): say \"connect google\" again")
    d.update(access_token=got['access_token'], expires=time.time() + int(got.get('expires_in', 3600)) - 60); _save(d)
    return d['access_token']

class GoogleError(RuntimeError):
    """Google answered with an error; code is its HTTP status (0: no answer at all)."""
    def __init__(self, message, code=0):
        super().__init__(message); self.code = code

def call(method, url, body=None, params=None, retry=True):
    """One API call, JSON in and out; a refused token is refreshed once; 429/5xx retried once after a pause."""
    if params:
        url += ('&' if '?' in url else '?') + urllib.parse.urlencode(params, doseq=True)
    for attempt in (1, 2):
        req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                                     headers={'Authorization': f'Bearer {_token()}', 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            if attempt == 1 and retry and e.code == 401:
                d = _load(); d.pop('access_token', None); _save(d); continue
            if attempt == 1 and retry and e.code in (429, 500, 502, 503):
                time.sleep(2); continue
            try:
                detail = json.load(e).get('error', {})
            except Exception:
                detail = {}
            raise GoogleError(f"Google refused it ({e.code}: {(detail or {}).get('message', '')[:120]})", e.code) from None
        except (OSError, TimeoutError) as e:   # no answer: whether it happened is unknown
            raise GoogleError(f"Google did not answer ({e!r})", 0) from None
    return {}

# ---------------------------------------------------------------------------------------------------------- Gmail

def _header(msg, name):
    return next((h['value'] for h in msg.get('payload', {}).get('headers', []) if h['name'].lower() == name.lower()), '')

def _plain(part):
    if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
        return base64.urlsafe_b64decode(part['body']['data'] + '===').decode('utf-8', 'replace')
    for p in part.get('parts', []) or []:
        t = _plain(p)
        if t:
            return t
    return ''

def messages(days=7, unread=False, words=None, n=30):
    """Recent mail, newest first, in mail.py's own shape, so everything that reads his mail works the same."""
    q = f'newer_than:{days}d' + (' is:unread' if unread else '') + (f' {words}' if words else '')
    got = call('GET', f'{GMAIL}/gmail/v1/users/me/messages', params={'q': q, 'maxResults': n})
    out = []
    for m in got.get('messages', [])[:n]:
        full = call('GET', f"{GMAIL}/gmail/v1/users/me/messages/{m['id']}", params={'format': 'full'})
        out.append({'uid': m['id'], 'thread': full.get('threadId', ''), 'from': _header(full, 'From'),
                    'to': _header(full, 'To'), 'subject': _header(full, 'Subject'), 'date': _header(full, 'Date'),
                    'id': _header(full, 'Message-ID'), 'refs': _header(full, 'References'),
                    'unread': 'UNREAD' in full.get('labelIds', []), 'text': _plain(full.get('payload', {}))[:8000]})
    return out

def _outbox():
    from . import store
    con = store.connect()
    con.execute('CREATE TABLE IF NOT EXISTS outbox (action_id TEXT PRIMARY KEY, kind TEXT NOT NULL, target TEXT NOT NULL, '
                'state TEXT NOT NULL, at REAL NOT NULL, result TEXT DEFAULT "")')
    return con

def action_id(*parts):
    return hashlib.sha256('\x1f'.join(str(p) for p in parts).encode()).hexdigest()[:24]

def send(to, subject, body, reply_to=None, sender=''):
    """Send one mail from his Gmail, once. Returns (ok, why). A second call with the same mail is not sent again."""
    aid = action_id('mail', to, subject, body, (reply_to or {}).get('id', ''))
    con = _outbox()
    row = con.execute('SELECT state FROM outbox WHERE action_id=?', (aid,)).fetchone()
    mid = f'<hive-{aid}@hive.local>'
    if row and row[0] == 'sent':
        return True, 'already sent'
    if row and row[0] == 'sending':   # cut off mid-way last time: did it go?
        found = call('GET', f'{GMAIL}/gmail/v1/users/me/messages', params={'q': f'rfc822msgid:{mid}'})
        if found.get('messages'):
            con.execute("UPDATE outbox SET state='sent' WHERE action_id=?", (aid,)); return True, 'already sent'
    con.execute('INSERT OR REPLACE INTO outbox (action_id, kind, target, state, at) VALUES (?,?,?,?,?)',
                (aid, 'mail', to, 'sending', time.time()))
    m = EmailMessage(); m['To'] = to; m['Subject'] = subject; m['Message-ID'] = mid
    if sender:
        m['From'] = sender
    if reply_to:
        if reply_to.get('id'):
            m['In-Reply-To'] = reply_to['id']; m['References'] = ((reply_to.get('refs') or '') + ' ' + reply_to['id']).strip()
    m.set_content(body)
    payload = {'raw': base64.urlsafe_b64encode(m.as_bytes()).decode()}
    if reply_to and reply_to.get('thread'):
        payload['threadId'] = reply_to['thread']
    try:
        got = call('POST', f'{GMAIL}/gmail/v1/users/me/messages/send', payload, retry=False)
    except GoogleError as e:
        # a clear refusal (a 4xx other than throttling) did not send; anything else may have: kept as 'sending', so the
        # next try looks for it in Gmail first (tests/test_google.py: a lost answer was sent twice)
        sure = 400 <= e.code < 500 and e.code not in (408, 429)
        con.execute('UPDATE outbox SET state=?, result=? WHERE action_id=?', ('failed' if sure else 'sending', str(e)[:200], aid))
        return False, str(e)
    con.execute("UPDATE outbox SET state='sent', result=? WHERE action_id=?", (got.get('id', ''), aid))
    return True, ''

# ------------------------------------------------------------------------------------------------------- Calendar

def _when(e):
    import datetime as dt
    s = e.get('dateTime') or e.get('date')
    if 'T' in s:
        return dt.datetime.fromisoformat(s.replace('Z', '+00:00')).astimezone().replace(tzinfo=None), False
    return dt.datetime.fromisoformat(s), True

def events(days=7, back=0):
    """His events, in calendar_.py's own shape."""
    import datetime as dt
    now = dt.datetime.now().astimezone()
    got = call('GET', f'{API}/calendar/v3/calendars/primary/events', params={
        'timeMin': (now - dt.timedelta(days=back)).isoformat(), 'timeMax': (now + dt.timedelta(days=days + 1)).isoformat(),
        'singleEvents': 'true', 'orderBy': 'startTime', 'maxResults': 250})
    out = []
    for e in got.get('items', []):
        if e.get('status') == 'cancelled':
            continue
        start, all_day = _when(e['start']); end = _when(e['end'])[0]
        out.append({'title': e.get('summary', '(no title)'), 'start': start, 'end': end, 'all_day': all_day,
                    'where': e.get('location', ''), 'notes': (e.get('description') or '')[:300], 'id': e.get('id')})
    return out

def add_event(title, start, end, where='', guests=()):
    """Add an event (after his yes). start/end: datetimes in his time. Once: the same event twice is added once."""
    aid = action_id('event', title, start.isoformat(), end.isoformat())
    con = _outbox()
    row = con.execute('SELECT state FROM outbox WHERE action_id=?', (aid,)).fetchone()
    if row and row[0] == 'sent':
        return True, 'already added'
    if row and row[0] == 'sending':   # cut off mid-way last time: is it there already?
        found = call('GET', f'{API}/calendar/v3/calendars/primary/events',
                     params={'privateExtendedProperty': f'hive_action={aid}'})
        if found.get('items'):
            con.execute("UPDATE outbox SET state='sent' WHERE action_id=?", (aid,)); return True, 'already added'
    con.execute('INSERT OR REPLACE INTO outbox (action_id, kind, target, state, at) VALUES (?,?,?,?,?)',
                (aid, 'event', title, 'sending', time.time()))
    body = {'summary': title, 'location': where, 'start': {'dateTime': start.astimezone().isoformat()},
            'end': {'dateTime': end.astimezone().isoformat()}, 'attendees': [{'email': g} for g in guests],
            'extendedProperties': {'private': {'hive_action': aid}}}
    got = call('POST', f'{API}/calendar/v3/calendars/primary/events', body,
               params={'sendUpdates': 'all' if guests else 'none'}, retry=False)
    con.execute("UPDATE outbox SET state='sent', result=? WHERE action_id=?", (got.get('id', ''), aid))
    return True, got.get('htmlLink', '')

def busy(start, end):
    """What is already in that time: [titles]."""
    return [e['title'] for e in events(days=max(1, (end - start).days + 1)) if e['start'] < end and start < e['end']]

# ---------------------------------------------------------------------------------------------------------- Drive

def drive_files(words='', n=20):
    """The Drive files Hive may see (drive.file: those it made or he picked)."""
    q = "trashed = false" + (f" and name contains '{words.replace(chr(39), '')}'" if words else '')
    return call('GET', f'{API}/drive/v3/files', params={'q': q, 'pageSize': n, 'fields': 'files(id,name,modifiedTime)'}
                ).get('files', [])

def drive_upload(path, name=None):
    """Put a file in his Drive (a report, an export). Returns its id."""
    import mimetypes, uuid
    name = name or os.path.basename(path); edge = uuid.uuid4().hex
    meta = json.dumps({'name': name}).encode()
    body = (f'--{edge}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n'.encode() + meta +
            f'\r\n--{edge}\r\nContent-Type: {mimetypes.guess_type(name)[0] or "application/octet-stream"}\r\n\r\n'.encode() +
            open(path, 'rb').read() + f'\r\n--{edge}--\r\n'.encode())
    req = urllib.request.Request(f'{API}/upload/drive/v3/files?uploadType=multipart', data=body, method='POST',
                                 headers={'Authorization': f'Bearer {_token()}',
                                          'Content-Type': f'multipart/related; boundary={edge}'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r).get('id')

def main(args):
    if args and args[0] == 'forget':
        forget(); print('Google disconnected: its tokens are removed from this computer.'); return 0
    if args and args[0] == 'setup':
        import getpass
        cid = input('OAuth client ID > ').strip(); sec = getpass.getpass('OAuth client secret (not shown) > ').strip()
        set_client(cid, sec)
        print('\nOpen this link, sign in and allow, then paste the address you land on (it will not load):\n')
        print(sign_in_link())
        ok, said = finish(input('\nAddress > ').strip()); print(said); return 0 if ok else 1
    d = _load()
    print('Google: ' + (f"connected ({', '.join(d.get('allowed', []))})" if d.get('refresh_token') else 'not connected') +
          ('' if d.get('client_id') else '; no OAuth client yet (hive google setup)'))
    return 0
