"""Memory 2.0 through Jarvis (hive/assistant.py with hive/store.py): what he says is kept with its kind and the person it
is about; replies recall what bears on his message; "what do you know about Asha?"; "forget that"; a change of mind
replaces the old rule; the conversation archive; `hive memory`. Fake Telegram, stand-in model; no network.
usage: python3 tests/test_memory2.py   (run from the hive repo root)"""
import json, os, subprocess, sys, tempfile, time
sys.path.insert(0, os.getcwd())
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home
from hive import assistant, explain, memory, recall, store, telegram
memory.DIR = os.path.join(home, '.hive', 'rules'); assistant.RUNS = os.path.join(home, '.hive', 'runs')
telegram.BUSY = os.path.join(home, '.hive', 'telegram.busy'); os.makedirs(os.path.join(home, '.hive'), exist_ok=True)
sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
from test_telegram_fake import FakeTelegram, ME, tap, say

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))

repo = os.path.join(home, 'shop'); subprocess.run(['git', 'init', '-q', '-b', 'main', repo])
subprocess.run(['git', '-C', repo, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'i'])
ch = lambda fake: telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake)
said = lambda fake: '\n'.join(m['text'] for m in fake.sent)

# 1. what he says is kept with its kind, the person, and the date it holds until
answers = {
    'Asha': {'note': 'Asha Mehta of Mehta Caterers orders 40 tiffins every Monday.', 'kind': 'person',
             'person': {'name': 'Asha Mehta', 'relation': 'customer', 'org': 'Mehta Caterers'}, 'until': ''},
    'licence': {'note': 'The FSSAI licence renewal is due on 30 November.', 'kind': 'deadline', 'person': None,
                'until': time.strftime('%Y-%m-%d', time.localtime(time.time() + 10 * 86400))},
    'mornings': {'note': 'He prefers updates in the morning, not at night.', 'kind': 'preference', 'person': None, 'until': ''},
}
_aj = explain.ask_json
def fake_model(prompt):
    if 'worth remembering' in prompt:
        msg = prompt.split('His newest message:')[1].split('\n')[1]
        return next((v for k, v in answers.items() if k in msg), {'note': ''})
    return _aj(prompt)
explain.ask_json = fake_model
for t in ("Asha from Mehta Caterers takes 40 tiffins every Monday", "the licence renewal is due on the 30th",
          "send me updates in the mornings please", "thanks"):
    assistant.remember(ch(FakeTelegram([])), repo, t).join(5)
explain.ask_json = _aj
P = memory.project_key(repo)
kinds = sorted((f['kind'], bool(f['person_id']), bool(f['due_at'])) for f in store.live_facts(P))
check('kept with its kind, the person it is about, and the date it holds until',
      kinds, [('deadline', False, True), ('person', True, False), ('preference', False, False)])
check('the person is known by name, with relation and company',
      (store.person('Asha Mehta') or {}).get('relation'), 'customer')
check('small talk is not kept', len(store.live_facts(P)), 3)
check('the plain notes builds and plans read still have them', len(memory.notes(repo)), 3)

# 1b. a change of mind about a fact (not only a rule): the old one is replaced, not kept beside the new
def fake_model2(prompt):
    if 'worth remembering' in prompt:   # one call: the fact, and which kept facts (numbered in the prompt) it replaces
        known = prompt.split('may be related (numbered):')[1].split('If his message changes')[0].strip().split('\n')
        if 'Gupta' in prompt.split('His newest message:')[1].split('\n')[1]:
            return {'note': 'Our dal supplier is now Gupta Foods.', 'kind': 'note', 'person': None, 'until': '',
                    'replaces': [i + 1 for i, l in enumerate(known) if 'Sharma' in l]}
        return {'note': 'Our dal supplier is Sharma Traders.', 'kind': 'note', 'person': None, 'until': '', 'replaces': []}
    return _aj(prompt)
explain.ask_json = fake_model2
assistant.remember(ch(FakeTelegram([])), repo, 'we buy our dal from Sharma Traders').join(5)
assistant.remember(ch(FakeTelegram([])), repo, 'we moved to Gupta Foods for dal').join(5)
explain.ask_json = _aj
live = [f['text'] for f in store.live_facts(P)]
check('a changed fact replaces the old one, in the store and the plain notes',
      ('Our dal supplier is now Gupta Foods.' in live, 'Our dal supplier is Sharma Traders.' in live,
       'Our dal supplier is Sharma Traders.' in memory.notes(repo)), (True, False, False))

# 2. a reply recalls what bears on his message, even when it is not among the newest
for i in range(25):
    memory.add_note(repo, f'Weekly update {i}: the team shipped small fixes.')
assistant.CURRENT['text'] = 'how many tiffins does asha take?'
facts = assistant.facts(repo)
check('a reply about Asha sees what is kept about her, though 25 notes came after it', '40 tiffins' in facts, True)
check('... and the latest note too', 'Weekly update 24' in facts, True)
assistant.CURRENT['text'] = ''

# 3. "what do you know about Asha?"
fake = FakeTelegram([])
r = assistant.handle(ch(fake), repo, 'What do you know about Asha Mehta?', poll=1)
check('he asks what Hive knows about someone: it is listed, numbered, with how to correct it',
      (r, 'Mehta Caterers' in said(fake), '1. Asha Mehta' in said(fake), 'forget 2' in said(fake)), ('memory_shown', True, True, True))
fake = FakeTelegram([])
r = assistant.handle(ch(fake), repo, 'what do you know about the Pune warehouse?', poll=1)
check('nothing kept: said so, nothing invented', (r, "don't have anything" in said(fake)), ('memory_none', True))

# 4. "forget that": shown first, done on his yes, gone from replies and from the notes
assistant.LAST_KEPT.update(text='He prefers updates in the morning, not at night.', at=time.time())
fake = FakeTelegram([tap('fgt|yes')])
r = assistant.handle(ch(fake), repo, 'forget that', poll=1)
assistant.CURRENT['text'] = 'when should I send him updates? morning'
check('"forget that": the fact is shown, then forgotten on his yes',
      (r, 'prefers updates in the morning' in fake.sent[0]['text'], 'prefers updates' in assistant.facts(repo),
       any('prefers updates' in n for n in memory.notes(repo))), ('forgotten', True, False, False))
fake = FakeTelegram([tap('fgt|no')])
assistant.handle(ch(FakeTelegram([])), repo, 'what do you know about the licence renewal?', poll=1)
r = assistant.handle(ch(fake), repo, 'forget 1', poll=1)
check('"forget 1" from the list, and "keep it" keeps it', (r, any('FSSAI' in f['text'] for f in store.live_facts(P))),
      ('forget_kept', True))
fake = FakeTelegram([tap('fgt|yes')])
r = assistant.handle(ch(fake), repo, 'forget everything about Asha Mehta', poll=1)
check('"forget everything about Asha": she and what was kept about her',
      (r, store.person('Asha Mehta'), any('tiffins' in f['text'] for f in store.live_facts(P))), ('forgotten', None, False))

# 5. a change of mind: the old rule is kept for the record, replaced by the new one
memory.add(repo, 'A late post is paid in full.')
memory.replace(repo, [0], 'A late post loses 2% per day.')
old = store.find_fact('A late post is paid in full.', 'rule', P)
check('a change of mind: the old rule is marked as replaced by the new',
      (bool(old and old['superseded_by']), [r['text'] for r in memory.load(repo)]), (True, ['A late post loses 2% per day.']))
memory.forget(repo, 1)
check('"hive rules forget": out of the store too', store.find_fact('A late post loses 2% per day.', 'rule', P)['deleted_at'] is not None, True)

# 6. the whole conversation is kept, a password taken out of it
c = telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=FakeTelegram([])); c.keep = True
c.remember('owner', 'the mail password is tiffin-2026, and the Diwali menu launches on the 1st')
c.forget('tiffin-2026')
got = store.search_messages('Diwali menu')
check('the whole conversation can be searched', bool(got), True)
check('a password he sent is taken out of the archive', any('tiffin-2026' in m['text'] for m in got), False)

# 7. hive memory
out = subprocess.run([sys.executable, '-m', 'hive', 'memory', 'search', 'licence'], cwd=repo, capture_output=True, text=True,
                     env=dict(os.environ, PYTHONPATH=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
check('hive memory search finds what is kept', 'FSSAI' in out.stdout, True)
dest = os.path.join(home, 'export.json')
subprocess.run([sys.executable, '-m', 'hive', 'memory', 'export', dest], cwd=repo, capture_output=True,
               env=dict(os.environ, PYTHONPATH=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
check('hive memory export: everything kept, as a file he can keep', 'FSSAI' in open(dest, encoding='utf-8').read(), True)
sys.exit(fail)
