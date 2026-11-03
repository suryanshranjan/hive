"""How he talks, so Hive talks back the same way (the owner: "if the founder is a little technical and says something
technical, Hive must catch it and say yes, let's do it"). A technical message is taken as the precise instruction it
is: restated in his terms, not turned into business situations; questions about it are the normal ones an engineer
would ask, only where something real is unclear. Plain words stay the default for an owner who isn't technical.

Once he has written technically twice (or says he is technical), it is remembered for every later conversation."""
import json, os, re

PATH = os.path.join(os.path.expanduser('~'), '.hive', 'profile.json')

STRONG = re.compile(r"\b(api|endpoints?|redis|postgres(ql)?|mysql|mongo(db)?|sqlite|sql|db schema|schema|migrations?|"
                    r"indexes|index on|webhooks?|jwt|oauth|graphql|rest api|grpc|docker|kubernetes|k8s|ci pipeline|cron( job)?|"
                    r"kafka|celery|rabbitmq|typescript|react|next\.?js|vue|svelte|tailwind|django|flask|fastapi|express\.?js|"
                    r"node\.?js|npm|pip install|unit tests?|integration tests?|e2e tests?|refactor\w*|regex|n\+1|latency|"
                    r"p9\d|caching|redis cache|ttl|cdn|orm|foreign key|null check|async|race condition|rate limit\w*|"
                    r"pagination|paginate|debounce|env var\w*|http \d{3}|\d{3} status|status code|stack trace|linter|"
                    r"dto|crud|uuid|json|yaml|s3 bucket|aws lambda|serverless|middleware|cors|csrf|xss|"
                    r"[a-z_]+\.(py|ts|tsx|js|jsx|go|rb|java|sql|css|html)|/[a-z][a-z0-9_/-]* (endpoint|route|api))\b")
SAYS_TECH = re.compile(r"\b(i'?m (a |an )?(developer|engineer|programmer|dev|cto|technical)|i (code|write code|know "
                       r"(python|js|react|sql))|i'?m technical)\b")

def terms(text):
    return sorted({m.group(0).lower() for m in STRONG.finditer(text or '')})

def is_technical(text):
    """Does this message speak in technical terms (a precise instruction an engineer would recognise)?"""
    t = (text or '').lower()
    return bool(SAYS_TECH.search(t)) or len(terms(t)) >= 1

def _load():
    try:
        return json.load(open(PATH))
    except (OSError, ValueError):
        return {}

def technical():
    """Is he a technical owner (remembered)?"""
    return bool(_load().get('technical'))

def notice(text):
    """Count a technical message; after two (or when he says so), he is technical from now on. Returns technical()."""
    p = _load()
    if SAYS_TECH.search((text or '').lower()):
        p['technical'] = True
    elif is_technical(text):
        p['seen'] = p.get('seen', 0) + 1
        if p['seen'] >= 2:
            p['technical'] = True
    else:
        return bool(p.get('technical'))
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    json.dump(p, open(PATH, 'w'))
    return bool(p.get('technical'))

def line(text=''):
    """For Jarvis's facts: how to talk to him now."""
    if technical() or is_technical(text):
        return ("He is technical and writes in technical terms: answer him in the same terms, precisely (file names, "
                "endpoints, errors and test results are welcome); never translate his instruction into business words, "
                "and never water it down.")
    return ''

CLARIFY = """An owner who knows his tech gave his software assistant this instruction for his product:
"{text}"

You are in a copy of his product. Read just enough of the code to understand where this goes. Is anything genuinely
unclear that would change how it is built, which neither his words nor the code settle (for example which data, which
behaviour on a failure, a number he didn't give)? Ask at most 2 short, normal questions an engineer would ask him, in
his terms, each with 2 or 3 likely answers. Never ask what the code or common practice settles; most instructions need
no question at all. Also restate his instruction in one precise line, in his terms, as you will build it.
Reply with JSON only: {{"restated": "...", "questions": [{{"q": "...", "options": ["...", "..."]}}]}}"""

def clarify(repo, text, timeout=300):
    """{'restated', 'questions': [{'q', 'options'}]} for a technical instruction, read against his code; or None."""
    from . import plan
    from .assistant import _scratch
    import shutil
    work, copy = _scratch(repo)
    try:
        got, _ = plan._ask(copy, CLARIFY.format(text=text), timeout)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    if not isinstance(got, dict):
        return None
    qs = [{'q': str(q.get('q', '')).strip(), 'options': [str(o) for o in (q.get('options') or [])][:3]}
          for q in (got.get('questions') or []) if isinstance(q, dict) and str(q.get('q', '')).strip()][:2]
    return {'restated': str(got.get('restated') or '').strip(), 'questions': qs}
