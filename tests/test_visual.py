"""The visual loop on the owner's phone (the owner: "it shares the screenshot on my phone; I say what's off, or send a
reference: make it like this"): screenshots out, his pictures in, his picture reaching the builders, before and after.
A fake Telegram, stand-in builds; real screenshots when Playwright is installed (skipped otherwise).
usage: python3 tests/test_visual.py   (run from the hive repo root)"""
import json, os, subprocess, sys, tempfile, time
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home
from hive import assistant, explain, memory, refs, screens, team, telegram
explain.CMD = '"' + sys.executable.replace(chr(92), '/') + '" tests/fake_explain.py'
memory.DIR = os.path.join(home, '.hive', 'rules'); telegram.BUSY = os.path.join(home, '.hive', 'telegram.busy')
telegram.PATH = os.path.join(home, '.hive', 'telegram.json')
assistant.RUNS = team.RUNS = os.path.join(home, '.hive', 'runs'); team.TEAM = os.path.join(home, '.hive', 'team.json')
from test_telegram_fake import FakeTelegram, ME, tap, say, photo

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))
git = lambda cwd, *a: subprocess.run(['git', '-C', cwd, *a], capture_output=True, text=True)
telegram.Channel.fetch = lambda self, file_path, local: open(local, 'wb').write(b'\x89PNG fake picture')
ch = lambda fake: telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake)

# 1. his picture arrives as his words plus the picture, kept on this machine
fake = FakeTelegram([photo('ref1', 'make the invite button like this')])
c = ch(fake); got = []
for _ in range(3):
    got += [t for t, _, _ in c.updates(timeout=0.1) if t]
    if got: break
text = got[0] if got else ''
check('a picture he sends arrives with his words and is saved here',
      (text.startswith('make the invite button like this [photo: '), refs.has(text), os.path.exists(refs.PHOTO.search(text).group(1)) if refs.has(text) else False),
      (True, True, True))
check('his words without the marker', refs.words(text), 'make the invite button like this')

# 2. a screenshot goes out with its caption
png = os.path.join(home, 'shot.png'); open(png, 'wb').write(b'\x89PNG')
fake = FakeTelegram([]); ch(fake).send_photo(png, 'Pricing page: how does it look?')
check('a screenshot is sent with its caption', (fake.sent[0]['text'], fake.sent[0]['photo']), ('[photo] Pricing page: how does it look?', png))

# 3. his picture travels into the code the builders get
code = os.path.join(home, 'code'); os.makedirs(code); git(code, 'init', '-q', '-b', 'main')
open(os.path.join(code, 'a.txt'), 'w').write('x'); git(code, 'add', '.'); git(code, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'i')
said = refs.attach(text, code, commit=True)
check('the picture is copied into the code (.hive/refs) and his words point to it, committed',
      ('(his picture: .hive/refs/ref_1.jpg; open it and match what it shows)' in said, os.path.exists(os.path.join(code, '.hive', 'refs', 'ref_1.jpg')),
       '.hive/refs/ref_1.jpg' in git(code, 'ls-files').stdout), (True, True, True))

# 4. mid-build, his picture reaches the builders through the shared branch
run = os.path.join(team.RUNS, 'invites-1103', 'build'); os.makedirs(run)
subprocess.run(['git', 'clone', '-q', '--bare', code, os.path.join(run, 'up.git')])
json.dump({'branch': 'main', 'workers': 1, 'started': int(time.time())}, open(os.path.join(run, 'run.json'), 'w'))
p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
json.dump({'w1': {'agent': 'claude', 'state': 'working', 'pid': p.pid, 'started': int(time.time())}}, open(os.path.join(run, 'builders.json'), 'w'))
assistant.BUILD.update(proc=p, goal='an invite page at /invite', started=time.time())
fake = FakeTelegram([])
r = assistant.handle(ch(fake), code, 'make the invite button like this [photo: ' + refs.PHOTO.search(text).group(1) + ']', poll=1)
show = lambda path: subprocess.run(['git', '--git-dir', os.path.join(run, 'up.git'), 'show', f'main:{path}'], capture_output=True,
                                   text=not path.endswith('.jpg'), errors='replace')   # a picture is bytes, not text (Linux)
check('a picture during a build goes to a builder with his words, and the picture is in the shared branch',
      (r, 'his picture: .hive/refs/ref_2.jpg' in show('OWNER.md').stdout, show('.hive/refs/ref_2.jpg').returncode == 0),
      ('instructed', True, True))
p.kill(); p.wait(); assistant.BUILD.clear()

# 5. "show me": screenshots at phone size, with an invitation to say what's off (a stand-in camera)
shots = [('/invite', png)]
real_take = screens.take
screens.take = lambda code_dir, pages, out_dir=None, size=None: list(shots)   # a fresh list, as the real camera
fake = FakeTelegram([])
check('"show me" is read without a model', assistant.SHOW_WORDS.search('show me the invite page') is not None, True)
r = assistant.handle(ch(fake), code, 'show me the invite page', poll=1)
check('"show me" sends the screens, asking what is off', (r, [m['text'].split(chr(10))[0] for m in fake.sent],
      'send a picture of what you' in fake.sent[-1]['text']), ('shown', ['[photo] /invite'], True))

# 6. after seeing it, a picture changes his latest build, and he sees before and after
st = {'repo': code, 'name': 'invites-1103', 'b': 'main', 'final': run, 'goal': 'an invite page at /invite', 'check': ''}
json.dump(st, open(os.path.join(team.RUNS, 'invites-1103', 'state.json'), 'w'))
applied = []
after = os.path.join(home, 'after.png'); open(after, 'wb').write(b'\x89PNG after')
def apply_build(state, rule, ch):
    applied.append(rule); shots[:] = [('/invite', after)]
fake = FakeTelegram([])
r = assistant.handle(ch(fake), code, 'bigger button, like this [photo: ' + refs.PHOTO.search(text).group(1) + ']', poll=1,
                     apply_build=apply_build)
sent = [(m['text'].split(chr(10))[0], m.get('photo')) for m in fake.sent]
check('a picture after a build changes that build (his words and picture to the fix round), then before and after',
      (r, len(applied), refs.has(applied[0]) if applied else False, ('[photo] Before: /invite', png) in sent, ('[photo] After: /invite', after) in sent),
      ('amended', 1, True, True, True))
check('with a picture, no tip to send one', 'a picture lands closer' in fake.sent[0]['text'], False)
fake = FakeTelegram([])
real_fast = assistant.fast_read
assistant.fast_read = lambda c, t: {'intent': 'amend', 'rule': t}   # as Claude reads it right after a build he saw
assistant.handle(ch(fake), code, 'make the header a darker colour', poll=1, apply_build=apply_build)
assistant.fast_read = real_fast
check('words about a look: the tip that a picture lands closer (Gate 105: 18/18 vs 13/18)',
      'a picture lands closer' in fake.sent[0]['text'], True)

# 7. when it cannot take screenshots, he is told why in plain words
screens.take = real_take
os.environ['HIVE_NO_PLAYWRIGHT'] = '1'
real_avail = screens.available
screens.available = lambda: False
fake = FakeTelegram([])
assistant.handle(ch(fake), code, 'show me', poll=1)
check('no browser here: he is told plainly how to enable screenshots', 'pip install playwright' in fake.sent[-1]['text'], True)
screens.available = real_avail

# 8. the real camera, when installed: a page at phone size
site = os.path.join(home, 'site'); os.makedirs(site)
open(os.path.join(site, 'index.html'), 'w').write('<h1>Sunny Shop</h1><button>Invite</button>')
check('the pages worth showing come from the goal, else the home page',
      (screens.pages_of('a pricing page at /pricing and /invite', site), screens.pages_of('a nicer header', site)), (['/pricing', '/invite'], ['/']))
check('a folder with index.html is a frontend; one without is not', (screens.is_frontend(site), screens.is_frontend(code)), (True, False))
check('a look job (no quiz, one builder): restyling, a picture; not a feature, and not on a project with nothing to see',
      [screens.is_look_job(g, r) for g, r in (
          ('Look up a site I like and redo the home page in its style', site),
          ('make it like this (his picture: .hive/refs/ref_1.png; open it and match what it shows)', site),
          ('add refunds to the store credit page with a nicer layout', site),
          ('make the header darker', code))], [True, True, False, False])
if screens.available():
    try:
        got = screens.take(site, ['/'], os.path.join(home, 'shots'))
        check('a real screenshot of the page is taken', (len(got), os.path.getsize(got[0][1]) > 1000), (1, True))
    except screens.Unavailable as e:
        print('skip real screenshot:', e)
else:
    print('skip real screenshot: Playwright is not installed here')
sys.exit(fail)
