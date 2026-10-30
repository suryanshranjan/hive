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

# 3a2b. "build again" after a failed build is read in context, never as a request to build "again" (the live test)
started = []
c = ch(FakeTelegram([tap('bld|yes')]))   # it restates the earlier request and asks once
c.remember('owner', 'build: a page showing creators their earnings'); c.remember('hive', 'The build stopped before it finished.')
r = assistant.handle(c, repo, 'Build again', poll=1, start_build=lambda rp, goal: started.append(goal))
check('"build again" builds the earlier request, not "again"', (r, started), ('built', ['a page showing creators their earnings']))

# 3a3. a build runs in the background: "status" says it is running, and if it stops, he is told why at once
# (the live cloud build stopped on "unsaved changes" and only the server's log knew)
os.environ['HIVE_BUILD_CMD'] = 'sh -c "sleep 2; echo You have unsaved changes. Commit or stash them first.; exit 3"'
fake = FakeTelegram([])
assistant.background_build(repo, 'a page saying Sunny Shop Creators', ch(fake))
assistant.handle(ch(fake), repo, 'status', poll=1)
running = fake.sent[-1]['text']
time.sleep(4)
check('while it builds, status says a build is running; when it stops, he is told why',
      ('build is running' in running, any('The build stopped' in m['text'] and "edits that aren't saved" in m['text'] for m in fake.sent)),
      (True, True))
del os.environ['HIVE_BUILD_CMD']; assistant.BUILD.clear()

# 3a4. stopping a build: said plainly, it stops at once; only read as a stop (Gate 48: a fast reader called "stop" for
# 22 messages, 9 of which meant it), it asks first, and "keep going" keeps the build
check('plain stop requests are recognised', [assistant.is_stop_request(t) for t in
      ('stop the build', 'ruko ruko build band karo', 'cancel it I changed my mind', 'stop', 'halt the build, wrong feature')],
      [True] * 5)
check('messages that only mention stopping are not', [assistant.is_stop_request(t) for t in
      ('stop sending me so many messages', 'stop charging late fees after 7 days', "you're slow today", 'thanks')], [False] * 4)
_ask_json = explain.ask_json
explain.ask_json = lambda prompt: {'intent': 'stop_build'} if 'newest message' in prompt else _ask_json(prompt)
for said, answer, how, want in (('this is all wrong, forget it', tap('stp|no'), 'a tap on "Keep going"', 'kept_building'),
                                ('this is all wrong, forget it', say('yes stop it'), '"yes stop it"', 'stopped'),
                                ('stop the build', None, 'nothing asked', 'stopped')):
    p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
    assistant.BUILD.update(proc=p, goal='a refund page for brands', started=time.time())
    fake = FakeTelegram([answer] if answer else [])
    r = assistant.handle(ch(fake), repo, said, poll=1)
    asked = any('Stop the build?' in m['text'] for m in fake.sent)
    check(f'"{said}", then {how}: {want}', (r, asked, p.poll() is None),
          (want, answer is not None, want == 'kept_building'))
    p.kill(); p.wait(); assistant.BUILD.clear()
explain.ask_json = _ask_json

# 3a5. what Hive never does (skip the tests, push straight to his main or live) is never started as a build
check('risky requests are recognised', [assistant.is_risky(t) for t in (
      'push it straight to main and skip the tests', 'deploy directly to production', 'tests chhod do, jaldi hai',
      'build the page without tests', 'merge this into main')], [True] * 5)
check('ordinary ones are not', [assistant.is_risky(t) for t in (
      'add tests for refunds', 'fix the failing tests', 'build a payouts page', 'what is on main?')], [False] * 4)
started = []
fake = FakeTelegram([])
r = assistant.handle(ch(fake), repo, 'push it straight to main and skip the tests', poll=1,
                     start_build=lambda rp, goal: started.append(goal))
check('a risky request is answered, not built', (r, started, any('Shall I build' in m['text'] for m in fake.sent)),
      ('chat', [], False))

# 3a6. why a build stopped reaches him in his words with the next step, never as a raw error line ("Iron Man")
check('every known reason is said plainly, with what to do', [assistant.plain_reason(l)[:30] for l in (
      'You have unsaved changes. Commit or stash them first.', 'fatal: not a git repository',
      "usage limit reached|1793300000", 'OSError: [Errno 28] No space left on device')],
      ['Your project has edits that ar', "I'm not pointed at your projec", "Claude's usage limit was reach", 'This computer is out of disk s'])
check('an unknown error is kept for his engineer, with what he can do', (
      'for your engineer: KeyError' in assistant.plain_reason("KeyError: 'x'"), 'build again' in assistant.plain_reason("KeyError: 'x'"),
      assistant.plain_reason('').startswith('No reason was recorded')), (True, True, True))

# 3a7. the fast local reader (Gate 49) decides alone only where it is safe; everything else goes to Claude
from hive import fastread
sys.path.insert(0, os.path.join(os.getcwd(), 'gates', 'gate48', 'referee'))
from run48 import INTENTS as G48
check('the fast reader is asked the exact 9 meanings it was trained on', assistant.INTENTS_V1, G48)
check('without Laya and a trained reader installed, Claude reads everything', fastread.read('', 'kya chal raha hai'), None)
_fr = fastread.read
fastread.read = lambda history, text: {'intent': {'kitna hua': 'status', 'stop w2': 'stop_build', 'thanks': 'reply',
                                                  'how do refunds work?': 'reply', 'shukriya': 'reply'}.get(text, 'reply'), 'fast': True}
c = ch(FakeTelegram([]))
check('no build running: it decides status and chat alone; a question, or a builder named, goes to Claude',
      [(assistant.fast_read(c, t) or {}).get('intent') for t in ('kitna hua', 'shukriya', 'how do refunds work?', 'stop w2',
                                                                  'use 2 codex builders')],
      ['status', 'reply', None, None, None])
p4 = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
assistant.BUILD.update(proc=p4, goal='a refund page', started=time.time())
check('while a build runs, only greetings and status are decided fast', [(assistant.fast_read(c, t) or {}).get('intent')
      for t in ('kitna hua', 'shukriya')], ['status', None])
p4.kill(); p4.wait(); assistant.BUILD.clear(); fastread.read = _fr

# 3a8. Jarvis remembers his business: a lasting fact from a chat is kept per project and is in mind from then on
_aj2 = explain.ask_json
explain.ask_json = lambda prompt: ({'note': 'Sunny Shop launches in Mumbai first, in January.'}
                                   if 'worth remembering' in prompt and 'Mumbai' in prompt else
                                   {'note': ''} if 'worth remembering' in prompt else _aj2(prompt))
assistant.remember(ch(FakeTelegram([])), repo, "btw we're launching in Mumbai first, in January").join(5)
assistant.remember(ch(FakeTelegram([])), repo, 'thanks').join(5)
explain.ask_json = _aj2
check('a lasting fact is kept, small talk is not, and it is in mind for every answer',
      (memory.notes(repo), 'Sunny Shop launches in Mumbai first, in January.' in assistant.facts(repo)),
      (['Sunny Shop launches in Mumbai first, in January.'], True))

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

# 3b3. every confirmation reads typed words as well as taps (the live test: typed answers were taken as "no")
moves = []
fake = FakeTelegram([say('yes please')])
r = assistant.handle(ch(fake), repo, 'Please move to the cloud', poll=1, cloud=lambda rp, on, login=True: moves.append(login) or 0)
check('a typed "yes" moves to the cloud (with the login, the recommended choice)', (r, moves), ('moved', [True]))
fake = FakeTelegram([say('do it without the login')])
moves.clear()
assistant.handle(ch(fake), repo, 'Please move to the cloud', poll=1, cloud=lambda rp, on, login=True: moves.append(login) or 0)
check('"without the login" picks that option', moves, [False])
applied = []
fake = FakeTelegram([say('replace it'), say('yes')])
r = assistant.handle(ch(fake), repo, 'Actually, I changed my mind: a late post loses 9% per day', poll=1,
                     apply_build=lambda st, rule, c: applied.append(rule))
check('a typed "replace it" replaces the ruling, and a typed "yes" updates the build',
      (r, applied, any('9% per day' in x['text'] for x in memory.load(repo))), ('applied', ['a late post loses 9% per day'], True))
check('"update the fee to 5%" is not a status request', (telegram.is_status('update the fee to 5%'), telegram.is_status('any update?')),
      (False, True))

# 3c. the interview on the phone: a tap, his own words, his confirmation of the reading -> rules for the builders
from hive import interview
fake = FakeTelegram([tap('q01|0'), say('Only after a week'), tap('q02|0')])
rules = interview.interview('Fees and tips for a shop', ch(fake), poll=1)
check('the interview turns a tap and confirmed own words into rules',
      rules, ['Asha tips a creator Rs 500 after a great post. -> No fee on a tip', 'A late fee is charged only after 7 days.'])
check("his rules go into the builders' instructions as tests to encode", 'Encode every one' in interview.instructions(rules), True)
t = interview.instructions(['Whenever a tip is paid, no fee.'], ['Whenever a tip is paid, no fee.', 'Asha tips Rs 500 -> No fee, even when late'])
check('with his rulings, the ones not already on the sheet follow, kept whole (Gate 41)',
      (t.count('Whenever a tip is paid'), 'Asha tips Rs 500 -> No fee, even when late' in t), (1, True))

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
check('a yes in his own words keeps the reading; "whatever" leaves it to the builders; a correction amends the reading '
      'of its situation, keeping what he did not object to (Gate 39)',
      rules, ['A late fee is charged only after 7 days.', 'A late fee is charged only after 7 days. Amended: Shut the campaign off'])

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
plain = list(seen); seen.clear(); explain.ask_json = lambda prompt: (seen.append(prompt), _ask_json(prompt))[1]
interview.write_situations('Fees and tips for a shop', inputs=True)
explain.ask_json = _ask_json
check('with inputs, the plan also lists what the product shows for unusual input (Gate 40); by default it does not',
      [any('Unusual input is a business decision' in p for p in ps) for ps in (seen, plain)], [True, False])

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
check('the rule sheet: general rules, a disagreement settled by him, a wrong rule amended by his words',
      (rules, any('Your rules for this feature' in m['text'] for m in fake.sent)),
      (['Whenever a tip is paid, no fee is charged.', 'Whenever a fee is late, the brand is reminded. Amended: Only after a week',
        'Is a late tip charged a fee? -> No fee'], True))

# 3j2. a sheet written from the built code (Gate 42): he marks the wrong rule, says it right, and adds what is missing
answers = iter(['2', 'Only after 7 days', 'Tips are never charged'])
got = interview.confirm_sheet(['A tip pays the usual fee.', 'A late fee starts at once.'], ask=lambda p: next(answers),
                              title='What the built code does now', missing=True)
check('a code sheet: the marked rule is amended, and what is missing is added',
      got, ['A tip pays the usual fee.', 'A late fee starts at once. Amended: Only after 7 days', 'Tips are never charged'])

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

# 3k2. the hand-over from the built code (Gate 42): the sheet is written from the code; he marks the wrong rule and says
# it right; the change goes to one fix round and is remembered; a sheet he accepts whole ends the hand-over
fixed = []
_apply, start.apply_ruling = start.apply_ruling, lambda st, rule, c=None: fixed.append(rule)
_sheet, start._code_sheet = start._code_sheet, lambda st: ['A tip pays the usual fee.', 'A late fee starts at once.']
fake = FakeTelegram([tap('sheet|2'), tap('sheet|done'), say('Only after 7 days'), tap('sheet|none'), tap('hand|ok')])
start.handover({'repo': repo}, ch(fake), poll=1)
check('the code sheet: he marks a rule, it is amended and sent to one fix round, then his yes',
      (any('What the build does now, as rules' in m['text'] for m in fake.sent), fixed),
      (True, ['A late fee starts at once. Amended: Only after 7 days']))
fake = FakeTelegram([tap('sheet|done'), tap('sheet|none')])
fixed.clear(); start.handover({'repo': repo}, ch(fake), poll=1)
check('a code sheet he accepts whole ends the hand-over with no fix round', (fixed, fake.sent[-1]['text']),
      ([], '🎉 Very good. It is yours.'))
start.apply_ruling, start._code_sheet = _apply, _sheet

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
      (any('went wrong on my side' in t for t in texts), any('The latest build' in t for t in texts)), (True, True))

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

# 3p. a long code sheet comes in short pages by area, each with "this section is fine" (the owner: "60-80 rules is too
# much to review"); a wrong rule is put right on its own page; what only repeats his own rules is not shown again
from hive import codesheet
sheet20 = [f'fees: rule {k}.' for k in range(1, 11)] + [f'payouts: rule {k}.' for k in range(11, 21)]
fake = FakeTelegram([tap('pg|2'), tap('pg|ok'), say('Only after a week'), tap('pg|ok'), tap('pg|ok'), tap('pg|ok'),
                     tap('sheet|none')])
done = interview.confirm_sheet(list(sheet20), ch(fake), poll=1, missing=True)
pages = [m['text'] for m in fake.sent if m['text'].startswith('📋')]
check('20 rules come as 4 short pages by area, and a wrong rule is amended on its page',
      (len(pages), pages[0].split('\n')[0].startswith('📋 fees'), done[1].startswith('fees: rule 2.'), done[1] != sheet20[1],
       done[2:] == sheet20[2:]), (4, True, True, True, True))
_ask_json = explain.ask_json
explain.ask_json = lambda prompt: {'repeats': [1]} if 'only say again' in prompt else _ask_json(prompt)
show, his = codesheet.split_known(['fees: a tip carries no fee.', 'fees: late fees start after 7 days.'],
                                  ['A tip carries no fee.'])
explain.ask_json = _ask_json
check('a rule that only repeats his own is not shown again', (show, his),
      (['fees: late fees start after 7 days.'], ['fees: a tip carries no fee.']))

# 3q. every question and every page says why it matters, so the owner sees it is worth his time (the founder: "the
# questions must feel important, not random")
fake = FakeTelegram([tap('w1|0')])
interview.interview('Fees', ch(fake), situations=[{'id': 'w1', 'situation': 'Case 1.', 'options': ['Yes', 'No'],
                                                    'why': 'A wrong answer here pays referrers twice.'}], poll=1, sheet=False)
check('a question shows why it matters', any('Why it matters: A wrong answer here pays referrers twice.' in m['text']
                                             for m in fake.sent), True)
_ask_json = explain.ask_json
explain.ask_json = lambda prompt: ({'why': {'fees': 'Fees decide what you earn on every deal.',
                                            'payouts': 'Payouts decide what creators receive.'}}
                                   if 'why it is worth his attention' in prompt else _ask_json(prompt))
fake = FakeTelegram([tap('pg|ok')] * 4 + [tap('sheet|none')])
interview.confirm_sheet(list(sheet20), ch(fake), poll=1, missing=True, goal='Fees and payouts')
explain.ask_json = _ask_json
pages = [m['text'] for m in fake.sent if m['text'].startswith('📋')]
check('each page of the sheet says why its area matters, and the opening says what the time buys',
      ('Why it matters: Fees decide what you earn on every deal.' in pages[0], 'Payouts decide' in pages[2],
       any('about 3 minutes' in m['text'] and 'costs far more to find' in m['text'] for m in fake.sent)), (True, True, True))

# 3q2. Gate 45, live: 46 rules came out as 40 pages (each rule's heading had its own detail in brackets); a question
# ("What does this means", "??") was filed as a correction and the page waited; "Good, do the rest" was filed too
from hive import codesheet
real = ([f'Referral rewards ({d}): rule {k}.' for k, d in enumerate(('amounts', 'reward types', 'situation names',
         'brand invites brand', 'amounts', 'limits', 'reward types', 'limits', 'timing', 'timing'), 1)] +
        [f'Invites ({d}): rule {k}.' for k, d in enumerate(('codes', 'expiry', 'codes', 'self-invites'), 11)])
pg = codesheet.areas(real)
check('rules with details in brackets share their area\'s pages (14 rules: 3 pages, not 13)',
      ([a for a, _ in pg], [len(i) for _, i in pg]), (['Referral rewards (1)', 'Referral rewards (2)', 'Invites'], [8, 2, 4]))
small = ['Self-referral: a.', 'Self-referral: b.', 'Shared device: c.', 'Existing users: d.', 'Two links: e.', 'Expiry: f.',
         'Expiry: g.', 'Expiry: h.', 'Expiry: i.']
check('small neighbouring areas share a page, at most 8 rules (Gate 45: 7 of 15 pages held one or two rules)',
      [(a, len(i)) for a, i in codesheet.areas(small)], [(chr(183).join(['Self-referral ', ' Shared device ', ' Existing users ', ' Two links']), 5), ('Expiry', 4)])
_aj = explain.ask_json
explain.ask_json = lambda prompt: ({'kind': 'question', 'explanation': 'Rule 3 means a capitalised name counts the same.'}
                                   if 'What does this means' in prompt or '??' in prompt else _aj(prompt))
fake = FakeTelegram([say('What does this means'), say('??'), say('Good i think do rest of the work as required'),
                     tap('pg|ok'), tap('pg|ok'), tap('sheet|none')])
done = interview.confirm_sheet(list(real), ch(fake), poll=1, missing=True)
explain.ask_json = _aj
texts = [m['text'] for m in fake.sent]
check('a question about a page is answered, never filed as a correction; "good, do the rest" passes the page',
      (sum('Rule 3 means a capitalised name counts the same.' in t for t in texts), any('Noted for this section' in t for t in texts),
       done == real), (2, False, True))
check('a page that took a note says what to tap next', interview.section_fine('theek hai next'), True)
check('"good, but ..." is not a pass', [interview.section_fine(t) for t in ('good but make it 5%', 'fine, except brands',
      'ok nahi')], [False, False, False])

# 3q3. every way he has replied, or might, on a page of the sheet (Gate 45 live: a question was filed as a correction)
v = [5, 6, 7, 8]
cases = [('What does this means', 'question'), ('??', 'question'), ('what does rule 6 mean?', 'question'),
         ('kya matlab hai 6 ka', 'question'), ('6 should be 7 days', 'fix'), ('Rule 6: only for brands', 'fix'),
         ('rule 6 is wrong', 'marks'), ('6 and 8 are wrong', 'marks'), ('7 galat hai', 'marks'), ('6', 'marks'),
         ('9', 'out'), ('12 should be 3 days', 'out'), ('👍', 'fine'), ('theek hai', 'fine'), ('do the rest', 'fine'),
         ('Good i think do rest of the work as required', 'fine'), ('brands should get double', 'note')]
check('each reply on a page is read for what it is', [interview.page_reply('text', a, v)[0] for a, _ in cases],
      [w for _, w in cases])
check('"6 should be 7 days" carries the fix itself', interview.page_reply('text', '6 should be 7 days', v), ('fix', (6, 'should be 7 days')))
# one page lived through: a question with a number, a wrong number, a fix in one go, a mark answered with a question,
# then "it's fine after all"; cut off and resumed, the finished page is not asked again
sheet8 = [f'Referral rewards ({d}): rule {k}.' for k, d in enumerate(('amounts',) * 4 + ('limits',) * 4, 1)] + \
         [f'Invites: rule {k}.' for k in range(9, 13)]
explain.ask_json = lambda prompt: ({'kind': 'question', 'explanation': 'Rule 2 caps the reward at 500 rupees.'}
                                   if 'rule 2 mean' in prompt or 'what is a cap' in prompt.lower() else
                                   {'rule': 'Rule 3, with the reward doubled for brands.'} if 'double for brands' in prompt
                                   else _aj(prompt))
saved = os.path.join(home, 'review.json')
fake = FakeTelegram([say('what does rule 2 mean?'), say('20'), say('3: double for brands'), say('5'), tap('pg|ok'),
                     say('what is a cap?'), say("no it's fine")])
try:
    interview.confirm_sheet(list(sheet8), ch(fake), poll=1, missing=True, save=saved)
except RuntimeError:
    pass   # he went quiet after the first page
texts = [m['text'] for m in fake.sent]
kept = json.load(open(saved))
check('one page lived through: explained, out of range said, fixed in one go, a question while fixing answered, "fine" keeps it',
      (sum('Rule 2 caps the reward at 500 rupees.' in t for t in texts), any("Rule 20 isn't on this page; here it's 1 to 8" in t for t in texts),
       kept['general'][2], kept['general'][4], kept['done']),
      (2, True, 'Rule 3, with the reward doubled for brands.', sheet8[4], 1))
fake = FakeTelegram([tap('pg|ok'), say('nothing')])
done = interview.confirm_sheet(list(sheet8), ch(fake), poll=1, missing=True, save=saved)
check('a review cut off midway picks up at the page it stopped on, with what he said kept',
      (any('Picking up where we stopped: section 2 of 2' in m['text'] for m in fake.sent),
       sum(m['text'].startswith('📋') for m in fake.sent), done[2]), (True, 1, 'Rule 3, with the reward doubled for brands.'))
explain.ask_json = _aj

# 3q4. the sheet as a conversation (the founder: a page of 8 rules was "so cluttered"; "it must be like a conversation"):
# Jarvis says how a part works, covering every rule; he asks, changes in his own words, and says yes
talk = ['Verification: rewards wait until the newcomer verifies, for up to 30 days.',
        'Verification: after 30 days unverified, the referral is cancelled.',
        'Verification: part-days round down.'] + [f'Invites: rule {k}.' for k in range(4, 12)]
def talker(prompt):
    if 'as a short spoken message' in prompt and 'Verification' in prompt:
        return {'say': 'A newcomer has 30 days to verify; until then both rewards wait.', 'ask': 'Is 30 days right?',
                'covers': [1, 2]}   # it left out rule 3: that is still said
    if 'as a short spoken message' in prompt:
        return {'say': 'Invites work as listed.', 'ask': 'All good?', 'covers': list(range(4, 12))}
    if 'He replied: "make it 45 days"' in prompt:
        return {'kind': 'change', 'changes': [{'n': 1, 'rule': 'Verification: rewards wait up to 45 days.'},
                                               {'n': 2, 'rule': 'Verification: after 45 days unverified, it is cancelled.'}],
                'new': [], 'said_back': 'Newcomers now get 45 days to verify.'}
    if 'He replied: "what if they verify on day 40?"' in prompt:
        return {'kind': 'question'}
    return _aj(prompt)
explain.ask_json = talker
_look, assistant_look = None, assistant.look
assistant.look = lambda ch, repo, text: 'On day 40 the referral is already cancelled, so nobody is paid.'
fake = FakeTelegram([say('what if they verify on day 40?'), say('make it 45 days'), say('yes'), tap('cv|ok'), tap('sheet|none')])
done = interview.confirm_sheet(list(talk), ch(fake), poll=1, missing=True, code=repo)
assistant.look = assistant_look; explain.ask_json = _aj
texts = [m['text'] for m in fake.sent]
check('a part is told as a conversation, with anything the summary left out still said',
      (texts[1].startswith('🗣'), 'A newcomer has 30 days to verify' in texts[1], 'part-days round down' in texts[1],
       any(t.startswith('📋') for t in texts)), (True, True, True, False))
check('his question is answered from the code, his change in his own words is applied and said back, "yes" goes on',
      (any('On day 40 the referral is already cancelled' in t for t in texts),
       any('Newcomers now get 45 days to verify.' in t for t in texts),
       done[:3], done[3:] == talk[3:]),
      (True, True, ['Verification: rewards wait up to 45 days.', 'Verification: after 45 days unverified, it is cancelled.',
                    'Verification: part-days round down.'], True))
fake = FakeTelegram([tap('cv|rules'), tap('pg|ok'), tap('cv|ok'), tap('sheet|none')])
explain.ask_json = talker
interview.confirm_sheet(list(talk), ch(fake), poll=1, missing=True)
explain.ask_json = _aj
check('"show the detailed rules" opens the page, one tap away',
      sum(m['text'].startswith('📋') for m in fake.sent), 1)

# 3q5. with no model to ask, a question still gets the rules that answer it, and a note is filed under its own area
vr = [(6, 'Verification: rewards wait until the newcomer verifies, for up to 30 days after joining.'),
      (7, 'Verification: after 30 days unverified, the referral is cancelled and nobody is paid.'),
      (4, 'Referral limit: at most 10 referrals.')]
check('no model: "what happens if they verify on day 31?" shows the two verification rules',
      [n for n, _ in interview.related(vr, 'what happens if they verify on day 31?')], [6, 7])
check('a note from a shared page is filed under the area it is about',
      interview._area_of(vr, 'make the verification window 45 days', 'Referral rewards · Referral limit · Verification'),
      'Verification')

# 3q6. spot checks after the rules (Gate 58): each correction applied to its own part only, the case shown again,
# a question answered first, a second correction when he still disagrees; on the phone and in the terminal
from hive import spotcheck
rules = ['Late fees: the fee is 2% of the amount for every 30 days late.', 'Late fees: the fee is rounded down to the rupee.',
         'Bulk price: 10 units or more get 5% off.']
check('the parts are read from the rules', spotcheck.parts_of(rules), ['Late fees', 'Bulk price'])
check('every part is spot-checked, the ones his review left alone first, then the ones it changed (Gate 63)',
      spotcheck.order(rules, [rules[0].replace('2', '3')] + rules[1:]), ['Bulk price', 'Late fees'])
def spotter(prompt):
    if 'He said: "No, the first 7 days are free"' in prompt or 'What he said: No, the first 7 days are free' in prompt:
        return {'changes': [{'n': 1, 'rule': 'Late fees: the first 7 days are free; after that 2% for every 30 days late.'}], 'new': []}
    if 'What he said: and 0 on day 7 too' in prompt:
        return {'changes': [{'n': 1, 'rule': 'Late fees: up to and including day 7 is free; after that 2% for every 30 days late.'}]}
    if 'Bulk price' in prompt and 'What he said' in prompt:
        return {'changes': [{'n': 3, 'rule': 'WRONG PART TOUCHED'}]}
    if 'by following these rules alone' in prompt and 'first 7 days are free' in prompt:
        return {'say': "Ravi's 100-rupee invoice, 5 days late: the fee comes to 0."}
    if 'by following these rules alone' in prompt:
        return {'say': "Ravi's 100-rupee invoice, 7 days late: the fee comes to 0."}
    return _aj(prompt)
explain.ask_json = spotter
spots = [{'part': 'Late fees', 'say': "Ravi's 100-rupee invoice, 5 days late: the fee comes to 2 rupees."},
         {'part': 'Bulk price', 'say': 'Asha orders 10 units at 100 rupees: she pays 950.'}]
_ex = interview._explain
interview._explain = lambda ch, a, rules_text, goal, code=None: 'It means the fee starts on day one.'
fake = FakeTelegram([say('what does that mean?'), say('No, the first 7 days are free'), tap('sc|ok'), tap('sc|ok')])
out, rec = spotcheck.review(list(rules), spots, ch(fake), poll=1)
texts = [m['text'] for m in fake.sent]
check('phone: a question is answered first, the correction applied to its own part, the case shown again and confirmed',
      (any('It means the fee starts on day one.' in t for t in texts),
       any("With your correction: Ravi's 100-rupee invoice, 5 days late: the fee comes to 0." in t for t in texts),
       out[0], out[2], rec[0]['confirmed'], len(rec)),
      (True, True, 'Late fees: the first 7 days are free; after that 2% for every 30 days late.', rules[2], True, 1))
said = iter(['No, the first 7 days are free', 'and 0 on day 7 too', ''])
out, rec = spotcheck.review(list(rules), spots[:1], ask=lambda p: next(said))
check('terminal: still wrong on re-show, his second correction is applied too',
      (out[0], rec[0]['confirmed'], rec[0]['said_again']),
      ('Late fees: up to and including day 7 is free; after that 2% for every 30 days late.', False, 'and 0 on day 7 too'))
interview._explain = _ex; explain.ask_json = _aj
os.environ['HIVE_SPOT_CMD'] = '"' + sys.executable.replace(chr(92), '/') + '" "' + os.path.abspath('tests/fake_spot.py').replace(chr(92), '/') + '"'
got = spotcheck.find(repo, 'Late fees', ['Late fees', 'Bulk price'])
os.environ.pop('HIVE_SPOT_CMD')
check('spot checks come from running a copy of the built code, one part at a time', [g['part'] for g in got], ['Late fees', 'Bulk price'])
check('HIVE_SPOTS=0 turns them off', (os.environ.__setitem__('HIVE_SPOTS', '0'), spotcheck.find(repo, 'x', ['Late fees']),
                                       os.environ.pop('HIVE_SPOTS'))[1], [])

# 3r. "stop the build" in the middle of a build's questions stops it cleanly; it is not taken as his answer; and an
# answer that merely contains "stop" is still an answer
fake = FakeTelegram([say('stop the build')])
try:
    interview.interview('Fees', ch(fake), situations=[{'id': 'z1', 'situation': 'Case 1.', 'options': ['Yes', 'No']}],
                        poll=1, sheet=False)
    stopped = False
except telegram.Stopped:
    stopped = True
check('"stop the build" mid-question stops, and says nothing was built or changed',
      (stopped, any("I've stopped: nothing was built or changed" in m['text'] for m in fake.sent)), (True, True))
fake = FakeTelegram([say('stop charging late fees after 7 days'), say('yes')])   # then confirms the reading
rules = interview.interview('Fees', ch(fake), situations=[{'id': 'z1', 'situation': 'Case 1.', 'options': ['Yes', 'No']}],
                            poll=1, sheet=False)
check('an answer that mentions "stop" is still his answer', len(rules), 1)

# 3s. a question about his product is answered by Claude reading the code, read-only, in his project
assistant.ASK_CMD = '"' + sys.executable.replace(chr(92), '/') + '" "' + os.path.abspath('tests/fake_look.py').replace(chr(92), '/') + '"'
fake = FakeTelegram([])
r = assistant.handle(ch(fake), repo, 'How do refunds work in my app?', poll=1)
check('"how do refunds work?" is answered from the code, not guessed', (r, fake.sent[-1]['text']),
      ('answered', '🐝 Refunds go back to the brand within 7 days, sir.'))
check('it works in a throwaway copy: anything it runs never touches his folder, and the copy is gone afterwards',
      (os.path.exists(os.path.join(repo, 'tried_it.txt')), [d for d in os.listdir(tempfile.gettempdir()) if d.startswith('hive_look_')]),
      (False, []))
check('a question during the sheet review is answered by reading the built code, with an example',
      interview._explain(ch(FakeTelegram([])), 'what does rule 6 mean?', '6. Brand invites brand: 500 rupees.', '', code=repo),
      'In the code, a brand that invites another brand gets 500 rupees once the new brand pays.')

# 4. the listener steps aside while a build or review is talking to the owner
json.dump({'pid': os.getppid(), 'at': time.time()}, open(telegram.BUSY, 'w'))
check('another live process talking: the listener steps aside', telegram.busy_elsewhere(), True)
json.dump({'pid': os.getppid(), 'at': time.time() - 600}, open(telegram.BUSY, 'w'))
check('a stale claim is ignored', telegram.busy_elsewhere(), False)
json.dump({'pid': os.getpid(), 'at': time.time()}, open(telegram.BUSY, 'w'))
check("its own claim doesn't block it", telegram.busy_elsewhere(), False)
sys.exit(fail)
