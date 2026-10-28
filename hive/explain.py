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

Write like a calm, capable chief of staff briefing a busy founder: short, warm, confident, no hedging. The owner should
be able to decide each one in a few seconds. For each assumption:
- "context": one short sentence on where this shows up and who notices it (a brand, a creator, the team).
- "example": one short sentence with a concrete made-up case: a real-sounding name, simple numbers (rupees, followers,
  views), and exactly what the product does now.
- "advice": your recommendation in the first person, in one short sentence: "I'd keep it." or "I'd change it: <what>."
  Recommend what most well-run businesses would want here, and what fits the feature's stated rules.
- "alternative": if you advise a change, the change itself in a few plain words (it becomes the owner's answer if they
  accept); otherwise "".
- "impact": 3 if it changes money or what customers see often, 2 if it matters sometimes, 1 if it is a rare edge case.
- "owner_can_judge": false if it is really a technical detail a business owner cannot meaningfully decide.
Never use technical words (numerator, denominator, null, array, field, error, input, function, string, parse, record).
Also write "summary": one plain sentence saying what was built, as you would tell the owner over coffee.

Reply with JSON only, in this shape:
{{"summary": "...", "items": [{{"id": "...", "context": "...", "example": "...", "advice": "...", "alternative": "",
"impact": 3, "owner_can_judge": true}}]}}"""

# In experiments, Hive's own recommendation could sway the owner (anchoring), so HIVE_ADVICE=0 leaves it out.
ADVICE = os.environ.get('HIVE_ADVICE', '1') != '0'

BACKUP = os.path.join(os.path.expanduser('~'), '.hive', 'llm.json')   # {"base_url", "api_key", "model"}; never in a repo

def _json_reply(text):
    if isinstance(text, dict):
        return text
    return json.loads(text[text.index('{'):text.rindex('}') + 1])

def _ask_claude(prompt):
    p = subprocess.run(shlex.split(CMD), input=prompt, capture_output=True, text=True, timeout=300)
    reply = json.loads(p.stdout)
    if isinstance(reply, dict) and (reply.get('is_error') or 'result' not in reply and 'items' not in reply):
        raise RuntimeError('claude call failed')
    return _json_reply(reply.get('result', reply) if isinstance(reply, dict) else reply)

def _ask_backup(prompt):
    """Any OpenAI-compatible endpoint the owner configured (for example NVIDIA NIM), used only when Claude fails."""
    if not os.path.exists(BACKUP):
        return None
    import urllib.request
    cfg = json.load(open(BACKUP))
    body = {'model': cfg['model'], 'temperature': 0.2, 'max_tokens': 4000,
            'messages': [{'role': 'user', 'content': prompt}]}
    req = urllib.request.Request(cfg['base_url'].rstrip('/') + '/chat/completions', data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json', 'Authorization': f"Bearer {cfg['api_key']}"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return _json_reply(json.load(r)['choices'][0]['message']['content'])

def setup_backup():
    """hive llm setup: store a backup model for the plain-words step (default: NVIDIA NIM). The key is typed hidden and
    saved to ~/.hive/llm.json with owner-only permissions."""
    import getpass
    print("\nA backup model puts the builders' decisions into plain words when Claude can't be reached.\n"
          "Note: it receives those decisions, which describe your business rules, so use a provider you trust.")
    base = input('  Endpoint (Enter for NVIDIA NIM: https://integrate.api.nvidia.com/v1) > ').strip() or \
        'https://integrate.api.nvidia.com/v1'
    model = input('  Model (Enter for meta/llama-3.3-70b-instruct) > ').strip() or 'meta/llama-3.3-70b-instruct'
    key = getpass.getpass('  API key (it will not be shown) > ').strip()
    if not key:
        print('  No key given; nothing saved.'); return 1
    os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
    with open(BACKUP, 'w') as f:
        json.dump({'base_url': base, 'api_key': key, 'model': model}, f)
    os.chmod(BACKUP, 0o600)
    try:
        reply = _ask_backup('Reply with JSON only: {"ok": true}')
        print('  Saved, and the backup model answered.' if reply.get('ok') else '  Saved, but the reply looked odd.')
        return 0
    except Exception as e:
        print(f'  Saved, but a test call failed ({e}). Check the key and model with hive llm setup.'); return 1

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
    prompt = PROMPT.format(goal=_goal_summary(goal), items=items)
    reply = None
    for ask in (_ask_claude, _ask_backup):   # Claude Code's login first; the owner's own backup model if that fails
        try:
            reply = ask(prompt)
            if reply:
                break
        except Exception:
            continue
    try:
        if reply is None:
            raise RuntimeError('no model reachable')
        by_id = {a['id']: a for a in assumptions}
        out = {'summary': reply.get('summary') or fallback['summary'], 'items': []}
        for it in reply.get('items', []):
            if it.get('id') not in by_id:
                continue
            text = ' '.join(x for x in (it.get('context'), it.get('example')) if x)
            advice, alt = (it.get('advice') or '', it.get('alternative') or '') if ADVICE else ('', '')
            out['items'].append({'id': it['id'], 'text': text or by_id[it['id']]['text'], 'advice': advice,
                                 'alternative': alt, 'impact': int(it.get('impact') or 2),
                                 'judge': bool(it.get('owner_can_judge', True))})
        seen = {i['id'] for i in out['items']}
        out['items'] += [i for i in fallback['items'] if i['id'] not in seen]   # never drop one silently
        if not out['items'] or reply is None:
            raise RuntimeError('no reply')
    except Exception:
        return dict(fallback, failed=True)   # not cached: try again next time
    json.dump(out, open(cache, 'w'), indent=1)
    return out

def plan(owner_dir, goal, assumptions):
    """(summary, items to show the owner, most important first, at most SHOW; the rest, set aside).
    Raises RuntimeError when the plain-words step could not run, so the owner is never handed the builders' raw list."""
    ex = explain(owner_dir, goal, assumptions)
    if ex.get('failed'):
        raise RuntimeError("I couldn't put the builders' decisions into plain words just now (the model could not be "
                           "reached). Nothing was sent; try again in a few minutes.")
    ranked = sorted((i for i in ex['items'] if i['judge']), key=lambda i: -i['impact'])
    shown = ranked[:SHOW]
    aside = [i for i in ex['items'] if i not in shown]
    return ex['summary'], shown, aside
