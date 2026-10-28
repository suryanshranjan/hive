"""hive listen with a fake Telegram and a stand-in model (no network, no tokens): the owner changes his mind any time;
Hive finds the ruling it overrides, confirms, updates the kept rulings and offers to update the latest build.
usage: python3 tests/test_assistant.py   (run from the hive repo root)"""
import json, os, subprocess, sys, tempfile, time
sys.path.insert(0, os.getcwd())
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home   # Windows: USERPROFILE
from hive import assistant, explain, memory, telegram
explain.CMD = '"' + sys.executable.replace(chr(92), '/') + '" tests/fake_explain.py'
memory.DIR = os.path.join(home, '.hive', 'rules')
assistant.RUNS = os.path.join(home, '.hive', 'runs')
telegram.BUSY = os.path.join(home, '.hive', 'telegram.busy')
os.makedirs(os.path.join(home, '.hive'), exist_ok=True)
sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
from test_telegram_fake import FakeTelegram, ME, tap, say

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))

repo = os.path.join(home, 'project'); subprocess.run(['git', 'init', '-q', '-b', 'main', repo])
subprocess.run(['git', '-C', repo, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'init'])
memory.add(repo, 'A late post is paid in full.'); memory.add(repo, 'Followers are counted once per account.')
ch = lambda fake: telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake)

# 1. a change of mind: the earlier ruling is found, confirmed and replaced; with no build yet, it waits for the next one
fake = FakeTelegram([tap('chg|replace')])
r = assistant.handle(ch(fake), repo, 'Actually, I changed my mind: a late post loses 2% per day', poll=1)
texts = [x['text'] for x in fake.sent]
check('it quotes the earlier ruling it would replace', any('Earlier you ruled:\n- A late post is paid in full.' in t for t in texts), True)
check('the earlier ruling is replaced by the new one', [x['text'] for x in memory.load(repo)],
      ['Followers are counted once per account.', 'a late post loses 2% per day'])
check('with no build yet, it says the next build will follow it', (r, texts[-1]), ('kept', '✅ Very good. The builders will follow it from the next build.'))

# 2. with a build on record, it offers to update that build, and does so on Yes
runs = os.path.join(home, '.hive', 'runs', 'b1'); os.makedirs(runs)
json.dump({'repo': repo, 'name': 'b1', 'check': '12 tests, all passing.', 'home': runs}, open(os.path.join(runs, 'state.json'), 'w'))
applied = []
fake = FakeTelegram([tap('chg|both'), tap('upd|yes')])
r = assistant.handle(ch(fake), repo, 'Actually, I changed my mind: a late post loses 5% per day', poll=1,
                     apply_build=lambda st, rule, c: applied.append((st['name'], rule)))
check('it offers to update the latest build and does it on Yes', (r, applied), ('applied', [('b1', 'a late post loses 5% per day')]))
check('"keep both" keeps the earlier ruling too', len(memory.load(repo)), 3)

# 3. a hello, a status request, and a new rule
fake = FakeTelegram([])
check('waking it up gets a greeting', (assistant.handle(ch(fake), repo, 'hi', poll=1), fake.sent[-1]['text'].startswith('🐝 At your service, Sir')),
      ('greeting', True))
fake = FakeTelegram([])
assistant.handle(ch(fake), repo, 'status?', poll=1)
check('status reports the latest build', fake.sent[-1]['text'], '📊 The latest build is on branch hive/b1. 12 tests, all passing.')
fake = FakeTelegram([])
r = assistant.handle(ch(fake), repo, 'I have already told you', poll=1)
check('a complaint is answered, never saved as a rule (the live test saved "I have already told you")',
      (r, 'I have already told you' in [x['text'] for x in memory.load(repo)]), ('chat', False))

# 3a2. the live conversation, done right: a correction while Hive asks, then "yes", read in context
started = []
c = ch(FakeTelegram([say('a page saying Sunny Shop Creators'), say('yes')]))
r = assistant.handle(c, repo, 'build: a page with suny shop creators on it', poll=1,
                     start_build=lambda rp, goal: started.append(goal))
check('a correction while Hive asks changes what it builds; "yes" then starts it (no "Just say the word")',
      (r, started), ('built', ['a page saying Sunny Shop Creators']))

# 3a3. a build runs in the background: "status" says it is running, and if it stops, he is told why at once
# (the live cloud build stopped on "unsaved changes" and only the server's log knew)
os.environ['HIVE_BUILD_CMD'] = 'sh -c "sleep 2; echo You have unsaved changes. Commit or stash them first.; exit 3"'
fake = FakeTelegram([])
assistant.background_build(repo, 'a page saying Sunny Shop Creators', ch(fake))
assistant.handle(ch(fake), repo, 'status', poll=1)
running = fake.sent[-1]['text']
time.sleep(4)
check('while it builds, status says a build is running; when it stops, he is told why',
      ('build is running' in running, any('The build stopped' in m['text'] and 'unsaved changes' in m['text'] for m in fake.sent)),
      (True, True))
del os.environ['HIVE_BUILD_CMD']; assistant.BUILD.clear()

# 3b. "build: ..." from the phone starts a build after one confirmation
started = []
fake = FakeTelegram([tap('bld|yes')])
r = assistant.handle(ch(fake), repo, 'build: a refund page for brands', poll=1, start_build=lambda rp, goal: started.append(goal))
check('"build: ..." asks once, then starts the build with that goal', (r, started), ('built', ['a refund page for brands']))

# 3b2. "move to the cloud" from the phone: one tap to confirm, then the machine is made and Hive moves; "delete the
# cloud machine" removes it; "not now" changes nothing
moves = []
fake = FakeTelegram([tap('cld|yes')])
r = assistant.handle(ch(fake), repo, 'Please move to the cloud, my laptop is going off', poll=1,
                     cloud=lambda rp, on: moves.append(on) or 0)
check('"move to the cloud" asks once, then moves (and the local listener stops)', (r, moves), ('moved', [True]))
fake = FakeTelegram([tap('cld|no')])
r = assistant.handle(ch(fake), repo, 'delete the cloud machine', poll=1, cloud=lambda rp, on: moves.append(on) or 0)
check('"not now" leaves the cloud machine alone', (r, moves), ('not_moved', [True]))
fake = FakeTelegram([tap('cld|yes')])
r = assistant.handle(ch(fake), repo, 'delete the cloud machine', poll=1, cloud=lambda rp, on: 5)
check('the cloud copy says it cannot delete itself, and how to (no AWS keys there)',
      (r, 'hive cloud --stop' in fake.sent[-1]['text']), ('cloud_elsewhere', True))

# 3c. the interview on the phone: a tap, his own words, his confirmation of the reading -> rules for the builders
from hive import interview
fake = FakeTelegram([tap('q01|0'), say('Only after a week'), tap('q02|0')])
rules = interview.interview('Fees and tips for a shop', ch(fake), poll=1)
check('the interview turns a tap and confirmed own words into rules',
      rules, ['Asha tips a creator Rs 500 after a great post. -> No fee on a tip', 'A late fee is charged only after 7 days.'])
check("his rules go into the builders' instructions as tests to encode", 'Encode every one' in interview.instructions(rules), True)

# 3d. a voice note: transcribed on this machine, shown back to the owner, and used as his answer
from hive import voice
voice.available = lambda: True
voice.transcribe = lambda path: 'Only after a week, and tell the brand first'
telegram.Channel.fetch = lambda self, file_path, local: open(local, 'wb').write(b'OggS')
fake = FakeTelegram([tap('q01|0'), say('VOICE:note1'), tap('q02|0')])
rules = interview.interview('Fees and tips for a shop', ch(fake), poll=1)
check('a spoken answer is transcribed, shown back, and taken as his own words',
      (any(m['text'] == '🎙 I heard: "Only after a week, and tell the brand first"' for m in fake.sent), len(rules)), (True, 2))
voice.available = lambda: False
fake = FakeTelegram([say('VOICE:note2'), say('Typed instead')])
texts = telegram._wait(ch(fake), 1, set())
check('without Whisper installed, it asks him to type, and takes the typed answer',
      (any('pip install faster-whisper' in m['text'] for m in fake.sent), texts), (True, ('text', 'Typed instead')))

# 3e. stopped partway (a lost process, a usage limit): a rerun picks up at the first unanswered one, nothing asked twice
class Stop(Exception): pass
def stop(fake): raise Stop()
save = os.path.join(home, 'iv')
qs = [{'id': f'q{k}', 'situation': f'Situation {k}.', 'options': ['Yes', 'No']} for k in (1, 2, 3)]
fake = FakeTelegram([tap('q1|0'), stop])
try:
    interview.interview('Fees', ch(fake), situations=qs, poll=1, save=save)
except Stop:
    pass
fake = FakeTelegram([tap('q1|1'), tap('q2|1'), tap('q3|0')])   # the old button first: answered, then the real ones
rules = interview.interview('Fees', ch(fake), situations=qs, poll=1, save=save)
texts = [m['text'] for m in fake.sent]
check('after a stop, it picks up at the first unanswered question',
      (any('Picking up where we left off: 1 of 3 answered' in t for t in texts), any('1 of 3' in t and 'Situation 1' in t for t in texts)),
      (True, False))
check('a tap on an earlier message is answered, not dropped in silence',
      any('That button is from an earlier message' in t for t in texts), True)
check('the answers from before the stop are kept', rules, ['Situation 1. -> Yes', 'Situation 2. -> No', 'Situation 3. -> Yes'])

# 3f. his own words on a reading: a yes in any words keeps it; "whatever you feel like" is no rule; a correction keeps
# the situation it is about (Gate 36: "It's exactly that's the thing I want" itself became a rule)
qs = [{'id': f'r{k}', 'situation': f'Case {k}.', 'options': ['Yes', 'No']} for k in (1, 2, 3)]
fake = FakeTelegram([say('Only after a week'), say('whatever you feel like'), say('Refund it'),
                     say("It's exactly that's the thing I want."), say('Shut the campaign off')])
rules = interview.interview('Fees', ch(fake), situations=qs, poll=1)
check('a yes in his own words keeps the reading; "whatever" leaves it to the builders; a correction keeps its situation',
      rules, ['A late fee is charged only after 7 days.', 'Case 3. -> Shut the campaign off'])

# 3g. an interview answer that contradicts an earlier ruling: he is asked which holds now, and his choice goes in
fake = FakeTelegram([tap('q01|1'), tap('q02|0'), tap('set|0|1')])
rules = interview.interview('Fees', ch(fake), rulings=['CONFLICT-ME: a tip carries no fee'], poll=1)
check('a contradiction with an earlier ruling is put to him, and his choice settles it',
      (any('pulls against an earlier ruling' in m['text'] for m in fake.sent), rules[-1].endswith('-> Total from the others')),
      (True, True))

# 3h. the interview asks about what the code must decide: the builders' decisions, with their defaults, steer the questions
seen, _ask_json = [], explain.ask_json
explain.ask_json = lambda prompt: (seen.append(prompt), _ask_json(prompt))[1]
qs = interview.write_situations('Fees and tips for a shop')
explain.ask_json = _ask_json
check("the questions are written from the build's own decisions and their defaults",
      (len(qs), any("A tip is paid (builders' outcome: the usual fee)" in p for p in seen)), (2, True))

# 3i. no redundant questions (Gate 37: the founder found the interview repetitive): two questions on the same decision
# become one, and an answer in his own words that already settles a later question skips it
_ask_json = explain.ask_json
explain.ask_json = lambda prompt: {'same': [[1, 3]]} if 'ask about the same decision' in prompt else _ask_json(prompt)
qs3 = [{'id': f'q{k:02d}', 'situation': s, 'options': ['A', 'B']}
       for k, s in enumerate(['Draft unreviewed for 3 days.', 'A late fee.', 'Draft unreviewed for 7 days.'], 1)]
check('two questions about the same decision become one', [q['situation'] for q in interview._dedupe(qs3)],
      ['Draft unreviewed for 3 days.', 'A late fee.'])
explain.ask_json = lambda prompt: ({'settled': [1]} if 'already decide' in prompt else _ask_json(prompt))
qs = [{'id': f't{k}', 'situation': f'Topic {k}.', 'options': ['Yes', 'No']} for k in (1, 2, 3)]
fake = FakeTelegram([say('Remind them after 3 days, cancel after 7'), tap('t3|0'), say("It's exactly that")])
rules = interview.interview('Fees', ch(fake), situations=qs, poll=1)
explain.ask_json = _ask_json
asked = [m['text'] for m in fake.sent if m['text'].startswith('📋') and 'Topic' in m['text']]
check('an answer that settles the next question skips it, and says so',
      (len(asked), any('Topic 2' in t for t in asked), any('also settles 1 of the coming' in m['text'] for m in fake.sent), rules),
      (2, False, True, ['Topic 3. -> Yes', 'A late fee is charged only after 7 days.']))

explain.ask_json = lambda prompt: ({'settled': [1]} if 'already decide' in prompt and 'Topic 1.' in prompt.split('still to come')[0]
                                   else {'settled': []} if 'already decide' in prompt else _ask_json(prompt))
fake = FakeTelegram([tap('t1|0'), tap('t3|1')])
rules = interview.interview('Fees', ch(fake), situations=qs, poll=1, sheet=False)
explain.ask_json = _ask_json
check('a tapped answer that settles a later question skips it too',
      (any('Topic 2' in m['text'] for m in fake.sent if m['text'].startswith('📋')), rules), (False, ['Topic 1. -> Yes', 'Topic 3. -> No']))

# 3j. the rule sheet: his answers become one general rule per decision; two answers that disagree are put to him; he
# marks the wrong rule and says it in his own words (Gate 37: answers to two framings agreed 1 of 8)
_ask_json = explain.ask_json
explain.ask_json = lambda prompt: ({'rules': [{'rule': 'Whenever a tip is paid, no fee is charged.', 'from': [1]},
                                              {'rule': 'Whenever a fee is late, the brand is reminded.', 'from': [2]}],
                                    'disagree': [{'from': [1, 2], 'question': 'Is a late tip charged a fee?',
                                                  'option_a': 'No fee', 'option_b': 'The late fee'}]}
                                   if 'Turn them into his policy' in prompt else _ask_json(prompt))
qs = [{'id': f'w{k}', 'situation': f'Case {k}.', 'options': ['Yes', 'No']} for k in (1, 2)]
fake = FakeTelegram([tap('w1|0'), tap('w2|1'), tap('dis|0|0'), tap('sheet|2'), tap('sheet|done'), say('Only after a week')])
rules = interview.interview('Fees', ch(fake), situations=qs, poll=1)
explain.ask_json = _ask_json
check('the rule sheet: general rules, a disagreement settled by him, a wrong rule rewritten in his words',
      (rules, any('Your rules for this feature' in m['text'] for m in fake.sent)),
      (['Whenever a tip is paid, no fee is charged.', 'A late fee is charged only after 7 days.',
        'Is a late tip charged a fee? -> No fee'], True))

# 3k. the hand-over: he sees what it does now by his rules; what he changes goes to a fix round; then his yes
from hive import start
fixed = []
_apply, start.apply_ruling = start.apply_ruling, lambda st, rule, c=None: fixed.append(rule)
fake = FakeTelegram([tap('hand|change'), say('Tips are never charged a fee'), tap('hand|ok')])
start.handover({'repo': repo, 'asked': ['Whenever a tip is paid, the usual fee applies.']}, ch(fake), poll=1)
start.apply_ruling = _apply
check('the hand-over shows his rules, sends a change to a fix round, and ends on his yes',
      (any('What it does now, by your rules' in m['text'] for m in fake.sent), fixed, fake.sent[-1]['text']),
      (True, ['Tips are never charged a fee'], '🎉 Very good. It is yours.'))

# 3l. "what does it mean?" is a question, not his answer (Gate 38): Hive reasons about the reply, explains the question
# in plain words, and asks again; a real answer in his own words still counts
_ask_json = explain.ask_json
explain.ask_json = lambda prompt: ({'kind': 'question', 'explanation': 'A review is the stars a brand and a creator give '
                                    'each other after a deal.'} if 'What does it mean' in prompt and 'Think about what he means' in prompt
                                   else {'kind': 'answer'} if 'Think about what he means' in prompt else _ask_json(prompt))
qs = [{'id': 'v1', 'situation': 'How long can a review be left?', 'options': ['7 days', '14 days']}]
fake = FakeTelegram([say('What does it mean'), tap('v1|1')])
rules = interview.interview('Ratings and reviews', ch(fake), situations=qs, poll=1, sheet=False)
explain.ask_json = _ask_json
check('a question about the question is explained, not taken as his rule',
      (any(m['text'].startswith('💡 A review is the stars') for m in fake.sent), rules),
      (True, ['How long can a review be left? -> 14 days']))
explain.ask_json = lambda prompt: ({'kind': 'answer', 'choice': 2} if 'Think about what he means' in prompt
                                   else _ask_json(prompt))
fake = FakeTelegram([say('the longer one')])
rules = interview.interview('Ratings and reviews', ch(fake), situations=qs, poll=1, sheet=False)
explain.ask_json = _ask_json
check('a choice picked in his own words counts as that choice', rules, ['How long can a review be left? -> 14 days'])
fake = FakeTelegram([say("What is review i font understand"), tap('v1|0')])   # no model reachable: the phrase list
rules = interview.interview('Ratings and reviews', ch(fake), situations=qs, poll=1, sheet=False)
check('without a model, the phrase list still catches it', rules, ['How long can a review be left? -> 7 days'])

# 3m. the listener never goes silent: an old tap Telegram refuses to acknowledge, and a message that fails, are survived
class OldTap(FakeTelegram):
    def __call__(self, method, **p):
        if method == 'answerCallbackQuery':
            raise RuntimeError('Telegram answerCallbackQuery: Bad Request: query is too old')
        return super().__call__(method, **p)
fake = OldTap([tap('cld|yes'), say('hi'), say('status')])
calls = iter([RuntimeError('boom'), None, None])
_handle = assistant.handle
def flaky_handle(*a, **k):
    e = next(calls)
    if e:
        raise e
    return _handle(*a, **k)
assistant.handle = flaky_handle
assistant.listen(repo, poll=1, until=lambda: not fake.script, ch=telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake, listener=True))
assistant.handle = _handle
texts = [m['text'] for m in fake.sent]
check('an old tap and a failing message do not stop the listener; it says sorry and answers the next',
      (any('something went wrong' in t for t in texts), any('The latest build' in t for t in texts)), (True, True))

# 3n. like Jarvis with Tony: messages that came together are read together, repeats are answered once with an apology,
# and a bare "hi" next to a real request gets no reply of its own; replies are in Hive's own voice, from real facts only
check('repeats are answered once, and a bare hi beside a request is folded in',
      assistant.coalesce(['Status', 'Hi', 'Status', 'status?', 'Hi']), (['Status'], True))
check('a lone hi is still answered', assistant.coalesce(['hi']), (['hi'], False))
_ask_json = explain.ask_json
seen = []
explain.ask_json = lambda prompt: (seen.append(prompt) or {'reply': 'All quiet on the build front, sir.'}
                                   if 'J.A.R.V.I.S.' in prompt else _ask_json(prompt))
fake = FakeTelegram([])
assistant.handle(ch(fake), repo, 'status?', poll=1)
explain.ask_json = _ask_json
check("status is said in Hive's own voice, from the project's real facts",
      (fake.sent[-1]['text'], 'Latest build: branch hive/b1' in seen[0]), ('🐝 All quiet on the build front, sir.', True))

# 3o. the conversation survives a restart: the real chat keeps its thread on disk (and moves with Hive)
c1 = telegram.Channel({'chat_id': ME, 'token': 'x'})
c1.remember('owner', 'build: a page for creators'); c1.remember('hive', 'Shall I build this?')
c2 = telegram.Channel({'chat_id': ME, 'token': 'x'})   # a new process: the listener restarted, or Hive moved
check('the conversation survives a restart', c2.history[-2:], [('owner', 'build: a page for creators'), ('hive', 'Shall I build this?')])
check('only for the real chat (test fakes never touch it)', ch(FakeTelegram([])).history, [])

# 4. the listener steps aside while a build or review is talking to the owner
json.dump({'pid': os.getppid(), 'at': time.time()}, open(telegram.BUSY, 'w'))
check('another live process talking: the listener steps aside', telegram.busy_elsewhere(), True)
json.dump({'pid': os.getppid(), 'at': time.time() - 600}, open(telegram.BUSY, 'w'))
check('a stale claim is ignored', telegram.busy_elsewhere(), False)
json.dump({'pid': os.getpid(), 'at': time.time()}, open(telegram.BUSY, 'w'))
check("its own claim doesn't block it", telegram.busy_elsewhere(), False)
sys.exit(fail)
