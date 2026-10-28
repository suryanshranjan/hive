"""hive cloud: move this project's Hive to a cloud machine and run it from the owner's phone.

  hive cloud --to user@host [--with-login] [--no-start]   copy the project and Hive there, start the listener there
  hive cloud pull --from user@host                        bring the result branches (hive/...) back here

What goes over (by SSH): the current branch of this repository (a git bundle, so history but no unsaved files), Hive
itself (pip install from GitHub), the owner's rulings for this project, the Telegram link and the backup-model settings.
The Claude login goes only with --with-login: otherwise run `claude` once on the machine to log in there.
Never sent: .env files, keys, node_modules (dependencies are installed fresh there), anything not committed.
For tests and mounted disks, --to may also be a local folder."""
import json, os, shlex, shutil, subprocess, tempfile

from . import memory, telegram

REMOTE_HOME = '~/hive-cloud'

class Target:
    """Where Hive goes: user@host over SSH, or a local folder (tests, a mounted disk)."""
    def __init__(self, to):
        self.local = os.path.isabs(to) or to.startswith('.') or (':' not in to and '@' not in to)
        self.to = os.path.abspath(to) if self.local else to

    def run(self, cmd, check=True):
        full = ['sh', '-c', cmd] if self.local else ['ssh', '-o', 'BatchMode=yes', self.to, cmd]
        p = subprocess.run(full, capture_output=True, text=True)
        if check and p.returncode != 0:
            raise RuntimeError(f'on {self.to}: {cmd}\n{p.stderr.strip()[:400]}')
        return p

    def put(self, src, dst):
        if self.local:
            os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(src, dst)
        else:
            self.run(f'mkdir -p {shlex.quote(os.path.dirname(dst))}')
            subprocess.run(['scp', '-q', '-o', 'BatchMode=yes', src, f'{self.to}:{dst}'], check=True)

    def home(self):
        return os.path.join(self.to, 'hive-cloud') if self.local else REMOTE_HOME

def _project(repo):
    return os.path.basename(os.path.abspath(repo)) or 'project'

def go(repo='.', to=None, with_login=False, start=True, say=print):
    repo = os.path.abspath(repo)
    if not to:
        say('Tell me where: hive cloud --to user@host'); return 2
    if subprocess.run(['git', '-C', repo, 'status', '--porcelain'], capture_output=True, text=True).stdout.strip():
        say('You have unsaved changes. Commit them first: only committed work goes to the cloud.'); return 3
    t = Target(to); name = _project(repo)
    proj = f'{t.home()}/{name}'
    branch = subprocess.run(['git', '-C', repo, 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True, text=True).stdout.strip()
    say(f"Moving {name} to {t.to}. Only committed work goes; .env files, keys and dependencies stay here.")
    t.run('true')   # reachable?
    tmp = tempfile.mkdtemp()
    bundle = os.path.join(tmp, 'project.bundle')
    subprocess.run(['git', '-C', repo, 'bundle', 'create', '-q', bundle, branch], check=True)
    t.put(bundle, f'{t.home()}/{name}.bundle')
    t.run(f'mkdir -p {t.home()} && cd {t.home()} && (test -d {name} && git -C {name} fetch -q ../{name}.bundle '
          f'{branch}:{branch} 2>/dev/null || git clone -q -b {branch} {name}.bundle {name}) && rm -f {name}.bundle')
    if not t.local:   # Hive itself, from GitHub (a local target shares this machine's Hive)
        t.run('python3 -m pip install -q --user git+https://github.com/suryanshranjan/hive 2>&1 | tail -1', check=False)
    # the owner's context: rulings for this project, the Telegram link, the backup model (never in the repository)
    hive_dir = os.path.join(os.path.expanduser('~'), '.hive')
    dst_hive = f'{t.home()}/.hive' if t.local else '~/.hive'
    rules = os.path.join(memory.DIR, memory.project_key(repo) + '.json')
    sent = []
    for src, dst in ((rules, f'{dst_hive}/rules/{os.path.basename(rules)}'), (telegram.PATH, f'{dst_hive}/telegram.json'),
                     (os.path.join(hive_dir, 'llm.json'), f'{dst_hive}/llm.json')):
        if os.path.exists(src):
            t.put(src, dst); sent.append(os.path.basename(src))
    if with_login:
        cred = os.path.join(os.path.expanduser('~'), '.claude', '.credentials.json')
        if os.path.exists(cred):
            t.put(cred, (f'{t.home()}/.claude' if t.local else '~/.claude') + '/.credentials.json'); sent.append('Claude login')
    t.run(f'chmod -R go-rwx {dst_hive} 2>/dev/null || true', check=False)
    # dependencies, installed fresh there
    for pj in subprocess.run(['git', '-C', repo, 'ls-files', 'package-lock.json', '*/package-lock.json'],
                             capture_output=True, text=True).stdout.split():
        d = os.path.dirname(pj) or '.'
        say(f'  Installing dependencies in {d} there...')
        t.run(f'cd {proj}/{d} && npm ci --silent >/dev/null 2>&1 || npm install --silent >/dev/null 2>&1', check=False)
    if subprocess.run(['git', '-C', repo, 'ls-files', 'requirements.txt'], capture_output=True, text=True).stdout.strip():
        t.run(f'cd {proj} && python3 -m pip install -q --user -r requirements.txt', check=False)
    json.dump({'to': t.to, 'project': proj, 'branch': branch}, open(os.path.join(hive_dir if os.path.isdir(hive_dir) else tmp,
                                                                                  'cloud.json'), 'w'))
    say(f"  Copied: the project ({branch}), " + (', '.join(sent) if sent else 'no Hive settings yet') + '.')
    if not with_login:
        say("  The Claude login did not go over. On that machine, run `claude` once to log in (or rerun with --with-login).")
    if start:
        t.run(f'cd {proj} && (nohup python3 -m hive listen > {t.home()}/listen.log 2>&1 &)', check=False)
        say("  Hive is listening there. Stop the listener on this machine, so only one Hive reads your Telegram.")
        cfg = telegram.load()
        if cfg:
            try:
                telegram.Channel(cfg).send(f"I'm now running in the cloud ({name}). Message me any time: 'build: ...', "
                                           "a change of mind, or 'status'.")
            except Exception:
                pass
    say(f"Done. Bring results back any time with: hive cloud pull --from {t.to}")
    return 0

def pull(repo='.', frm=None, say=print):
    """Fetch the hive/... result branches built in the cloud into this repository (your branches are not touched)."""
    repo = os.path.abspath(repo)
    if not frm:
        cfg = os.path.join(os.path.expanduser('~'), '.hive', 'cloud.json')
        frm = json.load(open(cfg))['to'] if os.path.exists(cfg) else None
    if not frm:
        say('Tell me where from: hive cloud pull --from user@host'); return 2
    t = Target(frm); proj = f'{t.home()}/{_project(repo)}'
    url = proj if t.local else f'{t.to}:{proj.replace("~/", "")}'
    p = subprocess.run(['git', '-C', repo, 'fetch', url, '+refs/heads/hive/*:refs/heads/hive/*'], capture_output=True, text=True)
    if p.returncode != 0:
        say(f'Could not fetch: {p.stderr.strip()[:300]}'); return 1
    got = subprocess.run(['git', '-C', repo, 'branch', '--list', 'hive/*'], capture_output=True, text=True).stdout.split()
    say(f"Brought back {len([g for g in got if g != '*'])} result branch(es): " + ', '.join(g for g in got if g != '*'))
    return 0
