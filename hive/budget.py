"""What it will cost, before the work; what it has cost, this month; and a cap he sets (the owner, as founder: surprise
bills kill trust). Estimates come from his own past builds on this project (the median of the last few), else
cautious defaults; they are said as "about", never promised."""
import glob, json, os, re, statistics, time

PATH = os.path.join(os.path.expanduser('~'), '.hive', 'budget.json')
DEFAULT = {'build': 1.5, 'step': 0.5, 'plan': 0.3}   # dollars, before this project has history (Gate 106: $0.21-0.43 a
                                                     # plan, $0.23-0.52 a step; Gate 105 fix rounds $0.25)

def _runs():
    from . import assistant
    for h in glob.glob(os.path.join(assistant.RUNS, '*', 'state.json')):
        try:
            yield json.load(open(h)), os.path.getmtime(h)
        except (OSError, ValueError):
            continue

def estimate(repo, kind='build', steps=1):
    """About what this will cost, in dollars."""
    past = sorted(((t, st.get('cost') or 0) for st, t in _runs()
                   if os.path.abspath(st.get('repo', '')) == os.path.abspath(repo) and (st.get('cost') or 0) > 0), reverse=True)
    per = statistics.median([c for _, c in past[:5]]) if past and kind == 'build' else DEFAULT[kind if kind in DEFAULT else 'build']
    total = per * steps + (DEFAULT['plan'] if kind == 'plan' else 0)
    return round(total, 2)

def say(amount):
    """'about $1', 'about $0.40', 'under $0.10'."""
    if amount < 0.1:
        return 'under $0.10'
    return f'about ${amount:.0f}' if amount >= 3 else f'about ${amount:.2f}'.replace('.00', '')

def spent_month(now=None):
    """What builds have cost this calendar month (every project)."""
    lt = time.localtime(now or time.time())
    start = time.mktime((lt.tm_year, lt.tm_mon, 1, 0, 0, 0, 0, 0, -1))
    return round(sum(st.get('cost') or 0 for st, t in _runs() if t >= start), 2)

def cap():
    try:
        return float(json.load(open(PATH)).get('monthly') or 0) or None
    except (OSError, ValueError, TypeError):
        return None

def set_cap(amount):
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    json.dump({'monthly': float(amount)}, open(PATH, 'w'))
    return float(amount)

def over(extra=0.0):
    """None, or a plain sentence: this would take him past his monthly cap."""
    c = cap()
    if c is None:
        return None
    s = spent_month()
    if s + extra <= c:
        return None
    return (f"That would take this month past your ${c:g} limit (spent ${s:.2f} so far, this is {say(extra)}).")

SET = re.compile(r"\b(budget|limit|cap|spend)\b[^.?!$\d]{0,30}\$?\s?(\d+(?:\.\d+)?)|\$\s?(\d+(?:\.\d+)?)\s*(a|per) month")

def set_from(text):
    """'set my budget to $50 a month' -> 50.0, or None."""
    m = SET.search((text or '').lower())
    if not m:
        return None
    return set_cap(m.group(2) or m.group(3))
