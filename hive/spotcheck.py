"""Spot checks after the rule review (Gate 58): concrete outcomes of the built code, one at a time, for every part of
the product the owner's review left as it was; each correction is applied on its own and the case is shown to him again.

Gate 55: an owner who skims a rule list corrects what he remembers and lets details pass. Gate 57: concrete outcomes
("Ravi's 100-rupee invoice, 31 days late: the fee comes to 2 rupees. Right?") draw his corrections, but one rewrite of
the whole sheet lost them, and 30 hand-picked cases left parts unshown. Gate 58 fixed both: cases for every part, each
correction applied alone and re-shown. With the same skimming owner, the sheet then stated 9 of 25 decisions right
against 4 after the list alone, hidden tests 58.8% against 43.2%, and he confirmed 9 of 10 corrected cases on re-show."""
import json, os, re, shutil, subprocess, tempfile

from . import argv, explain, telegram

CMD = os.environ.get('HIVE_SPOT_CMD', 'claude -p --output-format json --permission-mode acceptEdits '
                                      '--allowedTools Bash Read Write Glob Grep')

BRIEF = """You are preparing quick spot checks for a busy business owner. The folder {code} holds his product's code, just
built for this feature:

{goal}

Read it and run it, but do not change anything in that folder. For each part of the product listed below, find the
choices the code made that the owner might not expect or might decide differently (boundaries and cut-offs, rounding,
caps and minimums, what happens in each business situation, wrong or missing input the business would care about). For
each part write 2 to 5 spot checks, one choice each: pick one concrete case, run the code on it (its tests or a small
script), and write what actually comes out.

The parts:
{parts}

Write {out}: a JSON list of objects, grouped by part, the most important first within each:
{{"part": "<one of the parts above, exactly>", "say": "one sentence in plain business words, with names and amounts,
ending with the outcome"}}, for example "Ravi's 100-rupee invoice is paid 31 days late: the late fee comes to 2
rupees." No code words. Reply in one line: how many spot checks you wrote."""

APPLY = """A business owner checked one concrete outcome of his newly built software and corrected it. Below are the
current rules about that part of the software, numbered, and his correction.

Change only the rules his correction contradicts, so the software does what he said in this case and in every case like
it: keep every part of each rule he did not object to, state the general rule (not just his example), and keep every
number, cut-off and rounding unless he changed it. If no rule covers his correction, add one. Plain words.

Rules about this part:
{rules}

The outcome he was shown: {shown}
What he said: {said}

Reply with JSON only: {{"changes": [{{"n": <rule number>, "rule": "the whole rule as it now stands"}}], "new": ["..."]}}"""

RECHECK = """Below are rules describing what a business's software does, and one concrete case. Work out exactly what the
software does in that case by following these rules alone, and say it as one sentence in plain business words, with
the same names and amounts, ending with the outcome.

Rules:
{rules}

The case: {case}

Reply with JSON only: {{"say": "..."}}"""

def parts_of(rules):
    """The parts of the product the sheet's rules name ("Referral rewards: ..."), in order."""
    out = []
    for r in rules:
        head = r.partition(':')[0].split(' (')[0].strip() if ':' in r else ''
        if head and len(head) <= 60 and '.' not in head and head not in out:
            out.append(head)
    return out

def find(code_dir, goal, parts, timeout=1500):
    """Spot checks for these parts, from running the built code in a throwaway copy ([] if none could be made)."""
    if not parts or os.environ.get('HIVE_SPOTS') == '0':
        return []
    work = tempfile.mkdtemp(prefix='hive_spots_')
    try:
        code = os.path.join(work, 'code')
        shutil.copytree(code_dir, code, ignore=shutil.ignore_patterns('.git', 'node_modules', '__pycache__'))
        out = os.path.join(work, 'spots.json')
        try:
            subprocess.run(argv(os.environ.get('HIVE_SPOT_CMD') or CMD), cwd=work, input=BRIEF.format(code=code, goal=goal.strip()[:6000], out=out,
                                                                     parts='\n'.join(f'- {p}' for p in parts)),
                           capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
            got = json.load(open(out, encoding='utf-8'))
        except Exception:
            return []
        return [s for s in got if isinstance(s, dict) and isinstance(s.get('say'), str) and s['say'].strip()] \
            if isinstance(got, list) else []
    finally:
        shutil.rmtree(work, ignore_errors=True)

def _about(rules, part):
    return [n for n, r in enumerate(rules, 1) if part and r.lower().startswith(part.lower())]

def apply_one(rules, part, shown, said):
    """His one correction, applied to that part's rules only (Gate 57: one rewrite of the whole sheet lost detail)."""
    nums = _about(rules, part)
    got = explain.ask_json(APPLY.format(rules='\n'.join(f'{n}. {rules[n - 1]}' for n in nums) or '(none)', shown=shown,
                                        said=said))
    got = got if isinstance(got, dict) else {}
    out, changed = list(rules), 0
    for c in got.get('changes') or []:
        if isinstance(c, dict) and c.get('n') in nums and isinstance(c.get('rule'), str) and c['rule'].strip():
            out[c['n'] - 1] = c['rule'].strip(); changed += 1
    for r in got.get('new') or []:
        if isinstance(r, str) and r.strip():
            out.append(r.strip() if ':' in r[:60] else f'{part}: {r.strip()}'); changed += 1
    if not changed:   # nothing could be read from it: his words go to the builders as he said them
        out.append(f'{part or "Other"}: {shown} The owner says: {said}')
    return out

def recheck(rules, part, case):
    """The case worked out again from the corrected rules, to show him once more."""
    got = explain.ask_json(RECHECK.format(rules='\n'.join(rules[n - 1] for n in _about(rules, part)) or '(none)', case=case))
    return got.get('say').strip() if isinstance(got, dict) and isinstance(got.get('say'), str) and got['say'].strip() else None

def _terminal(text):
    """Phone text for a terminal: no markup, and nothing the terminal cannot show (a Windows console in an old code
    page crashed on an emoji)."""
    import sys
    text = re.sub(r'<[^>]+>', '', text)
    enc = getattr(sys.stdout, 'encoding', None) or 'utf-8'
    return text.encode(enc, 'ignore').decode(enc).strip()

def _plain_yes(text):
    from .interview import page_reply
    return not (text or '').strip() or page_reply('text', text, [])[0] == 'fine'

def review(rules, spots, ch=None, ask=None, poll=20, code=None, goal=''):
    """The spot checks one at a time, on the phone (`ch`) or in the terminal (`ask`). Returns the rules with his
    corrections applied, and the record [{shown, said, now, confirmed}]."""
    rules, record = list(rules), []
    if not spots:
        return rules, record
    def hear(text, buttons):
        if ch:
            ch.send(text, html=True, buttons=buttons)
            kind, a = telegram._wait(ch, poll, {'sc|ok'})
            return '' if a == 'sc|ok' else (a or '')
        return (ask or input)(_terminal(text) + '\n  (Enter = right, or say what should happen) > ').strip()
    ok = [[("✅ That's right", 'sc|ok')]]
    n = len(spots)
    intro = (f"🔎 <b>Last step, {'one quick check' if n == 1 else f'{n} quick checks'}</b> on what the build does in real cases. They catch what a list "
             "of rules hides. Tap ✅ if a result is right, or tell me what should happen.")
    if ch:
        ch.send(intro, html=True)
    else:
        print(_terminal(intro))
    for k, s in enumerate(spots, 1):
        part = s.get('part', '')
        said = hear(f"<b>{k} of {len(spots)}.</b> {telegram.esc(s['say'])}\n\n<i>Right?</i>", ok)
        from .interview import ASKING, _explain
        for _ in range(2):   # a question about the case is answered before anything changes
            if said and ASKING.search(' '.join(said.lower().split())):
                meaning = _explain(ch, said, '\n'.join(rules[n - 1] for n in _about(rules, part)), goal, code) or \
                    'That is what the build does today in that case.'
                said = hear(f"💬 {telegram.esc(meaning)}\n\n<i>So, is that result right?</i>", ok)
        if _plain_yes(said):
            continue
        entry = dict(part=part, shown=s['say'], said=said)
        rules = apply_one(rules, part, s['say'], said)
        now = recheck(rules, part, s['say'])
        entry['now'] = now
        if now:   # shown again, worked out from the corrected rules (Gate 58: 9 of 10 confirmed)
            again = hear(f"✍️ With your correction: {telegram.esc(now)}\n\n<i>Right now?</i>", ok)
            entry['confirmed'] = _plain_yes(again)
            if not entry['confirmed']:
                entry['said_again'] = again
                rules = apply_one(rules, part, now, again)
        record.append(entry)
    done = (f"✅ Thank you. {len(record)} of {n} case{'s' if n != 1 else ''} changed; the builders will make "
            f"{'it' if len(record) == 1 else 'them'} so." if record else '✅ Thank you. Every case is as you want it.')
    if ch:
        ch.send(done)
    else:
        print(_terminal(done))
    return rules, record
