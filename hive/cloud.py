"""hive cloud: move this project's Hive to a cloud machine and run it from the owner's phone.

  hive cloud --to user@host [--with-login] [--no-start]   copy the project and Hive there, start the listener there
  hive cloud pull --from user@host                        bring the result branches (hive/...) back here

What goes over (by SSH): the current branch of this repository (a git bundle, so history but no unsaved files), Hive
itself (pip install from GitHub), the owner's rulings for this project, the Telegram link and the backup-model settings.
The Claude login goes only with --with-login: otherwise run `claude` once on the machine to log in there.
Never sent: .env files, keys, node_modules (dependencies are installed fresh there), anything not committed.
For tests and mounted disks, --to may also be a local folder."""
import json, os, shlex, shutil, subprocess, tempfile, time

from . import access, memory, telegram

Q = shlex.quote   # every path in a shell command is quoted: owners' paths have spaces
REMOTE_HOME = 'hive-cloud'   # relative to the remote home folder (scp and ssh both start there; '~' is not expanded)

class Target:
    """Where Hive goes: user@host over SSH (with its own key, for a machine `hive cloud --new` made), or a local folder
    (tests, a mounted disk)."""
    def __init__(self, to, key=None):
        self.local = os.path.isabs(to) or to.startswith('.') or (':' not in to and '@' not in to)
        # forward slashes for a local folder: the shell dropped Windows backslashes from its path
        self.to = os.path.abspath(to).replace(os.sep, '/') if self.local else to
        # ConnectTimeout: a machine still booting can swallow the first connection, and without it one ssh waited 9
        # minutes while the machine sat ready (Gate 111); now it fails in 20 seconds and the wait tries again
        self.opts = ['-o', 'BatchMode=yes', '-o', 'ConnectTimeout=20'] + \
                    (['-i', key, '-o', 'StrictHostKeyChecking=accept-new'] if key else [])

    def run(self, cmd, check=True):
        full = ['sh', '-c', cmd] if self.local else ['ssh'] + self.opts + [self.to, cmd]
        p = subprocess.run(full, capture_output=True, text=True)
        if check and p.returncode != 0:
            raise RuntimeError(f'on {self.to}: {cmd}\n{p.stderr.strip()[:400]}')
        return p

    def put(self, src, dst):
        if self.local:
            os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(src, dst)
        else:
            self.run(f'mkdir -p {shlex.quote(os.path.dirname(dst))}')
            subprocess.run(['scp', '-q'] + self.opts + [src, f'{self.to}:{dst}'], check=True)

    def get(self, src, dst):
        """Copy a file back from there; False if it is not there."""
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if self.local:
            if not os.path.exists(src):
                return False
            shutil.copy2(src, dst); return True
        return subprocess.run(['scp', '-q'] + self.opts + [f'{self.to}:{src}', dst], capture_output=True).returncode == 0

    def home(self):
        return f'{self.to}/hive-cloud' if self.local else REMOTE_HOME

def _project(repo):
    return os.path.basename(os.path.abspath(repo)) or 'project'

def go(repo='.', to=None, with_login=False, start=True, say=print, key=None):
    repo = os.path.abspath(repo)
    if not to:
        say('Tell me where: hive cloud --to user@host'); return 2
    if subprocess.run(['git', '-C', repo, 'status', '--porcelain', '--untracked-files=no'], capture_output=True, text=True).stdout.strip():
        say('You have unsaved changes. Commit them first: only committed work goes to the cloud.'); return 3
    t = Target(to, key); name = _project(repo)
    proj = f'{t.home()}/{name}'
    branch = subprocess.run(['git', '-C', repo, 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True, text=True).stdout.strip()
    if branch == 'HEAD' or subprocess.run(['git', 'check-ref-format', '--branch', branch], capture_output=True).returncode:
        say('Check out a branch first: Hive moves a named branch, not a detached commit.'); return 3
    say(f"Moving {name} to {t.to}. Only committed work goes; .env files, keys and dependencies stay here.")
    t.run('true')   # reachable?
    tmp = tempfile.mkdtemp()
    bundle = os.path.join(tmp, 'project.bundle')
    subprocess.run(['git', '-C', repo, 'bundle', 'create', '-q', bundle, branch], check=True)
    t.put(bundle, f'{t.home()}/{name}.bundle')
    # first time: clone; again later: bring that branch up to date with this machine (git will not fetch into a branch
    # that is checked out, which a second real run hit). Hive's result branches (hive/...) there are left alone.
    # the folder and branch names are his, so each is quoted (the audit, Nov 15: a name with ; or $( ) ran as a command)
    n, b, nb = Q(name), Q(branch), Q(name + '.bundle')
    t.run(f'mkdir -p {Q(t.home())} && cd {Q(t.home())} && if test -d {n}/.git; then git -C {n} fetch -q {Q("../" + name + ".bundle")} '
          f'{b} && git -C {n} checkout -q {b} && git -C {n} reset -q --hard FETCH_HEAD; else '
          f'git clone -q -b {b} {nb} {n}; fi && rm -f {nb}')
    # Hive itself, from GitHub, in its own Python environment there: current Ubuntu refuses `pip install --user` into
    # the system Python (PEP 668), which the first real EC2 test hit. A local target shares this machine's Hive.
    py = 'python3'
    if not t.local:
        py = '"$HOME/hive-cloud/venv/bin/python"'
        say('  Installing Hive there (its own Python environment)...')
        t.run(f'mkdir -p {t.home()} && (test -x {t.home()}/venv/bin/python || python3 -m venv {t.home()}/venv)')
        p = t.run(f'{py} -m pip install -q --upgrade pytest git+https://github.com/suryanshranjan/hive', check=False)
        if p.returncode != 0:
            say(f'  Could not install Hive there: {p.stderr.strip()[-300:]}'); return 4
    # the owner's context: rulings for this project, the Telegram link, the backup model (never in the repository)
    hive_dir = os.path.join(os.path.expanduser('~'), '.hive')
    dst_hive = f'{t.home()}/.hive' if t.local else '.hive'
    rules = os.path.join(memory.DIR, memory.project_key(repo) + '.json')
    sent = []
    from . import brief, register
    try:   # his clock goes too: a UTC cloud machine sent "Good evening" and the morning brief at his 5 am (Nov 15)
        if register._load().get('utc_offset') is None:
            register.remember_timezone()
    except OSError:
        pass
    for src, dst in ((rules, f'{dst_hive}/rules/{os.path.basename(rules)}'), (telegram.PATH, f'{dst_hive}/telegram.json'),
                     (register.PATH, f'{dst_hive}/profile.json'),   # his time zone, team, technical or not
                     (brief.PATH, f'{dst_hive}/brief.json'),   # today's brief already sent: not again on arrival
                     (os.path.join(hive_dir, 'llm.json'), f'{dst_hive}/llm.json'),
                     (telegram.CONVERSATION, f'{dst_hive}/conversation.json'),
                     (memory._names(), f'{dst_hive}/names.json'),   # the thread goes too: "yes" stays in context
                     (memory._notes_path(repo), f'{dst_hive}/rules/{os.path.basename(memory._notes_path(repo))}'),   # his business
                     (os.path.join(hive_dir, 'resume.json'), f'{dst_hive}/resume.json'),   # work to pick up there ("I'm sleepy")
                     (access._path(repo), f'{dst_hive}/access/{os.path.basename(access._path(repo))}')):   # his data, read-only
        if os.path.exists(src):
            t.put(src, dst); sent.append(os.path.basename(src))
    from . import vault   # the files above may be encrypted (hive/vault.py): their key goes too, or he is told
    if vault.where() in ('file', 'keychain') and vault._key(create=False):
        kf = os.path.join(tmp, 'vault.key'); open(kf, 'wb').write(vault._key(create=False))
        t.put(kf, f'{dst_hive}/vault.key'); os.remove(kf); sent.append('the key to his secrets')
    elif vault.where() == 'env':
        say('  His secrets are encrypted with HIVE_MASTER_KEY: set the same HIVE_MASTER_KEY on that machine.')
    if with_login:
        cred = os.path.join(os.path.expanduser('~'), '.claude', '.credentials.json')
        if os.path.exists(cred):
            t.put(cred, (f'{t.home()}/.claude' if t.local else '.claude') + '/.credentials.json'); sent.append('Claude login')
            t.run('chmod 700 .claude 2>/dev/null; chmod 600 .claude/.credentials.json 2>/dev/null || true', check=False)
    t.run(f'chmod -R go-rwx {Q(dst_hive)} 2>/dev/null || true', check=False)
    # dependencies, installed fresh there
    for pj in subprocess.run(['git', '-C', repo, 'ls-files', 'package-lock.json', '*/package-lock.json'],
                             capture_output=True, text=True).stdout.split():
        d = os.path.dirname(pj) or '.'
        say(f'  Installing dependencies in {d} there...')
        t.run(f'cd {Q(proj + "/" + d)} && npm ci --silent >/dev/null 2>&1 || npm install --silent >/dev/null 2>&1', check=False)
    if subprocess.run(['git', '-C', repo, 'ls-files', 'requirements.txt'], capture_output=True, text=True).stdout.strip():
        say('  Installing the Python requirements there...')
        p = t.run(f'cd {Q(proj)} && {py} -m pip install -q -r requirements.txt', check=False)
        if p.returncode != 0:
            say(f'  The requirements did not install there: {p.stderr.strip()[-300:]}')
    json.dump({'to': t.to, 'project': proj, 'branch': branch, 'key': key}, open(os.path.join(hive_dir if os.path.isdir(hive_dir) else tmp,
                                                                                  'cloud.json'), 'w'))
    say(f"  Copied: the project ({branch}), " + (', '.join(sent) if sent else 'no Hive settings yet') + '.')
    # can builders work there? They run on Claude Code: check it answers (the owner: "else how will development continue")
    ready = None
    if not t.local:
        p = t.run('timeout 120 claude -p "Reply with the single word OK" 2>&1 | tail -1', check=False)
        ready = 'OK' in (p.stdout or '').upper()
        say('  Builders are ready there: Claude answers.' if ready else
            "  Builders can't work there yet: Claude isn't logged in on that machine. Run `claude` there once to log in, "
            "or move again with the login.")
    elif not with_login:
        say("  The Claude login did not go over. On that machine, run `claude` once to log in (or rerun with --with-login).")
    if start:
        t.run(f'cd {Q(proj)} && (nohup {py} -m hive listen > {Q(t.home()) if t.local else "$HOME/hive-cloud"}/listen.log 2>&1 &)',
              check=False)
        say("  Hive is listening there.")
        _stop_local_listener(say)
        cfg = telegram.load()
        if cfg:
            try:
                telegram.Channel(cfg).send(
                    f"☁️ <b>I'm now running in the cloud</b>, with your project <b>{telegram.esc(name)}</b>. Your computer "
                    "can be off. " + ("Builders are ready there. " if ready else
                                      "I can talk with you there, but builders can't work there until Claude is logged in "
                                      "on that machine. " if ready is False else '') +
                    "Message me any time: \"build: ...\", a change of mind, or \"status\".", html=True)
            except Exception:
                pass
    say(f"Done. Bring results back any time with: hive cloud pull --from {t.to}")
    return 0

def _stop_local_listener(say=print):
    """Only one Hive may read his chat: the listener on this computer stands down once the cloud copy is listening."""
    from .assistant import PIDFILE
    try:
        pid = int(open(PIDFILE).read().strip())
    except (OSError, ValueError):
        return
    if pid == os.getpid():
        return   # this is the listener itself (a move from the phone): it stands down on its own
    try:
        import signal
        os.kill(pid, signal.SIGTERM)
        say("  Stopped the listener on this computer: Hive now reads your Telegram in the cloud.")
    except (OSError, ProcessLookupError):
        pass
    try:
        os.remove(PIDFILE)
    except OSError:
        pass

def _remote_heads(repo, url, env):
    """{branch: commit} of every branch on the cloud copy."""
    p = subprocess.run(['git', '-C', repo, 'ls-remote', '--heads', url], capture_output=True, text=True, env=env)
    out = {}
    for line in p.stdout.splitlines():
        sha, _, ref = line.partition('\t')
        if ref.startswith('refs/heads/'):
            out[ref[len('refs/heads/'):]] = sha
    return out if p.returncode == 0 else None

def building(t):
    """True while a build is running on the cloud copy (deleting it then would lose the work in progress)."""
    if t.local:
        return False
    return bool(t.run("pgrep -f '[h]ive start' >/dev/null && echo yes || true", check=False).stdout.strip())

def pull(repo='.', frm=None, say=print, verify=False):
    """Bring everything done in the cloud to this computer: every branch (hive/... as your result branches, any other
    under hive-cloud/...), the build records, the rules and the conversation. With `verify`, check every branch arrived
    whole before anything may be deleted (the owner: no development may ever be lost). Returns 0 only when complete."""
    repo = os.path.abspath(repo)
    key = None
    cfg = os.path.join(os.path.expanduser('~'), '.hive', 'cloud.json')
    if os.path.exists(cfg):
        saved = json.load(open(cfg))
        if not frm or frm == saved.get('to'):
            frm, key = saved['to'], saved.get('key')
    if not frm:
        say('Tell me where from: hive cloud pull --from user@host'); return 2
    t = Target(frm, key); proj = f'{t.home()}/{_project(repo)}'
    url = proj if t.local else f'{t.to}:{proj}'
    env = dict(os.environ, GIT_SSH_COMMAND='ssh ' + ' '.join(shlex.quote(o) for o in Target(frm, key).opts)) if key else None
    heads = _remote_heads(repo, url, env)
    if heads is None:
        say('Could not reach the cloud copy to bring the work back.'); return 1
    # results as his hive/... branches; every other branch kept apart, never over his own
    p = subprocess.run(['git', '-C', repo, 'fetch', url, '+refs/heads/hive/*:refs/heads/hive/*',
                        '+refs/heads/*:refs/remotes/hive-cloud/*'], capture_output=True, text=True, env=env)
    if p.returncode != 0:
        say(f'Could not fetch: {p.stderr.strip()[:300]}'); return 1
    results = sorted(b for b in heads if b.startswith('hive/'))
    say(f"Brought back {len(results)} result branch(es)" + (': ' + ', '.join(results) if results else '') +
        (f"; {len(heads) - len(results)} other branch(es) under hive-cloud/..." if len(heads) > len(results) else '') + '.')
    # what he said there, and the records of every build made there
    src_hive = f'{t.home()}/.hive' if t.local else '.hive'
    rules = memory.project_key(repo) + '.json'
    back = [name for name, src, dst in (
        ('rules', f'{src_hive}/rules/{rules}', os.path.join(memory.DIR, rules)),
        ('conversation', f'{src_hive}/conversation.json', telegram.CONVERSATION),
        ('what he told me about his business', f'{src_hive}/rules/{memory.project_key(repo)}.notes.json',
         memory._notes_path(repo))) if t.get(src, dst)]
    runs_home = os.path.join(os.path.expanduser('~'), '.hive', 'runs-from-cloud', _project(repo))   # one copy, refreshed
    if t.local:
        src_runs = os.path.join(t.home(), '.hive', 'runs')
        if os.path.isdir(src_runs):
            shutil.copytree(src_runs, os.path.join(runs_home, 'runs'), dirs_exist_ok=True); back.append('build records')
    else:
        os.makedirs(runs_home, exist_ok=True)
        tar = subprocess.run(['ssh'] + t.opts + [t.to, 'test -d .hive/runs && tar czf - -C .hive runs || true'],
                             capture_output=True)
        if tar.returncode == 0 and tar.stdout:
            subprocess.run(['tar', 'xzf', '-', '-C', runs_home], input=tar.stdout, capture_output=True)
            back.append('build records')
    if back:
        say('  Also brought back: your ' + ', '.join(back) + '.')
    if not verify:
        return 0
    missing = []   # every branch there must now be here, at the same commit
    for b, sha in heads.items():
        local = f'refs/heads/{b}' if b.startswith('hive/') else f'refs/remotes/hive-cloud/{b}'
        got = subprocess.run(['git', '-C', repo, 'rev-parse', '--verify', '-q', local], capture_output=True, text=True).stdout.strip()
        if got != sha:
            missing.append(b)
    if missing:
        say("  These did NOT arrive whole: " + ', '.join(missing) + '. Nothing will be deleted.'); return 1
    say(f"  Checked: all {len(heads)} branch(es) are here, commit for commit.")
    return 0
