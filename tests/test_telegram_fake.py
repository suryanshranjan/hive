"""The fake Telegram shared by the tests (records what Hive sends, replies with scripted taps and messages)."""
import html, re
ME, STRANGER = 111, 999
fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))

class FakeTelegram:
    """Records what Hive sends; replies with the owner's scripted taps and messages, one batch per poll."""
    def __init__(self, script, stale=()):
        self.sent, self.script, self.uid, self.stale = [], list(script), 0, list(stale)
    def __call__(self, method, **p):
        if method == 'sendMessage':   # tests read the text as the owner sees it: tags dropped, entities unescaped
            p = dict(p, html=p['text'], text=html.unescape(re.sub(r'<[^>]+>', '', p['text'])))
            self.sent.append(p); return {'message_id': len(self.sent)}
        if method == 'answerCallbackQuery':
            return True
        if method == 'getFile':
            return {'file_path': 'voice/' + p['file_id'] + '.oga'}
        if method == 'getChat':
            return {'first_name': 'Suryansh'}
        if method == 'getUpdates':
            if p.get('timeout') == 0:   # Hive skipping what was sent before it started listening
                batch = [lambda f, s=s: [s] for s in self.stale][:1] and [self.stale.pop(0)] if self.stale else []
                return [{'update_id': self._next(), 'message': {'message_id': 1, 'chat': {'id': c}, 'text': t}}
                        for c, t, _, _ in batch]
            if not self.script:   # the owner has nothing more to say: a test still waiting on him is a bug, not a hang
                self.idle = getattr(self, 'idle', 0) + 1
                if self.idle > 200:
                    raise RuntimeError('the scripted owner ran out of replies while Hive was still waiting')
                return []
            batch = self.script.pop(0)(self)
            out = []
            for chat, text, data, reply_to in batch:
                self.uid += 1
                if data:
                    out.append({'update_id': self.uid, 'callback_query': {'id': str(self.uid), 'data': data,
                                'message': {'message_id': reply_to, 'chat': {'id': chat}}}})
                else:
                    m = {'message_id': 1000 + self.uid, 'chat': {'id': chat}}
                    if text.startswith('VOICE:'):   # a voice note: only a file id arrives
                        m['voice'] = {'file_id': text[6:], 'duration': 4}
                    else:
                        m['text'] = text
                    if reply_to:
                        m['reply_to_message'] = {'message_id': reply_to}
                    out.append({'update_id': self.uid, 'message': m})
            return out
        raise AssertionError(method)
    def _next(self):
        self.uid += 1; return self.uid


tap = lambda data: (lambda f: [(ME, None, data, 2)])
say = lambda words: (lambda f: [(ME, words, None, None)])
