"""The owner session: the owner's intent reaches a running swarm (Gates 13-24: owner examples plus questions).

Inside a run (HIVE_RUN set by `hive run`):
  workers:  hive ask "<question>"     ask the owner; blocks until answered; prints the answer
            hive answers              every question answered so far in this run (read before asking)
            hive assume "<default>"   record a default you applied that the goal does not state (with --assumptions)
            hive assumptions          every default recorded so far in this run
  owner:    hive owner --run <run>    answer pending questions in a terminal, as they arrive
            hive review --run <run>   after the build, check each recorded default; wrong ones go to corrections.md

Files under <run>/owner/: examples.md (the owner's worked examples, also put in every worker's prompt),
budget.json ({"questions": N}), questions/<id>.json, answers/<id>.json. Every answer is a ruling on that input:
the worker who asked encodes it as a test before landing."""
import glob, json, os, re, sys, time

# Owners are not engineers. A question must read like a real-life situation, not code: in Gate 25, questions full of
# code words led the founder to say "I don't remember" and hand the role over. These patterns are refused.
JARGON = [
    (r'\w\(|[{}\[\]]|=>|==', 'code symbols'),   # fee( or braces; plain "(please say)" and choice labels "A)" are fine
    (r"'[^']*'|\"[^\"]*\"", 'quoted code values'),
    (r'\b(?:BigInt|null|undefined|NaN|boolean|string|integer|float|JSON|API|JS|regex|enum|schema|throw|exception|'
     r'function|param(?:eter)?s?|payload|normaliz\w*|serializ\w*|paise)\b', 'programming words'),
    (r'\b(?:HTTP|status|code|error|with|return|throw)\s+(?:a\s+|an\s+)?[45]\d\d\b', 'status codes'),   # not "Rs 2,500"
    (r'\b[a-z]+_[a-z_]+\b|\b[a-z]+[A-Z]\w*\b', 'code names'),
]

def plain_language_problems(question):
    """Why a question is not plain enough for a non-technical owner (empty list when it is fine)."""
    return sorted({why for pat, why in JARGON
                   if re.search(pat, question, flags=0 if why in ('code names', 'quoted code values') else re.I)})

def _dir(run=None):
    run = run or os.environ.get('HIVE_RUN')
    if not run:
        raise SystemExit('not inside a hive run: HIVE_RUN is not set')
    d = os.path.join(run, 'owner')
    for sub in ('questions', 'answers', 'assumptions', 'reviews'):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    return d

def _later(d):
    p = os.path.join(d, 'budget.json')
    return bool(json.load(open(p)).get('later')) if os.path.exists(p) else False

def pending(run):
    """The questions recorded for the owner that he has not answered yet."""
    d = os.path.join(run, 'owner')
    qs = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(d, 'questions', '*.json')))]
    return [q for q in qs if not os.path.exists(os.path.join(d, 'answers', q['id'] + '.json'))]

def _budget(d):
    p = os.path.join(d, 'budget.json')
    return json.load(open(p)).get('questions') if os.path.exists(p) else None

LATER = ("\n## Questions for the owner's morning\nThe owner is away until the morning. For every business decision the goal "
         "leaves open (cut-offs and boundaries, rounding, minimums and caps, what happens with blank, missing, negative or "
         "oddly formatted information), record one question for him with `python3 -m hive ask \"<question>\"`: one real-life "
         "situation in plain words, with real amounts, one decision per question. It returns at once. Build your best guess "
         "and keep going: in the morning he answers every recorded question, and the team then changes the code to his "
         "answers (Gate 70: his morning answers took a night build from 39% to 94% of his rules, where reviewing the "
         "finished build reached 75%). Read `python3 -m hive answers` first and do not record a question a teammate has "
         "already recorded.\n")

def setup(run, examples=None, questions=None, assumptions=False, later=False):
    """Called by hive run: copy the owner's examples and set the question budget. Returns the prompt text. later=True:
    the owner is away, so questions are recorded for his morning instead of waited on (Gate 70)."""
    d = _dir(run)
    text = ''
    if later:   # questions are recorded for his morning; assumptions are still recorded, for a build that asked nothing
        json.dump({'questions': None, 'later': True}, open(os.path.join(d, 'budget.json'), 'w'))
        text += LATER
    if examples:
        ex = open(examples).read().strip() if os.path.exists(examples) else examples
        open(os.path.join(d, 'examples.md'), 'w').write(ex + '\n')
        text += ("\n## The owner's worked examples\nThe product owner wrote these: each shows one of their rules at work. "
                 "Encode every one that touches your areas as a test (do not change what they say), and work out the rule "
                 "behind each.\n\n" + ex + '\n')
    if questions is not None:
        json.dump({'questions': questions}, open(os.path.join(d, 'budget.json'), 'w'))
    if questions != 0 and not later:
        text += ("\n## Asking the owner\nThe owner is a business person, not an engineer. Ask with "
                 "`python3 -m hive ask \"<question>\"`, which blocks until they answer; first read `python3 -m hive answers` "
                 "(all answers so far). " + (f"The team has {questions} questions in all. " if questions else '') +
                 "Write every question as one real-life situation in plain words: real amounts in rupees, people and deals "
                 "instead of code, and 2 or 3 lettered choices (A, B, C), the last one being \"something else (please say)\". "
                 "No code, function names, quoted values, brackets or status codes: `hive ask` refuses them. Ask one thing "
                 "per question, the way you would ask a busy founder in person: one friendly sentence setting the scene "
                 "(who, what, how much), then the question, then the choices, under about 70 words in all. Translate the answer back into code yourself, encode it as a test before you land, and do not "
                 "stretch it into rules it does not state. **Ask before you build** (Gate 66): before you build an area, ask the "
                 "owner about every business decision the goal leaves open for it (cut-offs and boundaries, rounding, minimums "
                 "and caps, what happens with blank, missing, negative or oddly formatted information), one decision per "
                 "question, and build to his answers. Read `python3 -m hive answers` first and never ask what a teammate has "
                 "already asked." + (" With a fixed number of questions, spread them: at most 2 about one area before every "
                                     "area you own has had one (Gate 11)." if questions else '') + "\n")
    if assumptions:
        text += ("\n## Recording your assumptions\nThe owner will read, after the build, every default you chose that the goal "
                 "does not state, and correct the wrong ones. Builders miss most where they feel sure (Gate 27), so record every "
                 "such default, **especially the ones that seem obvious**: missing or unknown data, near matches, edge amounts, "
                 "mixed cases. For each one, before you land, run `python3 -m hive assume \"<one plain sentence>\"`: the situation "
                 "and what your code does, in the owner's words, with no code, for example: \"If a creator has not entered their "
                 "city, they are still shown for campaigns that require a city.\" Read `python3 -m hive assumptions` first so as "
                 "not to repeat one. If the goal does not list the allowed values of something (statuses, types, "
                 "categories, plans), record which values your code accepts and what it does with any other value: never "
                 "being told them caused the largest losses on a real company's rules (Gate 7).\n"
                 "The owner reads only **business** defaults: what a customer, partner or user would notice (who is included, "
                 "what is charged, what counts as a change, what happens with missing information). Keep them to the ones that "
                 "change an outcome. Record purely technical choices (refusing malformed input, error handling, ordering of a "
                 "list) with `python3 -m hive assume --technical \"...\"`: they go to the engineers' list, not the owner's.\n"
                 + ("**If you apply an owner's answer to any situation beyond the one asked**, record that wider rule as an "
                    "assumption too (\"The owner said a reworded item needs no new acceptance; I also treat a different item of "
                    "the same value that way\"). In Gate 28 a stretched answer broke a rule the owner held.\n" if questions != 0 else ''))
    return text

def ask(question, timeout_min=30):
    problems = plain_language_problems(question)
    if problems:
        print('Not asked: the owner is not an engineer. Rephrase it as one real-life situation in plain words, with amounts '
              'in rupees and 2 or 3 lettered choices, for example:\n'
              '  A creator was promised a bonus of up to Rs 2,000 but earned Rs 2,500. What should they get? '
              'A) Rs 2,000, the promised maximum  B) Rs 2,500, what they earned  C) something else (please say)\n'
              'Found: ' + ', '.join(problems)); return 5
    d = _dir(); budget = _budget(d)
    if _later(d):   # the owner is away: record it for his morning, and let the builder carry on (Gate 70)
        qid = f'{int(time.time() * 1000)}-{os.environ.get("HIVE_WORKER", "w")}'
        json.dump({'id': qid, 'worker': os.environ.get('HIVE_WORKER', '?'), 'question': question, 'asked': int(time.time()),
                   'later': True}, open(os.path.join(d, 'questions', qid + '.json'), 'w'))
        print('Recorded for the owner\'s morning. Build your best guess for now and keep going; the team will change the code '
              'to his answers.'); return 0
    asked = len(glob.glob(os.path.join(d, 'questions', '*.json')))
    if budget is not None and asked >= budget:
        print(f'question budget exhausted ({budget} for the whole team); decide from the goal, examples and answers'); return 3
    qid = f'{int(time.time() * 1000)}-{os.environ.get("HIVE_WORKER", "w")}'
    json.dump({'id': qid, 'worker': os.environ.get('HIVE_WORKER', '?'), 'question': question, 'asked': int(time.time())},
              open(os.path.join(d, 'questions', qid + '.json'), 'w'))
    path = os.path.join(d, 'answers', qid + '.json'); t0 = time.time()
    print(f'asked the owner (question {qid}); waiting for the answer...', flush=True)
    while time.time() - t0 < timeout_min * 60:
        if os.path.exists(path):
            a = json.load(open(path))
            print('ANSWER: ' + a['answer']); return 0
        time.sleep(3)
    print(f'no answer within {timeout_min} minutes; decide from the goal and examples, and say so when you land'); return 4

def assume(text, technical=False):
    """Record a default the goal does not state. Business defaults go to the owner's review; technical ones (Gate 28: most
    of a 27-item list was error handling an owner cannot judge) go to the engineers' list."""
    problems = [] if technical else plain_language_problems(text)
    if problems:
        print('Not recorded: write it for the owner, as one plain sentence about a real situation and what happens, for example:\n'
              '  If a creator has not entered their city, they are still shown for campaigns that require a city.\n'
              'Found: ' + ', '.join(problems) + '. If it is a purely technical choice, use hive assume --technical.'); return 5
    d = _dir(); aid = f'{int(time.time() * 1000)}-{os.environ.get("HIVE_WORKER", "w")}'
    json.dump({'id': aid, 'worker': os.environ.get('HIVE_WORKER', '?'), 'text': text.strip(), 'at': int(time.time()),
               'technical': technical}, open(os.path.join(d, 'assumptions', aid + '.json'), 'w'))
    print(f'recorded for the {"engineers" if technical else "owner"} to review (assumption {aid})'); return 0

def _assumptions(d, technical):
    rows = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(d, 'assumptions', '*.json')))]
    return [a for a in rows if bool(a.get('technical')) == technical]

def assumptions():
    d = _dir(); rows = _assumptions(d, False) + _assumptions(d, True)
    print('\n'.join(f"- ({a['worker']}){' [technical]' if a.get('technical') else ''} {a['text']}" for a in rows)
          if rows else 'no assumptions recorded yet'); return 0

def review(run, width=72, intro=True, goal=None, rulings=None):
    """The owner's check after the build: each recorded default, right or wrong. Wrong ones, with the owner's rule, go to
    <run>/owner/corrections.md for the workers who fix them (Gate 27: builders never ask about defaults they feel sure of).
    With the goal, each one is first put in plain words with an example, most important first (hive/explain.py)."""
    import textwrap
    d = _dir(run)
    tech = _assumptions(d, True)
    open(os.path.join(d, 'technical_assumptions.md'), 'w').write(
        '# Technical choices the builders made (for engineers; the owner is not asked)\n\n' +
        ('\n'.join(f"- ({a['worker']}) {a['text']}" for a in tech) if tech else 'None.') + '\n')
    todo = [a for a in _assumptions(d, False) if not os.path.exists(os.path.join(d, 'reviews', a['id'] + '.json'))]
    if goal and todo:
        from . import explain
        _, shown, aside = explain.plan(d, goal, todo, rulings)
        by_id = {a['id']: a for a in todo}
        todo = [dict(by_id[i['id']], text=i['text'], shown_as=i['text']) for i in shown + aside if i['id'] in by_id]
    if intro:
        print(f"\nThe builders made {len(todo)} assumption(s) your instructions did not cover. For each one, press Enter\n"
              "if it is right, or type what should happen instead. Ctrl+C to stop and come back later.", flush=True)
    try:
        i = 0
        while i < len(todo):
            a = todo[i]; n = i + 1
            lines = ['', '=' * width, f" Assumption {n} of {len(todo)}  -  from builder {a['worker']}", '=' * width, '']
            lines += textwrap.wrap(' '.join(a['text'].split()), width - 2, initial_indent='  ', subsequent_indent='  ')
            lines += ['', '  Right? Press Enter if yes, or say what should happen instead' +
                      (" (or type undo to change the last one)" if i else '') + ' > ']
            t0 = time.time(); print('\n'.join(lines), end='', flush=True)
            ans = sys.stdin.readline().strip()
            if ans.lower() == 'undo' and i:
                i -= 1; os.remove(os.path.join(d, 'reviews', todo[i]['id'] + '.json'))
                print('  No problem. Here it is again.', flush=True); continue
            ok = ans.lower() in ('', 'y', 'yes', 'right', 'ok', 'correct')
            json.dump({'id': a['id'], 'ok': ok, 'correction': None if ok else ans, 'seconds': int(time.time() - t0),
                       'shown_as': a.get('shown_as')}, open(os.path.join(d, 'reviews', a['id'] + '.json'), 'w'))
            print('  Kept.' if ok else '  Understood. The builders will change this.', flush=True)
            i += 1
    except KeyboardInterrupt:
        print('\nStopped; run hive review again to finish.')
    rows = write_corrections(d)
    if intro:
        print(f"\n{len(rows)} correction(s) written to {os.path.join(d, 'corrections.md')}. Thank you!")
    else:
        print('\nThanks. ' + ('Everything they assumed was right.' if not rows else f"{len(rows)} to fix."), flush=True)
    return 0

def write_corrections(d):
    """Every assumption the owner marked wrong, with the owner's rule, into <owner dir>/corrections.md."""
    rows = []
    for p in sorted(glob.glob(os.path.join(d, 'reviews', '*.json'))):
        r = json.load(open(p))
        if not r['ok']:
            a = json.load(open(os.path.join(d, 'assumptions', r['id'] + '.json')))
            shown = f"\n  (The owner saw it as: {r['shown_as']})" if r.get('shown_as') and r['shown_as'] != a['text'] else ''
            rows.append(f"- The builders assumed: {a['text']}{shown}\n  **The owner says:** {r['correction']}")
    res = os.path.join(d, 'resolutions.json')
    for c in (json.load(open(res)) if os.path.exists(res) else []):   # contradictions the owner settled; these win
        rows.append(f"- Two of the owner's answers contradicted each other: {c['question']}\n"
                    f"  **The owner decided:** {c['chosen']} (this overrides whichever answer above disagrees)")
    open(os.path.join(d, 'corrections.md'), 'w').write(
        "# The owner's corrections\n\nThe owner reviewed the defaults the builders applied, and each item below was wrong. "
        "Change the code to follow the owner, encode each correction as a test, and do not stretch it into rules it does not "
        "state. An existing test that asserts an overturned assumption is now wrong: change it to the owner's rule (the "
        "guard accepts an edited test that passes) and name it in your land message; leave every other test alone. "
        "**Record each change as built:** once a correction lands, run `python3 -m hive assume \"<one plain sentence>\"` "
        "saying exactly what the product now does in that situation, in the owner's words, for example: \"A failed "
        "renewal: the brand keeps its plan while the payment is retried for 30 days.\" The owner confirms each one. "
        "If other builders have already claimed every correction, "
        "stop at once: there is nothing left for you.\n\n" +('\n'.join(rows) if rows else 'No corrections: every assumption was right.') + '\n')
    return rows

def answers():
    d = _dir(); rows = []
    for p in sorted(glob.glob(os.path.join(d, 'answers', '*.json'))):
        a = json.load(open(p)); q = json.load(open(os.path.join(d, 'questions', a['id'] + '.json')))
        rows.append(f"Q ({q['worker']}): {q['question']}\nA: {a['answer']}\n")
    if _later(d):
        rows += [f"Q ({q['worker']}): {q['question']}\n(recorded for the owner's morning)\n" for q in pending(os.path.dirname(d))]
    print('\n'.join(rows) if rows else 'no answers yet'); return 0

def format_question(q, number, budget=None, width=72):
    """One question as the owner sees it: a header, the situation wrapped, then each lettered choice on its own line."""
    import textwrap
    parts = re.split(r'\s+(?=[A-D]\)\s)', q['question'].strip())
    situation, choices = parts[0], parts[1:]
    waited = max(0, int(time.time()) - q.get('asked', int(time.time())))
    head = f" Question {number}" + (f" of up to {budget}" if budget else '') + \
           f"  -  from builder {q['worker']}  -  asked {waited // 60}:{waited % 60:02d} ago"
    lines = ['', '=' * width, head, '=' * width, '']
    lines += textwrap.wrap(' '.join(situation.split()), width - 2, initial_indent='  ', subsequent_indent='  ')
    if choices:
        lines.append('')
        for c in choices:
            lines += textwrap.wrap(' '.join(c.split()), width - 4, initial_indent='    ', subsequent_indent='       ')
    lines += ['', '  Your answer (a letter, or say it in your own words) > ']
    return '\n'.join(lines)

NO_OWNER = ("The owner is not at the keyboard to answer. Decide as the goal most likely intends, and record your choice "
            "with `hive assume` so he can check it afterwards.")

def serve(run, poll=2, until=None, tick=None, greet=True):
    """The owner's terminal: show each unanswered question, read the answer, write it. Ctrl+C to stop.
    Inside `hive start`: tick() narrates progress between questions, and the loop ends once until() is true and no
    question is waiting."""
    if not os.path.exists(os.path.join(run, 'run.json')):
        print('Waiting for the builders to start...', flush=True)
        while not os.path.exists(os.path.join(run, 'run.json')):   # never create the run folder: hive run owns it
            time.sleep(poll)
    d = _dir(run); seen = set(); answered = 0; idle_note = False; closed = False
    if greet:
        print('\nHi! The builders are at work. When they hit a decision only you can make, the question appears here.\n'
              'Each one is a real situation: pick a letter, or answer in your own words, and press Enter.\n'
              'Press Enter on an empty line to come back to a question later; Ctrl+C when you are done.', flush=True)
    try:
        while True:
            if tick:
                tick()
            if until and until() and all(os.path.exists(os.path.join(d, 'answers', os.path.basename(p)))
                                         for p in glob.glob(os.path.join(d, 'questions', '*.json'))):
                return 0
            budget = _budget(d)
            for i, p in enumerate(sorted(glob.glob(os.path.join(d, 'questions', '*.json'))), 1):
                q = json.load(open(p))
                if q['id'] in seen or os.path.exists(os.path.join(d, 'answers', q['id'] + '.json')):
                    continue
                seen.add(q['id'])
                if closed:   # no one can answer here: the builder decides rather than waiting half an hour
                    json.dump({'id': q['id'], 'answer': NO_OWNER, 'answered': int(time.time()), 'seconds': 0, 'no_owner': True},
                              open(os.path.join(d, 'answers', q['id'] + '.json'), 'w'))
                    continue
                print(format_question(q, i, budget), end='', flush=True)
                line = sys.stdin.readline()
                if line == '':   # end of input (Gate 54: a closed input re-showed one question 173 times)
                    closed = True; seen.discard(q['id'])
                    print("\n  No one can answer here (the input is closed), so the builders will decide for themselves "
                          "and write down what they assumed; you can check those afterwards.", flush=True)
                    continue
                ans = line.strip()
                if not ans:
                    seen.discard(q['id']); print('  OK, I will show it again shortly.', flush=True); continue
                json.dump({'id': q['id'], 'answer': ans, 'answered': int(time.time()), 'seconds': int(time.time()) - q['asked']},
                          open(os.path.join(d, 'answers', q['id'] + '.json'), 'w'))
                answered += 1; idle_note = True
                print(f"  Thanks, sent to builder {q['worker']}. ({answered} answered so far)", flush=True)
            if idle_note and greet:
                print('\n  Waiting for the next question...', flush=True); idle_note = False
            time.sleep(poll)
    except KeyboardInterrupt:
        print(f'\nDone. You answered {answered} question(s). Thank you!')
        return 0
