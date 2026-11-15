"""Voice replies (hive/voice.py): when he speaks, Hive answers in voice too; what is not for the ear stays text; his
preference in his words; a real local voice note when Piper is installed. Fake Telegram.   usage: python3 tests/test_voice.py"""
import os, subprocess, sys, tempfile, time
sys.path.insert(0, os.getcwd()); sys.stdout.reconfigure(encoding='utf-8')
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home; os.environ['HIVE_EMBED'] = '0'
from hive import assistant, explain, memory, telegram, voice
memory.DIR = os.path.join(home, '.hive', 'rules'); telegram.BUSY = os.path.join(home, '.hive', 'telegram.busy')
sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
from test_telegram_fake import FakeTelegram, ME

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))

repo = os.path.join(home, 'shop'); subprocess.run(['git', 'init', '-q', '-b', 'main', repo])
subprocess.run(['git', '-C', repo, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'i'])
ch = lambda fake: telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake)

# 1. what is said aloud, and what stays text
check('emoji and the bee are not read out', voice.speakable('🐝 Good morning, sir. *Two* things need you.'),
      'Good morning, sir. Two things need you.')
check('a link, a long list or a code is not for the ear', [voice.speakable(t) for t in
      ('See https://dabba.example/try', '\n'.join(f'- item {i}' for i in range(12)), 'Your code is ABCD1234EFGH5678')],
      [None, None, None])

# 2. his preference, in his words
check('the default: voice when he sends voice', (voice.preference(), voice.wanted(True), voice.wanted(False)),
      ('when_voice', True, False))
fake = FakeTelegram([])
r = assistant.handle(ch(fake), repo, 'always reply in voice', poll=1)
check('"always reply in voice"', (r, voice.preference(), voice.wanted(False)), ('voice_pref', 'always', True))
assistant.handle(ch(FakeTelegram([])), repo, 'no voice replies', poll=1)
check('"no voice replies"', (voice.preference(), voice.wanted(True)), ('never', False))
assistant.handle(ch(FakeTelegram([])), repo, 'reply in voice when I send voice', poll=1)

# 3. he spoke: the answer comes as text and as a voice note (a stand-in voice; the real one below)
made = []
def fake_synth(text):
    d = tempfile.mkdtemp(); p = os.path.join(d, 'reply.ogg'); open(p, 'wb').write(b'OggS' + b'0' * 64); made.append(text); return p
_syn = voice.synthesize; voice.synthesize = fake_synth
explain.ask_json = lambda prompt: {'reply': 'Good morning, sir. Nothing needs you before noon.'}
os.environ.pop('HIVE_FAST_KEY', None); explain.fast_on = lambda: False
fake = FakeTelegram([]); c = ch(fake); c.heard_voice = True
assistant.speak(c, repo, 'Greet him.', 'Hello.')
for _ in range(50):
    if any(m['text'] == '[voice]' for m in fake.sent):
        break
    time.sleep(0.1)
check('he spoke: the text, then the same answer as a voice note', [m['text'][:20] for m in fake.sent],
      ['🐝 Good morning, sir.', '[voice]'])
fake = FakeTelegram([]); c = ch(fake); c.heard_voice = False
assistant.speak(c, repo, 'Greet him.', 'Hello.'); time.sleep(0.5)
check('he typed: text only', [m['text'][:6] for m in fake.sent], ['🐝 Good'])
voice.synthesize = _syn

# 4. the real thing, when Piper is installed: a voice note Telegram plays (OGG/Opus), made on this machine
if voice.provider() == 'piper' and voice.wait(900):
    p = voice.synthesize('Good morning, sir. Two things need you today: the refund for Asha, and the licence renewal.')
    check('a real local voice note: OGG/Opus, a few seconds long', (bool(p), open(p, 'rb').read(4) if p else b'',
          os.path.getsize(p) > 5000 if p else False), (True, b'OggS', True))
else:
    print('skip the real voice: pip install "hive-swarm[speech]"')
sys.exit(fail)
