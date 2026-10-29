"""Interview first: before building, Hive asks the owner about the situations where his rules are likely to matter, and
his answers become rules the builders must encode as tests.

Gates 30-35: the founder answered 48 of 48 concrete situations (28 differing from the obvious default) but reviewed
lists of the builders' decisions poorly (half found, all kept, none marked). So the owner's rules are asked for up front,
the way he answers best; the review after the build stays as a short safety net."""
import json, os, re

from . import explain, telegram

PLAN = """Software builders are about to build this feature for a business:
{goal}

List the decisions the code for this feature must take that the business owner could rule on (business outcomes, not
technical choices): each one a case the product must handle, in plain words, with the outcome a careful builder would
pick if nobody told him. If the description names the cases (a table, a list of situations, an interface), cover every
one of them. Leave out any decision the company's own documents (if included) already settle clearly; a document
that only says "as usual" or "the standard" does not settle it. One entry per decision: when the outcome depends on a number (days late, days waited, rounds used), that
is still one decision, not one per number. Reply with JSON only: {{"decisions": [{{"case": "...", "default": "..."}}]}}"""

WRITE = """You are preparing a short interview with a busy, non-technical business owner before his software builders start
work. The feature to build:
{goal}
{rulings}{decisions}
List the {n} situations where his own business rules are most likely to matter and differ from what builders would
assume: money, timing, limits, exceptions, missing information, conflicts between people. Skip anything the feature
description already settles. Each situation is one concrete case in plain words (names, rupees, days), with 2 or 3
realistic outcomes a business might choose, clearly different from each other. No technical words. For each, add
"why": one short line on what it costs his business if the builders simply guess (money paid out wrongly, an angry
customer, a legal risk, abuse), so he sees the question is worth his time.

Reply with JSON only: {{"situations": [{{"situation": "...", "options": ["...", "...", "..."], "why": "..."}}]}}"""

FROM_DECISIONS = """
These are the decisions the builders' code must take, each with the outcome they would pick if nobody told them:
{listing}
Ask only about these decisions, one situation for every decision, in this order (even ones that look minor: an
owner's surprising rules are often there, Gate 36). In each situation, one option is the builders' outcome in plain
words; the others are real alternatives. Never write two situations about the same decision: where a number matters,
ask once and let the options name the cut-off (for example "Accepted up to 3 days late, refused after that").
"""

READ = """An owner answered a question about how his product should behave.

Situation: {situation}
His answer: {answer}

Write his rule as one clear sentence a software builder can implement and test. Keep his meaning exactly; add nothing.
Reply with JSON only: {{"rule": "..."}}"""

SAME = """These questions will be put to a busy business owner, one after another:
{listing}

Which of them ask about the same decision, so that his answer to one would settle the other (for example the same case
with a different number of days)? Reply with JSON only: {{"same": [[1, 2], ...]}} (groups of question numbers; an empty
list if none)."""

SETTLED = """A business owner is answering questions about how his product should behave. He just answered:
Question: {situation}
His answer: {answer}

These questions are still to come:
{listing}

Think like his assistant: which of them does his answer already decide, given what it tells you about how he runs his
business, so asking would make him repeat himself? Only count a question if his answer clearly settles it. Reply with JSON only: {{"settled": [numbers]}} (an empty list if none)."""

MAX_QUESTIONS = 20   # about 5 minutes on a phone
MAX_WITH_INPUTS = 30   # when unusual input is asked too (Gate 40)

INPUTS = """
Unusual input is a business decision too: what the customer, the staff or the report sees when a value is missing,
blank or unreadable, in the wrong format, in another letter case or with extra spaces or separators, out of the usual
range (zero, negative, very large), or when a calculation leaves a fraction to round. List the business outcomes first,
then every such case the code must handle, each as its own decision with the outcome a careful builder would pick.
"""   # Gate 39: all 8 decisions the interview never asked were of this kind

def _dedupe(qs):
    """Drop questions that ask the same decision as an earlier one (Gate 37: the founder found the interview redundant;
    one decision had been asked at 3 and at 7 days, another at 2 and 9 days late)."""
    if len(qs) < 2:
        return qs
    listing = '\n'.join(f"{k}. {q['situation']}" for k, q in enumerate(qs, 1))
    got = explain.ask_json(SAME.format(listing=listing)) or {}
    drop = set()
    for group in got.get('same', []):
        nums = sorted(n for n in group if isinstance(n, int) and 1 <= n <= len(qs))
        drop |= set(nums[1:])
    kept = [q for k, q in enumerate(qs, 1) if k not in drop]
    return [dict(q, id=f'q{k:02d}') for k, q in enumerate(kept, 1)]

def settled_by(situation, answer, remaining):
    """Which of the remaining questions his answer (a tap or his own words) already decides (ids), so he is not asked
    twice (the founder: "Hive should understand the context from one situation and not ask similar questions")."""
    if not remaining:
        return []
    listing = '\n'.join(f"{k}. {q['situation']}" for k, q in enumerate(remaining, 1))
    got = explain.ask_json(SETTLED.format(situation=situation, answer=answer, listing=listing)) or {}
    return [remaining[n - 1]['id'] for n in got.get('settled', []) if isinstance(n, int) and 1 <= n <= len(remaining)]

def decisions(goal, inputs=False):
    """The business decisions the build must take, each with the builders' default (Gate 36: questions written from the
    description alone covered 4 of 9 of the owner's surprising rules; most asked about things the code never decides).
    With `inputs`, what the product shows for unusual input is listed too (Gate 40)."""
    plan = PLAN.replace('Reply with JSON only', INPUTS.strip() + ' Reply with JSON only') if inputs else PLAN
    got = explain.ask_json(plan.format(goal=re.sub(r'^#+\s*(goal:?)?\s*', '', goal.strip(), flags=re.I)[:24000])) or {}
    return [d for d in got.get('decisions', []) if isinstance(d, dict) and d.get('case')][:40]

def write_situations(goal, rulings=None, n=12, inputs=False):
    past = ("\nRules he has already given (don't ask about these again):\n" + '\n'.join(f'- {r}' for r in rulings[-40:])
            + '\n') if rulings else ''
    ds = decisions(goal, inputs)
    if ds:   # cover every decision the code takes, up to MAX_QUESTIONS: ranking cut 2 of the owner's 9 surprises (Gate 37 pilot)
        n = min(max(n, len(ds)), MAX_WITH_INPUTS if inputs else MAX_QUESTIONS)
    plan = FROM_DECISIONS.format(listing='\n'.join(f"- {d['case']} (builders' outcome: {d.get('default') or 'unsure'})"
                                                    for d in ds)) if ds else ''
    got = explain.ask_json(WRITE.format(goal=explain._goal_summary(goal), rulings=past, decisions=plan, n=n)) or {}
    out = []
    for k, s in enumerate(got.get('situations', [])[:n], 1):
        opts = [o for o in s.get('options', []) if isinstance(o, str) and o.strip()][:3]
        if s.get('situation') and len(opts) >= 2:
            out.append({'id': f'q{k:02d}', 'situation': s['situation'].strip(), 'options': opts}
                       | ({'why': s['why'].strip()} if isinstance(s.get('why'), str) and s['why'].strip() else {}))
    return _dedupe(out)

def _rule(situation, answer):
    got = explain.ask_json(READ.format(situation=situation, answer=answer)) or {}
    return (got.get('rule') or f'{situation} -> {answer}').strip()

AMEND = """Hive showed a business owner one of his rules, as it will be built:
{rule}

He replied: {reply}

Amend his rule as he now means it. Keep every part of the shown rule he did not object to, and apply his correction or
addition exactly. If his reply restates the whole rule, use his reply. Plain words a builder can implement and test;
add nothing of your own. Reply with JSON only: {{"rule": "..."}}"""

def _amend(rule, reply):
    """His reply to a rule he was shown ("mostly right, but you left out a minimum") amends it; it does not replace it.
    Gate 39: the correction alone became the rule, and the fee's rate and cap he had just confirmed were lost."""
    got = explain.ask_json(AMEND.format(rule=rule, reply=reply)) or {}
    return (got.get('rule') or f'{rule} Correction from the owner, which overrides anything above that it contradicts: '
            f'{reply}').strip()

def interview(goal, ch=None, rulings=None, n=12, ask=None, situations=None, poll=20, save=None, sheet=True, inputs=False):
    """Run the interview. Returns the owner's rules, one plain sentence each. On the phone if `ch` is given, otherwise
    in the terminal (`ask(prompt)` returns his typed answer). With `save` (a file path), the questions, his answers and
    the readings are kept as they come, so a rerun after a stop picks up where he left off."""
    kept = telegram._load(save and save + '.questions.json')
    qs = situations or kept.get('qs') or write_situations(goal, rulings, n, inputs)
    telegram._save(save and save + '.questions.json', {'qs': qs})
    if not qs:
        return []
    if ch:
        got = telegram.verdicts(ch, qs, intro=f"Before the builders start, {len(qs)} quick situations where your rules "
                                              "matter. Tap what should happen at your company, or tell me in your own "
                                              f"words. About {max(2, round(len(qs) / 4))} minutes; it saves you checking "
                                              "their work afterwards.",
                              poll=poll, save=save and save + '.answers.json', after_text=settled_by,
                              context=explain._goal_summary(goal)[:1500])
    else:
        got = {}
        for k, q in enumerate(qs, 1):
            if got.get(q['id']) == telegram.SETTLED:
                continue
            opts = '  '.join(f'{chr(65 + i)}) {o}' for i, o in enumerate(q['options']))
            a = (ask or input)(f"\n{k} of {len(qs)}. {q['situation']}\n  {opts}\n  Your answer (a letter, or your own words) > ").strip()
            for _ in range(3):   # "what does this mean?" gets an explanation, not taken as his answer
                if not a or re.fullmatch(r'([A-Ca-c])[).]?', a):
                    break
                kind, why = telegram.understand(a, (q['situation'], q['options'], explain._goal_summary(goal)[:1500]))
                if kind != 'question':
                    a = why or a   # a choice he picked in his own words counts as that choice
                    break
                a = (ask or input)(f"  {why}\n  So, what should happen? (a letter, or your own words) > ").strip()
            m = re.fullmatch(r'([A-Ca-c])[).]?', a)
            got[q['id']] = q['options'][ord(m.group(1).upper()) - 65] if m and ord(m.group(1).upper()) - 65 < len(q['options']) else a
            rest = [x for x in qs[k:] if x['id'] not in got]
            if got[q['id']] and rest:   # his answer may already settle what comes next
                done = settled_by(q['situation'], got[q['id']], rest)
                for i in done:
                    got[i] = telegram.SETTLED
                if done:
                    print(f"  (Your answer also settles {len(done)} of the coming question{'s' if len(done) != 1 else ''}; "
                          "I'll skip " + ('it.)' if len(done) == 1 else 'them.)'))
    rules, free = [], []
    for q in qs:
        a = got.get(q['id'], '')
        if not a or a == telegram.SETTLED or no_rule(a):   # settled by an earlier answer, or "whatever you feel like"
            continue
        if a in q['options']:
            rules.append(f"{q['situation']} -> {a}")
        else:
            free.append((q, a))
    if free:   # his own words: write each as a rule and let him confirm it
        old = {d['id']: d for d in telegram._load(save and save + '.drafts.json').get('drafts', [])}
        drafts = [old[q['id']] if q['id'] in old and old[q['id']]['own'] == a else
                  {'id': q['id'], 'situation': _rule(q['situation'], a), 'own': a, 'asked': q['situation'],
                   'options': ["Yes, exactly", 'Not quite']}
                  for q, a in free]
        telegram._save(save and save + '.drafts.json', {'drafts': drafts})
        if ch:
            ok = telegram.verdicts(ch, [{'id': d['id'], 'situation': f"Your rule, as I'll build it: {d['situation']}",
                                         'options': d['options']} for d in drafts],
                                   intro='Thank you. A few you answered in your own words; here is how I read them.',
                                   poll=poll, save=save and save + '.readings.json',
                                   context=explain._goal_summary(goal)[:1500])
        else:
            ok = {d['id']: (ask or input)(f"\nYour rule, as I'll build it: {d['situation']}\n  Right? (Enter = yes, or "
                                         "say what's off) > ").strip() or 'Yes, exactly' for d in drafts}
        for d in drafts:   # Gate 36: "It's exactly that's the thing I want" became a rule, and corrections lost
            v = ok.get(d['id'], 'Yes, exactly')   # the situation they were about
            asked = d.get('asked', '')
            if v == 'Yes, exactly' or is_yes(v):
                rules.append(d['situation'])
            elif v == 'Not quite':   # his own words stand
                rules.append(f"{asked} -> {d['own']}" if asked else d['own'])
            elif not no_rule(v):   # "mostly right, but ...": the reading, amended (Gate 39)
                rules.append(_amend(d['situation'], v))
    if sheet and len(rules) >= 2:
        rules = rule_sheet(rules, ch, ask, poll, save)
    if rulings and rules:
        rules = _settle(rules, list(rulings), ch, ask, poll)
    return rules

GENERAL = """A business owner answered questions about how his product should behave. His answers, numbered:
{listing}

Turn them into his policy: one general rule per decision, in plain words a builder can implement and test, saying when
it applies and what happens ("Whenever ..., ..."). Keep his meaning exactly and add nothing. Merge answers about the same
decision into one rule. If two answers about the same decision disagree, do not choose: list them under "disagree",
with a plain question and the two choices.
Reply with JSON only: {{"rules": [{{"rule": "...", "from": [1]}}], "disagree": [{{"from": [2, 5], "question": "...",
"option_a": "...", "option_b": "..."}}]}}"""

def rule_sheet(rules, ch=None, ask=None, poll=20, save=None):
    """Decide once, as a rule (Gate 37: his answers to two framings of one decision agreed 1 of 8 times in a session).
    His answers become one general rule per decision; answers that disagree are put to him; then he sees the whole
    sheet and marks only what is wrong. Returns the confirmed rules. If no model is reachable, the answers stand."""
    path = save and save + '.sheet.json'
    kept = telegram._load(path)
    if kept.get('done'):
        return kept['rules']
    got = kept.get('draft') or explain.ask_json(GENERAL.format(
        listing='\n'.join(f'{n}. {r}' for n, r in enumerate(rules, 1)))) or {}
    general = [r['rule'].strip() for r in got.get('rules', []) if isinstance(r, dict) and r.get('rule')]
    if not general:
        return rules
    telegram._save(path, {'draft': got})
    for n, c in enumerate(d for d in got.get('disagree', []) if isinstance(d, dict) and d.get('question')):
        opts = [c.get('option_a') or 'The first', c.get('option_b') or 'The second']
        if ch:
            ch.send(f"⚖️ <b>Two of your answers pull different ways on one decision.</b> Which is your policy?\n\n"
                    f"{telegram.esc(c['question'])}\n\n<b>1.</b> {telegram.esc(opts[0])}\n<b>2.</b> {telegram.esc(opts[1])}",
                    html=True, buttons=[('1', f'dis|{n}|0'), ('2', f'dis|{n}|1')])
            kind, a = telegram._wait(ch, poll, {f'dis|{n}|0', f'dis|{n}|1'})
            chosen = opts[int(a[-1])] if kind == 'tap' else a
        else:
            a = (ask or input)(f"\nTwo of your answers pull different ways on one decision. Which is your policy?\n"
                               f"{c['question']}\n  A) {opts[0]}  B) {opts[1]}\n  > ").strip()
            chosen = opts[0] if a.upper() in ('A', '1') else opts[1] if a.upper() in ('B', '2') else a
        general.append(f"{c['question']} -> {chosen}")
    general = confirm_sheet(general, ch, ask, poll)
    telegram._save(path, {'draft': got, 'done': True, 'rules': general})
    return general

SHEET_TITLE = 'Your rules for this feature, as the builders will follow them'
SHEET_NOTE = 'Each one applies to every case like it, not just the example.'

PAGED_FROM = 10   # longer sheets go page by page

POSITIVE = ('👍', '👌', '✅', '🙂', '😊', '👏', '💯', '🆗', '✔')
ASKING = re.compile(r"^(what|why|how|which|when|who|where|kya|kyu|kyon|kaise|matlab|meaning|explain|samjha|samajh)\b|\?\s*$|\b(mean|means|meaning|matlab|explain|samjh\w*|unclear|"
                    r"confus\w*|don't understand|dont understand|nahi samjha)\b")
NUMBERS_ONLY = re.compile(r"(rule|rules|no\.?|number|#|and|,|&|\s|\d)+")
LEAD_FIX = re.compile(r"^(?:rule\s*|no\.?\s*|#\s*)?(\d+)\s*(?:[:.\-–)]|\s)\s*(.*\S.*)$", re.S | re.I)
WRONG_WORDS = re.compile(r"\b(is|are|both|seems?|looks?)?\s*(wrong|incorrect|not right|galat( hai| h)?|theek nahi)\b")
KEEP = re.compile(r"^(no[, ]+)?(it'?s|its|that'?s|thats)?\s*(fine|right|correct|ok(ay)?)\b|^(keep|leave)( it| that)?\b|"
                  r"^(actually )?(it'?s|its) (fine|right|correct)\b|^(theek|sahi) (hai|h)\b")

def page_reply(kind, a, valid):
    """What his reply on a page of the sheet means, in every form it has come in. ('fine', None) | ('marks', [n]) |
    ('fix', (n, words)) | ('out', [n]) | ('question', words) | ('note', words). Gate 45: a question was filed as a
    correction, and "what does rule 6 mean?" would have marked rule 6 wrong."""
    if kind == 'tap':
        return ('fine', None) if a == 'pg|ok' else ('marks', [int(a.split('|')[1])])
    t = (a or '').strip()
    letters = re.sub(r'[^\w]', '', t)
    if not letters:   # "??", "👍", "✅"
        return ('fine', None) if any(e in t for e in POSITIVE) else ('question', t)
    low = ' '.join(t.lower().split())
    if ASKING.search(low):   # a question first, even with a number in it
        return 'question', t
    if is_yes(t) or no_rule(t) or section_fine(t):
        return 'fine', None
    bare = WRONG_WORDS.sub(' ', low).strip(' .!')   # "3 and 5 are wrong", "rule 6 is wrong": marks, not a fix
    if bare != low and NUMBERS_ONLY.fullmatch(bare or 'x'):
        low = bare
    if NUMBERS_ONLY.fullmatch(low):   # "3", "3 and 5", "rule 3, 4"
        nums = [int(x) for x in re.findall(r'\d+', low)]
        bad = [n for n in nums if n not in valid]
        return ('out', bad) if bad else ('marks', nums)
    m = LEAD_FIX.match(t)
    if m and int(m.group(1)) in valid:   # "6 should be 7 days", "rule 6: only for brands"
        return 'fix', (int(m.group(1)), m.group(2).strip())
    if m:
        return 'out', [int(m.group(1))]
    return 'note', t

STOP = {'the', 'a', 'an', 'is', 'are', 'what', 'if', 'they', 'it', 'to', 'of', 'on', 'in', 'and', 'or', 'for', 'happens',
        'does', 'do', 'mean', 'means', 'this', 'that', 'make', 'be', 'should', 'how', 'when', 'kya', 'hai', 'ka', 'ki', 'ko'}

def _words(t):
    return {w.rstrip('s') for w in re.findall(r'[a-z0-9]+', t.lower()) if w not in STOP and len(w) > 1}

def related(items, text, top=2):
    """The rules on a page his words are about, by shared words: what Hive can still show him with no model to ask
    (a dry run with no model answered "what happens if they verify on day 31?" with "which rule is unclear?")."""
    ask = _words(text)
    scored = sorted(((len(ask & _words(r)), n, r) for n, r in items), key=lambda x: (-x[0], x[1]))
    return [(n, r) for s, n, r in scored[:top] if s]

def _area_of(items, text, page_area):
    """The area his words belong to: the closest rule's own area, not a shared page's joined title."""
    near = related(items, text, 1)
    head = near[0][1].partition(':')[0] if near and ':' in near[0][1] else ''
    return head.split(' (')[0].strip() or page_area.split(' · ')[0]

def _explain(ch, a, rules_text, goal, code=None):
    """His question about rules on the sheet, answered in context. With `code` (the build's own folder), Claude reads
    the code and answers what it does, with an example (the owner: "agentic level contextual answers"); otherwise, or
    if that fails, from the rules and the goal."""
    if code and os.path.isdir(code):
        from .assistant import look
        got = look(ch, code, f'He is checking these rules, which say what the newly built code does:\n{rules_text}\n\n'
                             f'He asks: "{a}". Read the code and tell him what the rule means in practice, with one '
                             'concrete example (real amounts or names), in at most 3 plain sentences.')
        if got:
            return got
    k, meaning = telegram.understand(a, (rules_text, [], explain._goal_summary(goal)[:1500] if goal else ''))
    return meaning if k == 'question' and meaning else None

def _ask_fix(ch, poll, k, rule, goal, code=None):
    """His words for a wrong rule, put right: a question about it is answered first, "it's fine after all" keeps it,
    and an empty reply is asked again. Returns the rule as it now stands."""
    for _ in range(4):
        kind, a = telegram._wait(ch, poll, {'fx|keep'})
        if a == 'fx|keep' or (kind == 'text' and KEEP.search(' '.join(a.lower().split()))):
            ch.send(f'Very good: rule {k} stays as it was.'); return rule
        if kind != 'text' or not a.strip(' ?!.'):
            ch.send(f'What should rule {k} say instead? <i>Your own words, or 🎙 a voice note.</i>', html=True,
                    buttons=[[('↩️ Keep it as it was', 'fx|keep')]]); continue
        if ASKING.search(' '.join(a.lower().split())):
            meaning = _explain(ch, a, f'{k}. {rule}', goal, code) or 'It is the rule shown above, exactly as the builders made it.'
            ch.send(f"💬 {telegram.esc(meaning)}\n\n<b>So, what should rule {k} say?</b>", html=True,
                    buttons=[[('↩️ Keep it as it was', 'fx|keep')]]); continue
        return _amend(rule, a)
    return rule

TALK = """You are Hive, a founder's assistant, in the manner of J.A.R.V.I.S. with Tony Stark. His builders have just built
part of his product. Tell him, as a short spoken message, how this part now works, so he can say whether it is what he
wants. The part: {area}. What it does, rule by rule:
{rules}

Write 2 to 4 short sentences, under 80 words, in plain business words, with a concrete example (names, rupees, days)
where it helps.
Cover every rule above: merge similar ones, leave none out, add nothing. No code words, no rule numbers. Then one short
question asking whether that is how he wants it, pointing at the decision most worth his attention.
Reply with JSON only: {{"say": "...", "ask": "...", "covers": [the rule numbers your message covers]}}"""

HEAR = """Hive told a business owner how part of his product works. The rules behind it, numbered:
{rules}

He replied: "{reply}"

What does he mean? Reply with JSON only:
{{"kind": "fine" (he agrees, or wants to move on) | "question" (he asks what something means or what happens in a case)
         | "change" (he wants something to work differently),
 "changes": for a change, [{{"n": rule number, "rule": "that whole rule as he now wants it, keeping every part he did
            not object to"}}],
 "new": for a change that no rule covers, ["the new rule, in plain words"], else [],
 "said_back": for a change, one short sentence saying back exactly what will now happen}}"""

def _converse(ch, poll, area, items, general, goal, code, where, stake):
    """One part of the sheet as a conversation (the founder: "it must be like a conversation"; a page of 8 rules was
    "so cluttered"): Jarvis says how it works in a few sentences covering every rule, he answers in his own words, and
    each change is said back. Returns 'done', or 'pages' for the detailed rules (his choice, or no model to talk)."""
    nums = [n for n, _ in items]
    listing = '\n'.join(f'{n}. {general[n - 1]}' for n in nums)
    got = explain.ask_json(TALK.format(area=area, rules=listing))
    got = got if isinstance(got, dict) else {}
    say, ask = got.get('say'), got.get('ask')
    if not isinstance(say, str) or not say.strip():
        return 'pages'
    covered = {n for n in got.get('covers') or [] if isinstance(n, int)}
    left = [n for n in nums if n not in covered]   # anything the summary left out is said too: nothing hidden
    extra = ''.join(f"\n• {general[n - 1].split(':', 1)[-1].strip()}" for n in left)
    buttons = [[("✅ Yes, that's right", 'cv|ok')], [('📋 Show the detailed rules', 'cv|rules')]]
    more = "<i>Say yes, tell me what to change in your own words, or ask me anything.</i>"
    ch.send(f"🗣 <b>{telegram.esc(area)}</b>   {where}\n\n{stake}{telegram.esc(say.strip())}{telegram.esc(extra)}\n\n"
            f"<b>{telegram.esc((ask or 'Is that how you want it?').strip())}</b>\n{more}", html=True, buttons=buttons)
    for _ in range(15):
        kind, a = telegram._wait(ch, poll, {'cv|ok', 'cv|rules'})
        if a == 'cv|ok':
            return 'done'
        if a == 'cv|rules':
            return 'pages'
        if kind != 'text' or not (a or '').strip():
            continue
        if page_reply('text', a, nums)[0] == 'fine':
            return 'done'
        heard = explain.ask_json(HEAR.format(rules=listing, reply=a))
        heard = heard if isinstance(heard, dict) else {}
        if heard.get('kind') == 'fine':
            return 'done'
        if heard.get('kind') == 'question' or (heard.get('kind') != 'change' and ASKING.search(' '.join(a.lower().split()))):
            meaning = _explain(ch, a, listing, goal, code)
            if not meaning:   # no model: the rules that speak to it
                near = related(items, a)
                meaning = ('Here is what the rules say about that:\n' + '\n'.join(f'{n}. {general[n - 1]}' for n, _ in near)
                           if near else 'I could not work that out from what was built, sir.')
            ch.send(f"💬 {telegram.esc(meaning)}\n\n<i>Anything to change here, or shall we go on?</i>", html=True,
                    buttons=buttons)
            continue
        changed = []
        for c in heard.get('changes') or []:
            if isinstance(c, dict) and c.get('n') in nums and isinstance(c.get('rule'), str) and c['rule'].strip():
                general[c['n'] - 1] = c['rule'].strip(); changed.append(c['n'])
        for r in heard.get('new') or []:
            if isinstance(r, str) and r.strip():
                general.append(f'{area}: {r.strip()}'); changed.append(len(general))
        if changed:
            back = heard.get('said_back') if isinstance(heard.get('said_back'), str) else ''
            ch.send(f"✍️ {telegram.esc(back.strip() or 'Done: changed as you said.')} <i>Anything else here, or shall we "
                    "go on?</i>", html=True, buttons=buttons)
            continue
        general.append(f'{_area_of(items, a, area)}: {a.strip()}')   # nothing read from it: his words go to the builders
        ch.send("📝 Noted, in your words, for the builders. <i>Anything else here, or shall we go on?</i>", html=True,
                buttons=buttons)
    return 'done'

def _confirm_pages(general, ch, poll, title, note, missing, goal='', save=None, code=None, talk=True):
    """The sheet one area at a time, at most 8 rules a page: he taps a wrong rule's number, or "this section is fine";
    each wrong rule is put right on its own page, while the context is fresh. With `save`, progress is kept after every
    page, so a review cut off midway picks up at the page it stopped on."""
    from .codesheet import areas, stakes
    kept = telegram._load(save)
    if kept.get('pages') and len(kept.get('general', [])) >= len(general):
        general = kept['general']
        pages = [(a, [(n, general[n - 1]) for n in ns]) for a, ns in kept['pages']]
        done = kept.get('done', 0)
    else:
        pages, done = areas(general), 0
    why = stakes(pages, goal)
    def keep(p):
        telegram._save(save, {'general': general, 'pages': [(a, [n for n, _ in items]) for a, items in pages], 'done': p})
    mins = max(3, round(len(general) * 8 / 60))   # about 8 seconds a rule, most of them a glance
    ch.send((f"📜 <b>{telegram.esc(title)}</b>\n\n{len(general)} rules in {len(pages)} short sections, about {mins} minutes. "
             "Every rule here is something the builders decided on their own; a wrong one costs far more to find once "
             f"customers hit it. <i>{telegram.esc(note)} Most will be right: " +
             ("I'll tell you how each part works; say yes to move on, or tell me what to change. " if talk else
              "tap \"this section is fine\" to move on. ") + "If anything is unclear, just ask.</i>") if not done else
            f"📜 <b>Picking up where we stopped:</b> section {done + 1} of {len(pages)}.", html=True)
    for p, (area, items) in enumerate(pages, 1):
        if p <= done:
            continue
        items = [(n, general[n - 1]) for n, _ in items]
        listing = '\n'.join(f'<b>{n}.</b> {telegram.esc(r)}' for n, r in items)
        nums = [(str(n), f'pg|{n}') for n, _ in items]
        rows = [nums[i:i + 4] for i in range(0, len(nums), 4)] + [[('✅ This section is fine', 'pg|ok')]]
        stake = why.get(area.split(' · ')[0].split(' (')[0])   # a shared page shows its first area's stake
        stake = f"💡 <i>Why it matters: {telegram.esc(stake)}</i>\n\n" if stake else ''
        if talk and _converse(ch, poll, area, items, general, goal, code, f'{p} of {len(pages)}   '
                              f'{telegram.bar(p, len(pages))}', stake) == 'done':
            keep(p); continue
        listing = '\n'.join(f'<b>{n}.</b> {telegram.esc(general[n - 1])}' for n, _ in items)   # as he may have changed them
        ch.send(f"📋 <b>{telegram.esc(area)}</b>   {p} of {len(pages)}   {telegram.bar(p, len(pages))}\n\n{stake}{listing}\n\n"
                "<i>Tap the number of any rule that is wrong, or tell me. Ask if anything is unclear.</i>", html=True,
                buttons=rows)
        wrong, valid = [], [n for n, _ in items]
        again = "<i>Tap the number of any rule that is wrong, or ✅ This section is fine.</i>"
        while True:
            kind, a = telegram._wait(ch, poll, {d for row in rows for _, d in row})
            what, x = page_reply(kind, a, valid)
            if what == 'fine':
                break
            if what == 'question':   # Gate 45: answered, never filed as a correction
                meaning = _explain(ch, a, '\n'.join(f'{n}. {r}' for n, r in items), goal, code)
                if not meaning:   # no model answered: show him the rules that speak to it, rather than ask him back
                    near = related(items, a)
                    meaning = ("Here is what the rules say about that:\n" + '\n'.join(f'{n}. {r}' for n, r in near)
                               if near else 'Which rule here is unclear? Tell me its number and I will explain it in plain words.')
                ch.send(f"💬 {telegram.esc(meaning)}\n\n{again}", html=True, buttons=rows)
                continue
            if what == 'out':
                ch.send(f"Rule {', '.join(map(str, x))} isn't on this page; here it's {valid[0]} to {valid[-1]}. {again}",
                        html=True, buttons=rows)
                continue
            if what == 'fix':   # he said which rule and how, in one go: no need to ask again
                k, words = x
                general[k - 1] = _amend(general[k - 1], words)
                ch.send(f"✍️ Rule {k} is now: {telegram.esc(general[k - 1])}\n\n<i>Anything else here? Tap a number, "
                        "or ✅ This section is fine.</i>", html=True, buttons=rows)
                continue
            if what == 'note':   # his words without a rule number: a correction, filed under the area it is about
                general.append(f'{_area_of(items, x, area)}: {x}')
                ch.send(f"📝 Noted for this section. Anything else here? {again}", html=True, buttons=rows)
                continue
            for k in x:
                if k not in wrong:
                    wrong.append(k); ch.send(f'🔖 {k} marked. Tap more, or "this section is fine" when done.')
        for k in wrong:
            ch.send(f"✍️ <b>Rule {k}:</b> {telegram.esc(general[k - 1])}\n\n<b>What should it be?</b> <i>Your own words, "
                    "or 🎙 a voice note.</i>", html=True, buttons=[[('↩️ Keep it as it was', 'fx|keep')]])
            general[k - 1] = _ask_fix(ch, poll, k, general[k - 1], goal, code)
        keep(p)
    if missing:
        ch.send("➕ <b>Anything the builders should know that is not on these pages?</b> <i>Say it in your own words, "
                "or tap Nothing to add.</i>", html=True, buttons=[[('✅ Nothing to add', 'sheet|none')]])
        for _ in range(4):
            kind, a = telegram._wait(ch, poll, {'sheet|none'})
            t = ' '.join((a or '').lower().split())
            if kind != 'text' or not t.strip(' ?!.') or no_rule(a) or is_yes(a) or re.fullmatch(r"(no|nope|nah|nothing|nahi|kuch nahi|none)\W*", t):
                break
            if ASKING.search(t):
                ch.send("💬 Anything the builders should follow that none of the pages said: a case they missed, a limit, "
                        "a rule of your business. <i>Say it, or tap Nothing to add.</i>", html=True,
                        buttons=[[('✅ Nothing to add', 'sheet|none')]])
                continue
            general.append(a.strip()); break
    keep(len(pages))
    ch.send('✅ Thank you. These are your rules now; the builders will encode every one as a test.')
    return general

def confirm_sheet(general, ch=None, ask=None, poll=20, title=SHEET_TITLE, note=SHEET_NOTE, missing=False, goal='',
                  save=None, code=None):
    """Show the whole sheet; he marks the numbers of any wrong rules and says each one right; each is amended, not
    replaced (Gate 39). With `missing`, he is then asked what the builders should know that is not on it (Gate 42: a
    sheet written from the built code). Returns the confirmed rules."""
    general = list(general)
    listing = '\n'.join(f'<b>{n}.</b> {telegram.esc(r)}' for n, r in enumerate(general, 1))
    if ch and len(general) > PAGED_FROM:   # a long sheet in pages by area (the owner: "60-80 rules is too much")
        return _confirm_pages(general, ch, poll, title, note, missing, goal, save, code)
    if ch:
        nums = [(str(n), f'sheet|{n}') for n in range(1, len(general) + 1)]
        rows = [nums[i:i + 5] for i in range(0, len(nums), 5)] + [[('✅ All correct', 'sheet|done')]]
        ch.send(f"📜 <b>{title}</b>\n\n{listing}\n\n<i>{note} Tap the number of any rule that is wrong, then "
                "All correct.</i>", html=True, buttons=rows)
        wrong = []
        while True:
            kind, a = telegram._wait(ch, poll, {d for row in rows for _, d in row})
            if a == 'sheet|done' or (kind == 'text' and is_yes(a)):
                break
            for k in ([int(a.split('|')[1])] if kind == 'tap' else [int(x) for x in re.findall(r'\d+', a)]):
                if 1 <= k <= len(general) and k not in wrong:
                    wrong.append(k); ch.send(f'🔖 {k} marked. Tap more, or All correct.')
        for k in wrong:
            ch.send(f"✍️ <b>Rule {k}:</b> {telegram.esc(general[k - 1])}\n\n<b>What should it be?</b> <i>Your own words, "
                    "or 🎙 a voice note.</i>", html=True)
            general[k - 1] = _amend(general[k - 1], telegram._wait(ch, poll, set())[1])
        if missing:
            ch.send("➕ <b>Anything the builders should know that is not on this list?</b> <i>Say it in your own words, "
                    "or tap All correct.</i>", html=True, buttons=[[('✅ Nothing to add', 'sheet|none')]])
            kind, a = telegram._wait(ch, poll, {'sheet|none'})
            if kind == 'text' and a.strip() and not no_rule(a) and not is_yes(a):
                general.append(a.strip())
        ch.send('✅ Thank you. These are your rules now; the builders will encode every one as a test.')
    else:
        print(f'\n{title} ({note[0].lower() + note[1:].rstrip(".")}):')
        for n, r in enumerate(general, 1):
            print(f'  {n}. {r}')
        for k in [int(x) for x in re.findall(r'\d+', (ask or input)("  Numbers of any that are wrong (Enter = all correct) > "))]:
            if 1 <= k <= len(general):
                general[k - 1] = _amend(general[k - 1], (ask or input)(   # restated, as on the phone (Gate 39)
                    f"  Rule {k}: {general[k - 1]}\n  What should it be? > ").strip())
        if missing:
            a = (ask or input)("  Anything the builders should know that is not on this list? (Enter = nothing) > ").strip()
            if a and not no_rule(a) and not is_yes(a):
                general.append(a)
    return general

def _settle(rules, rulings, ch=None, ask=None, poll=20):
    """A new answer that contradicts one of his earlier rulings: ask which holds now, before the builders get both
    (Gate 36: an interview answer on pausing pulled against his earlier verdict on the same situation)."""
    earlier = [f'Earlier ruling: {r}' for r in rulings[-40:]]
    for n, c in enumerate(explain.conflicts(earlier + [f'New answer: {r}' for r in rules])):
        if max(c['a'], c['b']) < len(earlier):   # two old rulings: not this interview's business
            continue
        opts = [c['option_a'], c['option_b']]
        if ch:
            ch.send(f"⚖️ <b>One thing before the builders start:</b> this answer pulls against an earlier ruling of "
                    f"yours.\n\n{telegram.esc(c['question'])}\n\n<b>1.</b> {telegram.esc(opts[0])}\n<b>2.</b> "
                    f"{telegram.esc(opts[1])}", html=True, buttons=[('1', f'set|{n}|0'), ('2', f'set|{n}|1')])
            kind, got = telegram._wait(ch, poll, {f'set|{n}|0', f'set|{n}|1'})
            chosen = opts[int(got[-1])] if kind == 'tap' else got
            ch.send('✅ Understood. That settles it.')
        else:
            got = (ask or input)(f"\nOne thing: this answer pulls against an earlier ruling of yours.\n{c['question']}\n"
                                 f"  A) {opts[0]}  B) {opts[1]}\n  Which holds now? > ").strip()
            chosen = opts[0] if got.upper() in ('A', '1') else opts[1] if got.upper() in ('B', '2') else got
        rules.append(f"Settled by the owner (this replaces any earlier ruling it contradicts): {c['question']} -> {chosen}")
    return rules

YES_WORDS = ('exactly', "that's it", 'thats it', "that's right", 'thats right', 'correct', 'yes', 'yep', 'yeah',
             'haan', 'perfect', 'spot on', 'the thing i want', 'what i want', 'what i meant')
NO_RULE = re.compile(r"(nothing|none|no rule|no preference|skip|pass|anything|any|no idea|i don'?t know|"
                     r"(it )?doesn'?t matter|(it'?s )?up to you|you decide|your call|you choose|as you (like|wish|feel)|"
                     r"whatever( you| u)?( feel like| think| want| like| wish| prefer)?( is (best|right))?)"
                     r"( sir| bro| man| yaar)?")

def is_yes(text):
    """His own words agree with the reading ("yes", "it's exactly that", "spot on"); not "yes, but ...". """
    t = ' ' + re.sub(r"[^a-z' ]", ' ', text.lower()) + ' '
    if text.strip().lower().strip('.! ') in telegram.YES:
        return True
    return (len(t) < 60 and any(f' {w} ' in re.sub(' +', ' ', t) for w in YES_WORDS)
            and not any(f' {w} ' in t for w in ('not', 'no', 'but', 'except', 'only', 'wrong')))

FINE = re.compile(r"(good|fine|ok(ay)?|all good|looks (good|fine|right)|correct|right|perfect|theek( hai)?|sahi( hai)?|"
                  r"badhiya|go ahead|proceed|carry on|continue|next|done|do (the )?rest|move on|aage|chalo)\b")

def section_fine(text):
    """His words pass the page ("good, do the rest", "looks fine", "theek hai, next"); not "good, but ...". Gate 45:
    "Good i think do rest of the work as required" was filed as a correction."""
    t = ' '.join(re.sub(r"[^a-z' ]", ' ', text.lower()).split())
    return bool(FINE.match(t)) and len(t) < 80 and not any(f' {w} ' in f' {t} ' for w in (
        'but', 'except', 'not', 'wrong', 'change', 'should', 'instead', 'only', 'nahi', 'galat', 'lekin', 'magar'))

def no_rule(text):
    """The whole reply leaves it to the builders ("whatever you feel like", "nothing", "up to you"): no rule."""
    return bool(NO_RULE.fullmatch(re.sub(r"[^a-z' ]", ' ', text.lower()).strip().replace('  ', ' ')))

def instructions(rules, rulings=None):
    """The rules as they go into the builders' goal: each must be encoded as a test before landing. With `rulings` (his
    answers to each situation, before they were merged into the sheet), those follow, kept whole (Gate 41)."""
    if not rules:
        return ''
    text = ("\n\n## The owner's rules for this feature (from his interview)\nThe owner decided each of these himself. Encode "
            "every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond "
            "the situation it describes.\n\n" + '\n'.join(f'- {r}' for r in rules) + '\n')
    extra = [r for r in (rulings or []) if r not in rules]
    if extra:
        text += ("\nHis answers to each situation, word for word (the rules above were written from them). Where an answer "
                 "says more than the rules, the answer holds; encode it as a test too.\n\n" + '\n'.join(f'- {r}' for r in extra) + '\n')
    return text
