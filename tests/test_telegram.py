"""The owner's phone channel with a fake Telegram (no network): questions out, answers and reviews back, strangers ignored.
usage: python3 tests/test_telegram.py   (run from the hive repo root)"""
import json, os, sys, tempfile, time
sys.path.insert(0, os.getcwd())
from hive import owner, telegram

ME, STRANGER = 111, 999
fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))

class FakeTelegram:
    """Records what Hive sends; replies with the owner's scripted taps and messages, one batch per poll."""
    def __init__(self, script):
        self.sent, self.script, self.uid = [], list(script), 0
    def __call__(self, method, **p):
        if method == 'sendMessage':
            self.sent.append(p); return {'message_id': len(self.sent)}
        if method == 'answerCallbackQuery':
            return True
        if method == 'getUpdates':
            if not self.script:
                return []
            batch = self.script.pop(0)(self)
            out = []
            for chat, text, data, reply_to in batch:
                self.uid += 1
                if data:
                    out.append({'update_id': self.uid, 'callback_query': {'id': str(self.uid), 'data': data,
                                'message': {'message_id': reply_to, 'chat': {'id': chat}}}})
                else:
                    m = {'message_id': 1000 + self.uid, 'chat': {'id': chat}, 'text': text}
                    if reply_to:
                        m['reply_to_message'] = {'message_id': reply_to}
                    out.append({'update_id': self.uid, 'message': m})
            return out
        raise AssertionError(method)

def make_run():
    run = tempfile.mkdtemp(); d = owner._dir(run)
    return run, d

def question(d, qid, worker, text):
    json.dump({'id': qid, 'worker': worker, 'question': text, 'asked': int(time.time())},
              open(os.path.join(d, 'questions', qid + '.json'), 'w'))

# 1. a question goes out with letter buttons; the owner's tap becomes the answer; a stranger's message is ignored
run, d = make_run()
question(d, 'q1', 'w2', 'Priya lives in Navi Mumbai and the campaign wants Mumbai. Show her? A) Yes B) No C) something else (please say)')
fake = FakeTelegram([lambda f: [(STRANGER, 'A', None, None)], lambda f: [(ME, None, 'q1|B', 1)]])
ch = telegram.Channel({'chat_id': ME, 'token': 'x'}, api=fake)
telegram.bridge_questions(run, ch, until=lambda: True, poll=0)
check('the question reached the phone', 'Navi Mumbai' in fake.sent[0]['text'], True)
check('it came with letter buttons', [b['text'] for b in fake.sent[0]['reply_markup']['inline_keyboard'][0]], ['A', 'B', 'C'])
a = json.load(open(os.path.join(d, 'answers', 'q1.json')))
check("the owner's tap became the answer, not the stranger's message", (a['answer'], a['via']), ('B', 'telegram'))
check('the owner was thanked', 'Sent to builder w2' in fake.sent[-1]['text'], True)

# 2. a typed reply (not a button) answers the oldest waiting question
run, d = make_run()
question(d, 'q1', 'w1', 'A deal is cut by Rs 500. Must both accept again? A) Yes B) No')
question(d, 'q2', 'w3', 'A typo is fixed in the brief. Must both accept again? A) Yes B) No')
fake = FakeTelegram([lambda f: [(ME, 'Yes, any cut needs both', None, None)], lambda f: [(ME, 'No', None, 2)]])
telegram.bridge_questions(run, telegram.Channel({'chat_id': ME, 'token': 'x'}, api=fake), until=lambda: True, poll=0)
check('a typed reply answers the oldest question', json.load(open(os.path.join(d, 'answers', 'q1.json')))['answer'],
      'Yes, any cut needs both')
check('a reply to a message answers that question', json.load(open(os.path.join(d, 'answers', 'q2.json')))['answer'], 'No')

# 3. the review: only business assumptions go to the phone; Right / Wrong plus the owner's rule
run, d = make_run()
os.environ['HIVE_RUN'] = run; os.environ['HIVE_WORKER'] = 'w1'
owner.assume('If two sources disagree on a total, the total shows as not available.')
time.sleep(0.01)
owner.assume('If the same account is imported twice, its followers are counted twice.')
time.sleep(0.01)
owner.assume('aggregate() throws TypeError on a non-array input.', technical=True)
fake = FakeTelegram([lambda f: [(ME, None, f"{owner._assumptions(d, False)[0]['id']}|ok", 1)],
                     lambda f: [(ME, None, f"{owner._assumptions(d, False)[1]['id']}|no", 2)],
                     lambda f: [(ME, 'Count each account once.', None, None)]])
rows = telegram.review(run, telegram.Channel({'chat_id': ME, 'token': 'x'}, api=fake), poll=0)
check('only the 2 business assumptions went to the phone', sum('Assumption' in m['text'] for m in fake.sent), 2)
check('the technical choice never reached the owner', any('TypeError' in m['text'] for m in fake.sent), False)
check('one kept, one corrected', len(rows), 1)
check("the correction carries the owner's words", 'Count each account once.' in open(os.path.join(d, 'corrections.md')).read(), True)

# 4. not connected: hive behaves as before
os.environ['HIVE_TELEGRAM'] = '0'
check('without a connection, nothing is sent', telegram.load(), None)
sys.exit(fail)
