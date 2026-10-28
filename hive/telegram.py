"""The owner's phone: Hive's questions and morning reviews over Telegram (Gate 28: the founder was away from the laptop,
so his review had to be done by a proxy).

  hive telegram setup        connect your Telegram once (asks for a bot token from @BotFather, then for one message)
  hive telegram test         send yourself a test message
  hive telegram call <name>  how Hive addresses you, for example: hive telegram call sir

Once connected, `hive start` sends builders' questions to your phone and takes your replies as answers, and an overnight
build sends its summary and its assumptions to your phone when it finishes. Safety: the token lives in
~/.hive/telegram.json (never in a repository); only messages from the chat that connected are read; a message is only
ever stored as an answer or a correction, never run.

Voice: a composed, courteous, quietly confident assistant that is a step ahead: short sentences, a clear recommendation,
never flustered or chatty, and every message leaves the owner one easy thing to do."""
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
        self.chat = cfg['chat_id']; self.address = cfg.get('address')
        self.api = api or (lambda method, **p: _call(cfg['token'], method, **p))
        self.offset = None

    def send(self, text, buttons=None, reply_to=None):
        p = {'chat_id': self.chat, 'text': text}
        if buttons:
            p['reply_markup'] = {'inline_keyboard': [[{'text': label, 'callback_data': data} for label, data in buttons]]}
        if reply_to:
            p['reply_to_message_id'] = reply_to
        return self.api('sendMessage', **p)['message_id']

    def drain(self):
        """Skip anything sent before now (an old "hi" from setup must not count as an answer)."""
        while True:
            p = {'timeout': 0}
            if self.offset is not None:
                p['offset'] = self.offset
            batch = self.api('getUpdates', **p)
            if not batch:
                return
            self.offset = batch[-1]['update_id'] + 1

    def name(self):
        """How to address the owner: the chosen form (for example "sir"), else the first name on Telegram."""
        if self.address:
            return self.address
        try:
            return self.api('getChat', chat_id=self.chat).get('first_name') or ''
        except Exception:
            return ''

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
                who = ch.name()
                sent[q['id']] = ch.send(f"{who + ', a' if who else 'A'} quick one from the builders:\n\n{q['question']}\n\n"
                                        "A tap is enough, or tell me in your own words.",
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
            ch.send('Thank you. Passing it on.', reply_to=sent.get(qid))

YES = ('right', 'yes', 'ok', 'okay', 'correct', 'y', 'keep', 'keep it', 'fine', 'sure', 'yes thats right')

def _wait(ch, poll, want):
    """Block until the owner taps one of `want` (button data) or types something: ('tap', data) or ('text', words)."""
    while True:
        for text, data, _ in ch.updates(timeout=poll):
            if data in want:
                return 'tap', data
            if text:
                return 'text', text

def _ask_one(ch, d, item, header, poll, can_undo):
    """One decision, answered in a tap: take Hive's suggestion, keep what the builders did, or say something else.
    Returns 'undo' when the owner wants the previous decision back; otherwise records the review."""
    k = item['id']; alt = item.get('alternative')
    buttons = ([('As you suggest', f'{k}|alt')] if alt else []) + [('Keep it', f'{k}|ok'), ('Something else', f'{k}|no')]
    if can_undo:
        buttons.append(('↩ Undo last', f'{k}|undo'))
    advice = f"\n\n{item['advice']}" if item.get('advice') else ''
    msg = ch.send(f"{header}\n\n{item['text']}{advice}", buttons=buttons)
    t0 = time.time()
    kind, got = _wait(ch, poll, {data for _, data in buttons})
    if got == f'{k}|undo':
        return 'undo'
    if got == f'{k}|alt':
        ok, correction = False, alt
    elif got == f'{k}|ok' or (kind == 'text' and got.lower().strip('. !') in YES):
        ok, correction = True, None
    elif kind == 'text':
        ok, correction = False, got
    else:   # "Something else": ask for the owner's words
        ch.send('Of course. What would you prefer?', reply_to=msg)
        _, words = _wait(ch, poll, set())
        ok, correction = False, words
    json.dump({'id': k, 'ok': ok, 'correction': correction, 'seconds': int(time.time() - t0), 'via': 'telegram',
               'shown_as': item['text'] + advice}, open(os.path.join(d, 'reviews', k + '.json'), 'w'))
    if not ok:
        ch.send('Very good. I\'ll see to it.' if got == f'{k}|alt' else "Understood. I'll have it done that way.")

def _walk(ch, d, items, label, poll):
    """Ask each item in turn; "Undo last" takes the previous answer back and asks it again."""
    i = 0
    while i < len(items):
        if _ask_one(ch, d, items[i], f'{label} {i + 1} of {len(items)}'.strip(), poll, can_undo=i > 0) == 'undo':
            i -= 1
            os.remove(os.path.join(d, 'reviews', items[i]['id'] + '.json'))
            ch.send('Of course. Back to the previous one.')
        else:
            i += 1

def review(run, ch, goal='', check='', poll=20, greeting='Good morning'):
    """The owner checks the builders' business assumptions on the phone: rewritten with context and an example, most
    important first, at most a handful; the smaller ones only if the owner asks to see them."""
    from . import explain, owner
    d = os.path.join(run, 'owner')
    todo = [a for a in owner._assumptions(d, False) if not os.path.exists(os.path.join(d, 'reviews', a['id'] + '.json'))]
    ch.drain()
    summary, shown, aside = explain.plan(d, goal, todo)
    who = ch.name()
    mins = max(1, round(len(shown) * 0.3))
    ch.send(f"{greeting}{', ' + who if who else ''}. While you were away, the builders finished this: {summary}\n\n"
            + (f"{check}\n\n" if check else '')
            + (f"There {'is' if len(shown) == 1 else 'are'} {len(shown)} decision{'s' if len(shown) != 1 else ''} I'd like "
               f"you to make, about {mins} minute{'s' if mins != 1 else ''}. I've put my recommendation on each, so a "
               "tap is enough." if shown else "Nothing needs your attention."))
    _walk(ch, d, shown, '', poll)
    if aside:
        ch.send(f"{len(aside)} minor one{'s' if len(aside) != 1 else ''} remain{'s' if len(aside) == 1 else ''}. I'd leave "
                f"{'it' if len(aside) == 1 else 'them'} as the builders had {'it' if len(aside) == 1 else 'them'}, unless "
                "you'd like a look.",
                buttons=[('Show me', 'aside|show'), ('Leave them', 'aside|leave')])
        kind, got = _wait(ch, poll, {'aside|show', 'aside|leave'})
        if got == 'aside|show' or (kind == 'text' and got.lower().startswith(('show', 'yes', 'see'))):
            _walk(ch, d, aside, 'Smaller one', poll)
        else:
            for item in aside:
                json.dump({'id': item['id'], 'ok': True, 'correction': None, 'seconds': 0, 'via': 'telegram',
                           'auto': 'left as built at the owner\'s choice', 'shown_as': item['text']},
                          open(os.path.join(d, 'reviews', item['id'] + '.json'), 'w'))
    # one last look before anything goes to the builders
    while True:
        changes = [json.load(open(os.path.join(d, 'reviews', i['id'] + '.json'))) for i in shown + aside
                   if os.path.exists(os.path.join(d, 'reviews', i['id'] + '.json'))]
        n = sum(not r['ok'] for r in changes)
        ch.send(f"That's everything: {n} change{'s' if n != 1 else ''}. Shall I send {'it' if n == 1 else 'them'} to the "
                "builders?" if n else "That's everything, and nothing needs changing. Shall I close it out?",
                buttons=[('Send it' if n else 'Close it out', 'final|send'), ('↩ Undo last', 'final|undo')])
        kind, got = _wait(ch, poll, {'final|send', 'final|undo'})
        if got != 'final|undo':
            break
        last = (aside if aside and os.path.exists(os.path.join(d, 'reviews', aside[-1]['id'] + '.json'))
                and not json.load(open(os.path.join(d, 'reviews', aside[-1]['id'] + '.json'))).get('auto') else shown)
        if not last:
            break
        os.remove(os.path.join(d, 'reviews', last[-1]['id'] + '.json'))
        ch.send('Of course. Back to the previous one.')
        _walk(ch, d, [last[-1]], '', poll)
    rows = owner.write_corrections(d)
    ch.send(('Right away. The builders are on it. ' + "I'll let you know the moment it's done.") if rows else
            'Very good. Everything stands as built.')
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
    address = input(f'\n4. How should Hive address you? (Enter for "{who}"; or for example: sir) > ').strip() or who
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    with open(PATH, 'w') as f:
        json.dump({'token': token, 'chat_id': chat, 'address': address}, f)
    os.chmod(PATH, 0o600)
    _call(token, 'sendMessage', chat_id=chat, text=f"Hello, {address}. I'm connected and at your service. When the "
                                                  "builders need a decision, I'll bring it here, with my recommendation. "
                                                  "I listen to this chat only.")
    print(f'  Connected. Hive will address you as "{address}". (Saved to {PATH}; keep it private.)'); return 0

def call(address):
    """Change how Hive addresses the owner."""
    cfg = load()
    if not cfg:
        print('Not connected yet: run hive telegram setup.'); return 1
    cfg['address'] = address.strip()
    with open(PATH, 'w') as f:
        json.dump(cfg, f)
    os.chmod(PATH, 0o600)
    Channel(cfg).send(f'Very good, {cfg["address"]}.'); print(f'Hive will address you as "{cfg["address"]}".'); return 0

def test():
    cfg = load()
    if not cfg:
        print('Not connected yet: run hive telegram setup.'); return 1
    ch = Channel(cfg); who = ch.name()
    ch.send(f"At your service{', ' + who if who else ''}. All systems are working; this is where your decisions will "
            "arrive."); print('Sent.'); return 0
