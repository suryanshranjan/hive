"""Turn the builders' assumptions into something a business owner can judge in seconds.

Builders write assumptions for engineers ("missing the numerator or the denominator..."). Before the owner sees them,
each one is rewritten with context (where in the product it shows up, who notices), a concrete example with names and
simple numbers, and a yes-or-no question; then they are ranked by how much they change what customers see or pay, and
the ones an owner cannot meaningfully judge are set aside. The rewrite is done once per build by a headless model call
and cached in <owner dir>/explained.json; if it fails, the builders' own words are used."""
import json, os, re, shlex, subprocess

CMD = os.environ.get('HIVE_EXPLAIN_CMD', 'claude -p --output-format json')
SHOW = 8   # at most this many go to the owner, most important first

PROMPT = """You help a busy, non-technical business owner check decisions that software builders made while building a
feature in the owner's product. The owner knows the business well but not code.

The feature that was built:
{goal}

The builders' assumptions (decisions the instructions did not cover), as JSON:
{items}

For each assumption, write what the owner will read:
- "context": one short sentence on where this shows up in the product and who notices it (a brand, a creator, the team).
- "example": one or two sentences with a concrete made-up case: real-sounding names, simple numbers (rupees, followers,
  views), and exactly what the product would show or do.
- "question": a short yes-or-no question, for example "Is that what you want?"
- "impact": 3 if it changes money or what customers see often, 2 if it matters sometimes, 1 if it is a rare edge case.
- "owner_can_judge": false if it is really a technical detail a business owner cannot meaningfully decide.
Never use technical words (numerator, denominator, null, array, field, error, input, function, string, parse, record).
Also write "summary": one plain sentence saying what was built, as you would tell the owner over coffee.

Reply with JSON only, in this shape:
{{"summary": "...", "items": [{{"id": "...", "context": "...", "example": "...", "question": "...", "impact": 3,
"owner_can_judge": true}}]}}"""

def _goal_summary(goal):
    text = re.sub(r'^#+\s*(goal:?)?\s*', '', goal.strip(), flags=re.I)
    return text[:3000]

def explain(owner_dir, goal, assumptions):
    """{'summary': str, 'items': [{id, text, impact, judge}]} for the owner, cached; falls back to the builders' words."""
    cache = os.path.join(owner_dir, 'explained.json')
    if os.path.exists(cache):
        return json.load(open(cache))
    fallback = {'summary': _goal_summary(goal).split('\n')[0][:200],
                'items': [{'id': a['id'], 'text': a['text'], 'impact': 2, 'judge': True} for a in assumptions]}
    if not assumptions:
        return fallback
    items = json.dumps([{'id': a['id'], 'assumption': a['text']} for a in assumptions], indent=1)
    try:
        p = subprocess.run(shlex.split(CMD), input=PROMPT.format(goal=_goal_summary(goal), items=items),
                           capture_output=True, text=True, timeout=300)
        reply = json.loads(p.stdout)
        reply = reply.get('result', reply) if isinstance(reply, dict) else reply
        if isinstance(reply, str):
            reply = json.loads(reply[reply.index('{'):reply.rindex('}') + 1])
        by_id = {a['id']: a for a in assumptions}
        out = {'summary': reply.get('summary') or fallback['summary'], 'items': []}
        for it in reply.get('items', []):
            if it.get('id') not in by_id:
                continue
            text = ' '.join(x for x in (it.get('context'), it.get('example'), it.get('question')) if x)
            out['items'].append({'id': it['id'], 'text': text or by_id[it['id']]['text'],
                                 'impact': int(it.get('impact') or 2), 'judge': bool(it.get('owner_can_judge', True))})
        seen = {i['id'] for i in out['items']}
        out['items'] += [i for i in fallback['items'] if i['id'] not in seen]   # never drop one silently
    except Exception:
        out = fallback
    json.dump(out, open(cache, 'w'), indent=1)
    return out

def plan(owner_dir, goal, assumptions):
    """(summary, items to show the owner, most important first, at most SHOW; the rest, set aside)."""
    ex = explain(owner_dir, goal, assumptions)
    ranked = sorted((i for i in ex['items'] if i['judge']), key=lambda i: -i['impact'])
    shown = ranked[:SHOW]
    aside = [i for i in ex['items'] if i not in shown]
    return ex['summary'], shown, aside
