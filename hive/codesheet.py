"""The rule sheet written from the built code (Gate 42): complete by construction, so the owner only marks what is wrong.

The first build already decides every case, including the unusual ones nobody asked about. A describer reads and runs
the built code (read-only) and writes every business behaviour as a plain rule. The owner sees the whole sheet, marks
the rules that are not his policy and says each one right, then adds anything missing; the changes go to a fix round.

Gate 42 (synthetic owner who knows his rules): the corrected code sheet took fresh builders to 99.6% hidden, against
68.4% from Hive's interview and 100% from the owner's own complete sheet. The cost moved to the owner's reading: 68
rules, 34 marked. A real owner reading such a sheet is not yet tested."""
import json, os, shlex, shutil, subprocess, tempfile

CMD = os.environ.get('HIVE_DESCRIBE_CMD', 'claude -p --output-format json --permission-mode acceptEdits '
                                          '--allowedTools Bash Read Write Glob Grep')

BRIEF = """You are documenting what a piece of software does, so that its business owner can check it. The folder
{code} holds the code, just built for this feature:

{goal}

Read it and run it, but do not change anything in that folder. Write {out}: a JSON list of strings, one rule per
string, in plain words the owner can check ("Whenever ..., ..."), each naming the part of the product it is about.
- Cover every business behaviour of this feature: the normal outcome, and what happens with missing, blank or
  unreadable values, wrong formats, letter case, spaces and separators, zero, negative or very large numbers,
  boundaries and rounding. Describe what the code actually does, even where it looks odd.
- Check each rule by running the code or its tests.
- One behaviour per rule, one or two sentences each. Business words, no code, no file or function internals.
Reply in one line: how many rules you wrote."""

def describe(code_dir, goal, timeout=1800):
    """Every business behaviour of the built code, as plain rules ([] if the describer could not run)."""
    work = tempfile.mkdtemp(prefix='hive_sheet_')
    try:
        code = os.path.join(work, 'code')
        shutil.copytree(code_dir, code, ignore=shutil.ignore_patterns('.git', 'node_modules', '__pycache__'))
        out = os.path.join(work, 'rules.json')
        try:
            subprocess.run(shlex.split(CMD), cwd=work, input=BRIEF.format(code=code, goal=goal.strip()[:6000], out=out),
                           capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
            got = json.load(open(out, encoding='utf-8'))
        except Exception:
            return []
        return [r.strip() for r in got if isinstance(r, str) and r.strip()] if isinstance(got, list) else []
    finally:
        shutil.rmtree(work, ignore_errors=True)

KNOWN = """A business owner already gave these rules for his product:
{known}

Below are rules written from what the built code does, numbered:
{sheet}

Which of the numbered rules only say again what one of his rules already says (the same case, the same outcome)? A rule
that adds any case or detail his rules do not state is not a repeat. Reply with JSON only: {{"repeats": [numbers]}}"""

def split_known(sheet, known):
    """(to show, already his): the sheet's rules that only repeat a rule he already gave need not be read again (the
    owner: "60-80 rules is too much to review"). Best effort: everything is shown if no model answers."""
    from . import explain
    if not sheet or not known:
        return list(sheet), []
    got = explain.ask_json(KNOWN.format(known='\n'.join(f'- {k}' for k in known[-60:]),
                                        sheet='\n'.join(f'{n}. {r}' for n, r in enumerate(sheet, 1)))) or {}
    rep = {n for n in got.get('repeats', []) if isinstance(n, int) and 1 <= n <= len(sheet)}
    return [r for n, r in enumerate(sheet, 1) if n not in rep], [r for n, r in enumerate(sheet, 1) if n in rep]

def areas(sheet, page=8):
    """The sheet in pages a person can take in at once: by the part of the product each rule names ("fees: ..."), at
    most `page` rules a page. Returns [(area, [(number, rule)])], numbered across the whole sheet."""
    groups, order = {}, []
    for n, r in enumerate(sheet, 1):
        head, _, rest = r.partition(':')
        area = head.strip() if rest and 0 < len(head.strip()) <= 40 and '.' not in head else ''
        if area not in groups:
            groups[area] = []; order.append(area)
        groups[area].append((n, r))
    out = []
    for a in order:
        items = groups[a]
        for i in range(0, len(items), page):
            part = (f' ({i // page + 1})' if len(items) > page else '')
            out.append(((a or 'Other rules') + part, items[i:i + page]))
    return out

STAKES = """A business owner is about to check, area by area, what his newly built product does. The product:
{goal}

The areas, each with its rules:
{areas}

For each area, write one short line telling him why it is worth his attention: what it costs his business if a rule
there is wrong (money paid out wrongly, an angry customer or partner, a legal risk, abuse). Plain words, no technical
terms, at most 20 words. Reply with JSON only: {{"why": {{"<area>": "..."}}}}"""

def stakes(pages, goal=''):
    """{area: why it matters to his business}, so he sees each page is worth his time (the founder: questions must feel
    important, not random). Best effort: {} if no model answers."""
    from . import explain
    names = []
    for a, _ in pages:
        base = a.split(' (')[0]
        if base not in names:
            names.append(base)
    listing = '\n'.join(f"{a}: " + ' | '.join(r[:120] for p, items in pages if p.split(' (')[0] == a for _, r in items[:3])
                        for a in names)
    got = explain.ask_json(STAKES.format(goal=(goal or '')[:1500], areas=listing)) or {}
    why = got.get('why') if isinstance(got.get('why'), dict) else {}
    return {a: str(w).strip() for a, w in why.items() if str(w).strip()}
