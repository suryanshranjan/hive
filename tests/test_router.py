"""hive/router.py: a message read as a plan of steps; the step runner (each step through the one check, a later step
using an earlier result, stopping plainly when a step cannot be done); one-step plans through the usual code.
A stand-in model and stand-in mail and calendar; fake Telegram. usage: python3 tests/test_router.py"""
import os, subprocess, sys, tempfile
sys.path.insert(0, os.getcwd()); sys.stdout.reconfigure(encoding='utf-8')
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home; os.environ['HIVE_EMBED'] = '0'
from hive import assistant, explain, memory, office, mail, router, store, telegram
memory.DIR = os.path.join(home, '.hive', 'rules'); telegram.BUSY = os.path.join(home, '.hive', 'telegram.busy')
sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
from test_telegram_fake import FakeTelegram, ME, tap

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))

repo = os.path.join(home, 'shop'); subprocess.run(['git', 'init', '-q', '-b', 'main', repo])
subprocess.run(['git', '-C', repo, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'i'])
ch = lambda fake: telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake)

# 1. the plan: unknown tools dropped, at most 4 steps
explain.ask_json = lambda prompt: {'steps': [{'tool': 'mail_find', 'args': {'about': 'Asha tasting'}},
                                             {'tool': 'launch_rockets', 'args': {}},
                                             {'tool': 'calendar_add', 'args': {'what': 'call with Asha', 'when': 'Thursday 4 pm',
                                                                               'guests': ['$1.email']}}]}
from hive.tools import Refused
try:
    router.plan('', 'find Asha mail and put a call with her on Thursday at 4')
    refused = False
except Refused:
    refused = True
check('an unsupported plan is refused rather than partially executed', refused, True)
original = explain.ask_json
explain.ask_json = lambda prompt: dict(original(prompt), steps=[s for s in original(prompt)['steps'] if s['tool'] != 'launch_rockets'])
p = router.plan('', 'find Asha mail and put a call with her on Thursday at 4')
check('a later step refers to an earlier result', router._ref(['$1.email'], {1: {'email': 'asha@mehta.example'}}),
      ['asha@mehta.example'])

# 2. the step runner: find the mail, then the event with her address as the guest
mail.find = lambda repo, words: {'from': 'Asha Mehta <asha@mehta.example>', 'subject': 'Tasting', 'text': 'Thursday?',
                                  'id': '<a@x>', 'uid': '1'}
added = []
office.add_event = lambda ch_, repo_, text, poll: added.append(text) or 'event_added'
fake = FakeTelegram([])
done = router.run_chain(ch(fake), repo, p['steps'], 'find Asha mail and put a call with her on Thursday at 4', poll=1)
check('both steps done, the second using the first', (done, added), (['done', 'event_added'],
      ['put call with Asha on my calendar Thursday 4 pm with asha@mehta.example']))
check('he is told what is happening: how many things, what was found',
      ('2 things' in fake.sent[0]['text'], 'Found it: Tasting' in fake.sent[1]['text']), (True, True))

# 3. a step that cannot be done stops the rest, and says which and why
mail.find = lambda repo, words: None
added.clear(); fake = FakeTelegram([])
done = router.run_chain(ch(fake), repo, p['steps'], 'x', poll=1)
check('a mail not found: stopped at step 1, said plainly, the event never added',
      (done, added, 'stopped at step 1' in fake.sent[-1]['text']), (['not_found'], [], True))

# 4. a new mail to an address: shown, sent only on his yes; no address, nothing sent
sent = []
mail.send = lambda repo, to, subject, body, reply_to=None: sent.append((to, subject, body)) or (True, '')
steps = [{'tool': 'mail_send', 'args': {'to': 'priya@kestrel.example', 'subject': 'Orders this week', 'say': '142 orders.'}}]
fake = FakeTelegram([tap('mls|no')]); router.run_chain(ch(fake), repo, steps, 'x', poll=1)
check('"Don\'t": nothing sent', sent, [])
fake = FakeTelegram([tap('mls|yes')]); router.run_chain(ch(fake), repo, steps, 'x', poll=1)
check('"Send it": sent once, as shown', sent, [('priya@kestrel.example', 'Orders this week', '142 orders.')])
done = router.run_chain(ch(FakeTelegram([])), repo, [{'tool': 'mail_send', 'args': {'to': 'Priya', 'say': 'hi'}}], 'x', poll=1)
check('no address: not sent, said why', done, ['failed'])

# 5. remember, as a step
router.run_chain(ch(FakeTelegram([])), repo, [{'tool': 'remember', 'args': {'fact': 'Gupta Foods is our dal supplier now.'}}],
                 'x', poll=1)
check('"remember": kept', any('Gupta Foods' in f['text'] for f in store.live_facts(memory.project_key(repo))), True)

# 6. one-step plans run through the usual code, as the old reader's answer
check('one step reads as the old intent', router.as_intent({'tool': 'build', 'args': {'what': 'an invite page'}}, 'x'),
      {'intent': 'build', 'rule': 'an invite page'})
check('office steps go to the right office handler', [router.as_intent({'tool': t, 'args': {}}, 'x').get('office')
      for t in ('mail_read', 'calendar_check', 'calendar_add', 'mail_reply')], ['mail', 'cal', 'add_event', 'reply_mail'])

# 7. through Jarvis, with the plan reader on: a chain is run; a step from outside is refused
os.environ['HIVE_ROUTER'] = 'plan'
explain.ask_json = lambda prompt: ({'steps': [{'tool': 'remember', 'args': {'fact': 'The kitchen opens at 6 am.'}},
                                              {'tool': 'remember', 'args': {'fact': 'The kitchen closes at 10 pm.'}}]}
                                   if 'The steps you can use' in prompt else {'note': ''})
fake = FakeTelegram([])
r = assistant.handle(ch(fake), repo, 'remember the kitchen opens at 6 and closes at 10', poll=1)
check('with the plan reader on, two steps run in order', (r, sum('Kept:' in m['text'] for m in fake.sent)), ('chain:done,done', 2))
os.environ['HIVE_ROUTER'] = 'intent'
check('the old reader stays available (HIVE_ROUTER=intent)', assistant.router_mode(), 'intent')
sys.exit(fail)
