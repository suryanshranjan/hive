"""His numbers, so Hive can tell him whether a change worked (the owner: Jarvis says "sign-ups are up 18% since the
shorter form", not only "it's built").

Where they come from, any of:
- a source set up once (`hive numbers setup`, or by his engineer): a command that prints JSON, a web address that
  returns JSON, or a JSON file: {"sign-ups this week": 142, "first deals this week": 31, ...};
- what he tells Jarvis ("we had 120 sign-ups this week"), kept as he said it.
Each reading is kept with its time (~/.hive/numbers/<project>.jsonl), and what Hive did is kept beside it (a plan
agreed, a build sent to his engineer), so a later reading can be compared with the one before the change."""
import json, os, subprocess, time, urllib.request

DIR = os.path.join(os.path.expanduser('~'), '.hive', 'numbers')

def _key(repo):
    from . import memory
    return memory.project_key(repo)

def _path(repo, kind):
    return os.path.join(DIR, f'{_key(repo)}.{kind}')

def source(repo):
    try:
        return json.load(open(_path(repo, 'source.json')))
    except (OSError, ValueError):
        return {}

def set_source(repo, cmd=None, url=None, file=None):
    os.makedirs(DIR, exist_ok=True)
    src = {k: v for k, v in (('cmd', cmd), ('url', url), ('file', file)) if v}
    json.dump(src, open(_path(repo, 'source.json'), 'w'))
    return src

def _clean(values):
    out = {}
    for k, v in (values or {}).items():
        try:
            out[str(k).strip()[:60]] = float(v)
        except (TypeError, ValueError):
            continue
    return out

def fetch(repo, timeout=60):
    """A fresh reading from his source, or {} (none set up, or it failed)."""
    src = source(repo)
    try:
        if src.get('cmd'):
            p = subprocess.run(src['cmd'], shell=True, cwd=repo, capture_output=True, text=True, timeout=timeout)
            return _clean(json.loads(p.stdout))
        if src.get('url'):
            with urllib.request.urlopen(src['url'], timeout=timeout) as r:
                return _clean(json.loads(r.read().decode('utf-8')))
        if src.get('file'):
            return _clean(json.load(open(os.path.join(repo, src['file']))))
    except Exception:
        return {}
    return {}

def record(repo, values, how='source'):
    """Keep one reading. Returns the values kept."""
    values = _clean(values)
    if values:
        os.makedirs(DIR, exist_ok=True)
        with open(_path(repo, 'jsonl'), 'a', encoding='utf-8') as f:
            f.write(json.dumps({'t': time.time(), 'how': how, 'values': values}, ensure_ascii=False) + '\n')
    return values

def readings(repo):
    try:
        return [json.loads(l) for l in open(_path(repo, 'jsonl'), encoding='utf-8') if l.strip()]
    except (OSError, ValueError):
        return []

def mark(repo, what, kind='did'):
    """Something that may move his numbers: Hive did it (a plan agreed, a build sent to his engineer; kind 'did'), or
    a customer hit it (kind 'complaint', for the brief)."""
    os.makedirs(DIR, exist_ok=True)
    with open(_path(repo, 'events'), 'a', encoding='utf-8') as f:
        f.write(json.dumps({'t': time.time(), 'what': what, 'kind': kind}, ensure_ascii=False) + '\n')

def events(repo):
    try:
        return [json.loads(l) for l in open(_path(repo, 'events'), encoding='utf-8') if l.strip()]
    except (OSError, ValueError):
        return []

def refresh(repo):
    """Take a reading from his source now, if there is one; returns it ({} if none)."""
    return record(repo, fetch(repo)) if source(repo) else {}

def _when(t):
    return time.strftime('%b %d', time.localtime(t)).replace(' 0', ' ')

def changes(repo):
    """Plain lines: each number now, and how it moved since the last thing Hive did before it ('since the shorter
    sign-up form went to your engineer on Nov 3: 120 -> 142, up 18%'); else since the first reading."""
    rs = readings(repo)
    if not rs:
        return []
    latest = rs[-1]
    marks = [e for e in events(repo) if e['t'] < latest['t'] and e.get('kind', 'did') == 'did']
    out = []
    for name, now in latest['values'].items():
        series = [r for r in rs if name in r['values']]
        since, what = series[0], None
        if marks:
            m = marks[-1]
            before = [r for r in series if r['t'] <= m['t']]
            if before:
                since, what = before[-1], m['what']
        was = since['values'][name]
        line = f'{name}: {now:g}'
        if since is not latest and was:
            pct = (now - was) / abs(was) * 100
            move = 'no change' if abs(pct) < 1 else f"{'up' if pct > 0 else 'down'} {abs(pct):.0f}%"
            line += (f' ({move} from {was:g} since {what} on {_when(since["t"])})' if what else
                     f' ({move} from {was:g} on {_when(since["t"])})')
        out.append(line)
    return out

TOLD = """A business owner told his assistant: "{text}"
Does he state numbers about his business (a count, an amount, a rate)? Reply with JSON only:
{{"numbers": {{"<what it counts, in his words, short>": <number>}}}} (empty if none)"""

def told(repo, text):
    """Numbers he states in a message ("we had 120 sign-ups this week"), kept; returns them."""
    from . import explain
    got = explain.ask_json(TOLD.format(text=text)) or {}
    return record(repo, got.get('numbers') if isinstance(got, dict) else {}, how='he said')
