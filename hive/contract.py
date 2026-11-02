"""The goal's stated interfaces, checked against the delivered code (Gate 84).

Gate 83: after an owner's answer, a builder added keys to a function's result that the goal had fixed as exactly
{'amount': ..., 'method': ...}; the builders had asked 3 questions, so the review was skipped and nothing caught it.
When the review is skipped, Hive now reads the interfaces the goal states (file, function, arguments, and the keys of a
dict result), checks the delivered code against them from its syntax, and sends a builder to put back anything that
differs. It costs the owner nothing.

Only what the goal states outright is checked, and only where the code shows it plainly (a function missing, an argument
renamed, a returned dict literal with other keys). Anything else is left alone, so the check does not cry wolf."""
import ast, json, os, re

STATED = """A software goal follows. List every function it names explicitly, with what it states about each: the file, the
function's name, its arguments in order (only if the goal lists them), and, if the goal states the result as a dict with
named keys, those keys exactly as written. Do not add anything the goal does not state.

Goal:
{goal}

Reply with JSON only: {{"functions": [{{"file": "path or null", "name": "...", "args": ["..."] or null,
"result_keys": ["..."] or null}}]}}"""

def stated(goal):
    """The interfaces the goal states, as a list of dicts; [] if none or no model answers."""
    from . import explain
    got = explain.ask_json(STATED.format(goal=(goal or '').strip()[:6000])) or {}
    out = []
    for f in got.get('functions', []) if isinstance(got, dict) else []:
        if isinstance(f, dict) and isinstance(f.get('name'), str) and f['name'].strip():
            out.append(dict(file=f.get('file') if isinstance(f.get('file'), str) else None, name=f['name'].strip(),
                            args=[a for a in f['args'] if isinstance(a, str)] if isinstance(f.get('args'), list) else None,
                            result_keys=[k for k in f['result_keys'] if isinstance(k, str)]
                            if isinstance(f.get('result_keys'), list) and f['result_keys'] else None))
    return out

def _module(path):
    try:
        return ast.parse(open(path, encoding='utf-8', errors='replace').read())
    except (SyntaxError, OSError):
        return None

def _find(code_dir, iface):
    """(path, FunctionDef) for the stated function, or (None, None)."""
    paths = [os.path.join(code_dir, iface['file'])] if iface.get('file') else []
    if not paths or not os.path.exists(paths[0]):
        paths = [os.path.join(r, f) for r, ds, fs in os.walk(code_dir) for f in fs if f.endswith('.py')
                 and '.git' not in r and 'test' not in f]
    for p in paths:
        try:
            tree = ast.parse(open(p, encoding='utf-8', errors='replace').read())
        except (SyntaxError, OSError):
            continue
        for n in tree.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == iface['name']:
                return p, n
    return None, None

def _returned_keys(fn, module=None, depth=2):
    """The key sets of every dict literal the function returns, directly or through a helper in the same file that it
    returns the result of (Gate 97: `return _split(order, ...)` hid a result with extra keys), up to `depth` helpers deep."""
    helpers = {n.name: n for n in (module.body if module else []) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    sets = []
    def walk(node):
        for c in ast.iter_child_nodes(node):
            if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                continue
            if isinstance(c, ast.Return) and isinstance(c.value, ast.Dict):
                if all(isinstance(k, ast.Constant) and isinstance(k.value, str) for k in c.value.keys):
                    sets.append((c.lineno, [k.value for k in c.value.keys]))
            elif (isinstance(c, ast.Return) and isinstance(c.value, ast.Call) and isinstance(c.value.func, ast.Name)
                  and depth > 0 and c.value.func.id in helpers and helpers[c.value.func.id] is not fn):
                sets.extend(_returned_keys(helpers[c.value.func.id], module, depth - 1))
            walk(c)
    walk(fn)
    return sets

def check(goal, code_dir, interfaces=None):
    """Every way the delivered code differs from an interface the goal states: [{'name', 'file', 'problem'}]."""
    out = []
    for iface in interfaces if interfaces is not None else stated(goal):
        if not iface.get('file') or not re.fullmatch(r'[A-Za-z_]\w*', iface['name']):
            continue   # Gate 94: only a function the goal places in a file, named as code (a bug report's "QuerySet.alias",
                       # "ExpressionWrapper" or "URL translation function" raised three false alarms)
        path, fn = _find(code_dir, iface)
        where = os.path.relpath(path, code_dir) if path else iface.get('file')
        if fn is None:
            out.append(dict(name=iface['name'], file=where, problem=f"`{iface['name']}` is not in the code"))
            continue
        if iface.get('args'):
            have = [a.arg for a in fn.args.posonlyargs + fn.args.args]
            if have[:len(iface['args'])] != iface['args']:
                out.append(dict(name=iface['name'], file=where, problem=f"its arguments are ({', '.join(have)}); the goal "
                                f"states ({', '.join(iface['args'])})"))
        if iface.get('result_keys'):
            want = set(iface['result_keys'])
            for line, keys in _returned_keys(fn, _module(path)):
                if set(keys) != want:
                    extra, missing = sorted(set(keys) - want), sorted(want - set(keys))
                    out.append(dict(name=iface['name'], file=where, problem=(
                        f"line {line} returns a dict with " + ', '.join(f"`{k}`" for k in keys) + "; the goal states exactly "
                        + ', '.join(f"`{k}`" for k in iface['result_keys'])
                        + (f" (extra: {', '.join(extra)})" if extra else '') + (f" (missing: {', '.join(missing)})" if missing else ''))))
                    break
    return out

def note(problems):
    """The instruction for the builder that puts the stated interfaces back."""
    return ("\n\n# Put back what the goal states\n\nThe goal fixes these interfaces, and other code relies on them exactly. The "
            "build differs:\n" + '\n'.join(f"- `{p['file']}`, `{p['name']}`: {p['problem']}" for p in problems) +
            "\n\nMake the code match the goal exactly: same names, same arguments, and a result with exactly the stated keys. "
            "Keep the behaviour the owner's rules and answers asked for inside that form. If an answer seems to need more "
            "than the form allows, keep the form and say so in your land message. Change any test that asserts the old form, "
            "and leave everything else alone.\n")
