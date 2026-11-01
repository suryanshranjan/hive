"""Gate 86 harness: SWE-bench Verified Django issues, run without Docker (a uv Python 3.9 environment and the Django
checkout at each issue's base commit), following SWE-bench's own method: the issue's test patch is applied, the test
modules it touches are run with Django's runner, and an issue is resolved when every FAIL_TO_PASS and PASS_TO_PASS test
passes. Data: Ambig-SWE's release (github.com/sani903/InteractiveSWEAgents: full_summaries_verified.xlsx, with each
issue's original text and its underspecified rewrite). Log parsing: SWE-bench's parse_log_django.
usage: python3 swe86.py validate <n> [seed]      choose n Django issues (versions 3.0-4.2) and check the gold patch resolves each"""
import json, os, random, re, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PRIV = os.path.join(ROOT, 'private', 'g86'); DJANGO = '/home/claude/swe/django'; PY = '/home/claude/swe/venv39/bin/python'

def instances():
    import openpyxl
    rows = list(openpyxl.load_workbook(os.path.join(PRIV, 'full_summaries_verified.xlsx'), read_only=True).active.iter_rows(values_only=True))
    head = rows[0]
    return [dict(zip(head, r)) for r in rows[1:]]

def directives(test_patch):
    files = re.findall(r'^diff --git a/(\S+) b/', test_patch, re.M)
    return sorted({f[len('tests/'):-3].replace('/', '.') for f in files if f.startswith('tests/') and f.endswith('.py')})

def parse(log):
    status = {}
    prev = None
    for line in log.split('\n'):
        line = line.strip()
        if ' ... ' in line: prev = line.split(' ... ')[0]
        for suf, st in ((' ... ok', 'PASSED'), (' ... OK', 'PASSED'), (' ...  OK', 'PASSED'), (' ... skipped', 'SKIPPED'),
                        (' ... FAIL', 'FAILED'), (' ... ERROR', 'ERROR')):
            if line.endswith(suf) or (suf.strip('. ') in ('skipped',) and suf in line):
                status[line.split(' ... ')[0]] = st; break
        if line.startswith('FAIL:') or line.startswith('ERROR:'):
            t = line.split(' ', 1)[1].strip()
            if t.count('(') == 1: status[t] = 'FAILED' if line.startswith('FAIL') else 'ERROR'
        if line.strip() == 'ok' and prev: status[prev] = 'PASSED'
    return status

def worktree(inst, where):
    subprocess.run(['git', '-C', DJANGO, 'worktree', 'add', '-q', '--detach', '-f', where, inst['base_commit']], check=True, capture_output=True)
    return where

def apply(where, patch):
    p = os.path.join(where, '.patch.diff'); open(p, 'w').write(patch)
    r = subprocess.run(['git', 'apply', '-v', '--whitespace=nowarn', p], cwd=where, capture_output=True, text=True)
    os.remove(p); return r.returncode == 0

def run_tests(where, inst, timeout=1800):
    cmd = [PY, 'tests/runtests.py', '--verbosity', '2', '--settings=test_sqlite', '--parallel', '1', *directives(inst['test_patch'])]
    r = subprocess.run(cmd, cwd=where, capture_output=True, text=True, timeout=timeout, env=dict(os.environ, PYTHONPATH=where, LANG='C.UTF-8'))
    return parse(r.stdout + '\n' + r.stderr), r.stdout + r.stderr

def _list(text):
    """A JSON list from a spreadsheet cell; Excel cuts cells at 32,767 characters, so a cut list keeps its whole entries."""
    try:
        return json.loads(text)
    except Exception:
        return re.findall(r'"((?:[^"\\]|\\.)*)"(?=\s*[,\]])', text)

def resolved(status, inst, p2p=None):
    """p2p: the tests that pass both before and with the gold patch (measured, as SWE-bench built its own lists)."""
    f2p = _list(inst['FAIL_TO_PASS']); p2p = p2p if p2p is not None else _list(inst['PASS_TO_PASS'])
    ok = lambda t: status.get(t) in ('PASSED', 'SKIPPED')
    return all(ok(t) for t in f2p) and all(ok(t) for t in p2p), sum(ok(t) for t in f2p), len(f2p), sum(not ok(t) for t in p2p)

def validate(n, seed=86):
    allx = [i for i in instances() if i['repo'] == 'django/django' and str(i['version']) in ('3', '3.0', '3.1', '3.2', '4', '4.0', '4.1', '4.2')]
    rng = random.Random(seed); rng.shuffle(allx)
    out = []
    for inst in allx:
        if len(out) >= n: break
        d = tempfile.mkdtemp(prefix='g86v-', dir='/home/claude/swe'); w = worktree(inst, os.path.join(d, 'w'))
        try:
            ok_t = apply(w, inst['test_patch'])
            st0, _ = run_tests(w, inst); before = resolved(st0, inst, [])
            ok_g = apply(w, inst['patch'])
            st1, log = run_tests(w, inst)
            p2p = sorted(t for t, v in st1.items() if v == 'PASSED' and st0.get(t) == 'PASSED')
            after = resolved(st1, inst, p2p)
            good = ok_t and ok_g and not before[0] and after[0]
            if good: json.dump(dict(f2p=_list(inst['FAIL_TO_PASS']), p2p=p2p), open(os.path.join(PRIV, f"tests_{inst['instance_id']}.json"), 'w'))
            print(f"{inst['instance_id']} v{inst['version']}: before {before[1]}/{before[2]} f2p, gold {after[1]}/{after[2]} f2p, {after[3]} p2p broken -> {'valid' if good else 'INVALID'}", flush=True)
            if good: out.append(inst['instance_id'])
            else: open(os.path.join(PRIV, f"invalid_{inst['instance_id']}.log"), 'w').write(log[-6000:])
        finally:
            subprocess.run(['git', '-C', DJANGO, 'worktree', 'remove', '--force', w], capture_output=True)
    json.dump(out, open(os.path.join(PRIV, 'valid.json'), 'w'), indent=1)
    return out

if __name__ == '__main__':
    if sys.argv[1] == 'validate':
        print(validate(int(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 86))
