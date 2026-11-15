"""What Hive did outside his computer, and on whose yes (the audit, Nov 15: a mail sent, a pull request opened, a page
put live left no record beyond the chat). One JSON line per action in ~/.hive/audit.jsonl, append-only, owner-only;
never a secret, a mail body or a key, only what was done, to what, and the result.

  hive audit [n]     the last n actions (default 20)"""
import json, os, time

def path():
    return os.path.join(os.path.expanduser('~'), '.hive', 'audit.jsonl')

def record(action, target='', approved='owner tap', ok=True, detail=''):
    """Keep one line. Never raises: a full disk must not stop the action it records."""
    try:
        p = path(); os.makedirs(os.path.dirname(p), exist_ok=True)
        line = json.dumps({'at': time.strftime('%Y-%m-%dT%H:%M:%S'), 'action': action, 'target': str(target)[:200],
                           'approved': approved, 'ok': bool(ok), 'detail': str(detail)[:200]}, ensure_ascii=False)
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass

def last(n=20):
    try:
        return [json.loads(l) for l in open(path(), encoding='utf-8').read().splitlines()[-n:] if l.strip()]
    except (OSError, ValueError):
        return []

def show(n=20):
    rows = last(n)
    if not rows:
        print('Nothing recorded yet.'); return 0
    for r in rows:
        print(f"{r['at']}  {'ok ' if r['ok'] else 'FAILED'}  {r['action']}: {r['target']}  ({r['approved']})")
    return 0

def logged(action, target=lambda *a, **k: ''):
    """Decorator: record each call of an outward action and whether it worked (a dict with 'ok', or (ok, why))."""
    import functools
    def wrap(fn):
        @functools.wraps(fn)
        def inner(*a, **k):
            try:
                r = fn(*a, **k)
            except Exception as e:
                record(action, _safe(target, a, k), ok=False, detail=type(e).__name__); raise
            ok = r[0] if isinstance(r, tuple) and r else (r.get('ok') if isinstance(r, dict) else bool(r))
            record(action, _safe(target, a, k), ok=bool(ok))
            return r
        return inner
    return wrap

def _safe(target, a, k):
    try:
        return target(*a, **k)
    except Exception:
        return ''
