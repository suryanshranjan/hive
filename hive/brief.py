"""The morning brief, unprompted (the owner: Jarvis speaks first: "Morning, sir. Sign-ups are up 18% since the shorter
form; two creators complained about the reward, that's your rule 2"). Once a day, after HIVE_BRIEF_HOUR (default 9,
his computer's time), and whenever he asks ("what's new?"): what landed, what waits on him, what customers hit, and
how his numbers moved since what Hive did."""
import glob, json, os, re, time

PATH = os.path.join(os.path.expanduser('~'), '.hive', 'brief.json')

def _last():
    try:
        return json.load(open(PATH))
    except (OSError, ValueError):
        return {}

def due(now=None):
    """True once a day, after the brief hour."""
    now = now or time.time()
    lt = time.localtime(now)
    return lt.tm_hour >= int(os.environ.get('HIVE_BRIEF_HOUR', 9)) and _last().get('date') != time.strftime('%Y-%m-%d', lt)

def _sent(now=None):
    now = now or time.time()
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    json.dump({'date': time.strftime('%Y-%m-%d', time.localtime(now)), 't': now}, open(PATH, 'w'))

def _goal(text):
    t = re.sub(r'\n\n# .*', '', text or '', flags=re.S)
    t = re.sub(r'\(his picture:[^)]*\)|\[photo:[^\]]*\]', '', t)
    return ' '.join(t.split())[:110]

def facts(repo, since):
    """What the brief can say, as plain lines: what landed, what waits on him, customers, numbers."""
    from . import assistant, numbers
    landed, waiting = [], []
    for h in glob.glob(os.path.join(assistant.RUNS, '*', 'state.json')):
        try:
            st = json.load(open(h))
        except (OSError, ValueError):
            continue
        if os.path.abspath(st.get('repo', '')) != os.path.abspath(repo):
            continue
        if os.path.getmtime(h) > since:
            landed.append(f"Built: {_goal(st.get('goal'))}. {st.get('check', '')}")
        if not st.get('shipped') and not st.get('folded') and not st.get('undone') and os.path.getmtime(h) > since - 7 * 86400:
            waiting.append(f"Ready, not yet sent to his engineer: {_goal(st.get('goal'))} (he says \"ship it\").")
    p = assistant.PLAN
    if p.get('steps') and not p.get('running') and p.get('step', 0) == 0:
        waiting.append(f"A plan he held for \"{p.get('goal', '')[:80]}\" (he says \"do the plan\").")
    if p.get('running'):
        landed.append(f"His plan is being built: step {p['step']} of {len(p['steps'])}.")
    complaints = [e['what'] for e in numbers.events(repo) if e.get('kind') == 'complaint' and e['t'] > since]
    numbers.refresh(repo)
    lines = [f'What landed since the last brief: {x}' for x in landed[:5]]
    lines += [f'Waiting on him: {x}' for x in waiting[:3]]
    lines += [f'A customer complained: {c}' for c in complaints[:3]]
    lines += [f'His numbers: {x}' for x in numbers.changes(repo)[:5]]
    if lines:
        from . import budget
        c = budget.cap()
        lines.append(f'Spent on builds this month: ${budget.spent_month():.2f}' + (f' of his ${c:g} limit' if c else ''))
    return lines

def compose(repo, ch=None, since=None):
    """The brief, in Jarvis's voice (at most 5 short lines), or a plain fallback."""
    from . import assistant, telegram
    since = since if since is not None else (_last().get('t') or time.time() - 86400)
    lines = facts(repo, since)
    who = (assistant._who(ch) if ch else '') or 'sir'
    hour = time.localtime().tm_hour
    hello = 'Good morning' if hour < 12 else 'Good afternoon' if hour < 17 else 'Good evening'
    if not lines:
        return f"🐝 {hello}, {who}. A quiet one: nothing new, and nothing waiting on you. Tell me what you want for the business."
    fallback = f"🐝 <b>{hello}, {who}.</b>\n" + '\n'.join('• ' + telegram.esc(l.split(': ', 1)[1]) for l in lines)
    from . import explain
    got = explain.ask_json(assistant.VOICE.format(who=who, facts='\n'.join(lines), task=(
        "Write his morning brief: at most 5 short lines, the most important first (what needs him, then what moved, "
        "then what landed). Numbers exactly as given, with what Hive did that may explain them; never claim a cause "
        "the facts don't support. End with the one thing he could do next.")))
    reply = got.get('reply') if isinstance(got, dict) else None
    return ('🐝 ' + telegram.esc(reply.strip())) if isinstance(reply, str) and reply.strip() else fallback

def send(ch, repo, since=None):
    ch.send(compose(repo, ch, since), html=True)
    _sent()
