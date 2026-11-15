"""Builders in a container (the owner's choice, Nov 15: by default wherever Docker is there).

A builder is a coding agent running shell commands without asking. On his computer it could read anything he can:
~/.hive (his bot token, mail password, payment keys), his other projects, his SSH keys. In a container it sees only:
  /hive-run   the run folder (its clone, the shared upstream, the owner's questions and answers, the guard's cache)
  /opt/hive   Hive's own code, read-only
  ~/.claude, ~/.codex   a copy of its agent's login, made for this run and deleted after it
and its model key in the environment. Network stays open (the model's API, packages).

  HIVE_SANDBOX=auto     (default) in a container when Docker is running and his tests run there; else on this
                        computer, and he is told why once
  HIVE_SANDBOX=docker   in a container or not at all
  HIVE_SANDBOX=off      on this computer, as before

The image (deploy/builder/Dockerfile: Python, Node, git, pytest, Claude Code, Codex, Gemini) is built the first time,
which takes a few minutes. Before a build starts, his project's tests are run once inside it: a project whose tests
need something the image does not have builds on this computer instead, and he is told. A custom HIVE_WORKER_CMD is
his own and runs on this computer unless HIVE_SANDBOX_CUSTOM=1."""
import hashlib, os, shlex, shutil, subprocess, time

IMAGE = 'hive-builder:2'   # bump when deploy/builder/Dockerfile changes
RUN_DIR = '/hive-run'
HIVE_DIR = '/opt/hive'
HOME = '/home/hive'
HIVE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCKERFILE = os.path.join(HIVE_ROOT, 'deploy', 'builder', 'Dockerfile')

# what goes into the container's environment: model keys and the run's own settings, nothing else of his
MODEL_KEYS = ('ANTHROPIC_API_KEY', 'ANTHROPIC_BASE_URL', 'ANTHROPIC_MODEL', 'CLAUDE_CODE_USE_BEDROCK',
              'CLAUDE_CODE_USE_VERTEX', 'OPENAI_API_KEY', 'OPENAI_BASE_URL', 'CODEX_API_KEY', 'GEMINI_API_KEY',
              'GOOGLE_API_KEY', 'GOOGLE_CLOUD_PROJECT')
PASS_PREFIXES = ('HIVE_',)
NEVER = ('HIVE_MASTER_KEY', 'HIVE_FAST_KEY', 'HIVE_PAIR_CODE', 'HIVE_RUN', 'HIVE_GUARD_CACHE', 'HIVE_DOCKER',
         'HIVE_SANDBOX', 'HIVE_SANDBOX_CUSTOM', 'HIVE_WORKER_CMD')
LOGINS = {'claude': [('.claude', '.credentials.json'), ('', '.claude.json')], 'codex': [('.codex', 'auth.json')],
          'gemini': [('.gemini', 'oauth_creds.json'), ('.gemini', 'settings.json')]}

def mode():
    m = (os.environ.get('HIVE_SANDBOX') or 'auto').strip().lower()
    return {'0': 'off', 'no': 'off', 'false': 'off', '1': 'docker', 'on': 'docker', 'yes': 'docker'}.get(m, m)

def docker():
    return shlex.split(os.environ.get('HIVE_DOCKER', 'docker'))

def _docker(args, timeout=60):
    from . import run as _run
    exe = docker()
    if os.name == 'nt' and exe and not os.path.dirname(exe[0]):
        exe[0] = shutil.which(exe[0]) or exe[0]
    try:
        return _run.run(exe + args, timeout)
    except OSError:
        return None

def running():
    """True when Docker is installed and its engine answers."""
    p = _docker(['info', '--format', '{{.ServerVersion}}'], timeout=30)
    return bool(p and p.returncode == 0 and p.stdout.strip())

def ensure_image(say=print):
    """The builders' image, built once (a few minutes). True when it is there."""
    p = _docker(['image', 'inspect', IMAGE], timeout=30)
    if p and p.returncode == 0:
        return True
    say('Preparing the builders\' sandbox (a container image, once; about 3-5 minutes)...')
    p = _docker(['build', '-q', '-t', IMAGE, '-f', DOCKERFILE, os.path.dirname(DOCKERFILE)], timeout=1800)
    return bool(p and p.returncode == 0)

def host_path(path):
    """A folder on this computer as Docker's -v wants it (forward slashes; Docker Desktop takes C:/...)."""
    return os.path.abspath(path).replace('\\', '/')

def inside(text, run):
    """Text written for this computer (a prompt, a path) as the builder sees it in the container."""
    import re
    run = os.path.abspath(run)
    for form in sorted({run, run.replace('\\', '/'), run.replace('/', '\\')}, key=len, reverse=True):
        # the run folder and the path after it, in the container's slashes (C:\...\run\work\w1 -> /hive-run/work/w1)
        text = re.sub(re.escape(form) + r'''([\\/][^\s`'"]*)?''',
                      lambda m: RUN_DIR + (m.group(1) or '').replace('\\', '/'), text)
    from . import PY
    return text.replace(f'{PY} -m hive', 'python3 -m hive')

def name(run, me):
    return f"hive-{hashlib.sha1(os.path.abspath(run).encode()).hexdigest()[:10]}-{me}"

def env_for(base, me):
    """The container's environment: model keys and Hive's run settings, never his secrets or this computer's paths."""
    out = {k: v for k, v in base.items() if (k in MODEL_KEYS or k.startswith(PASS_PREFIXES)) and k not in NEVER}
    out.update(HIVE_WORKER=me, HIVE_RUN=RUN_DIR, HIVE_GUARD_CACHE=f'{RUN_DIR}/guard_cache', PYTHONIOENCODING='utf-8',
               PYTHONPATH=HIVE_DIR)
    return out

def logins(run, agent, home=None):
    """A copy of the agent's login for this run (it may refresh its token there). Returns [(on this computer, in the
    container)]: its folder (~/.claude, ~/.codex) with only the login in it, and a file at HOME (~/.claude.json)."""
    home = home or os.path.expanduser('~')
    out = []
    for sub, f in LOGINS.get(agent, []):
        src = os.path.join(home, sub, f)
        if not os.path.isfile(src):
            continue
        dst_dir = os.path.join(run, '.logins', agent, sub)
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, f); shutil.copy2(src, dst)
        try:
            os.chmod(dst, 0o600)
        except OSError:
            pass
        if not sub:
            out.append((dst, f'{HOME}/{f}'))
    # a folder is mounted whole (the agent writes its own state beside the login; a single mounted file left the folder
    # to Docker, owned by root, and Codex could not start), a file at HOME on its own
    for sub in sorted({s for s, _ in LOGINS.get(agent, []) if s}):
        d = os.path.join(run, '.logins', agent, sub)
        if os.path.isdir(d):
            out.append((d, f'{HOME}/{sub}'))
    return out

def forget_logins(run):
    shutil.rmtree(os.path.join(run, '.logins'), ignore_errors=True)

def _git_setup(work):
    """Shell lines that set the container's own git up: the clone's upstream (a path on this computer) is
    /hive-run/up.git, and the run folder, which Docker shows as another user's, is trusted. In the container's global
    settings, not the environment: git drops GIT_CONFIG_* when it serves a local upstream, which then refused it."""
    url = subprocess.run(['git', '-C', work, 'remote', 'get-url', 'origin'], capture_output=True, text=True).stdout.strip()
    lines = ["git config --global --add safe.directory '*'", 'git config --global core.autocrlf false']
    if url:
        lines.append(f'git config --global {shlex.quote(f"url.{RUN_DIR}/up.git.insteadOf")} {shlex.quote(url)}')
    return ' && '.join(lines)

def command(run, me, cmd, base_env, agent='claude', workdir=None):
    """The docker command that runs `cmd` (a builder's command line) for builder `me`, prompt on stdin."""
    work = workdir or os.path.join(run, 'work', me)
    rel = os.path.relpath(work, run).replace('\\', '/')
    args = ['run', '--rm', '-i', '--name', name(run, me), '--network', 'bridge',
            '-v', f'{host_path(run)}:{RUN_DIR}', '-v', f'{host_path(HIVE_ROOT)}:{HIVE_DIR}:ro',
            '-w', f'{RUN_DIR}/{rel}']
    if os.name != 'nt' and hasattr(os, 'getuid'):   # Linux: files the builder writes stay his
        args += ['--user', f'{os.getuid()}:{os.getgid()}', '-e', f'HOME={HOME}']
    for src, dst in logins(run, agent):
        args += ['-v', f'{host_path(src)}:{dst}']
    env = env_for(base_env, me)
    for k in sorted(env):
        args += ['-e', k]   # values go through the environment of the docker command, never its command line
    return docker() + args + [IMAGE, 'sh', '-c', f'{_git_setup(work)} && {cmd}'], env

def popen_env(base_env, env):
    """The environment for the `docker run` process itself: what it passes in, plus what docker needs to run."""
    keep = {k: v for k, v in base_env.items() if k.upper() in ('PATH', 'SYSTEMROOT', 'TEMP', 'TMP', 'USERPROFILE',
                                                               'HOME', 'APPDATA', 'LOCALAPPDATA', 'PROGRAMDATA',
                                                               'DOCKER_HOST', 'DOCKER_CONFIG', 'DOCKER_CONTEXT',
                                                               'DOCKER_CERT_PATH', 'DOCKER_TLS_VERIFY')}
    return dict(keep, **env)

def kill(run, me):
    _docker(['rm', '-f', name(run, me)], timeout=60)

def preflight(run, test_cmd, junit, base_env):
    """Run the project's tests once in the sandbox, in builder w1's clone. (ok, why)."""
    work = os.path.join(run, 'work', 'w1')
    xml = os.path.join(work, junit)
    if os.path.exists(xml):
        os.remove(xml)
    cmd, env = command(run, 'preflight', f'mkdir -p "$(dirname {shlex.quote(junit)})" && {test_cmd}', base_env,
                       agent='none', workdir=work)
    from . import run as _run
    p = _run.run(cmd, 900, env=popen_env(base_env, env), stdin=subprocess.DEVNULL)
    ok = os.path.exists(xml)
    if os.path.exists(xml):
        os.remove(xml)
    if p is None:
        return False, 'its tests ran past 15 minutes in the sandbox'
    return ok, '' if ok else f"its tests don't run in the sandbox ({(p.stderr or p.stdout).strip()[-160:]})"

def decide(run, test_cmd, junit, base_env, say=print, custom=False):
    """Whether this run's builders go in containers: True, or False with the reason said once. Raises SystemExit
    under HIVE_SANDBOX=docker when they can't."""
    m = mode()
    if m == 'off':
        return False
    def no(why):
        if m == 'docker':
            raise SystemExit(f"The builders' sandbox is required (HIVE_SANDBOX=docker), but {why}.")
        told = os.path.join(os.path.expanduser('~'), '.hive', 'sandbox_told')
        try:
            before = open(told, encoding='utf-8').read()
        except OSError:
            before = ''
        if before != why:   # said once for each reason, not before every build
            say(f"Builders run on this computer, not in a sandbox: {why}.")
            try:
                os.makedirs(os.path.dirname(told), exist_ok=True); open(told, 'w', encoding='utf-8').write(why)
            except OSError:
                pass
        return False
    if custom and os.environ.get('HIVE_SANDBOX_CUSTOM') != '1':
        return False   # his own builder command: his to place
    if not running():
        if m != 'docker' and (os.path.exists('/.dockerenv') or os.environ.get('HIVE_HOST') == 'render'):
            return False   # Hive itself is in a container on a machine of its own (Render, a cloud box): nothing to say
        return no("Docker isn't running here (start Docker Desktop, or install Docker, for the safer way)")
    if not ensure_image(say):
        return no("the sandbox image could not be built")
    ok, why = preflight(run, test_cmd, junit, base_env)
    return True if ok else no(why)
