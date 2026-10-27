"""The guard: land a worker's change on main only if it breaks nothing that passes on main.

Runner-agnostic version of gates/gate23/tools/land.py (Gates 3, 21-23). In order:
  1. commit the work and release the worker's lock;
  2. rebase onto origin/main;
  3. refuse new duplicate definitions in Python files (git merges them silently and the last one wins);
  4. refuse any test that passes on main but fails with the change, per test, using the project's own test
     command and its JUnit XML;
  5. push.
Main's results are cached by code content (Gate 23: lock commits change no code, so they reuse the landing's run).
Exit codes: 0 landed; 2 push kept failing; 5 rebase conflict; 6 duplicate definitions; 7 regressions."""
import ast, hashlib, io, json, os, subprocess, sys, tarfile, tempfile, time

from . import config, junit

LOCK_DIR = 'current_tasks'

def sh(*a, **k):
    return subprocess.run(list(a), capture_output=True, text=True, **k)

def log(event):
    p = os.environ.get('HIVE_LOG')
    if p:
        open(p, 'a').write(f'{int(time.time())} {event}\n')

# ---------------------------------------------------------------- duplicate definitions (Python files)

def dup_defs(sources):
    out = set()
    for path, src in sources.items():
        try:
            tree = ast.parse(src)
        except SyntaxError:
            out.add((path, '<syntax error>', '')); continue
        scopes = [('<module>', tree.body)] + [(n.name, n.body) for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        for scope, body in scopes:
            seen = {}
            for n in body:
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if any(isinstance(d, ast.Attribute) or (isinstance(d, ast.Name) and d.id == 'property') for d in n.decorator_list):
                        continue  # property setters and overloads legitimately repeat names
                    seen[n.name] = seen.get(n.name, 0) + 1
            out |= {(path, scope, name) for name, c in seen.items() if c > 1}
    return out

def python_sources(rev):
    files = [f for f in sh('git', 'ls-tree', '-r', '--name-only', rev).stdout.split() if f.endswith('.py')]
    return {f: sh('git', 'show', f'{rev}:{f}').stdout for f in files}

# ---------------------------------------------------------------- running the suite

def run_suite(code_dir, cfg):
    """Run the project's test command in code_dir and return {test id: passed} from its JUnit XML."""
    xml = os.path.join(code_dir, cfg['junit'])
    if os.path.exists(xml):
        os.remove(xml)
    os.makedirs(os.path.dirname(xml) or '.', exist_ok=True)
    subprocess.run(cfg['test_cmd'], shell=True, cwd=code_dir, capture_output=True, text=True)
    try:
        return junit.results(xml)
    except Exception:
        return {}

def main_snapshot(cfg):
    """origin/main checked out in a temporary folder, with dependency folders linked from this clone."""
    d = tempfile.mkdtemp(prefix='hive-main-')
    data = subprocess.run(['git', 'archive', 'origin/main'], capture_output=True).stdout
    tar = tarfile.open(fileobj=io.BytesIO(data))
    try:
        tar.extractall(d, filter='data')      # Python 3.12, and 3.11.4+
    except TypeError:
        tar.extractall(d)                     # older Pythons: the archive is our own git tree, so no filter is needed
    for link in cfg.get('snapshot_links', []):
        if os.path.exists(link) and not os.path.exists(os.path.join(d, link)):
            os.symlink(os.path.abspath(link), os.path.join(d, link))
    return d

# ---------------------------------------------------------------- the cache, keyed by code content

def code_key(rev):
    """Hash of every tracked path and blob at rev except lock files: lock commits keep the key."""
    entries = sh('git', 'ls-tree', '-r', rev).stdout.splitlines()
    kept = [e for e in entries if not e.split('\t', 1)[-1].startswith(LOCK_DIR + '/')]
    return hashlib.sha1('\n'.join(kept).encode()).hexdigest()

def cache_dir():
    origin = sh('git', 'remote', 'get-url', 'origin').stdout.strip()
    d = os.path.join(os.environ.get('HIVE_GUARD_CACHE', os.path.join(tempfile.gettempdir(), 'hive_guard_cache')),
                     hashlib.sha1(origin.encode()).hexdigest()[:12])
    os.makedirs(d, exist_ok=True)
    return d

def cache_put(rev, res):
    if not res:
        return
    key = code_key(rev); d = cache_dir(); tmp = os.path.join(d, f'.{key}.{os.getpid()}')
    json.dump(res, open(tmp, 'w')); os.replace(tmp, os.path.join(d, key + '.json'))

def main_results(cfg):
    d = cache_dir(); p = os.path.join(d, code_key('origin/main') + '.json')
    try:
        res = json.load(open(p)); open(os.path.join(d, 'stats.log'), 'a').write('hit\n'); return res
    except Exception:
        res = run_suite(main_snapshot(cfg), cfg); cache_put('origin/main', res)
        open(os.path.join(d, 'stats.log'), 'a').write('miss\n'); return res

# ---------------------------------------------------------------- landing

def land(name, message):
    """message is a commit message, or '--continue' after resolving a rebase conflict."""
    cfg = config.load()
    lock = os.path.join(LOCK_DIR, f'{name}.txt')
    if message != '--continue':
        if os.path.exists(lock):
            sh('git', 'rm', '-q', '--cached', lock); os.remove(lock)
        sh('git', 'add', '-A')
        r = sh('git', 'commit', '-q', '-m', f'{message} (lock {name} released)')
        if r.returncode and 'nothing to commit' not in r.stdout + r.stderr:
            print(r.stdout, r.stderr); return 2
    for _ in range(8):
        if sh('git', 'pull', '--rebase', 'origin', 'main').returncode:
            files = sh('git', 'diff', '--name-only', '--diff-filter=U').stdout.split()
            log(f'CONFLICT {name} {" ".join(files)}')
            print('Rebase conflict in: ' + ', '.join(files) + f'\nResolve, git add, git rebase --continue, then: hive land {name} --continue')
            return 5
        new_dups = dup_defs(python_sources('HEAD')) - dup_defs(python_sources('origin/main'))
        if new_dups:
            log(f'BLOCKED_DUP {name} {len(new_dups)}')
            print('New duplicate definitions (the last one silently wins):')
            for f, scope, n in sorted(new_dups):
                print(f'  {f}: {scope}.{n}')
            print(f'Rename or merge them, commit, then: hive land {name} --continue'); return 6
        base = main_results(cfg); mine = run_suite(os.getcwd(), cfg)
        regressed = sorted(k for k, v in base.items() if v and not mine.get(k))
        if regressed:
            log(f'BLOCKED_REGRESSION {name} {len(regressed)}')
            print(f'{len(regressed)} tests pass on main but fail with your change, e.g.: ' + ', '.join(regressed[:8]))
            print(f'Fix, commit, then: hive land {name} --continue'); return 7
        cache_put('HEAD', mine)   # stored before pushing: any later commit with the same code finds it
        if sh('git', 'push', '-q', 'origin', 'HEAD:main').returncode == 0:
            log(f'LAND {name} {sum(mine.values())}')
            print(f'landed {name}: {sum(mine.values())}/{len(mine)} tests pass'); return 0
    print('push kept being rejected; run again'); return 2
