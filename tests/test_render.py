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
                                                                          for e in env.values()), True)
    check('blueprint: the bot and model keys asked', {'TELEGRAM_BOT_TOKEN', 'ANTHROPIC_API_KEY'} <= set(env), True)
    check('blueprint: the Dockerfile it names exists', os.path.exists(svc['dockerfilePath']), True)
except ImportError:   # CI has no YAML reader: the same facts, read as text
    check('blueprint: a worker on docker', bool(re.search(r'type: worker', text) and re.search(r'runtime: docker', text)), True)
    check('blueprint: a disk at /data', 'mountPath: /data' in text, True)
    keys = re.findall(r'- key: (\w+)', text)
    check('blueprint: every setting asked in the form', text.count('sync: false') == len(keys) and 'value:' not in text, True)
    check('blueprint: the bot and model keys asked', {'TELEGRAM_BOT_TOKEN', 'ANTHROPIC_API_KEY'} <= set(keys), True)
    check('blueprint: the Dockerfile it names exists', os.path.exists('deploy/render/Dockerfile'), True)
docker = open('deploy/render/Dockerfile', encoding='utf-8').read()
check('image: HOME on the disk, setup knows it is on Render', ('HOME=/data/home' in docker, 'HIVE_HOST=render' in docker), (True, True))
check('image: starts with hive boot', 'hive boot' in docker, True)

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
tg = json.load(open(os.path.join(h, '.hive', 'telegram.json')))
check('telegram: token only, owner not chosen yet', tg, {'token': '123:abc'})
check('fast replies: any provider', json.load(open(os.path.join(h, '.hive', 'fast.json'))),
      {'provider': 'openai', 'api_key': 'sk-fast', 'model': 'm1', 'base_url': 'https://api.example.com/v1'})
check('claude code: no first-run questions', json.load(open(os.path.join(h, '.claude.json'))).get('hasCompletedOnboarding'), True)
check('github token: in git\'s own store', 'ghp_secret' in open(os.path.join(h, '.git-credentials')).read(), True)
proj_files = ''.join(open(os.path.join(r, f), errors='ignore').read() for r, _, fs in os.walk(project) for f in fs)
check('github token: never in the project', 'ghp_secret' in proj_files, False)
log = subprocess.run(['git', '-C', project, 'log', '--format=%s'], capture_output=True, text=True).stdout.split()
check('no repository: a new project, committed', log, ['Start'])
json.dump({'token': '123:abc', 'chat_id': 555}, open(os.path.join(h, '.hive', 'telegram.json'), 'w'))
boot.configure(env, h)
check('restart: his chat kept', json.load(open(os.path.join(h, '.hive', 'telegram.json'))).get('chat_id'), 555)
boot.configure(dict(env, TELEGRAM_BOT_TOKEN='999:new'), h)
check('a new bot: owner chosen again', json.load(open(os.path.join(h, '.hive', 'telegram.json'))), {'token': '999:new'})
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
bot = Bot([[msg(1, -40, 'group')], [msg(2, 777), msg(3, 888, name='Ravi')]])
said = []
check('bind: the first private chat', telegram.bind_first('999:new', api=bot, wait_s=5, say=said.append), 777)
saved = json.load(open(telegram.PATH))
check('bind: saved with the token, addressed by name', saved, {'token': '999:new', 'chat_id': 777, 'address': 'Asha'})
check('bind: a group never binds; he is greeted with "set me up"',
      [c for c, _ in bot.sent] == [777] and 'set me up' in bot.sent[0][1], True)
check('bind: again, nothing asked (restart)', telegram.bind_first('999:new', api=Bot([]), wait_s=1, say=said.append), 777)
check('bind: nobody writes, nothing bound', telegram.bind_first('111:other', api=Bot([]), wait_s=1, say=said.append), None)
json.dump(saved, open(telegram.PATH, 'w'))
ch = telegram.Channel(telegram.load(), api=Bot([[msg(4, 888, name='Ravi', text='who are you')],
                                                [msg(5, 888, name='Ravi', text='hello?'), msg(6, 777, text='status')]]))
first = ch.updates(timeout=0); second = ch.updates(timeout=0)
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
sys.exit(fail)
