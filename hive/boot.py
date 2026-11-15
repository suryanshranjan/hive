"""hive boot: start Hive on a host with no one at a keyboard (Render's "Deploy" button, from a phone).

The founder fills a form on his phone; the host passes it in as settings (environment variables), and this turns them
into Hive's own files on the host's disk, then listens on Telegram:
  TELEGRAM_BOT_TOKEN   required: his bot, from @BotFather. The first private chat that writes to it becomes his.
  ANTHROPIC_API_KEY    the builders (Claude Code) and Hive's fast replies run on it.
  HIVE_FAST_PROVIDER, HIVE_FAST_KEY, HIVE_FAST_MODEL, HIVE_FAST_BASE_URL
                       optional: fast replies from another provider (any OpenAI-style API), as `hive llm api` would set.
  GITHUB_TOKEN, HIVE_REPO
                       optional: his product on GitHub ("owner/name" or its address), cloned once. Without them Hive
                       starts an empty project ("I want to build something new").
Everything lives under HOME, which the host keeps on a disk, so a restart or a redeploy keeps his chat, his rules and
his work. Secrets are written owner-only and never into the project."""
import json, os, re, subprocess, sys

from . import explain, telegram

def _private(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(text)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass

def _git(*args, cwd=None):
    return subprocess.run(['git'] + list(args), cwd=cwd, capture_output=True, text=True)

def repo_url(spec):
    """'owner/name', 'github.com/owner/name' or a full address, as an https clone address (no secret in it)."""
    spec = (spec or '').strip().rstrip('/')
    if not spec:
        return None
    if re.fullmatch(r'[\w.-]+/[\w.-]+', spec):
        spec = 'github.com/' + spec
    spec = re.sub(r'^(https?://)?', 'https://', spec)
    return spec if spec.endswith('.git') else spec + '.git'

def configure(env=None, home=None):
    """Turn the host's settings into Hive's files. Returns the project folder to listen in. Never talks to Telegram."""
    env = dict(os.environ if env is None else env)
    home = home or os.path.expanduser('~')
    hive = os.path.join(home, '.hive')
    token = (env.get('TELEGRAM_BOT_TOKEN') or '').strip()
    if not token:
        raise SystemExit('TELEGRAM_BOT_TOKEN is not set: make a bot with @BotFather and paste its token in the host\'s form.')
    tg = os.path.join(hive, 'telegram.json')
    try:
        old = json.load(open(tg))
    except (OSError, ValueError):
        old = {}
    if old.get('token') != token:   # a new bot: whoever writes to it first is its owner (telegram.bind_first)
        _private(tg, json.dumps({'token': token}))
    if env.get('HIVE_FAST_KEY'):
        fast = {'provider': env.get('HIVE_FAST_PROVIDER') or 'openai', 'api_key': env['HIVE_FAST_KEY']}
        for k, v in (('model', env.get('HIVE_FAST_MODEL')), ('base_url', env.get('HIVE_FAST_BASE_URL'))):
            if v:
                fast[k] = v
        _private(os.path.join(hive, 'fast.json'), json.dumps(fast))
    claude = os.path.join(home, '.claude.json')   # Claude Code runs headless on the API key: no first-run questions
    if env.get('ANTHROPIC_API_KEY') and not os.path.exists(claude):
        _private(claude, json.dumps({'hasCompletedOnboarding': True}))
    gitcfg = ['-c', f'core.hooksPath={os.devnull}']
    os.environ['HOME'] = home   # git reads its global settings from HOME
    for k, v in (('user.name', 'Hive'), ('user.email', 'hive@localhost'), ('init.defaultBranch', 'main')):
        if _git('config', '--global', '--get', k).returncode != 0:
            _git('config', '--global', k, v)
    if env.get('GITHUB_TOKEN'):   # the token goes to git's own store on the disk, never into an address or the project
        _git('config', '--global', 'credential.helper', 'store')
        _private(os.path.join(home, '.git-credentials'), f"https://x-access-token:{env['GITHUB_TOKEN']}@github.com\n")
    project = os.path.join(home, 'project')
    url = repo_url(env.get('HIVE_REPO'))
    if not os.path.isdir(os.path.join(project, '.git')):
        if url:
            r = _git('clone', url, project)
            if r.returncode != 0:
                raise SystemExit(f'Could not get {url} ({r.stderr.strip()[-200:]}). Check HIVE_REPO and GITHUB_TOKEN.')
        else:
            os.makedirs(project, exist_ok=True)
            _git('init', '-q', cwd=project)
            open(os.path.join(project, 'README.md'), 'w').write('# A new project\n\nStarted with Hive.\n')
            _git(*gitcfg, 'add', 'README.md', cwd=project); _git(*gitcfg, 'commit', '-q', '-m', 'Start', cwd=project)
    return project

def main(env=None, home=None, api=None, listen=True):
    project = configure(env, home)
    cfg = json.load(open(os.path.join(home or os.path.expanduser('~'), '.hive', 'telegram.json')))
    telegram.PATH = os.path.join(home or os.path.expanduser('~'), '.hive', 'telegram.json')
    if not cfg.get('chat_id') and not telegram.bind_first(cfg['token'], api=api):
        return 1
    print(f'Hive is up: project {project}; fast replies {"on" if explain.fast_on() else "off"}.', flush=True)
    if not listen:
        return 0
    os.chdir(project)
    from .__main__ import main as hive
    return hive(['listen'])

if __name__ == '__main__':
    sys.exit(main())
