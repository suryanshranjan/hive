"""Claims: a worker locks one or more areas of the codebase before working on them (Gate 3's protocol, generalized).

A claim is a lock file current_tasks/<short_name>.txt pushed to the shared branch, listing its areas. Areas come from
.hive/config.json "areas" (name -> list of test-file globs); when none are configured, any name is accepted.
No two locks may share an area. If two workers claim overlapping areas at the same moment, the lock that reached the
shared branch first wins and the other is withdrawn automatically.
Exit codes: 0 claimed; 1 taken (choose other areas); 2 sync problem, retry; 3 commit or stash first; 4 unknown area."""
import glob, os, time

from . import config
from .guard import LOCK_DIR, branch, log, sh

def locks():
    """{lock name: set of areas} as currently checked out."""
    out = {}
    for f in glob.glob(os.path.join(LOCK_DIR, '*.txt')):
        areas = set()
        for line in open(f):
            if line.startswith('areas:'):
                areas = {a.strip() for a in line.split(':', 1)[1].split(',') if a.strip()}
        out[os.path.basename(f)[:-4]] = areas
    return out

def _added_at(path):
    """Position of the commit that added a lock file in the shared history (smaller = earlier)."""
    h = sh('git', 'log', '--format=%H', '--diff-filter=A', '--', path).stdout.split()
    return int(sh('git', 'rev-list', '--count', h[-1]).stdout.strip() or 10**9) if h else 10**9

def _push(b):
    for _ in range(8):
        if sh('git', 'push', '-q', 'origin', f'HEAD:{b}').returncode == 0:
            return True
        if sh('git', 'pull', '-q', '--rebase', 'origin', b).returncode:
            sh('git', 'rebase', '--abort'); sh('git', 'reset', '-q', '--hard', f'origin/{b}')
            return False
    return False

def claim(name, areas, desc):
    cfg = config.load(); b = branch(cfg)
    wanted = {a.strip() for a in areas.split(',') if a.strip()}
    known = set(cfg.get('areas', {}))
    if known and wanted - known:
        print('unknown areas: ' + ', '.join(sorted(wanted - known)) + '; known: ' + ', '.join(sorted(known))); return 4
    if sh('git', 'status', '--porcelain', '--untracked-files=no').stdout.strip():
        print('working tree not clean: commit or stash first'); return 3
    if sh('git', 'pull', '-q', '--rebase', 'origin', b).returncode:
        sh('git', 'rebase', '--abort'); return 2
    held = locks()
    if name in held:
        print('lock name already used:', name); return 1
    for other, theirs in held.items():
        if theirs & wanted:
            print(f'already held by lock {other}: ' + ', '.join(sorted(theirs & wanted))); return 1
    me = sh('git', 'config', 'user.name').stdout.strip()
    path = os.path.join(LOCK_DIR, f'{name}.txt'); os.makedirs(LOCK_DIR, exist_ok=True)
    open(path, 'w').write(f'{me}: {desc}\nareas: {",".join(sorted(wanted))}\n')
    sh('git', 'add', path); sh('git', 'commit', '-q', '-m', f'Lock: {name} ({",".join(sorted(wanted))})', '--', path)
    if not _push(b):
        sh('git', 'reset', '-q', '--hard', f'origin/{b}'); print('lost race for', name); return 1
    # race check: an overlapping lock that reached the shared branch earlier wins
    sh('git', 'pull', '-q', '--rebase', 'origin', b)
    mine = _added_at(path)
    for other, theirs in locks().items():
        if other != name and theirs & wanted and _added_at(os.path.join(LOCK_DIR, f'{other}.txt')) < mine:
            sh('git', 'rm', '-q', path); sh('git', 'commit', '-q', '-m', f'Withdraw lock {name}: overlaps {other}')
            _push(b)
            print(f'lost race to {other} for ' + ', '.join(sorted(theirs & wanted))); return 1
    log(f'CLAIM {name} {",".join(sorted(wanted))}')
    print('claimed', name, '->', ', '.join(sorted(wanted))); return 0

def status():
    """Each configured area and who holds it (after syncing)."""
    cfg = config.load(); b = branch(cfg)
    sh('git', 'pull', '-q', '--rebase', 'origin', b)
    holder = {a: n for n, areas in locks().items() for a in areas}
    for a in sorted(set(cfg.get('areas', {})) | set(holder)):
        print(f'{a:30s} {"held by " + holder[a] if a in holder else "free"}')
    return 0
