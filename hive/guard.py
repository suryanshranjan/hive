"""The guard: land a worker's change on main only if it breaks nothing that passes on main.

Runner-agnostic version of gates/gate23/tools/land.py (Gates 3, 21-23). In order:
  1. commit the work and release the worker's lock;
  2. rebase onto the shared branch (config "branch", else the remote default);
  3. refuse new duplicate definitions in Python files (git merges them silently and the last one wins);
  4. refuse any test that passes on the shared branch but fails with the change, per test, using the project's own test
     command and its JUnit XML;
  5. push.
Main's results are cached by code content (Gate 23: lock commits change no code, so they reuse the landing's run).
Before committing it refuses secrets (.env files other than templates, private keys, credential files; projects can
add patterns with "never_commit") and leaves build artifacts and dependency folders out of the commit.
Exit codes: 0 landed; 2 push kept failing; 5 rebase conflict; 6 duplicate definitions; 7 regressions; 8 forbidden files."""
import ast, fnmatch, hashlib, io, json, os, re, subprocess, sys, tarfile, tempfile, time

from . import config, junit, law

LOCK_DIR = 'current_tasks'
NEVER_COMMIT = ['.env', '.env.*', '*.pem', '*.key', '*.p12', '*.pfx', 'id_rsa*', 'id_ed25519*', '*credentials*.json',
                '*service-account*.json', '.npmrc', '.pypirc']
ARTIFACTS = ['node_modules', '.venv', 'venv', '__pycache__', '*.pyc', '.pytest_cache', '.mypy_cache', '.next', '.turbo',
             'coverage', '.hive']
TEMPLATES = ('.example', '.sample', '.template')

def _matches(path, patterns):
    return any(fnmatch.fnmatch(part, pat) for part in path.split('/') for pat in patterns)

def forbidden(path, extra=()):
    """True for a secret-like file that must never be committed (.env.example and other templates are allowed)."""
    return _matches(path, NEVER_COMMIT + list(extra)) and not path.endswith(TEMPLATES)

def artifact(path):
    """True for build output and dependencies, which are left out of commits."""
    return _matches(path, ARTIFACTS) and not (path == '.hive/config.json')

def sh(*a, **k):
    return subprocess.run(list(a), capture_output=True, text=True, **k)

def branch(cfg):
    """The shared branch: .hive/config.json "branch", else the remote's default branch (origin/HEAD), else main."""
    if cfg.get('branch'):
        return cfg['branch']
    ref = sh('git', 'symbolic-ref', '--short', 'refs/remotes/origin/HEAD').stdout.strip()
    return ref.split('/', 1)[1] if ref.startswith('origin/') else 'main'

def log(event):
    p = os.environ.get('HIVE_LOG')
    if p:
        open(p, 'a').write(f'{int(time.time())} {event}\n')
    run = os.environ.get('HIVE_RUN')   # the whole swarm's landings and collisions, for the notes switch
    if run and event.split()[0] in ('LAND', 'CONFLICT') and os.path.isdir(run):
        open(os.path.join(run, 'landings.log'), 'a').write(f'{int(time.time())} {event.split()[0]}\n')

def swarm_collisions():
    """(collisions, landings) so far in this swarm (0, 0 outside a Hive run)."""
    run = os.environ.get('HIVE_RUN'); path = run and os.path.join(run, 'landings.log')
    if not path or not os.path.exists(path):
        return 0, 0
    kinds = [l.split()[1] for l in open(path) if len(l.split()) > 1]
    return kinds.count('CONFLICT'), kinds.count('LAND')

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
    """The shared branch checked out in a temporary folder, with dependency folders linked from this clone."""
    d = tempfile.mkdtemp(prefix='hive-main-')
    data = subprocess.run(['git', 'archive', f'origin/{branch(cfg)}'], capture_output=True).stdout
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
    main = f'origin/{branch(cfg)}'; d = cache_dir(); p = os.path.join(d, code_key(main) + '.json')
    try:
        res = json.load(open(p)); open(os.path.join(d, 'stats.log'), 'a').write('hit\n'); return res
    except Exception:
        res = run_suite(main_snapshot(cfg), cfg); cache_put(main, res)
        open(os.path.join(d, 'stats.log'), 'a').write('miss\n'); return res

# ---------------------------------------------------------------- landing

NOTE = 'Team-note:'

def team_notes(b=None, n=8):
    """The latest one-line team notes on the shared branch, newest first: (who, note)."""
    b = b or branch(config.load())
    sh('git', 'fetch', '-q', 'origin', b)
    out = sh('git', 'log', f'origin/{b}', '-n', '200', '--format=%an%x00%B%x01').stdout
    got = []
    for entry in out.split('\x01'):
        if '\x00' not in entry:
            continue
        who, body = entry.split('\x00', 1)
        got += [(who.strip(), l.split(NOTE, 1)[1].strip()) for l in body.splitlines() if l.strip().startswith(NOTE)]
    return got[:n]

def show_notes(n=8):
    got = team_notes(n=n)
    print('\n'.join(f'{who}: {note}' for who, note in got) if got else '(no team notes yet)')
    return 0

def land(name, message, note=None):
    """message is a commit message, or '--continue' after resolving a rebase conflict. A note (one line others should
    know: a shared helper, a changed interface, a file many touch) rides in the commit as a Team-note trailer."""
    cfg = config.load(); b = branch(cfg)
    note = ' '.join((note or '').split())[:300]
    if note and message != '--continue':
        message = f'{message}\n\n{NOTE} {note}'
    elif note:   # after a conflict: the note goes on the commit being landed
        body = sh('git', 'log', '-1', '--format=%B').stdout.rstrip()
        sh('git', 'commit', '-q', '--amend', '-m', f'{body}\n\n{NOTE} {note}')
    lock = os.path.join(LOCK_DIR, f'{name}.txt')
    if message != '--continue':
        if os.path.exists(lock):
            sh('git', 'rm', '-q', '--cached', lock); os.remove(lock)
        sh('git', 'add', '-A')
        staged = sh('git', 'diff', '--cached', '--name-only').stdout.splitlines()
        skip = [f for f in staged if f and artifact(f)]
        if skip:
            sh('git', 'reset', '-q', '--', *skip)
        bad = sorted(f for f in staged if f and forbidden(f, cfg.get('never_commit', [])))
        if bad:
            sh('git', 'reset', '-q')
            log(f'BLOCKED_FORBIDDEN {name} {len(bad)}')
            print('Refused: these files must never be committed (secrets or dependencies): ' + ', '.join(bad[:10]))
            print('Delete them or add them to .gitignore, then run hive land again.'); return 8
        head, _, rest = message.partition('\n')
        r = sh('git', 'commit', '-q', '-m', f'{head} (lock {name} released)' + ('\n' + rest if rest else ''))
        if r.returncode and not re.search(r'nothing (added )?to commit', r.stdout + r.stderr):   # already committed by itself
            print(r.stdout, r.stderr); return 2
    for _ in range(8):
        if sh('git', 'pull', '--rebase', 'origin', b).returncode:
            files = sh('git', 'diff', '--name-only', '--diff-filter=U').stdout.split()
            log(f'CONFLICT {name} {" ".join(files)}')
            print('Rebase conflict in: ' + ', '.join(files) + f'\nResolve, git add, git rebase --continue, then: hive land {name} --continue')
            got = team_notes(b, 5)   # a collision is when notes matter (Gates 43-44: rarely otherwise)
            if got:
                print('Recent team notes (others may be changing the same code):\n' + '\n'.join(f'  {w}: {t}' for w, t in got))
            print('If what you resolved affects others, add --note "<one line>" to the --continue.')
            c, l = swarm_collisions()
            on, why = law.notes(0, c, l)
            if on:   # switched on only when this swarm's builders keep colliding
                print(f'Team notes are now on for this swarm ({why}): run `hive notes` at each sync, and add '
                      '--note "<one line>" when you land something others must know about.')
            return 5
        # what the builder committed by itself, with plain git, skipped the checks above (Gate 38: a builder's own
        # commit carried the shared node_modules link onto main)
        added = sh('git', 'diff', '--name-only', '--diff-filter=A', f'origin/{b}...HEAD').stdout.splitlines()
        bad = sorted(f for f in added if f and forbidden(f, cfg.get('never_commit', [])))
        if bad:
            log(f'BLOCKED_FORBIDDEN {name} {len(bad)}')
            print('Refused: your commits add files that must never be committed (secrets): ' + ', '.join(bad[:10]))
            print(f'Undo them with `git reset --soft origin/{b}`, remove those files, then run hive land again.'); return 8
        junk = [f for f in added if f and artifact(f)]
        if junk:
            sh('git', 'rm', '-r', '-q', '--cached', '--', *junk)
            sh('git', 'commit', '-q', '-m', 'hive: leave build output and dependencies out of the shared branch')
        new_dups = dup_defs(python_sources('HEAD')) - dup_defs(python_sources(f'origin/{b}'))
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
        if sh('git', 'push', '-q', 'origin', f'HEAD:{b}').returncode == 0:
            log(f'LAND {name} {sum(mine.values())}')
            print(f'landed {name}: {sum(mine.values())}/{len(mine)} tests pass'); return 0
    print('push kept being rejected; run again'); return 2
