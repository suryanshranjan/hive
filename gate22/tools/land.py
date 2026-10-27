#!/usr/bin/env python3
"""Land your work safely.

usage: tools/land.py <short_name> "<commit message>"     # commits your changes, releases the lock, lands
       tools/land.py <short_name> --continue              # after you resolved a rebase conflict

What it does, in order: commit (code + lock release), rebase onto main, then two checks before pushing:
  1. no NEW duplicate definitions (two functions or methods with the same name in one scope,
     which git merges silently and the last one wins);
  2. no test that passes on current main fails with your change (full visible suite, per test).
     Main's results are cached per commit on this machine (Gates 21, 22), so usually only your change is run.
If a check fails it prints what broke and does not push: fix it, commit, and run with --continue.
Exit 0 landed; 5 rebase conflict (resolve, git add, git rebase --continue, then --continue);
6 new duplicate definitions; 7 regressions; 2 push kept failing.
"""
import ast, glob, hashlib, json, os, subprocess, sys, tarfile, tempfile, time, io

def sh(*a, **k):
    return subprocess.run(list(a), capture_output=True, text=True, **k)

def log(event):
    p = os.environ.get('HIVE_LOG')
    if p:
        open(p, 'a').write(f'{int(time.time())} {event}\n')

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
                    if any(isinstance(d, ast.Name) and d.id in ('property',) or isinstance(d, ast.Attribute) for d in n.decorator_list):
                        continue  # property setters legitimately repeat names
                    seen[n.name] = seen.get(n.name, 0) + 1
            out |= {(path, scope, name) for name, c in seen.items() if c > 1}
    return out

def sources_at(rev):
    files = sh('git', 'ls-tree', '-r', '--name-only', rev, 'minisql').stdout.split()
    return {f: sh('git', 'show', f'{rev}:{f}').stdout for f in files if f.endswith('.py')}

def run_suite(code_dir):
    out = os.path.join(tempfile.mkdtemp(), 'res.json')
    sh(sys.executable, os.path.join(code_dir, 'run_tests.py'), os.path.abspath('tests/visible'), '--json', out, cwd=code_dir)
    try:
        return json.load(open(out))
    except Exception:
        return {}

def cache_dir():
    origin = sh('git', 'remote', 'get-url', 'origin').stdout.strip()
    d = os.path.join(os.environ.get('HIVE_GUARD_CACHE', '/tmp/hive_guard_cache'), hashlib.sha1(origin.encode()).hexdigest()[:12])
    os.makedirs(d, exist_ok=True); return d

def cache_put(rev, res):
    if not res: return
    d = cache_dir(); tmp = os.path.join(d, f'.{rev}.{os.getpid()}')
    json.dump(res, open(tmp, 'w')); os.replace(tmp, os.path.join(d, rev + '.json'))

def main_results():
    # suite results of origin/main: from the shared cache when another worker already ran them, else run once and store
    rev = sh('git', 'rev-parse', 'origin/main').stdout.strip(); d = cache_dir(); p = os.path.join(d, rev + '.json')
    try:
        res = json.load(open(p)); open(os.path.join(d, 'stats.log'), 'a').write('hit\n'); return res
    except Exception:
        res = run_suite(main_snapshot()); cache_put(rev, res)
        open(os.path.join(d, 'stats.log'), 'a').write('miss\n'); return res

def main_snapshot():
    d = tempfile.mkdtemp()
    data = subprocess.run(['git', 'archive', 'origin/main', 'minisql', 'run_tests.py'], capture_output=True).stdout
    tarfile.open(fileobj=io.BytesIO(data)).extractall(d, filter="data")
    return d

def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(2)
    name, arg = sys.argv[1], sys.argv[2]
    lock = f'current_tasks/{name}.txt'
    if arg != '--continue':
        if os.path.exists(lock):
            sh('git', 'rm', '-q', '--cached', lock); os.remove(lock)
        sh('git', 'add', '-A')
        r = sh('git', 'commit', '-q', '-m', f'{arg} (lock {name} released)')
        if r.returncode and 'nothing to commit' not in r.stdout + r.stderr:
            print(r.stdout, r.stderr); sys.exit(2)
    for attempt in range(8):
        r = sh('git', 'pull', '--rebase', 'origin', 'main')
        if r.returncode:
            files = sh('git', 'diff', '--name-only', '--diff-filter=U').stdout.split()
            log(f'CONFLICT {name} {" ".join(files)}')
            print('Rebase conflict in: ' + ', '.join(files) + '\nResolve, git add, git rebase --continue, then: tools/land.py ' + name + ' --continue')
            sys.exit(5)
        new_dups = dup_defs(sources_at('HEAD')) - dup_defs(sources_at('origin/main'))
        if new_dups:
            log(f'BLOCKED_DUP {name} {len(new_dups)}')
            print('New duplicate definitions (the last one silently wins):')
            for f, scope, n in sorted(new_dups): print(f'  {f}: {scope}.{n}')
            print('Rename or merge them, commit, then: tools/land.py ' + name + ' --continue'); sys.exit(6)
        base = main_results(); mine = run_suite(os.getcwd())
        regressed = sorted(k for k, v in base.items() if v and not mine.get(k))
        if regressed:
            log(f'BLOCKED_REGRESSION {name} {len(regressed)}')
            print(f'{len(regressed)} tests pass on main but fail with your change, e.g.: ' + ', '.join(regressed[:8]))
            print('Fix, commit, then: tools/land.py ' + name + ' --continue'); sys.exit(7)
        head = sh('git', 'rev-parse', 'HEAD').stdout.strip()
        cache_put(head, mine)   # stored before pushing (Gate 22): whoever rebases onto this commit finds it; harmless if the push fails
        if sh('git', 'push', '-q', 'origin', 'HEAD:main').returncode == 0:
            total = sum(mine.values())
            log(f'LAND {name} {total}')
            print(f'landed {name}: {total}/{len(mine)} visible tests pass'); sys.exit(0)
    print('push kept being rejected; run again'); sys.exit(2)

if __name__ == '__main__':
    main()
