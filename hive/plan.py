"""A business goal in, a plan out (the owner: "how Tony just gives him the business"). He states an outcome ("I want
more creators signing up this month"); Claude reads his product in a throwaway copy, finds what stands in the way, and
proposes 2-4 changes in his words, each with the precise instruction its builder gets and, only where needed, the one
decision only he can make. Hive then builds them one after another on one branch (hive/assistant.py pursue)."""
import json, os, re, shutil, subprocess

PLAN = """You are the business owner's assistant, planning how to reach a goal he has for his product. You are in a
throwaway copy of his product: read the code (pages, flows, wording) to find what actually stands in the way of his
goal for his customers. Look before you propose; every step must rest on something you saw in this product.
First break his goal into the 3 to 5 questions that decide it for his customers (who they are here, where they start,
what they must do, what stops or puts them off, why), and answer each from the pages and code. Only cite what you saw;
if the product does not show something, say so rather than assume it.

His goal: "{goal}"

What you know about his business:
{notes}

His standing rules (never plan against them):
{rules}

Propose 2 to 4 changes to the product, most effective first, that together move his goal. Each step must be buildable
in this codebase now, by one builder, in under an hour. Do not propose marketing, ads, outreach, pricing changes or
anything outside the product. For each step:
- "title": what it is, in at most 8 plain words a shop owner would use ("A shorter sign-up form").
- "why": one plain sentence on what you saw that holds his customers back, and how this helps ("Sign-up asks for 9
  things, bank details included, before a creator sees what they'd earn.").
- "build": the exact instruction for the builder: files, behaviour, what to keep, what tests to add.
- "seen": where you saw it: the page or file, and what it shows ("signup.html: 9 required fields, bank details
  among them"). A step with nothing seen is not a step.
- "look": true if the change is mostly about how a page looks or reads.
- "decide": a question only he can answer, because it is about his business (an amount, a promise to customers, what
  can wait), with 2 or 3 short "options"; empty if the step needs nothing from him. Never ask what the code, the page
  or common sense can settle. At most 2 steps may have a question.
Reply with JSON only:
{{"finding": "one sentence: the main thing holding his customers back, as you saw it",
  "steps": [{{"title": "...", "why": "...", "seen": "...", "build": "...", "look": false, "decide": "", "options": []}}]}}"""

PANEL = """Here is a plan to change a product, and what we know about the business and its customers.

His goal: "{goal}"
What we know about his business:
{notes}

The plan (from reading the product):
{plan}

Play a small panel of 4 of his real kinds of customers, as the notes and the product suggest (different situations:
eager, doubtful, busy, one who already left), each with a name, who they are, what they want and what puts them off.
Each reacts to each step in one honest sentence: would it change what they do? Then, as the planner, revise the plan:
keep, reorder, change or drop steps by what the panel showed, and add a step only if the panel exposed something the
product shows (read the product again if you need to). The same rules hold: 2 to 4 steps, each with something seen,
at most 2 questions for him. Treat the panel as a way to think, not as evidence. Reply with JSON only:
{{"panel": [{{"who": "...", "says": "..."}}], "changed": "one sentence: what the panel changed in the plan, or 'nothing'",
  "finding": "...", "steps": [same fields as before]}}"""

CMD = os.environ.get('HIVE_PLAN_CMD', 'claude -p --output-format json --allowedTools Read Grep Glob Bash')

def _json(text):
    m = re.search(r'\{.*\}', text or '', re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except ValueError:
        return None

def clean(plan):
    """A plan Hive can run: 1-4 steps, each with a title and a build instruction; at most 2 questions."""
    if not isinstance(plan, dict):
        return None
    steps = []
    for s in plan.get('steps') or []:
        if not isinstance(s, dict) or not str(s.get('title', '')).strip() or not str(s.get('build', '')).strip():
            continue
        if not str(s.get('seen', '')).strip():   # grounded or not a step (borrowed idea: claims only from what was read)
            continue
        q = str(s.get('decide') or '').strip()
        opts = [str(o).strip() for o in (s.get('options') or []) if str(o).strip()][:3]
        steps.append({'title': str(s['title']).strip()[:80], 'why': str(s.get('why', '')).strip()[:300],
                      'seen': str(s.get('seen', '')).strip()[:300],
                      'build': str(s['build']).strip(), 'look': bool(s.get('look')),
                      'decide': q if q and sum(1 for x in steps if x['decide']) < 2 else '', 'options': opts if q else []})
    steps = steps[:4]
    out = {'finding': str(plan.get('finding', '')).strip()[:300], 'steps': steps}
    if isinstance(plan.get('panel'), list):
        out['panel'] = [p for p in plan['panel'] if isinstance(p, dict)][:5]; out['changed'] = str(plan.get('changed', ''))[:300]
    return out if steps else None

def _ask(copy, prompt, timeout):
    """One Claude call in the copy: (parsed JSON or None, cost). One retry when the reply does not parse."""
    from . import argv
    cost = 0.0
    for _ in range(2):
        try:
            p = subprocess.run(argv(CMD), cwd=copy, input=prompt, capture_output=True, text=True, encoding='utf-8',
                               errors='replace', timeout=timeout)
            out = json.loads(p.stdout)
        except Exception:
            continue
        cost += float(out.get('total_cost_usd') or 0)
        got = None if out.get('is_error') else _json(out.get('result'))
        if got:
            return got, cost
    return None, cost

def make(repo, goal, notes=(), rules=(), timeout=600, panel=None):
    """{'finding', 'steps': [...], 'cost'} for this goal on this product, or None if Claude could not plan it.
    panel (default: on when HIVE_PLAN_PANEL=1): a simulated customer panel reacts and the plan is revised (under test)."""
    from .assistant import _scratch
    panel = os.environ.get('HIVE_PLAN_PANEL', '0') == '1' if panel is None else panel
    work, copy = _scratch(repo)
    notes_text = '\n'.join(f'- {n}' for n in notes) or '(nothing yet)'
    try:
        got, cost = _ask(copy, PLAN.format(goal=goal, notes=notes_text,
                                           rules='\n'.join(f'{k}. {r}' for k, r in enumerate(rules, 1)) or '(none yet)'), timeout)
        plan = clean(got)
        if plan and panel:
            again, c2 = _ask(copy, PANEL.format(goal=goal, notes=notes_text, plan=json.dumps(plan, ensure_ascii=False)), timeout)
            cost += c2
            plan = clean(again) or plan
        if plan:
            plan['cost'] = cost
        return plan
    finally:
        shutil.rmtree(work, ignore_errors=True)

def instruction(step, answer=''):
    """What the builder of one step is told."""
    text = f"{step['title']}. {step['why']}\n\n{step['build']}"
    if step.get('decide') and answer:
        text += f"\n\nThe owner decided: {step['decide']} -> {answer}"
    return text
