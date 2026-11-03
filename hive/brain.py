"""The company brain: Hive learns his business from what he already has (the founder's view: it should know the
business without being told it twice). He sends a document on Telegram (a policy, a pitch deck as PDF, notes,
FAQs), or his engineer runs `hive brain add <file or folder>`; Hive reads it, keeps the lasting facts as business notes
(the same notes plans and answers use), and keeps how-the-product-should-behave statements as his rules only when the
document plainly states them. Text, Markdown, CSV, JSON, HTML and PDF (with pypdf installed)."""
import json, os, re

READ = """Here is a document from a business owner about his business ("{name}"):
---
{text}
---
What does it say that his software assistant should remember for good: who his customers are, what he offers (prices,
rewards, promises, timings), how the business works, its limits and policies? Keep each as one short plain sentence,
the facts exactly as written (numbers included), at most 15, most useful first. Separately, list the statements that
plainly say how his product must behave (a rule a builder could test), at most 8, exactly as the document states them.
Reply with JSON only: {{"facts": ["..."], "rules": ["..."]}}"""

TEXT = ('.txt', '.md', '.markdown', '.csv', '.json', '.html', '.htm', '.rst', '.yaml', '.yml')

def text_of(path, limit=60000):
    """The words in a document, or '' if Hive can't read this kind."""
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == '.pdf':
            try:
                from pypdf import PdfReader
            except ImportError:
                return ''
            return '\n'.join((p.extract_text() or '') for p in PdfReader(path).pages)[:limit]
        if ext in TEXT or ext == '':
            t = open(path, encoding='utf-8', errors='replace').read()
            if ext in ('.html', '.htm'):
                t = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', t, flags=re.S | re.I); t = re.sub(r'<[^>]+>', ' ', t)
            return t[:limit]
    except Exception:
        return ''
    return ''

def learn(repo, path, name=None):
    """Read one document and keep what lasts. Returns {'facts': [...], 'rules': [...]} kept, or None if unreadable."""
    from . import explain, memory
    text = text_of(path)
    if not text.strip():
        return None
    got = explain.ask_json(READ.format(name=name or os.path.basename(path), text=text)) or {}
    facts = [str(f).strip() for f in (got.get('facts') or []) if str(f).strip()][:15]
    rules = [str(r).strip() for r in (got.get('rules') or []) if str(r).strip()][:8]
    for f in facts:
        memory.add_note(repo, f)
    have = {r['text'].lower() for r in memory.load(repo)}
    for r in rules:
        if r.lower() not in have:
            memory.add(repo, r, 'document')
    return {'facts': facts, 'rules': rules}

def learn_all(repo, target):
    """A file or a folder of them. Returns (documents read, facts kept, rules kept)."""
    files = [target] if os.path.isfile(target) else [os.path.join(d, f) for d, _, fs in os.walk(target) for f in fs]
    n = facts = rules = 0
    for f in files:
        got = learn(repo, f)
        if got:
            n += 1; facts += len(got['facts']); rules += len(got['rules'])
    return n, facts, rules

DOC = re.compile(r'\[document: ([^|\]]+) \| ([^\]]+)\]')
