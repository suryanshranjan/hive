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
one of them. One entry per decision: when the outcome depends on a number (days late, days waited, rounds used), that
is still one decision, not one per number. Reply with JSON only: {{"decisions": [{{"case": "...", "default": "..."}}]}}"""

WRITE = """You are preparing a short interview with a busy, non-technical business owner before his software builders start
work. The feature to build:
{goal}
{rulings}{decisions}
List the {n} situations where his own business rules are most likely to matter and differ from what builders would
assume: money, timing, limits, exceptions, missing information, conflicts between people. Skip anything the feature
description already settles. Each situation is one concrete case in plain words (names, rupees, days), with 2 or 3
realistic outcomes a business might choose, clearly different from each other. No technical words.

Reply with JSON only: {{"situations": [{{"situation": "...", "options": ["...", "...", "..."]}}]}}"""

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

def decisions(goal):
    """The business decisions the build must take, each with the builders' default (Gate 36: questions written from the
    description alone covered 4 of 9 of the owner's surprising rules; most asked about things the code never decides)."""
    got = explain.ask_json(PLAN.format(goal=re.sub(r'^#+\s*(goal:?)?\s*', '', goal.strip(), flags=re.I)[:8000])) or {}
    return [d for d in got.get('decisions', []) if isinstance(d, dict) and d.get('case')][:40]

def write_situations(goal, rulings=None, n=12):
    past = ("\nRules he has already given (don't ask about these again):\n" + '\n'.join(f'- {r}' for r in rulings[-40:])
            + '\n') if rulings else ''
    ds = decisions(goal)
    if ds:   # cover every decision the code takes, up to MAX_QUESTIONS: ranking cut 2 of the owner's 9 surprises (Gate 37 pilot)
        n = min(max(n, len(ds)), MAX_QUESTIONS)
    plan = FROM_DECISIONS.format(listing='\n'.join(f"- {d['case']} (builders' outcome: {d.get('default') or 'unsure'})"
                                                    for d in ds)) if ds else ''
    got = explain.ask_json(WRITE.format(goal=explain._goal_summary(goal), rulings=past, decisions=plan, n=n)) or {}
    out = []
    for k, s in enumerate(got.get('situations', [])[:n], 1):
        opts = [o for o in s.get('options', []) if isinstance(o, str) and o.strip()][:3]
        if s.get('situation') and len(opts) >= 2:
            out.append({'id': f'q{k:02d}', 'situation': s['situation'].strip(), 'options': opts})
    return _dedupe(out)

def _rule(situation, answer):
    got = explain.ask_json(READ.format(situation=situation, answer=answer)) or {}
    return (got.get('rule') or f'{situation} -> {answer}').strip()

def interview(goal, ch=None, rulings=None, n=12, ask=None, situations=None, poll=20, save=None, sheet=True):
    """Run the interview. Returns the owner's rules, one plain sentence each. On the phone if `ch` is given, otherwise
    in the terminal (`ask(prompt)` returns his typed answer). With `save` (a file path), the questions, his answers and
    the readings are kept as they come, so a rerun after a stop picks up where he left off."""
    kept = telegram._load(save and save + '.questions.json')
    qs = situations or kept.get('qs') or write_situations(goal, rulings, n)
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
            elif not no_rule(v):
                rules.append(f"{asked} -> {d['own'] if v == 'Not quite' else v}" if asked else v)
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
    listing = '\n'.join(f'<b>{n}.</b> {telegram.esc(r)}' for n, r in enumerate(general, 1))
    if ch:
        nums = [(str(n), f'sheet|{n}') for n in range(1, len(general) + 1)]
        rows = [nums[i:i + 5] for i in range(0, len(nums), 5)] + [[('✅ All correct', 'sheet|done')]]
        ch.send(f"📜 <b>Your rules for this feature, as the builders will follow them</b>\n\n{listing}\n\n<i>Each one "
                "applies to every case like it, not just the example. Tap the number of any rule that is wrong, then "
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
            general[k - 1] = _rule(general[k - 1], telegram._wait(ch, poll, set())[1])
        ch.send('✅ Thank you. These are your rules now; the builders will encode every one as a test.')
    else:
        print('\nYour rules for this feature, as the builders will follow them (each applies to every case like it):')
        for n, r in enumerate(general, 1):
            print(f'  {n}. {r}')
        for k in [int(x) for x in re.findall(r'\d+', (ask or input)("  Numbers of any that are wrong (Enter = all correct) > "))]:
            if 1 <= k <= len(general):
                general[k - 1] = _rule(general[k - 1], (ask or input)(f"  Rule {k}: what should it be? > ").strip())
    telegram._save(path, {'draft': got, 'done': True, 'rules': general})
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

def no_rule(text):
    """The whole reply leaves it to the builders ("whatever you feel like", "nothing", "up to you"): no rule."""
    return bool(NO_RULE.fullmatch(re.sub(r"[^a-z' ]", ' ', text.lower()).strip().replace('  ', ' ')))

def instructions(rules):
    """The rules as they go into the builders' goal: each must be encoded as a test before landing."""
    if not rules:
        return ''
    return ("\n\n## The owner's rules for this feature (from his interview)\nThe owner decided each of these himself. Encode "
            "every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond "
            "the situation it describes.\n\n" + '\n'.join(f'- {r}' for r in rules) + '\n')
