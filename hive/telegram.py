"""The owner's phone: Hive's questions and morning reviews over Telegram (Gate 28: the founder was away from the laptop,
so his review had to be done by a proxy).

  hive telegram setup     connect your Telegram once (asks for a bot token from @BotFather, then for one message from you)
  hive telegram test      send yourself a test message

Once connected, `hive start` sends builders' questions to your phone and takes your replies as answers, and an overnight
build sends its summary and its assumptions to your phone when it finishes. Safety: the token lives in
~/.hive/telegram.json (never in a repository); only messages from the chat that connected are read; a message is only
ever stored as an answer or a correction, never run."""
import getpass, json, os, time, urllib.request

PATH = os.path.join(os.path.expanduser('~'), '.hive', 'telegram.json')

def _call(token, method, **params):
    req = urllib.request.Request(f'https://api.telegram.org/bot{token}/{method}', data=json.dumps(params).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=params.get('timeout', 0) + 30) as r:
        body = json.load(r)
    if not body.get('ok'):
        raise RuntimeError(f"Telegram {method}: {body.get('description')}")
    return body['result']

def load():
    if os.environ.get('HIVE_TELEGRAM') == '0' or not os.path.exists(PATH):
        return None
    cfg = json.load(open(PATH))
    return cfg if cfg.get('token') and cfg.get('chat_id') else None

class Channel:
    """One owner's chat. `api(method, **params)` is the Telegram Bot API (replaced by a fake in tests)."""
    def __init__(self, cfg, api=None):
        self.chat = cfg['chat_id']
        self.api = api or (lambda method, **p: _call(cfg['token'], method, **p))
        self.offset = None

    def send(self, text, buttons=None, reply_to=None):
        p = {'chat_id': self.chat, 'text': text}
        if buttons:
            p['reply_markup'] = {'inline_keyboard': [[{'text': label, 'callback_data': data} for label, data in buttons]]}
        if reply_to:
            p['reply_to_message_id'] = reply_to
        return self.api('sendMessage', **p)['message_id']

    def updates(self, timeout=20):
        """New replies from the owner's chat only: (text or None, button data or None, id of the message replied to)."""
        p = {'timeout': timeout, 'allowed_updates': ['message', 'callback_query']}
        if self.offset is not None:
            p['offset'] = self.offset
        out = []
        for u in self.api('getUpdates', **p):
            self.offset = u['update_id'] + 1
            if 'callback_query' in u:
                cq = u['callback_query']
                if cq.get('message', {}).get('chat', {}).get('id') != self.chat:
                    continue
                self.api('answerCallbackQuery', callback_query_id=cq['id'])
                out.append((None, cq.get('data'), cq.get('message', {}).get('message_id')))
            elif 'message' in u:
                m = u['message']
                if m.get('chat', {}).get('id') != self.chat or not m.get('text'):
                    continue   # someone else, or not text: ignored
                out.append((m['text'].strip(), None, (m.get('reply_to_message') or {}).get('message_id')))
        return out

def _letters(question):
    import re
    return [c for c in 'ABCD' if re.search(rf'(^|\s){c}\)\s', question)]

def bridge_questions(run, ch, until, poll=2, tick=None):
    """Send each new builder question to the phone; store the owner's replies as answers. Ends once until() is true and
    nothing is waiting. A reply goes to the question it replies to, or else to the oldest unanswered question."""
    d = os.path.join(run, 'owner'); sent = {}   # question id -> message id
    def unanswered():
        qs = [json.load(open(os.path.join(d, 'questions', f))) for f in sorted(os.listdir(os.path.join(d, 'questions')))]
        return [q for q in qs if not os.path.exists(os.path.join(d, 'answers', q['id'] + '.json'))]
    while True:
        if tick:
            tick()
        open_qs = unanswered()
        for q in open_qs:
            if q['id'] not in sent:
                n = len(os.listdir(os.path.join(d, 'questions')))
                sent[q['id']] = ch.send(f"Question from builder {q['worker']}:\n\n{q['question']}\n\n"
                                        "Tap a letter, or reply with your own words.",
                                        buttons=[(c, f"{q['id']}|{c}") for c in _letters(q['question'])])
        if until() and not open_qs:
            return 0
        for text, data, reply_to in ch.updates(timeout=poll):
            if data and '|' in data:
                qid, ans = data.split('|', 1)
            else:
                by_msg = {m: qid for qid, m in sent.items()}
                waiting = [q['id'] for q in unanswered() if q['id'] in sent]
                qid = by_msg.get(reply_to) or (waiting[0] if waiting else None)
                ans = text
            path = os.path.join(d, 'answers', f'{qid}.json') if qid else None
            if not qid or not ans or os.path.exists(path):
                continue
            q = json.load(open(os.path.join(d, 'questions', qid + '.json')))
            json.dump({'id': qid, 'answer': ans, 'answered': int(time.time()), 'seconds': int(time.time()) - q['asked'],
                       'via': 'telegram'}, open(path, 'w'))
            ch.send(f"Got it. Sent to builder {q['worker']}.", reply_to=sent.get(qid))

def review(run, ch, poll=20):
    """The owner checks the business assumptions on the phone, one at a time: Right, or Wrong plus the owner's rule."""
    from . import owner
    d = os.path.join(run, 'owner')
    todo = [a for a in owner._assumptions(d, False) if not os.path.exists(os.path.join(d, 'reviews', a['id'] + '.json'))]
    for n, a in enumerate(todo, 1):
        msg = ch.send(f"Assumption {n} of {len(todo)}:\n\n{a['text']}\n\nIs that right?",
                      buttons=[('Right', f"{a['id']}|ok"), ('Wrong', f"{a['id']}|no")])
        t0 = time.time(); verdict = None
        while verdict is None:
            for text, data, reply_to in ch.updates(timeout=poll):
                if data == f"{a['id']}|ok":
                    verdict = (True, None)
                elif data == f"{a['id']}|no":
                    ch.send('What should happen instead? Reply in a few words.', reply_to=msg)
                elif text:
                    low = text.lower().strip('. !')
                    verdict = (True, None) if low in ('right', 'yes', 'ok', 'correct', 'y') else (False, text)
                if verdict:
                    break
        ok, correction = verdict
        json.dump({'id': a['id'], 'ok': ok, 'correction': correction, 'seconds': int(time.time() - t0), 'via': 'telegram'},
                  open(os.path.join(d, 'reviews', a['id'] + '.json'), 'w'))
    rows = owner.write_corrections(d)
    ch.send('Thanks. ' + ('Everything they assumed was right.' if not rows else
                          f"{len(rows)} to fix. I'm sending the builders back now; I'll message you when it's done."))
    return rows

def setup():
    print('\nLet\'s connect Hive to your Telegram, so questions reach your phone.\n'
          '1. In Telegram, open @BotFather, send /newbot, and follow the two steps (a name, then a username ending in "bot").\n'
          '2. BotFather replies with a token like 123456:ABC-DEF... Paste it here (it will not be shown).')
    token = getpass.getpass('  Token > ').strip()
    try:
        bot = _call(token, 'getMe')
    except Exception as e:
        print(f'  That token did not work ({e}). Check it and run hive telegram setup again.'); return 1
    print(f"\n3. Now open your bot, @{bot['username']}, in Telegram and send it any message (for example: hi).")
    offset, chat = None, None
    deadline = time.time() + 300
    while chat is None and time.time() < deadline:
        p = {'timeout': 20}
        if offset is not None:
            p['offset'] = offset
        for u in _call(token, 'getUpdates', **p):
            offset = u['update_id'] + 1
            m = u.get('message')
            if m and m.get('chat', {}).get('type') == 'private':
                chat = m['chat']['id']; who = m.get('from', {}).get('first_name', 'you')
    if chat is None:
        print('  No message arrived within 5 minutes. Run hive telegram setup again.'); return 1
    _call(token, 'getUpdates', offset=offset, timeout=0)   # mark it read
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    with open(PATH, 'w') as f:
        json.dump({'token': token, 'chat_id': chat}, f)
    os.chmod(PATH, 0o600)
    _call(token, 'sendMessage', chat_id=chat, text=f"Hi {who}! Hive is connected. Builders' questions and your morning "
                                                  "reviews will come here. I only listen to this chat.")
    print(f'  Connected. Hive will message {who} from now on. (Saved to {PATH}; keep it private.)'); return 0

def test():
    cfg = load()
    if not cfg:
        print('Not connected yet: run hive telegram setup.'); return 1
    Channel(cfg).send('Test from Hive: this is where your questions will arrive.'); print('Sent.'); return 0
