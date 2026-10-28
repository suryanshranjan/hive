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
        self.note = None   # what to say when the owner asks for status (set by whoever is running)

    def send(self, text, buttons=None, reply_to=None):
        p = {'chat_id': self.chat, 'text': text}
        if buttons:   # a flat list is one row; a list of lists is one row each
            rows = buttons if isinstance(buttons[0], list) else [buttons]
            p['reply_markup'] = {'inline_keyboard': [[{'text': label, 'callback_data': data} for label, data in row]
                                                     for row in rows]}
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
    ch.note = lambda: status_of(run)
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
                sent[q['id']] = ch.send(f"{who[:1].upper() + who[1:] + ', a' if who else 'A'} quick one from the builders:\n\n{q['question']}\n\n"
                                        "A tap is enough, or tell me in your own words.",
                                        buttons=[(c, f"{q['id']}|{c}") for c in _letters(q['question'])])
        if until() and not open_qs:
            ch.note = None
            return 0
        for text, data, reply_to in ch.updates(timeout=poll):
            if not data and answer_status(ch, text):
                continue
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
STATUS = ('status', 'how is it going', "how's it going", 'hows it going', 'progress', 'update', 'where are we',
          'any news', 'what is happening', "what's happening", 'how far')

def is_status(text):
    t = text.lower().strip(' ?!.')
    return any(t == s or t.startswith(s) for s in STATUS)

def status_of(run):
    """One plain paragraph on how a build is going, from the run folder alone."""
    import subprocess
    try:
        meta = json.load(open(os.path.join(run, 'run.json')))
    except Exception:
        return "The builders haven't started yet."
    n = meta.get('workers', 0)
    done = sum(1 for f in os.listdir(os.path.join(run, 'out')) if os.path.getsize(os.path.join(run, 'out', f)) > 0)
    log = subprocess.run(['git', '-C', os.path.join(run, 'up.git'), 'log', '--format=%s', meta['branch']],
                         capture_output=True, text=True).stdout.splitlines()
    landed = [s for s in log if not s.startswith('Lock:') and not s.startswith('hive:')]
    base = subprocess.run(['git', '-C', meta['repo'], 'log', '--format=%s', meta['branch']], capture_output=True,
                          text=True).stdout.splitlines() if os.path.isdir(meta.get('repo', '')) else []
    new = max(0, len(landed) - len([s for s in base if not s.startswith('Lock:') and not s.startswith('hive:')]))
    mins = max(0, int((time.time() - (meta.get('started') or time.time())) / 60))
    waiting = 0
    qdir = os.path.join(run, 'owner', 'questions')
    if os.path.isdir(qdir):
        waiting = sum(1 for f in os.listdir(qdir) if not os.path.exists(os.path.join(run, 'owner', 'answers', f)))
    if done >= n:
        line = 'All the builders have finished. I\'m checking the result now.'
    else:
        line = (f"The builders are {mins} minute{'s' if mins != 1 else ''} in. {done} of {n} have finished, and "
                f"{new} piece{'s' if new != 1 else ''} of work {'has' if new == 1 else 'have'} landed so far, each one "
                "passing every test.")
    if waiting:
        line += f" {waiting} question{'s' if waiting != 1 else ''} for you {'is' if waiting == 1 else 'are'} waiting above."
    return line

def answer_status(ch, text):
    """True when the owner asked how things are going (and was answered)."""
    if not text or not is_status(text):
        return False
    who = ch.name()
    note = ch.note() if callable(getattr(ch, 'note', None)) else None
    ch.send(f"{who[:1].upper() + who[1:] + '. ' if who else ''}{note or 'All quiet: nothing is running at the moment.'}")
    return True

def listen(run, ch, until, poll=2, tick=None):
    """While a build runs with no questions to ask (overnight, or a fix round), still answer "status"."""
    ch.note = lambda: status_of(run)
    while not until():
        if tick:
            tick()
        for text, _, _ in ch.updates(timeout=poll):
            answer_status(ch, text)
    ch.note = None

def _wait(ch, poll, want):
    """Block until the owner taps one of `want` (button data) or types something: ('tap', data) or ('text', words).
    A request for status is answered on the spot and the wait goes on."""
    while True:
        for text, data, _ in ch.updates(timeout=poll):
            if data in want:
                return 'tap', data
            if text and answer_status(ch, text):
                continue
            if text:
                return 'text', text

def _ask_one(ch, d, item, header, poll, can_undo):
    """One decision, answered in a tap: keep what the builders did, pick one of the real alternatives, or say
    something else. Disagreeing costs the same one tap as agreeing (Gate 29: rulings that only accept Hive's
    suggestion add nothing a builder would not reach alone). Returns 'undo' to go back; otherwise records the review."""
    k = item['id']
    options = item.get('options') or ([{'label': 'As you suggest', 'text': item['alternative']}]
                                      if item.get('alternative') else [])
    rec = item.get('recommend')
    star = lambda n, label: ('★ ' if rec == n else '') + label
    rows = [[(star(0, 'Keep it as is'), f'{k}|ok')]] + [[(star(n, o['label'] or f'Option {n}'), f'{k}|o{n}')]
                                                        for n, o in enumerate(options, 1)]
    rows.append([('Something else', f'{k}|no')] + ([('↩ Undo last', f'{k}|undo')] if can_undo else []))
    choices = ''.join(f"\n{n}. {o['text']}" for n, o in enumerate(options, 1))
    advice = f"\n\n{item['advice']}" if item.get('advice') else ''
    shown = item['text'] + (f"\n\nOther ways to do it:{choices}" if choices else '') + advice
    t0 = time.time()
    if options and item.get('impact', 2) >= 3:
        # High stakes: ask openly first, so a menu cannot frame the owner's own rule (Gate 30: offered options led the
        # founder away from his free-text verdict). The options come only if he asks for them.
        first = [[('Keep it as is', f'{k}|ok')], [('Show me some options', f'{k}|show')]]
        first.append([('↩ Undo last', f'{k}|undo')] if can_undo else [])
        msg = ch.send(f"{header}\n\n{item['text']}\n\nWhat should happen here? Tell me in your own words, or keep it "
                      "as is.", buttons=[r for r in first if r])
        kind, got = _wait(ch, poll, {data for row in first for _, data in row})
        if got == f'{k}|undo':
            return 'undo'
        if got != f'{k}|show':
            ok = got == f'{k}|ok' or (kind == 'text' and got.lower().strip('. !') in YES)
            correction = None if ok else got
            json.dump({'id': k, 'ok': ok, 'correction': correction, 'seconds': int(time.time() - t0), 'via': 'telegram',
                       'shown_as': item['text'], 'asked_open': True, 'followed_suggestion': None},
                      open(os.path.join(d, 'reviews', k + '.json'), 'w'))
            if not ok:
                ch.send("Understood. I'll have it done that way.")
            return None
    msg = ch.send(f"{header}\n\n{shown}", buttons=rows)
    kind, got = _wait(ch, poll, {data for row in rows for _, data in row})
    if got == f'{k}|undo':
        return 'undo'
    picked = got[len(k) + 2:] if kind == 'tap' and got.startswith(f'{k}|o') else ''
    if picked.isdigit() and 1 <= int(picked) <= len(options):
        ok, correction = False, options[int(picked) - 1]['text']
    elif got == f'{k}|ok' or (kind == 'text' and got.lower().strip('. !') in YES):
        ok, correction = True, None
    elif kind == 'text':
        ok, correction = False, got
    else:   # "Something else": ask for the owner's words
        ch.send('Of course. What would you prefer?', reply_to=msg)
        _, words = _wait(ch, poll, set())
        ok, correction = False, words
    followed = (ok and rec == 0) or (picked.isdigit() and rec == int(picked))
    json.dump({'id': k, 'ok': ok, 'correction': correction, 'seconds': int(time.time() - t0), 'via': 'telegram',
               'shown_as': shown, 'followed_suggestion': followed if rec is not None else None},
              open(os.path.join(d, 'reviews', k + '.json'), 'w'))
    if not ok:
        ch.send('Very good. I\'ll see to it.' if followed else "Understood. I'll have it done that way.")

def _walk(ch, d, items, label, poll):
    """Ask each item in turn; "Undo last" takes the previous answer back and asks it again."""
    i = 0
    while i < len(items):
        ch.note = lambda: (f"We're on decision {i + 1} of {len(items)}{' (the minor ones)' if label else ''}. Once you've "
                           "answered, the builders make your changes and I'll report back.")
        if _ask_one(ch, d, items[i], f'{label} {i + 1} of {len(items)}'.strip(), poll, can_undo=i > 0) == 'undo':
            i -= 1
            os.remove(os.path.join(d, 'reviews', items[i]['id'] + '.json'))
            ch.send('Of course. Back to the previous one.')
        else:
            i += 1

def _resolve_conflicts(ch, d, items, poll, rulings=None):
    """Before anything is sent: if two of the owner's decisions contradict each other, or a new one contradicts a ruling
    he gave on an earlier build (Gate 30: an answer contradicted his own verdict from an hour before), ask which wins."""
    from . import explain
    reviewed = [(i, json.load(open(os.path.join(d, 'reviews', i['id'] + '.json')))) for i in items
                if os.path.exists(os.path.join(d, 'reviews', i['id'] + '.json'))]
    reviewed = [(i, r) for i, r in reviewed if not r.get('auto')]
    earlier = [f'Earlier ruling: {t}' for t in (rulings or [])[-40:]]
    sentences = earlier + [(f"Keep as built: {i['text']}" if r['ok'] else f"Change it to: {r['correction']} (about: {i['text']})")
                           for i, r in reviewed]
    found = [c for c in explain.conflicts(sentences) if max(c['a'], c['b']) >= len(earlier)]   # at least one new answer
    path = os.path.join(d, 'resolutions.json')
    resolutions = json.load(open(path)) if os.path.exists(path) else []
    for n, c in enumerate(found):
        who = ch.name()
        ch.send(f"One thing before I send this{', ' + who if who else ''}: two of your answers pull in different "
                f"directions.\n\n{c['question']}",
                buttons=[(c['option_a'], f'conf|{n}|a'), (c['option_b'], f'conf|{n}|b')])
        kind, got = _wait(ch, poll, {f'conf|{n}|a', f'conf|{n}|b'})
        chosen = c['option_a'] if got == f'conf|{n}|a' else c['option_b'] if got == f'conf|{n}|b' else got
        resolutions.append({'question': c['question'], 'chosen': chosen})
        ch.send('Understood. That settles it.')
    if found:
        json.dump(resolutions, open(path, 'w'), indent=1)

def review(run, ch, goal='', check='', poll=20, greeting='Good morning', rulings=None):
    """The owner checks the builders' business assumptions on the phone: rewritten with context and an example, most
    important first, at most a handful; the smaller ones only if the owner asks to see them."""
    from . import explain, owner
    d = os.path.join(run, 'owner')
    todo = [a for a in owner._assumptions(d, False) if not os.path.exists(os.path.join(d, 'reviews', a['id'] + '.json'))]
    ch.drain()
    summary, shown, aside = explain.plan(d, goal, todo, rulings)
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
    _resolve_conflicts(ch, d, shown + aside, poll, rulings)
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

def collect(ch, question, poll=20):
    """Ask the owner an open question and gather every reply until "Done": a list of the owner's lines."""
    ch.drain()
    who = ch.name()
    ch.send(f"{who[:1].upper() + who[1:] + ', a' if who else 'A'} question for you:\n\n{question}\n\n"
            "Send as many messages as you like, one point each is perfect. Tap Done when you've finished.",
            buttons=[('Done', 'collect|done')])
    lines, prev = [], ch.note
    ch.note = lambda: f"I have {len(lines)} point{'s' if len(lines) != 1 else ''} from you so far. Tap Done when you've finished."
    while True:
        kind, got = _wait(ch, poll, {'collect|done'})
        if got == 'collect|done' or (kind == 'text' and got.lower().strip('. !') in ('done', 'that is all', "that's all")):
            if lines:
                break
            ch.send("I haven't had any points from you yet. Finish anyway?",   # an accidental tap must not end it
                    buttons=[('Yes, finish', 'collect|empty'), ("No, I'll write them", 'collect|more')])
            if _wait(ch, poll, {'collect|empty', 'collect|more'})[1] == 'collect|empty':
                break
            ch.send('Of course. Send your points whenever you are ready.')
            continue
        new = [l.strip(' -•*\t') for l in got.splitlines() if l.strip(' -•*\t')]
        lines += new
        ch.send(f"Noted ({len(lines)} so far). Anything else? Tap Done when you've finished.",
                buttons=[('Done', 'collect|done')])
    ch.note = prev
    ch.send(f"Thank you. I have {len(lines)} point{'s' if len(lines) != 1 else ''}. I'll take it from here.")
    return lines

def verdicts(ch, cases, poll=20, intro=None):
    """Put situations to the owner, each with outcome buttons (and "Something else"); undo goes back one.
    cases: [{id, situation, options: [text, ...]}]. Returns {id: chosen outcome in the owner's terms}."""
    ch.drain()
    if intro:
        ch.send(intro)
    out, i = {}, 0
    while i < len(cases):
        c = cases[i]
        ch.note = lambda: f"We're on situation {i + 1} of {len(cases)}."
        rows = [[(o[:60], f"{c['id']}|{n}")] for n, o in enumerate(c['options'])]
        rows.append([('Something else', f"{c['id']}|x")] + ([('↩ Undo last', f"{c['id']}|undo")] if i else []))
        msg = ch.send(f"{i + 1} of {len(cases)}\n\n{c['situation']}\n\nWhat should happen?", buttons=rows)
        kind, got = _wait(ch, poll, {d for row in rows for _, d in row})
        if got == f"{c['id']}|undo":
            i -= 1; out.pop(cases[i]['id'], None); ch.send('Of course. Back to the previous one.'); continue
        if kind == 'tap' and got.split('|')[-1].isdigit():
            out[c['id']] = c['options'][int(got.split('|')[-1])]
        elif kind == 'text':
            out[c['id']] = got
        else:
            ch.send('Of course. What should happen?', reply_to=msg)
            out[c['id']] = _wait(ch, poll, set())[1]
        i += 1
    ch.note = None
    ch.send(f"That's all {len(cases)}. Thank you{', ' + ch.name() if ch.name() else ''}.")
    return out

def ask_cli(question, out):
    """hive telegram ask "<question>" --out file: collect the owner's open answer into a private file."""
    cfg = load()
    if not cfg:
        print('Not connected yet: run hive telegram setup.'); return 1
    lines = collect(Channel(cfg), question)
    with open(out, 'w') as f:
        json.dump({'question': question, 'answers': lines, 'at': int(time.time())}, f, indent=1)
    os.chmod(out, 0o600)
    print(f'{len(lines)} point(s) saved to {out}.'); return 0

def verdicts_cli(cases_file, out, intro=None):
    """hive telegram verdicts <cases.json> --out file: the owner's verdict on each situation, into a private file."""
    cfg = load()
    if not cfg:
        print('Not connected yet: run hive telegram setup.'); return 1
    cases = json.load(open(cases_file))
    got = verdicts(Channel(cfg), cases, intro=intro)
    with open(out, 'w') as f:
        json.dump(got, f, indent=1)
    os.chmod(out, 0o600)
    print(f'{len(got)} verdict(s) saved to {out}.'); return 0
