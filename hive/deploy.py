"""Where his product lives, his choice: Vercel, Netlify, Railway, Azure, Fly, Render, or his own command (the owner:
"if he wants to connect any cloud, Vercel, Azure, Railway, it's up to him").

Two things Hive does with it, never more:
- a preview: the latest build at its own address, a link he taps on his phone and uses; his live product is untouched;
- going live: only his own main version, only after his engineer has merged the build into it, only when he says so,
  and only with every test passing. Hive never puts an unmerged build live (the limit Jarvis states).

The host's own tool does the work, logged in once on this computer by him or his engineer (`vercel login`, ...).
Set up once per project: `hive deploy setup <host>`, or on the phone ("connect Vercel")."""
import json, os, re, shutil, subprocess, tempfile

DIR = os.path.join(os.path.expanduser('~'), '.hive', 'deploy')

HOSTS = {   # name: (tool, preview command or None, live command, how to log in)
    'vercel': ('vercel', 'vercel deploy --yes', 'vercel deploy --prod --yes', 'vercel login'),
    'netlify': ('netlify', 'netlify deploy --json', 'netlify deploy --prod --json', 'netlify login'),
    'railway': ('railway', None, 'railway up --detach', 'railway login'),
    'azure': ('swa', 'swa deploy --env preview', 'swa deploy --env production', 'swa login'),
    'fly': ('fly', None, 'fly deploy', 'fly auth login'),
    'render': (None, None, None, 'a deploy hook address from Render (Settings, Deploy Hook)'),
}
LINKS = ('.vercel', '.netlify', '.railway', '.azure', 'staticwebapp.config.json', 'swa-cli.config.json', 'fly.toml')

def _key(repo):
    from . import memory
    return memory.project_key(repo)

def title(repo):
    """His host, as he would say it: "Vercel", "Netlify", or "your site" for his own commands."""
    h = config(repo).get('host', '')
    return {'custom': 'your site', 'fly': 'Fly'}.get(h, h.title() or 'your site')

def config(repo):
    try:
        return json.load(open(os.path.join(DIR, _key(repo) + '.json')))
    except (OSError, ValueError):
        return {}

def setup(repo, host, preview=None, live=None, hook=None):
    """Remember where his product lives. host: one of HOSTS, or 'custom' with his own commands. Returns the config."""
    host = host.lower().strip()
    if host not in HOSTS and host != 'custom':
        raise ValueError(f"I don't know {host!r}. Choose one of: {', '.join(HOSTS)}, or custom with your own commands.")
    cfg = {'host': host}
    if host == 'custom':
        cfg.update(preview=preview, live=live)
    elif host == 'render':
        cfg.update(live=f'curl -fsS -X POST "{hook}"' if hook else None)
    else:
        cfg.update(preview=preview or HOSTS[host][1], live=live or HOSTS[host][2])
    os.makedirs(DIR, exist_ok=True)
    json.dump(cfg, open(os.path.join(DIR, _key(repo) + '.json'), 'w'), indent=1)
    return cfg

def ready(repo):
    """('ok', '') or (problem, what to do): set up, and the host's tool installed on this computer."""
    cfg = config(repo)
    if not cfg:
        return 'none', ("Your product isn't connected to where it lives yet. Tell me where (Vercel, Netlify, Railway, Azure, "
                        "Fly, Render, or your own way), or your engineer runs: hive deploy setup <host>.")
    tool = HOSTS.get(cfg['host'], (None,))[0]
    if tool and not shutil.which(tool):
        return 'tool', (f"{cfg['host'].title()}'s tool isn't on this computer. Your engineer installs it once and logs in "
                        f"({HOSTS[cfg['host']][3]}).")
    return 'ok', ''

def _copy(repo, branch):
    """A clean copy of one branch, with the host's project link files (kept out of git) carried over."""
    work = tempfile.mkdtemp(prefix='hive_deploy_')
    code = os.path.join(work, 'code')
    sha = subprocess.run(['git', '-C', repo, 'rev-parse', '-q', '--verify', branch + '^{commit}'], capture_output=True,
                         text=True).stdout.strip()   # a branch here, or his remote's main (origin/main)
    ok = sha and subprocess.run(['git', 'clone', '-q', '--no-checkout', os.path.abspath(repo), code], capture_output=True).returncode == 0 \
        and subprocess.run(['git', '-C', code, 'checkout', '-q', sha], capture_output=True).returncode == 0
    if not ok:
        shutil.rmtree(work, ignore_errors=True)
        return None, None
    for name in LINKS:
        src = os.path.join(repo, name)
        if os.path.exists(src) and not os.path.exists(os.path.join(code, name)):
            (shutil.copytree if os.path.isdir(src) else shutil.copy)(src, os.path.join(code, name))
    return work, code

def _run(cmd, cwd, timeout=900):   # the host's tool (tests replace this)
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace',
                          timeout=timeout)

def _url(out):
    try:   # netlify --json
        j = json.loads(out)
        for k in ('deploy_url', 'url', 'site_url'):
            if j.get(k):
                return j[k]
    except (ValueError, AttributeError):
        pass
    found = re.findall(r'https://[^\s"\'<>]+', out or '')
    return found[-1].rstrip('.,)') if found else None

def preview(repo, branch):
    """Put this branch at its own address. {'ok', 'url', 'why'}; why: 'none', 'tool', 'no_preview', 'failed'."""
    state, why = ready(repo)
    if state != 'ok':
        return {'ok': False, 'why': state, 'say': why}
    cfg = config(repo)
    if not cfg.get('preview'):
        return {'ok': False, 'why': 'no_preview', 'say': f"{cfg['host'].title()} has no separate preview address the way "
                "I set it up; screenshots will have to do until it goes live."}
    work, code = _copy(repo, branch)
    if not code:
        return {'ok': False, 'why': 'failed', 'say': "I couldn't find that build to put up."}
    try:
        p = _run(cfg['preview'], code)
        url = _url(p.stdout + '\n' + p.stderr) if p.returncode == 0 else None
        return {'ok': bool(url), 'url': url, 'why': None if url else 'failed',
                'say': '' if url else f"{cfg['host'].title()} refused the preview (for your engineer: "
                                      f"{(p.stderr or p.stdout).strip()[-200:]})"}
    finally:
        shutil.rmtree(work, ignore_errors=True)

def merged(repo, branch, main='main'):
    """Is this build in his main version (his engineer merged it), here or on his remote's main?"""
    subprocess.run(['git', '-C', repo, 'fetch', '-q', 'origin'], capture_output=True)
    for m in (f'origin/{main}', main):
        if subprocess.run(['git', '-C', repo, 'rev-parse', '-q', '--verify', m], capture_output=True).returncode == 0 and \
           subprocess.run(['git', '-C', repo, 'merge-base', '--is-ancestor', branch, m], capture_output=True).returncode == 0:
            return m
    return None

def live(repo, main_ref, test_cmd=None):
    """Put his main version live, after its tests pass. {'ok', 'url', 'why', 'say'}."""
    state, why = ready(repo)
    if state != 'ok':
        return {'ok': False, 'why': state, 'say': why}
    cfg = config(repo)
    if not cfg.get('live'):
        return {'ok': False, 'why': 'none', 'say': "I don't have a way to put it live yet (for Render: its deploy hook address)."}
    work, code = _copy(repo, main_ref)
    if not code:
        return {'ok': False, 'why': 'failed', 'say': "I couldn't get a clean copy of your main version."}
    try:
        if test_cmd:
            from .start import run_tests
            res = run_tests(code, test_cmd)
            if not res or not all(res.values()):
                return {'ok': False, 'why': 'tests', 'say': f"{sum(1 for v in res.values() if not v) if res else 'The'} "
                        "tests fail on your main version, so it stays as it is. Your engineer should look first."}
        p = _run(cfg['live'], code)
        if p.returncode:
            return {'ok': False, 'why': 'failed', 'say': f"{cfg['host'].title()} refused it (for your engineer: "
                    f"{(p.stderr or p.stdout).strip()[-200:]}). Nothing changed on your live product."}
        url = _url(p.stdout + '\n' + p.stderr)
        sha = subprocess.run(['git', '-C', code, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
        cfg.setdefault('history', []).append({'t': __import__('time').time(), 'sha': sha, 'url': url})   # for undo
        json.dump(cfg, open(os.path.join(DIR, _key(repo) + '.json'), 'w'), indent=1)
        return {'ok': True, 'url': url, 'why': None, 'say': ''}
    finally:
        shutil.rmtree(work, ignore_errors=True)

def note_before(repo, main_ref):
    """The first time Hive puts his product live: remember his main version from just before the merge as what was
    live, so "undo that" has somewhere to go back to (his main is what his host was showing)."""
    cfg = config(repo)
    if cfg.get('history'):
        return False
    sha = subprocess.run(['git', '-C', repo, 'rev-parse', '-q', '--verify', f'{main_ref}^1'], capture_output=True,
                         text=True).stdout.strip()
    if not sha:
        return False
    cfg['history'] = [{'t': 0, 'sha': sha, 'url': None, 'assumed': True}]
    json.dump(cfg, open(os.path.join(DIR, _key(repo) + '.json'), 'w'), indent=1)
    return True

def back(repo):
    """Put live the version that was live before the last one Hive put live (undo). {'ok', 'url', 'say', 'when'}"""
    h = config(repo).get('history') or []
    if len(h) < 2:
        return {'ok': False, 'say': "I've no earlier version of yours that I put live, so I can't take it back from here; "
                "your host can (on Vercel: Deployments, then Promote the previous one)."}
    prev = h[-2]
    r = live(repo, prev['sha'])   # it passed its tests when it went live
    if r['ok']:   # the restored version is the current one again
        cfg = config(repo); cfg['history'] = h[:-1]
        json.dump(cfg, open(os.path.join(DIR, _key(repo) + '.json'), 'w'), indent=1)
    return dict(r, when=prev['t'])
