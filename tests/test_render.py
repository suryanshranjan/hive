"""Hive from only a phone, on Render, with no network and no tokens:
- render.yaml is a Blueprint with a worker, a disk where Hive keeps everything, and every secret asked in the form;
- `hive boot` turns the host's settings into Hive's files (token-only Telegram, fast replies, Claude Code headless,
  a GitHub token kept out of the project, an empty project when there is no repository);
- the first private chat to write to the bot becomes its owner, survives a restart, and strangers are told once;
- setup on Render says it is already always on; elsewhere, Render is one of his choices and never picked for him.
usage: python3 tests/test_render.py   (run from the hive repo root)"""
import json, os, re, subprocess, sys, tempfile
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
home = tempfile.mkdtemp()
os.environ['HOME'] = os.environ['USERPROFILE'] = home
for k in ('RENDER', 'HIVE_HOST', 'ANTHROPIC_API_KEY', 'GIT_CONFIG_GLOBAL'):
    os.environ.pop(k, None)
from hive import vault
from hive import boot, cloud_aws, onboard, telegram
from test_telegram_fake import FakeTelegram, tap, say

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))

# 1. the Blueprint
text = open('render.yaml', encoding='utf-8').read()
try:
    import yaml
    svc = yaml.safe_load(text)['services'][0]
    check('blueprint: a worker', (svc['type'], svc['runtime']), ('worker', 'docker'))
    check('blueprint: a paid plan with a disk where HOME lives', (svc['plan'] != 'free', svc['disk']['mountPath']), (True, '/data'))
    env = {e['key']: e for e in svc['envVars']}
    check('blueprint: every setting asked in the form, none written in', all(e.get('sync') is False and 'value' not in e
                                                                          for k, e in env.items() if k != 'HIVE_MASTER_KEY'), True)
    check('blueprint: Render makes the key that encrypts his secrets', env['HIVE_MASTER_KEY'].get('generateValue'), True)
    check('blueprint: the bot and model keys asked', {'TELEGRAM_BOT_TOKEN', 'ANTHROPIC_API_KEY'} <= set(env), True)
    check('blueprint: the Dockerfile it names exists', os.path.exists(svc['dockerfilePath']), True)
except ImportError:   # CI has no YAML reader: the same facts, read as text
    check('blueprint: a worker on docker', bool(re.search(r'type: worker', text) and re.search(r'runtime: docker', text)), True)
    check('blueprint: a disk at /data', 'mountPath: /data' in text, True)
    keys = re.findall(r'- key: (\w+)', text)
    check('blueprint: every setting asked in the form', text.count('sync: false') == len(keys) - 1 and 'value:' not in text, True)
    check('blueprint: Render makes the key that encrypts his secrets', bool(re.search(r'HIVE_MASTER_KEY.*\n\s+generateValue: true', text)), True)
    check('blueprint: the bot and model keys asked', {'TELEGRAM_BOT_TOKEN', 'ANTHROPIC_API_KEY'} <= set(keys), True)
    check('blueprint: the Dockerfile it names exists', os.path.exists('deploy/render/Dockerfile'), True)
docker = open('deploy/render/Dockerfile', encoding='utf-8').read()
check('image: HOME on the disk, setup knows it is on Render', ('HOME=/data/home' in docker, 'HIVE_HOST=render' in docker), (True, True))
check('image: starts with hive boot', 'hive boot' in docker, True)
check('image: Hive runs as its own user, never root', ('useradd' in docker, 'runuser -u hive' in docker, 'IS_SANDBOX' in docker), (True, True, False))

# 2. hive boot: settings in, files out
check('repo: owner/name', boot.repo_url('acme/shop'), 'https://github.com/acme/shop.git')
check('repo: an address', boot.repo_url('https://github.com/acme/shop/'), 'https://github.com/acme/shop.git')
check('repo: none', boot.repo_url(''), None)
h = os.path.join(home, 'render'); os.makedirs(h)
try:
    boot.configure({}, h); check('no token: stops with a plain reason', False, True)
except SystemExit as e:
    check('no token: stops with a plain reason', 'TELEGRAM_BOT_TOKEN' in str(e), True)
env = {'TELEGRAM_BOT_TOKEN': '123:abc', 'ANTHROPIC_API_KEY': 'sk-ant-x', 'GITHUB_TOKEN': 'ghp_secret',
       'HIVE_FAST_KEY': 'sk-fast', 'HIVE_FAST_BASE_URL': 'https://api.example.com/v1', 'HIVE_FAST_MODEL': 'm1'}
project = boot.configure(env, h)
tg = vault.load_json(os.path.join(h, '.hive', 'telegram.json'))
check('telegram: token and a 6-digit pairing word, owner not chosen yet',
      (tg['token'], 'chat_id' in tg, bool(re.fullmatch(r'\d{6}', tg.get('pair', '')))), ('123:abc', False, True))
first_pair = tg['pair']
boot.configure(env, h)
check('restart before pairing: the same word', vault.load_json(os.path.join(h, '.hive', 'telegram.json'))['pair'], first_pair)
boot.configure(dict(env, HIVE_PAIR_CODE='blue mango'), h)
check('his own word from the form wins', vault.load_json(os.path.join(h, '.hive', 'telegram.json'))['pair'], 'blue mango')
check('fast replies: any provider', vault.load_json(os.path.join(h, '.hive', 'fast.json')),
      {'provider': 'openai', 'api_key': 'sk-fast', 'model': 'm1', 'base_url': 'https://api.example.com/v1'})
check('claude code: no first-run questions', json.load(open(os.path.join(h, '.claude.json'))).get('hasCompletedOnboarding'), True)
disk = ''.join(open(os.path.join(r, f), errors='ignore').read() for r, _, fs in os.walk(h) for f in fs if '.git' + os.sep not in os.path.join(r, f) + os.sep)
helper = subprocess.run(['git', 'config', '--global', '--get', 'credential.https://github.com.helper'], capture_output=True, text=True).stdout
check('github token: never written to the disk; git asks the environment', ('ghp_secret' in disk, 'GITHUB_TOKEN' in helper), (False, True))
if vault.where() != 'plain':
    raw = open(os.path.join(h, '.hive', 'telegram.json')).read() + open(os.path.join(h, '.hive', 'fast.json')).read()
    check('the bot token and model keys are encrypted on disk', ('123:abc' in raw, 'sk-fast' in raw, vault.sealed(json.loads(
          open(os.path.join(h, '.hive', 'telegram.json')).read()))), (False, False, True))
proj_files = ''.join(open(os.path.join(r, f), errors='ignore').read() for r, _, fs in os.walk(project) for f in fs)
check('github token: never in the project', 'ghp_secret' in proj_files, False)
log = subprocess.run(['git', '-C', project, 'log', '--format=%s'], capture_output=True, text=True).stdout.split()
check('no repository: a new project, committed', log, ['Start'])
json.dump({'token': '123:abc', 'chat_id': 555}, open(os.path.join(h, '.hive', 'telegram.json'), 'w'))
boot.configure(env, h)
check('restart: his chat kept', vault.load_json(os.path.join(h, '.hive', 'telegram.json')).get('chat_id'), 555)
boot.configure(dict(env, TELEGRAM_BOT_TOKEN='999:new'), h)
nb = vault.load_json(os.path.join(h, '.hive', 'telegram.json'))
check('a new bot: owner chosen again, with a new word', (nb['token'], 'chat_id' in nb, bool(nb.get('pair'))), ('999:new', False, True))
check('restart: the project is not made twice',
      subprocess.run(['git', '-C', project, 'log', '--format=%s'], capture_output=True, text=True).stdout.split(), ['Start'])

# 3. the first private chat binds; strangers are told once
class Bot:
    def __init__(self, batches):
        self.batches, self.sent = list(batches), []
    def __call__(self, method, **p):
        if method == 'getMe':
            return {'username': 'hive_test_bot'}
        if method == 'sendMessage':
            self.sent.append((p['chat_id'], p['text'])); return {'message_id': len(self.sent)}
        if method == 'getUpdates':
            return self.batches.pop(0) if self.batches and (p.get('timeout') != 0 or 'allowed_updates' in p) else []
        return True
msg = lambda uid, chat, kind='private', name='Asha', text='hi': {
    'update_id': uid, 'message': {'message_id': uid, 'chat': {'id': chat, 'type': kind}, 'from': {'first_name': name}, 'text': text}}
telegram.PATH = os.path.join(h, '.hive', 'telegram.json')
# the audit (Nov 15): the first chat to write used to win, so whoever found the bot's name first owned it
bot = Bot([[msg(1, -40, 'group', text='4821 93')], [msg(2, 888, name='Ravi', text='hi'), msg(3, 777, text='482193'),
                                                   msg(4, 888, name='Ravi', text='482193')]])
said = []
check('bind: only the chat that sends the pairing word (a stranger writing first is not bound)',
      telegram.bind_first('999:new', api=bot, wait_s=5, say=said.append, code='482193'), 777)
check('bind: the stranger is asked for the word, never told it', [c for c, t in bot.sent if '482193' in t], [])
try:
    telegram.bind_first('999:x', api=Bot([]), wait_s=1, say=said.append); nocode = False
except ValueError:
    nocode = True
check('bind: never without a pairing word', nocode, True)
guess = Bot([[msg(10 + k, 666, name='Bad', text=f'{k:06d}') for k in range(8)]])
check('bind: guessing words does not bind', telegram.bind_first('999:g', api=guess, wait_s=2, say=said.append, code='482193'), None)
check('bind: a guesser is answered at most 5 times', len([c for c, _ in guess.sent if c == 666]), 5)

saved = vault.load_json(telegram.PATH)
check('bind: saved with the token, addressed by name', saved, {'token': '999:new', 'chat_id': 777, 'address': 'Asha'})
check('bind: a group never binds; he is greeted with "set me up"',
      -40 not in [c for c, _ in bot.sent] and any(c == 777 and 'set me up' in t for c, t in bot.sent), True)
check('bind: again, nothing asked (restart)', telegram.bind_first('999:new', api=Bot([]), wait_s=1, say=said.append, code='1'), 777)
check('bind: nobody writes, nothing bound', telegram.bind_first('111:other', api=Bot([]), wait_s=1, say=said.append, code='1'), None)
json.dump(saved, open(telegram.PATH, 'w'))
ch = telegram.Channel(telegram.load(), api=Bot([[msg(4, 888, name='Ravi', text='who are you')],
                                                [msg(5, 888, name='Ravi', text='hello?'), msg(6, 777, text='status')]]))
first = []; second = []
for _ in range(5):
    first.extend(ch.updates(timeout=0))
check('after a restart: only his chat is read', [t for t, _, _ in first + second], ['status'])
check('a stranger: told once that it is someone else\'s', [c for c, _ in ch.api.sent], [888])

# 4. where Hive runs: on Render it says so; elsewhere Render is one choice of four
repo = tempfile.mkdtemp()
os.environ['HIVE_HOST'] = 'render'
fake = FakeTelegram([]); ch = telegram.Channel({'token': 't', 'chat_id': 111}, api=fake)
onboard.step_home(ch, repo, 0, 6, 6)
check('on render: already always on, nothing to choose', ('already always on' in fake.sent[-1]['text'],
      'reply_markup' in fake.sent[-1], onboard.progress(repo).get('home')), (True, False, 'render'))
os.environ.pop('HIVE_HOST')
fake = FakeTelegram([tap('onb|home|render')]); ch = telegram.Channel({'token': 't', 'chat_id': 111}, api=fake)
onboard.step_home(ch, tempfile.mkdtemp(), 1, 6, 6)
labels = [b['text'] for row in fake.sent[0]['reply_markup']['inline_keyboard'] for b in row]
check('elsewhere: four choices, Render among them, priced', any(l.startswith('☁️ Render, ~$') for l in labels) and len(labels) == 4, True)
check('elsewhere: nothing chosen for him (he taps)', 'render' in fake.sent[0]['text'].lower(), True)
steps = fake.sent[-1]['text']
check('chose render: the deploy link and a new bot', (cloud_aws.RENDER_DEPLOY in steps, '/newbot' in steps), (True, True))
fake = FakeTelegram([say('render please')]); ch = telegram.Channel({'token': 't', 'chat_id': 111}, api=fake)
r2 = tempfile.mkdtemp(); onboard.step_home(ch, r2, 1, 6, 6)
check('said "render": understood', onboard.progress(r2).get('home'), 'render')
check('price: 1c-2g plus a 10 GB disk', cloud_aws.render_monthly(), 28)
# a mistyped token: said plainly and stopped, never silence for ever (Gate 117 prep: it waited on "@your bot")
said = []
def refused(method, **p):
    raise RuntimeError('Telegram getMe: Unauthorized')
try:
    telegram.bind_first('123:bogus', api=refused, wait_s=1, say=said.append, code='1'); code = None
except SystemExit as e:
    code = e.code
check('a refused token: a plain reason and a stop', (code, any('refused' in s and 'BotFather' in s for s in said)), (2, True))

sys.exit(fail)
