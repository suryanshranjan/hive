"""What Hive brings to mind for a message (memory 2.0): the facts that bear on what he just said, not only the last few.

Before, every reply saw his 15 most recent business notes, whatever he asked: a fact from two months ago about a
supplier never came back when he asked about that supplier. Now each reply sees:
  - the facts that match his words (full-text search over everything kept: notes, rules, preferences, deadlines),
  - what is kept about anyone he names,
  - a few of the most recent facts, so the latest context is always there,
best first, at most k. Facts read from outside (mail, documents) are marked as data, never instructions."""
import json, re, time

from . import store

RECENT = 5      # the newest facts, always included
K = 12          # at most this many in a reply

def _project(repo):
    from . import memory
    try:
        return memory.project_key(repo)
    except Exception:
        return ''

def _named_people(text):
    """People he names in this message who are known (by name or another name)."""
    out = []
    low = ' ' + re.sub(r'[^\w\s]', ' ', (text or '').lower()) + ' '
    for p in store.people():
        names = [p['norm']] + json.loads(p.get('aliases') or '[]')
        if any(f' {n} ' in low for n in names if n):
            out.append(p)
    return out

def recall(repo, text, k=K):
    """The facts that bear on his message, best first: [fact dict]."""
    project = _project(repo)
    try:
        store.sync(repo)
    except Exception:
        pass
    now, scored = time.time(), {}
    def add(f, score):
        if f['id'] not in scored or scored[f['id']][1] < score:
            scored[f['id']] = (f, score)
    hits = store.search(text, project=project, k=k * 2)
    top = max([s for _, s in hits] or [1.0]) or 1.0
    for f, s in hits:   # how well it matches, a little for being recent, a little for coming from him
        age_days = (now - f['created']) / 86400
        add(f, 2.0 * s / top + 0.3 / (1 + age_days / 30) + (0.2 if f['trust'] == 'owner' else 0))
    try:   # close in meaning, when the embedding model is here (hive/embed.py): "lentils" finds "dal"
        sem = store.semantic(text, project=project, k=k)
    except Exception:
        sem = []
    if sem:
        best = sem[0][1]
        for f, sim in sem:   # only what stands out from the rest (unrelated facts sit about 0.1 below related ones)
            if sim >= best - 0.08 and sim >= 0.5:
                add(f, 2.0 * sim / best + (0.2 if f['trust'] == 'owner' else 0))
    for p in _named_people(text):
        for f in store.facts_about(p['id'], project=project)[-6:]:
            add(f, 1.5)
    for f in store.live_facts(project, kinds=('note', 'preference', 'deadline', 'person'), limit=RECENT):
        add(f, 0.5)
    best = sorted(scored.values(), key=lambda fs: -fs[1])[:k]
    return [f for f, _ in best]

def render(facts):
    """Facts as lines for a prompt: his own as they are; anything read from outside marked as data."""
    from .explain import untrusted
    own = [f for f in facts if f.get('trust') != 'outside']
    outside = [f for f in facts if f.get('trust') == 'outside']
    lines = []
    for f in own:
        from . import register
        date = f.get('due_at') or f.get('valid_until')
        until = f" ({'due' if f.get('due_at') else 'until'} {time.strftime('%d %b', register.his_time(date))})" if date else ''
        lines.append(f"- {f['text']}{until}")
    if outside:
        lines.append(untrusted('\n'.join(f"- {f['text']} (from {f.get('source') or 'outside'})" for f in outside),
                               'memory'))
    return '\n'.join(lines)
