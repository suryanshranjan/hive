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
    def __init__(self, script, stale=()):
        self.sent, self.script, self.uid, self.stale = [], list(script), 0, list(stale)
    def __call__(self, method, **p):
        if method == 'sendMessage':
            self.sent.append(p); return {'message_id': len(self.sent)}
        if method == 'answerCallbackQuery':
            return True
        if method == 'getChat':
            return {'first_name': 'Suryansh'}
        if method == 'getUpdates':
            if p.get('timeout') == 0:   # Hive skipping what was sent before it started listening
                batch = [lambda f, s=s: [s] for s in self.stale][:1] and [self.stale.pop(0)] if self.stale else []
                return [{'update_id': self._next(), 'message': {'message_id': 1, 'chat': {'id': c}, 'text': t}}
                        for c, t, _, _ in batch]
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
    def _next(self):
        self.uid += 1; return self.uid

def make_run():
    run = tempfile.mkdtemp(); d = owner._dir(run)
    return run, d

def question(d, qid, worker, text):
    json.dump({'id': qid, 'worker': worker, 'question': text, 'asked': int(time.time())},
              open(os.path.join(d, 'questions', qid + '.json'), 'w'))

# 1. a question goes out with letter buttons; the owner's tap becomes the answer; a stranger's message is ignored
run, d = make_run()
question(d, 'q1', 'w2', 'Asha lives just outside the delivery area. Deliver to her? A) Yes B) No C) something else (please say)')
fake = FakeTelegram([lambda f: [(STRANGER, 'A', None, None)], lambda f: [(ME, None, 'q1|B', 1)]])
ch = telegram.Channel({'chat_id': ME, 'token': 'x'}, api=fake)
telegram.bridge_questions(run, ch, until=lambda: True, poll=1)
check('the question reached the phone', 'delivery area' in fake.sent[0]['text'], True)
check('it came with letter buttons', [b['text'] for b in fake.sent[0]['reply_markup']['inline_keyboard'][0]], ['A', 'B', 'C'])
a = json.load(open(os.path.join(d, 'answers', 'q1.json')))
check("the owner's tap became the answer, not the stranger's message", (a['answer'], a['via']), ('B', 'telegram'))
check('the owner was thanked', fake.sent[-1]['text'] == 'Thank you. Passing it on.', True)

# 2. a typed reply (not a button) answers the oldest waiting question
run, d = make_run()
question(d, 'q1', 'w1', 'A deal is cut by Rs 500. Must both accept again? A) Yes B) No')
question(d, 'q2', 'w3', 'A typo is fixed in the brief. Must both accept again? A) Yes B) No')
fake = FakeTelegram([lambda f: [(ME, 'Yes, any cut needs both', None, None)], lambda f: [(ME, 'No', None, 2)]])
telegram.bridge_questions(run, telegram.Channel({'chat_id': ME, 'token': 'x'}, api=fake), until=lambda: True, poll=1)
check('a typed reply answers the oldest question', json.load(open(os.path.join(d, 'answers', 'q1.json')))['answer'],
      'Yes, any cut needs both')
check('a reply to a message answers that question', json.load(open(os.path.join(d, 'answers', 'q2.json')))['answer'], 'No')

# 3. the review: a greeting by name; business assumptions in plain words, most important first; the one an owner cannot
#    judge set aside unless asked; an old "hi" from before is not taken as an answer
from hive import explain
explain.CMD = '"' + sys.executable.replace('\\', '/') + '" tests/fake_explain.py'   # shlex would eat Windows backslashes
run, d = make_run()
os.environ['HIVE_RUN'] = run; os.environ['HIVE_WORKER'] = 'w1'
owner.assume('If two sources disagree on a total, the total shows as not available.')
time.sleep(0.01)
owner.assume('If the same order is imported twice, it is counted twice.')
time.sleep(0.01)
owner.assume('If a customer has no postcode, their order shows as not available.')
time.sleep(0.01)
owner.assume('aggregate() throws TypeError on a non-array input.', technical=True)
ids = [a['id'] for a in owner._assumptions(d, False)]
# the owner: takes the suggestion on #1, then undoes it and keeps #1 as built; on #2 says "something else" in his own
# words; leaves the smaller one; at the final check undoes #2 and answers it again in his own words; then sends.
tap = lambda data: (lambda f: [(ME, None, data, 2)])
say = lambda words: (lambda f: [(ME, words, None, None)])
fake = FakeTelegram([tap(f'{ids[0]}|show'), tap(f'{ids[0]}|o1'), tap(f'{ids[1]}|undo'), tap(f'{ids[0]}|ok'),
                     tap(f'{ids[1]}|no'), say('Show it per customer instead.'), tap('aside|leave'),
                     tap('final|undo'), tap(f'{ids[1]}|no'), say('Count each order once.'), tap('final|send')],
                    stale=[(ME, 'hi', None, None)])
rows = telegram.review(run, telegram.Channel({'chat_id': ME, 'token': 'x'}, api=fake), goal='# Goal: combine metrics',
                       check='419 tests, all passing.', poll=1)
check('it greets the owner by name and says what was built',
      'Good morning, Suryansh. While you were away, the builders finished this: A report that adds up daily shop orders.'
      in fake.sent[0]['text'], True)
check('the greeting says how things stand and that a tap is enough',
      ('419 tests, all passing.' in fake.sent[0]['text'], 'a tap is enough' in fake.sent[0]['text']), (True, True))
decisions = [m for m in fake.sent if m.get('reply_markup') and 'Keep it' in str(m['reply_markup'])]
check('each decision is in plain words with an example',
      all('In the shop report' in m['text'] and 'Asha' in m['text'] for m in decisions), True)
menu = [m for m in decisions if 'Other ways to do it:' in m['text']]
check("a high-stakes decision is asked openly first; options only on request",
      ('What should happen here?' in decisions[0]['text'], 'Other ways' in decisions[0]['text'],
       'Show me some options' in str(decisions[0]['reply_markup'])), (True, False, True))
check("the options offer real alternatives, each one tap, with Hive's pick starred",
      ('★ Count once' in str(menu[0]['reply_markup']), 'Count every time' in str(menu[0]['reply_markup']),
       "I'd go with" in menu[0]['text']), (True, True, True))
second = [m for m in decisions if m['text'].startswith('2 of 2')]
check('the first decision has no undo; later ones do',
      ('Undo' in str(decisions[0]['reply_markup']), 'Undo' in str(second[0]['reply_markup'])), (False, True))
check('undo took the suggestion back: #1 ended as kept', json.load(open(os.path.join(d, 'reviews', ids[0] + '.json')))['ok'], True)
check('a final check came before anything was sent', any('Send it' in str(m.get('reply_markup')) for m in fake.sent), True)
check('the final undo let the owner change #2', json.load(open(os.path.join(d, 'reviews', ids[1] + '.json')))['correction'],
      'Count each order once.')
check('the one an owner cannot judge was offered, not pushed', any('minor one' in m['text'] for m in fake.sent), True)
check('the technical choice never reached the owner', any('TypeError' in m['text'] for m in fake.sent), False)
check('the old "hi" did not count as an answer', sum('hi' == m.get('text') for m in fake.sent), 0)
check('one change goes to the builders', len(rows), 1)
text = open(os.path.join(d, 'corrections.md')).read()
check("the change carries the owner's final words and what the owner saw",
      ('Count each order once.' in text, 'Show it per customer' in text, 'The owner saw it as: In the shop report' in text),
      (True, False, True))
check('the reply sounds like an assistant on it', fake.sent[-1]['text'].startswith('Right away.'), True)

# 4. the owner chose how to be addressed ("sir"): every greeting uses it
run, d = make_run()
question(d, 'q9', 'w1', 'A deal is cut by Rs 500. Must both accept again? A) Yes B) No')
fake = FakeTelegram([tap('q9|A')])
telegram.bridge_questions(run, telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake),
                          until=lambda: True, poll=1)
check('a question opens with the chosen address', fake.sent[0]['text'].startswith('Sir, a quick one from the builders'), True)

# 5. "status?" at any time: answered on the spot, without being taken as an answer
import subprocess
run = tempfile.mkdtemp(); owner._dir(run); os.makedirs(os.path.join(run, 'out'))
repo = os.path.join(run, 'repo'); subprocess.run(['git', 'init', '-q', '-b', 'main', repo])
subprocess.run(['git', '-C', repo, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'base'])
subprocess.run(['git', 'clone', '-q', '--bare', repo, os.path.join(run, 'up.git')])
for k in (1, 2):
    subprocess.run(['git', '-C', repo, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', f'work {k}'])
subprocess.run(['git', '-C', repo, 'push', '-q', os.path.join(run, 'up.git'), 'main'])
subprocess.run(['git', '-C', repo, 'reset', '-q', '--hard', 'HEAD~2'])
json.dump({'repo': repo, 'branch': 'main', 'workers': 4, 'started': int(time.time()) - 125}, open(os.path.join(run, 'run.json'), 'w'))
open(os.path.join(run, 'out', 'w1.json'), 'w').write('{}')
question(owner._dir(run), 'q7', 'w2', 'A typo is fixed. Must both accept again? A) Yes B) No')
fake = FakeTelegram([say("How's it going?"), tap('q7|B')])
telegram.bridge_questions(run, telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake),
                          until=lambda: True, poll=1)
reply = [m['text'] for m in fake.sent if m['text'].startswith('Sir. The builders')]
check('during a build, "how\'s it going" gets a plain progress report',
      reply[:1] == ['Sir. The builders are 2 minutes in. 1 of 4 have finished, and 2 pieces of work have landed so far, '
                    'each one passing every test. 1 question for you is waiting above.'], True)
check('and is not taken as the answer', json.load(open(os.path.join(run, 'owner', 'answers', 'q7.json')))['answer'], 'B')

run, d = make_run(); os.environ['HIVE_RUN'] = run
owner.assume('If two sources disagree on a total, the total shows as not available.'); time.sleep(0.01)
owner.assume('If a platform name differs only by capital letters, it counts as the same platform.')
ids = [a['id'] for a in owner._assumptions(d, False)]
fake = FakeTelegram([say('status'), tap(f'{ids[0]}|ok'), tap('aside|leave'), tap('final|send')])
telegram.review(run, telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake), goal='combine metrics', poll=1)
check('during a review, "status" says where we are',
      any(m['text'].startswith("Sir. We're on decision 1 of 1") for m in fake.sent), True)
check('and the decision still waits for a real answer', json.load(open(os.path.join(d, 'reviews', ids[0] + '.json')))['ok'], True)

# 6. two answers contradict each other: before sending, Hive asks which should win, and that ruling goes to the builders
run, d = make_run(); os.environ['HIVE_RUN'] = run
owner.assume('If one order is missing a price, the whole day total shows as not available.'); time.sleep(0.01)
owner.assume('If two sources disagree, the total shows as not available.'); time.sleep(0.01)
owner.assume('If a platform name differs only by capital letters, it counts as the same platform.')
ids = [a['id'] for a in owner._assumptions(d, False)]
fake = FakeTelegram([tap(f'{ids[0]}|ok'), tap(f'{ids[1]}|no'), say('Add up the others. CONFLICT-ME'),
                     tap('aside|leave'), tap('conf|0|b'), tap('final|send')])
rows = telegram.review(run, telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake),
                       goal='combine metrics', poll=1)
check('the contradiction is put to the owner before sending',
      any('two of your answers pull in different directions' in m['text'] for m in fake.sent), True)
text = open(os.path.join(d, 'corrections.md')).read()
check("the owner's ruling on it reaches the builders and overrides", ('Total from the others' in text, 'overrides' in text),
      (True, True))

# 7. disagreeing with Hive costs one tap too, and is recorded as the owner's own call
run, d = make_run(); os.environ['HIVE_RUN'] = run
owner.assume('If the same order is imported twice, it is counted twice.'); time.sleep(0.01)
owner.assume('If a platform name differs only by capital letters, it counts as the same platform.')
ids = [a['id'] for a in owner._assumptions(d, False)]
fake = FakeTelegram([tap(f'{ids[0]}|show'), tap(f'{ids[0]}|o2'), tap('aside|leave'), tap('final|send')])
telegram.review(run, telegram.Channel({'chat_id': ME, 'token': 'x'}, api=fake), goal='combine metrics', poll=1)
r = json.load(open(os.path.join(d, 'reviews', ids[0] + '.json')))
check("picking the option Hive did not recommend is one tap, recorded as the owner's own call",
      (r['correction'], r['followed_suggestion']), ('count it every time it appears', False))
check('the stored wording is the decision itself, not the "1 of 1" header', r['shown_as'].startswith('In the shop report'), True)

# 7b. asked openly, the owner answers in his own words (no menu shown); a new answer that contradicts a ruling he gave on
#     an earlier build is caught before sending
run, d = make_run(); os.environ['HIVE_RUN'] = run
owner.assume('If the same order is imported twice, it is counted twice.'); time.sleep(0.01)
owner.assume('If a platform name differs only by capital letters, it counts as the same platform.')
ids = [a['id'] for a in owner._assumptions(d, False)]
fake = FakeTelegram([say('Merge them, and tell the shop. CONFLICT-ME'), tap('aside|leave'), tap('conf|0|a'), tap('final|send')])
telegram.review(run, telegram.Channel({'chat_id': ME, 'token': 'x'}, api=fake), goal='combine metrics', poll=1,
                rulings=['Duplicates are always kept apart.'])
r = json.load(open(os.path.join(d, 'reviews', ids[0] + '.json')))
check("asked openly, the owner's own words become the rule, with no menu shown",
      (r['correction'], r.get('asked_open'), any('Other ways' in m['text'] for m in fake.sent)),
      ('Merge them, and tell the shop. CONFLICT-ME', True, False))
check('a new answer that contradicts an earlier ruling is put to the owner',
      any('two of your answers pull in different directions' in m['text'] for m in fake.sent), True)

# 7c. many decisions: all listed one line each; the owner marks the ones he'd change; only those are asked in full
run, d = make_run(); os.environ['HIVE_RUN'] = run
for k in range(10):
    owner.assume(f'Rule number {k} of the shop works the obvious way.'); time.sleep(0.01)
ids = [a['id'] for a in owner._assumptions(d, False)]
fake = FakeTelegram([tap('tri|3'), tap('tri|3'), say('2 and 5'), tap('tri|next'), tap('tri|next'),
                     say('Do it my way'), tap(f'{ids[4]}|ok'), tap('final|send')])
rows = telegram.review(run, telegram.Channel({'chat_id': ME, 'token': 'x'}, api=fake), goal='combine metrics', poll=1)
pages = [m for m in fake.sent if m['text'].startswith('Page ')]
check('every decision is listed, one line each, across pages', (len(pages), '9. Rule number 8' in pages[1]['text']), (2, True))
full = [m for m in fake.sent if 'What should happen here?' in m['text']]
check('only the marked ones (2 and 5) are asked in full, openly first', len(full), 2)
check("the owner's words on #2 become the rule; #5 kept; the rest left as built",
      (json.load(open(os.path.join(d, 'reviews', ids[1] + '.json')))['correction'],
       json.load(open(os.path.join(d, 'reviews', ids[4] + '.json')))['ok'],
       sum(bool(json.load(open(os.path.join(d, 'reviews', i + '.json'))).get('auto')) for i in ids)), ('Do it my way', True, 8))
check('one change goes to the builders', len(rows), 1)

# 8. an open question gathers every reply until Done; situations get one-tap verdicts, with undo and own words
fake = FakeTelegram([tap('collect|done'), tap('collect|more'),   # an accidental early Done, taken back
                     say('- they treat goods like cash\n- they promise dates'), say("status"), say('they skip the brief'),
                     tap('collect|done')])
lines = telegram.collect(telegram.Channel({'chat_id': ME, 'token': 'x'}, api=fake), 'What do new people get wrong?', poll=1)
check('an open question gathers every point until Done, ignoring a status request',
      lines, ['they treat goods like cash', 'they promise dates', 'they skip the brief'])
cases = [{'id': 's1', 'situation': 'A box arrives damaged.', 'options': ['Full refund', 'Replace it']},
         {'id': 's2', 'situation': 'A code expired yesterday.', 'options': ['Refuse it', 'Accept it']}]
fake = FakeTelegram([tap('s1|0'), tap('s2|undo'), tap('s1|1'), say('Accept it, once, with a note')])
got = telegram.verdicts(telegram.Channel({'chat_id': ME, 'token': 'x'}, api=fake), cases, poll=1)
check('verdicts: a tap, an undo, then the owner\'s own words', got, {'s1': 'Replace it', 's2': 'Accept it, once, with a note'})

# 9. not connected: hive behaves as before
os.environ['HIVE_TELEGRAM'] = '0'
check('without a connection, nothing is sent', telegram.load(), None)
sys.exit(fail)
