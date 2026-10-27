#!/usr/bin/env python3
"""Claim test categories safely.

usage: tools/claim.py <short_name> <category>[,<category>...] "<one-line description>"

Exit 0: you hold the lock. Exit 1: another worker holds one of those categories (choose others).
Exit 2: sync problem, retry. Exit 3: commit or stash your work first. Exit 4: unknown category.
A lock file lists its categories; no two locks may share a category. If two workers claim
overlapping categories at the same moment, the claim that reached main first wins and the
other is withdrawn automatically.
"""
import glob, json, os, subprocess, sys, time

def sh(*a, check=False):
    r = subprocess.run(list(a), capture_output=True, text=True)
    if check and r.returncode:
        raise SystemExit(2)
    return r

def locks():
    out = {}
    for f in glob.glob('current_tasks/*.txt'):
        cats = set()
        for line in open(f):
            if line.startswith('categories:'):
                cats = {c.strip() for c in line.split(':', 1)[1].split(',') if c.strip()}
        out[os.path.basename(f)[:-4]] = cats
    return out

def first_commit_index(path):
    # position of the commit that added this lock in main's history (smaller = earlier)
    r = sh('git', 'log', '--format=%H', '--diff-filter=A', '--', path)
    h = r.stdout.split()[-1] if r.stdout.split() else None
    if not h:
        return 10**9
    return int(sh('git', 'rev-list', '--count', h).stdout.strip() or 10**9)

def log(event):
    p = os.environ.get('HIVE_LOG')
    if p:
        open(p, 'a').write(f'{int(time.time())} {event}\n')

def main():
    if len(sys.argv) < 4:
        print(__doc__); sys.exit(2)
    name, cats, desc = sys.argv[1], {c.strip() for c in sys.argv[2].split(',') if c.strip()}, sys.argv[3]
    known = {json.load(open(f))['category'] for f in glob.glob('tests/visible/*.json')}
    bad = cats - known
    if bad:
        print('unknown categories:', ', '.join(sorted(bad))); sys.exit(4)
    if sh('git', 'status', '--porcelain').stdout.strip():
        print('working tree not clean: commit or stash first'); sys.exit(3)
    if sh('git', 'pull', '-q', '--rebase', 'origin', 'main').returncode:
        sh('git', 'rebase', '--abort'); sys.exit(2)
    me = sh('git', 'config', 'user.name').stdout.strip()
    held = locks()
    if name in held:
        print('lock name already used:', name); sys.exit(1)
    for other, oc in held.items():
        if oc & cats:
            print(f'already held by lock {other}: ' + ', '.join(sorted(oc & cats))); sys.exit(1)
    path = f'current_tasks/{name}.txt'
    open(path, 'w').write(f'{me}: {desc}\ncategories: {",".join(sorted(cats))}\n')
    sh('git', 'add', path); sh('git', 'commit', '-q', '-m', f'Lock: {name} ({",".join(sorted(cats))})', '--', path)
    for _ in range(8):
        if sh('git', 'push', '-q', 'origin', 'HEAD:main').returncode == 0:
            break
        if sh('git', 'pull', '-q', '--rebase', 'origin', 'main').returncode:
            sh('git', 'rebase', '--abort'); sh('git', 'reset', '-q', '--hard', 'origin/main')
            print('lost race for', name); sys.exit(1)
    else:
        sh('git', 'reset', '-q', '--hard', 'origin/main'); sys.exit(2)
    # race check: an overlapping lock that reached main earlier wins
    sh('git', 'pull', '-q', '--rebase', 'origin', 'main')
    mine = first_commit_index(path)
    for other, oc in locks().items():
        if other != name and oc & cats and first_commit_index(f'current_tasks/{other}.txt') < mine:
            sh('git', 'rm', '-q', path); sh('git', 'commit', '-q', '-m', f'Withdraw lock {name}: overlaps {other}')
            for _ in range(8):
                if sh('git', 'push', '-q', 'origin', 'HEAD:main').returncode == 0:
                    break
                sh('git', 'pull', '-q', '--rebase', 'origin', 'main')
            print(f'lost race to {other} for ' + ', '.join(sorted(oc & cats))); sys.exit(1)
    log(f'CLAIM {name} {",".join(sorted(cats))}')
    print('claimed', name, '->', ', '.join(sorted(cats)))

if __name__ == '__main__':
    main()
