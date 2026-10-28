"""Interview first: before building, Hive asks the owner about the situations where his rules are likely to matter, and
his answers become rules the builders must encode as tests.

Gates 30-35: the founder answered 48 of 48 concrete situations (28 differing from the obvious default) but reviewed
lists of the builders' decisions poorly (half found, all kept, none marked). So the owner's rules are asked for up front,
the way he answers best; the review after the build stays as a short safety net."""
import json, os, re

from . import explain, telegram

WRITE = """You are preparing a short interview with a busy, non-technical business owner before his software builders start
work. The feature to build:
{goal}
{rulings}
List the {n} situations where his own business rules are most likely to matter and differ from what builders would
assume: money, timing, limits, exceptions, missing information, conflicts between people. Skip anything the feature
description already settles. Each situation is one concrete case in plain words (names, rupees, days), with 2 or 3
realistic outcomes a business might choose, clearly different from each other. No technical words.

Reply with JSON only: {{"situations": [{{"situation": "...", "options": ["...", "...", "..."]}}]}}"""

READ = """An owner answered a question about how his product should behave.

Situation: {situation}
His answer, in his own words: {answer}

Write his rule as one clear sentence a software builder can implement and test. Keep his meaning exactly; add nothing.
Reply with JSON only: {{"rule": "..."}}"""

def write_situations(goal, rulings=None, n=12):
    past = ("\nRules he has already given (don't ask about these again):\n" + '\n'.join(f'- {r}' for r in rulings[-40:])
            + '\n') if rulings else ''
    got = explain.ask_json(WRITE.format(goal=explain._goal_summary(goal), rulings=past, n=n)) or {}
    out = []
    for k, s in enumerate(got.get('situations', [])[:n], 1):
        opts = [o for o in s.get('options', []) if isinstance(o, str) and o.strip()][:3]
        if s.get('situation') and len(opts) >= 2:
            out.append({'id': f'q{k:02d}', 'situation': s['situation'].strip(), 'options': opts})
    return out

def _rule(situation, answer):
    got = explain.ask_json(READ.format(situation=situation, answer=answer)) or {}
    return (got.get('rule') or f'{situation} -> {answer}').strip()

def interview(goal, ch=None, rulings=None, n=12, ask=None, situations=None, poll=20):
    """Run the interview. Returns the owner's rules, one plain sentence each. On the phone if `ch` is given, otherwise
    in the terminal (`ask(prompt)` returns his typed answer)."""
    qs = situations or write_situations(goal, rulings, n)
    if not qs:
        return []
    if ch:
        got = telegram.verdicts(ch, qs, intro=f"Before the builders start, {len(qs)} quick situations where your rules "
                                              "matter. Tap what should happen at your company, or tell me in your own "
                                              "words. About 3 minutes; it saves you checking their work afterwards.",
                              poll=poll)
    else:
        got = {}
        for k, q in enumerate(qs, 1):
            opts = '  '.join(f'{chr(65 + i)}) {o}' for i, o in enumerate(q['options']))
            a = (ask or input)(f"\n{k} of {len(qs)}. {q['situation']}\n  {opts}\n  Your answer (a letter, or your own words) > ").strip()
            m = re.fullmatch(r'([A-Ca-c])[).]?', a)
            got[q['id']] = q['options'][ord(m.group(1).upper()) - 65] if m and ord(m.group(1).upper()) - 65 < len(q['options']) else a
    rules, free = [], []
    for q in qs:
        a = got.get(q['id'], '')
        if not a:
            continue
        if a in q['options']:
            rules.append(f"{q['situation']} -> {a}")
        else:
            free.append((q, a))
    if free:   # his own words: write each as a rule and let him confirm it
        drafts = [{'id': q['id'], 'situation': _rule(q['situation'], a), 'own': a, 'options': ["Yes, exactly", 'Not quite']}
                  for q, a in free]
        if ch:
            ok = telegram.verdicts(ch, [{'id': d['id'], 'situation': f"Your rule, as I'll build it: {d['situation']}",
                                         'options': d['options']} for d in drafts],
                                   intro='Thank you. A few you answered in your own words; here is how I read them.',
                                   poll=poll)
        else:
            ok = {d['id']: (ask or input)(f"\nYour rule, as I'll build it: {d['situation']}\n  Right? (Enter = yes, or "
                                         "say what's off) > ").strip() or 'Yes, exactly' for d in drafts}
        for d in drafts:
            v = ok.get(d['id'], 'Yes, exactly')
            rules.append(d['situation'] if v == 'Yes, exactly' else d['own'] if v == 'Not quite' else v)
    return rules

def instructions(rules):
    """The rules as they go into the builders' goal: each must be encoded as a test before landing."""
    if not rules:
        return ''
    return ("\n\n## The owner's rules for this feature (from his interview)\nThe owner decided each of these himself. Encode "
            "every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond "
            "the situation it describes.\n\n" + '\n'.join(f'- {r}' for r in rules) + '\n')
