"""Gate 80: which emptied functions each builder rebuilt in its own commits (landed or not), from its clone's reflog.
A builder rebuilt a function if one of its commits turned that function from "emptied" (raises NotImplementedError) into
something else. Duplicated: functions rebuilt by 2 or more builders."""
import ast, subprocess
from collections import Counter

def _body(src, name):
    try:
        for n in ast.parse(src).body:
            if isinstance(n, ast.FunctionDef) and n.name == name:
                return ast.get_source_segment(src, n) or ''
    except SyntaxError:
        return None
    return None

def _show(work, rev, path):
    r = subprocess.run(['git', 'show', f'{rev}:{path}'], cwd=work, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None

def rebuilt(work, me, functions):
    revs = subprocess.run(['git', 'log', '--reflog', '--all', f'--author={me}', '--format=%H %P'], cwd=work, capture_output=True, text=True).stdout.split('\n')
    got = set()
    for line in revs:
        parts = line.split()
        if len(parts) < 2: continue
        h, parent = parts[0], parts[1]
        files = set(subprocess.run(['git', 'diff', '--name-only', parent, h], cwd=work, capture_output=True, text=True).stdout.split())
        for f in functions:
            path, name = f.split('::')
            if path not in files or f in got: continue
            before, after = _show(work, parent, path), _show(work, h, path)
            b, a = (_body(before, name) if before else None), (_body(after, name) if after else None)
            if b and 'NotImplementedError("emptied' in b and a and 'NotImplementedError("emptied' not in a:
                got.add(f)
    return got

def duplicated(run, workers, functions):
    import os
    per = {w: sorted(rebuilt(os.path.join(run, 'work', w), w, functions)) for w in workers}
    c = Counter(f for s in per.values() for f in s)
    return per, sum(1 for f in c if c[f] >= 2), len(c)
