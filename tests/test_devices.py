"""Screenshots on any screen he asks for (the owner: "show me how it looks on desktop; tell me in tablet"): which
screens and pages his words name, "and on desktop?" right after a screenshot, captions as he would say them, and (when
Playwright is installed) real shots at each screen's width. A fake Telegram; no network, no tokens.
usage: python3 tests/test_devices.py   (run from the hive repo root)"""
import os, struct, subprocess, sys, tempfile
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home
from hive import assistant, explain, memory, screens, telegram
explain.CMD = '"' + sys.executable.replace(chr(92), '/') + '" tests/fake_explain.py'
memory.DIR = os.path.join(home, '.hive', 'rules'); telegram.BUSY = os.path.join(home, '.hive', 'telegram.busy')
assistant.RUNS = os.path.join(home, '.hive', 'runs')
from test_telegram_fake import FakeTelegram, ME

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))
ch = lambda fake: telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake)

# 1. the screens his words name
check('desktop', screens.devices_in('show me how it will look on desktop'), ['desktop'])
check('tablet, in his words', screens.devices_in('in tablet tell me'), ['tablet'])
check('two at once, in a fixed order', screens.devices_in('on laptop and ipad'), ['tablet', 'desktop'])
check('every screen', screens.devices_in('show it on all devices'), ['phone', 'tablet', 'desktop'])
check('none named', screens.devices_in('show me the page'), [])

# 2. the pages his words name, found among his product's pages
repo = os.path.join(home, 'site'); os.makedirs(os.path.join(repo, 'pages'))
for f in ('index.html', 'pricing.html', 'sign-up.html'):
    open(os.path.join(repo, f), 'w').write(f'<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>{f}</title></head><body><h1>{f}</h1></body></html>')
open(os.path.join(repo, 'pages', 'invite.tsx'), 'w').write('export default () => null')
subprocess.run(['git', 'init', '-q', '-b', 'main', repo])
subprocess.run(['git', '-C', repo, 'add', '-A']); subprocess.run(['git', '-C', repo, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'site'])
check("his product's pages", screens.all_pages(repo), ['/', '/invite', '/pricing.html', '/sign-up.html'])
check('the pricing page', screens.pages_named('show me the pricing page on desktop', repo), ['/pricing.html'])
check('sign up, said in two words', screens.pages_named('how does sign up look on tablet', repo), ['/sign-up.html'])
check('the home page', screens.pages_named('send me a screenshot of the home page', repo), ['/'])
check('a page he does not have is not invented', screens.pages_named('show me the careers page', repo), [])

# 3. from the phone, with a stand-in camera
taken = []
def fake_take_on(code, pages, devices, out_dir=None, sizes=None):
    taken.append((list(pages), list(devices)))
    out = []
    for p in pages:
        for d in devices:
            png = os.path.join(home, f'{len(taken)}_{d}.png'); open(png, 'wb').write(b'\x89PNG'); out.append((p, d, png))
    return out
real_take_on, real_available = screens.take_on, screens.available
screens.take_on = fake_take_on
assistant.SHOWN.clear()
fake = FakeTelegram([])
r = assistant.handle(ch(fake), repo, 'show me the pricing page on desktop', poll=1)
check('"the pricing page on desktop" shoots that page on that screen', (r, taken[-1]), ('shown', (['/pricing.html'], ['desktop'])))
check('the caption names the page and the screen', fake.sent[-1]['text'].startswith('[photo] Pricing page on desktop'), True)
fake = FakeTelegram([])
r = assistant.handle(ch(fake), repo, 'and on tablet?', poll=1)
check('"and on tablet?" right after shows the same page on a tablet', (r, taken[-1]), ('shown', (['/pricing.html'], ['tablet'])))
fake = FakeTelegram([])
r = assistant.handle(ch(fake), repo, 'how will it look on every screen', poll=1)
check('"every screen" shows phone, tablet and desktop', taken[-1][1], ['phone', 'tablet', 'desktop'])
check('one photo per page and screen', len([m for m in fake.sent if m['text'].startswith('[photo]')]), 3)
check('"make the menu bigger on desktop" is not a screenshot request', assistant.SHOW_WORDS.search('make the menu bigger on desktop'), None)
check('a long sentence naming a screen is not a follow-up', assistant._device_follow_up('please change the header on desktop to blue'), False)
screens.take_on = real_take_on

# 4. real screenshots at each screen's width (when Playwright and its browser are here)
def png_width(path):
    with open(path, 'rb') as f:
        head = f.read(24)
    return struct.unpack('>I', head[16:20])[0]
if screens.available():
    try:
        shots = screens.take_on(repo, ['/pricing.html'], ['phone', 'tablet', 'desktop'])
        check('real shots: phone at 2x, tablet and desktop at their widths',
              [(d, png_width(p)) for _, d, p in shots], [('phone', 780), ('tablet', 820), ('desktop', 1440)])
        check('the phone-only path still names files as before', os.path.basename(screens.take(repo, ['/'])[0][1]), '01_home.png')
    except screens.Unavailable as e:
        print(f'skip real screenshots ({e})')
else:
    print('skip real screenshots (Playwright not installed)')

sys.exit(fail)
