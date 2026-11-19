"""hive cloud: move this project's Hive to a cloud machine and run it from the owner's phone.

  hive cloud --to user@host [--with-login] [--no-start]   copy the project and Hive there, start the listener there
  hive cloud pull --from user@host                        bring the result branches (hive/...) back here

What goes over (by SSH): the current branch of this repository (a git bundle, so history but no unsaved files), Hive
itself (pip install from GitHub), the owner's rulings for this project, the Telegram link and the backup-model settings.
The Claude login goes only with --with-login: otherwise run `claude` once on the machine to log in there.
Never sent: .env files, keys, node_modules (dependencies are installed fresh there), anything not committed.
For tests and mounted disks, --to may also be a local folder."""
import json, os, shlex, shutil, subprocess, tempfile, time
from pathlib import Path

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
        from . import run as _run
        limit = _run.seconds('HIVE_REMOTE_SECONDS', 1800)   # a hung command there (a lost connection, an install
        p = _run.run(full, limit)                            # waiting on a prompt) no longer holds Hive for ever
        if p is None:
            raise RuntimeError(f'on {self.to}: {cmd}: stopped after {int(limit)} s with no answer (HIVE_REMOTE_SECONDS)')
        if check and p.returncode != 0:
            raise RuntimeError(f'on {self.to}: {cmd}\n{p.stderr.strip()[:400]}')
        return p

    def put(self, src, dst):
        if self.local:
            os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(src, dst)
        else:
            self.run(f'mkdir -p {shlex.quote(os.path.dirname(dst))}')
            subprocess.run(['scp', '-q'] + self.opts + [src, f'{self.to}:{dst}'], check=True, timeout=1800)

    def get(self, src, dst):
        """Copy a file back from there; False if it is not there."""
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if self.local:
            if not os.path.exists(src):
                return False
            shutil.copy2(src, dst); return True
        return subprocess.run(['scp', '-q'] + self.opts + [f'{self.to}:{src}', dst], capture_output=True, timeout=120).returncode == 0

    def home(self):
        return f'{self.to}/hive-cloud' if self.local else REMOTE_HOME

def _project(repo):
    return os.path.basename(os.path.abspath(repo)) or 'project'

def go(repo='.', to=None, with_login=False, start=True, say=print, key=None):
    from . import handoff, tools

    if not to:
        say('Tell me where: hive cloud --to user@host')
        return 2
    manifest = None
    try:
        manifest = handoff.freeze(repo)
        handoff.quiet_reader(repo, manifest)
        with tempfile.TemporaryDirectory(prefix='hive-handoff-') as temporary:
            rc = _go(repo, to, with_login, start, say, key, manifest, temporary)
    except tools.Refused as exc:
        say(str(exc))
        rc = 8
    finally:
        if manifest and not manifest.get('transferred'):
            handoff.release(manifest)
    return rc


def _go(repo, to, with_login, start, say, key, manifest, tmp):
    repo = os.path.abspath(repo)
    if not to:
        say('Tell me where: hive cloud --to user@host'); return 2
    if subprocess.run(['git', '-C', repo, 'status', '--porcelain', '--untracked-files=no'], capture_output=True, text=True).stdout.strip():
        say('You have unsaved changes. Commit them first: only committed work goes to the cloud.'); return 3
    t = Target(to, key); name = _project(repo)
    state_path = f'{t.home()}/.hive/hive.db' if t.local else '.hive/hive.db'
    exists = os.path.isfile(state_path) if t.local else t.run('test -s ' + Q(state_path), check=False).returncode == 0
    if exists:
        say('The destination already contains Hive memory. Pull and preserve that state before another handoff; I will not overwrite it.')
        return 8
    proj = f'{t.home()}/{name}'
    branch = subprocess.run(['git', '-C', repo, 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True, text=True).stdout.strip()
    if branch == 'HEAD' or subprocess.run(['git', 'check-ref-format', '--branch', branch], capture_output=True).returncode:
        say('Check out a branch first: Hive moves a named branch, not a detached commit.'); return 3
    say(f"Moving {name} to {t.to}. Only committed work goes; .env files, keys and dependencies stay here.")
    t.run('true')   # reachable?
    bundle = os.path.join(tmp, 'project.bundle')
    subprocess.run(['git', '-C', repo, 'bundle', 'create', '-q', bundle, '--branches'], check=True)
    t.put(bundle, f'{t.home()}/{name}.bundle')
    # first time: clone; again later: bring that branch up to date with this machine (git will not fetch into a branch
    # that is checked out, which a second real run hit). Hive's result branches (hive/...) there are left alone.
    # the folder and branch names are his, so each is quoted (the audit, Nov 15: a name with ; or $( ) ran as a command)
    n, b, nb = Q(name), Q(branch), Q(name + '.bundle')
    if t.run('test -e ' + Q(proj), check=False).returncode == 0:
        say('The destination project directory already exists. Preserve it and select an empty destination.')
        return 8
    t.run(f'mkdir -p {Q(t.home())} && cd {Q(t.home())} && git clone -q -b {b} {nb} {n} && rm -f {nb}')
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
        from . import store

        probe = f'from hive import store; assert len(store.MIGRATIONS) == {len(store.MIGRATIONS)}'
        if t.run(f'{py} -c ' + Q(probe), check=False).returncode:
            say('The destination needs the same Hive database schema before it can receive this handoff.')
            return 4
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
        if os.path.exists(src) and not (manifest['tasks'] and os.path.basename(src) == 'resume.json'):
            t.put(src, dst)   # said by what it is, so he knows his data's addresses went (encrypted: hive/vault.py)
            sent.append('his data sources (encrypted)' if src == access._path(repo) else os.path.basename(src))
    from . import store, vault
    snapshot = os.path.join(tmp, 'hive.db')
    import sqlite3
    dest = sqlite3.connect(snapshot)
    with store._LOCK:
        store.connect().backup(dest)
    memory_baseline = store.fingerprint(dest)
    dest.close()
    os.chmod(snapshot, 0o600)
    for secret_file in vault.files():
        rel = os.path.relpath(secret_file, hive_dir).replace('\\', '/')
        t.put(secret_file, f'{dst_hive}/{rel}')
    from . import handoff

    handoff.export(t, dst_hive, tmp, manifest, proj)
    sent.append('memory, pending actions and event state')
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
    # Install the database last. Keep the source fenced if acknowledgement of the transfer is lost.
    t.put(snapshot, f'{dst_hive}/incoming-{manifest["nonce"]}.db')
    location=Path(hive_dir)/'cloud.json'
    location.parent.mkdir(exist_ok=True,parents=True)
    checkpoint=location.with_suffix('.tmp')
    checkpoint.write_text(json.dumps(dict(to=t.to,project=proj,branch=branch,key=key,
                                          memory_baseline=memory_baseline,handoff=manifest)),encoding='utf-8')
    os.replace(checkpoint,location)
    manifest['transferred'] = True
    incoming = f'{dst_hive}/incoming-{manifest["nonce"]}.db'
    t.run(f'mv {Q(incoming)} {Q(dst_hive+"/hive.db")} && chmod -R go-rwx {Q(dst_hive)}')
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
        import sys

        launch_py = Q(Path(sys.executable).as_posix()) if t.local else py
        environment = f'env HOME={Q(t.home())} USERPROFILE={Q(t.home())} ' if t.local else ''
        startup = t.run(
            f'cd {Q(proj)} && (nohup {environment}{launch_py} -m hive listen > '
            f'{Q(t.home()) if t.local else "$HOME/hive-cloud"}/listen.log 2>&1 &)',
            check=False,
        )
        probe = f"from hive import handoff; raise SystemExit(not handoff.listener_ready('.', {manifest['nonce']!r}))"
        if (
            startup.returncode
            or t.run(f'cd {Q(proj)} && {environment}{launch_py} -c ' + Q(probe), check=False).returncode
        ):
            say(
                'The snapshot arrived. Destination listener startup is unconfirmed. Inspect listen.log or return ownership.'
            )
            return 8
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


def _pull_state(t, repo, src_hive, saved, cfg, say, conflict='', reconcile=None):
    """Return the authoritative DB, preserving both sides on any conflict.

    This is a single-owner handoff, not a merge. A changed local database must
    never be overwritten by an older cloud copy. Both snapshots remain private.
    """
    import sqlite3, secrets
    from . import store, vault
    folder = os.path.join(os.path.dirname(store.path()), 'returns', memory.project_key(repo))
    os.makedirs(folder, exist_ok=True)
    vault.private_permissions(folder, directory=True)
    snapshot = os.path.join(folder, 'cloud-' + secrets.token_hex(8) + '.db')
    source = f'{src_hive}/hive.db'
    if t.local:
        if not os.path.isfile(source):
            say('  The cloud memory database is missing. Nothing will be deleted.'); return False
        remote = sqlite3.connect(__import__('pathlib').Path(source).as_uri() + '?mode=ro', uri=True)
        dest = sqlite3.connect(snapshot)
        try:
            remote.backup(dest)
        finally:
            remote.close(); dest.close()
    else:
        remote_copy = f'{src_hive}/return-{secrets.token_hex(8)}.db'
        code = ('import sqlite3; '
                f's=sqlite3.connect("file:"+{source!r}+"?mode=ro",uri=True); '
                f'd=sqlite3.connect({remote_copy!r}); s.backup(d); d.close(); s.close()')
        result = t.run('umask 077; python3 -c ' + Q(code), check=False)
        if result.returncode or not t.get(remote_copy, snapshot):
            say('  Could not snapshot cloud memory. Nothing will be deleted.'); return False
        t.run('rm -f ' + Q(remote_copy), check=False)
    vault.private_permissions(snapshot)
    remote = sqlite3.connect(snapshot)
    try:
        if remote.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
            say('  Cloud memory failed its integrity check. Nothing will be deleted.'); return False
        if remote.execute('SELECT max(v) FROM schema_version').fetchone()[0] != len(store.MIGRATIONS):
            say('  Cloud memory has a different schema. Both copies were kept.'); return False
        if conflict:
            say(conflict + ' Both snapshots were kept.')
            return False
        with store._LOCK:
            local = store.connect()
            current = store.fingerprint(local)
            different = current != store.fingerprint(remote)
            if different or reconcile:
                if different and (not saved.get('memory_baseline') or current != saved['memory_baseline']):
                    say('  Local memory changed since handoff. Both databases were kept; automatic restore and deletion were refused.')
                    return False
                backup = sqlite3.connect(os.path.join(folder, 'local-' + secrets.token_hex(8) + '.db'))
                try:
                    local.backup(backup)
                    remote.backup(local)
                    if reconcile:
                        reconcile()
                except BaseException:
                    backup.backup(local)
                    raise
                finally:
                    backup.close()
            # Rebuild compatibility exports rather than reimporting either copy.
            for path in (memory._path(repo), memory._notes_path(repo)):
                local.execute('INSERT OR REPLACE INTO synced VALUES(?,?)', (path, time.time()))
            memory._export(repo)
            saved['memory_baseline'] = store.fingerprint(local)
            with open(cfg, 'w', encoding='utf-8') as fh:
                json.dump(saved, fh)
    finally:
        remote.close()
    say('  Memory, pending actions and notification state returned; the earlier local snapshot was kept.')
    return True


def _return_manifest(target, repo, project, settings, remote_home):
    """Quiesce on the machine that owns the work before reading its database."""
    from . import handoff, store, tools
    import sys

    original = settings['handoff']
    root = f'{remote_home}/return-{original["nonce"]}'
    code = 'from hive import handoff,memory; '
    if target.local:
        code += 'memory.DIR=' + repr(str(Path(remote_home) / 'rules')) + '; '
    code += f'handoff.prepare_return({project!r},{repo!r},{root!r},{original["nonce"]!r})'
    if target.local:
        result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True)
    else:
        result = target.run('"$HOME/hive-cloud/venv/bin/python" -c ' + Q(code), check=False)
    if result.returncode:
        raise tools.Refused('The other machine could not confirm a quiescent checkpoint.')
    folder = Path(store.path()).parent / 'returns' / original['nonce']
    manifest = folder / 'handoff.json'
    if not target.get(root + '/handoff.json', str(manifest)):
        raise tools.Refused('The return manifest is missing.')
    data = json.loads(manifest.read_text('utf-8'))
    if data.get('unopened') == original['nonce']:
        return None
    data = handoff.read_manifest(manifest)
    if data.get('project_id') != original['project_id'] or data.get('repository') != original['repository']:
        raise tools.Refused('The cloud database belongs to another project.')
    for build in data['builds']:
        if build.get('directory'):
            rel = f'handoff-{data["nonce"]}/{build["directory"]}'
            for name in ('artifact.bundle', 'state.json'):
                target.get(f'{root}/{rel}/{name}', str(folder / rel / name))
    return manifest


def pull(repo='.', frm=None, say=print, verify=False):
    """Bring everything done in the cloud to this computer: every branch (hive/... as your result branches, any other
    under hive-cloud/...), the build records, the rules and the conversation. With `verify`, check every branch arrived
    whole before anything may be deleted (the owner: no development may ever be lost). Returns 0 only when complete."""
    repo = os.path.abspath(repo)
    key = None
    saved = {}
    cfg = os.path.join(os.path.expanduser('~'), '.hive', 'cloud.json')
    if os.path.exists(cfg):
        saved = json.load(open(cfg))
        target_matches=bool(saved.get('to') and frm and (
            frm==saved['to'] or (Target(frm).local and Target(saved['to']).local and
                os.path.normcase(os.path.realpath(frm))==os.path.normcase(os.path.realpath(saved['to'])))))
        if not frm or target_matches:
            frm, key = saved['to'], saved.get('key')
        else:
            saved = {}  # a different target cannot inherit this handoff's authority
    if not frm:
        say('Tell me where from: hive cloud pull --from user@host'); return 2
    t = Target(frm, key); proj = f'{t.home()}/{_project(repo)}'
    url = proj if t.local else f'{t.to}:{proj}'
    env = dict(os.environ, GIT_SSH_COMMAND='ssh ' + ' '.join(shlex.quote(o) for o in Target(frm, key).opts)) if key else None
    from . import build_receipts, handoff, projects, store, tools

    original = saved.get('handoff', {})
    src_hive = f'{t.home()}/.hive' if t.local else '.hive'
    manifest = None
    if original:
        try:
            manifest = _return_manifest(t, repo, proj, saved, src_hive)
        except tools.Refused as exc:
            say(str(exc))
            return 1
    heads = _remote_heads(repo, url, env)
    if heads is None:
        say('Could not reach the cloud copy to bring the work back.'); return 1
    # results as his hive/... branches; every other branch kept apart, never over his own
    p = subprocess.run(
        ['git', '-C', repo, 'fetch', '--no-tags', url, '+refs/heads/*:refs/remotes/hive-cloud/*'],
        capture_output=True,
        text=True,
        env=env,
    )
    if p.returncode != 0:
        say(f'Could not fetch: {p.stderr.strip()[:300]}'); return 1
    results = sorted(b for b in heads if b.startswith('hive/'))
    current = handoff.refs(repo)
    expected = saved.get('local_refs', original.get('refs'))
    checked = build_receipts.git(repo, 'symbolic-ref', 'HEAD', required=False)
    conflict = ''
    if original and (
        expected != current
        or projects.repository(repo) != original['repository']
        or projects.path(repo) != original['source']
        or checked != original['branch']
        or build_receipts.git(repo, 'status', '--porcelain', '--untracked-files=normal')
    ):
        conflict = 'The source checkout changed after the handoff.'
    changes = []
    resulting = dict(current)
    for name in results:
        ref = 'refs/heads/' + name
        old = current.get(ref)
        sha = heads[name]
        if old == sha:
            continue
        if ref == checked or (
            old
            and subprocess.run(
                ['git', '-C', repo, 'merge-base', '--is-ancestor', old, sha], capture_output=True
            ).returncode
        ):
            conflict = 'A result branch diverged.'
        changes.append(f'update {ref} {sha} {old or "0"*len(sha)}')
        resulting[ref] = sha
    if manifest:
        returned = json.loads(manifest.read_text('utf-8'))
        if returned['branch'] != checked or any(
            heads.get(ref.removeprefix('refs/heads/')) != sha for ref, sha in resulting.items()
        ):
            conflict = 'The remote project branch or a recorded commit differs.'

    def reconcile():
        if handoff.refs(repo) != current:
            raise tools.Refused('Source branches changed during return.')
        if changes:
            subprocess.run(
                ['git', '-C', repo, 'update-ref', '--stdin'],
                input=('\n'.join(changes) + '\n').encode('utf-8'),
                capture_output=True,
                check=True,
            )
        try:
            if manifest:
                returned['refs'] = resulting
                manifest.write_text(json.dumps(returned), encoding='utf-8')
                handoff.restore(repo, manifest)
            if original:
                handoff.release(original)
        except BaseException:
            undo = []
            for ref, sha in resulting.items():
                if current.get(ref) != sha:
                    undo.append(f'update {ref} {current[ref]} {sha}' if ref in current else f'delete {ref} {sha}')
            if undo:
                subprocess.run(
                    ['git', '-C', repo, 'update-ref', '--stdin'],
                    input=('\n'.join(undo) + '\n').encode('utf-8'),
                    capture_output=True,
                    check=True,
                )
            raise
        saved['local_refs'] = resulting

    try:
        if not _pull_state(t, repo, src_hive, saved, cfg, say, conflict=conflict, reconcile=reconcile):
            return 1
    except Exception:
        say('  Could not safely return cloud memory. Both copies were kept; nothing will be deleted.'); return 1
    say(f'Brought back {len(results)} checked result branch(es).')
    rules = memory.project_key(repo) + '.json'
    back = [name for name, src, dst in (
        ('conversation', f'{src_hive}/conversation.json', telegram.CONVERSATION),
    ) if t.get(src, dst)]
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
