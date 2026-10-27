"""The owner session: the owner's intent reaches a running swarm (Gates 13-24: owner examples plus questions).

Inside a run (HIVE_RUN set by `hive run`):
  workers:  hive ask "<question>"     ask the owner; blocks until answered; prints the answer
            hive answers              every question answered so far in this run (read before asking)
  owner:    hive owner --run <run>    answer pending questions in a terminal, as they arrive

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
    for sub in ('questions', 'answers'):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    return d

def _budget(d):
    p = os.path.join(d, 'budget.json')
    return json.load(open(p)).get('questions') if os.path.exists(p) else None

def setup(run, examples=None, questions=None):
    """Called by hive run: copy the owner's examples and set the question budget. Returns the prompt text."""
    d = _dir(run)
    text = ''
    if examples:
        ex = open(examples).read().strip() if os.path.exists(examples) else examples
        open(os.path.join(d, 'examples.md'), 'w').write(ex + '\n')
        text += ("\n## The owner's worked examples\nThe product owner wrote these: each shows one of their rules at work. "
                 "Encode every one that touches your areas as a test (do not change what they say), and work out the rule "
                 "behind each.\n\n" + ex + '\n')
    if questions is not None:
        json.dump({'questions': questions}, open(os.path.join(d, 'budget.json'), 'w'))
    if questions != 0:
        text += ("\n## Asking the owner\nThe owner is a business person, not an engineer. Ask with "
                 "`python3 -m hive ask \"<question>\"`, which blocks until they answer; first read `python3 -m hive answers` "
                 "(all answers so far). " + (f"The team has {questions} questions in all. " if questions else '') +
                 "Write every question as one real-life situation in plain words: real amounts in rupees, people and deals "
                 "instead of code, and 2 or 3 lettered choices (A, B, C), the last one being \"something else (please say)\". "
                 "No code, function names, quoted values, brackets or status codes: `hive ask` refuses them. Ask one thing "
                 "per question, the way you would ask a busy founder in person: one friendly sentence setting the scene "
                 "(who, what, how much), then the question, then the choices, under about 70 words in all. Translate the answer back into code yourself, encode it as a test before you land, and do not "
                 "stretch it into rules it does not state.\n")
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

def answers():
    d = _dir(); rows = []
    for p in sorted(glob.glob(os.path.join(d, 'answers', '*.json'))):
        a = json.load(open(p)); q = json.load(open(os.path.join(d, 'questions', a['id'] + '.json')))
        rows.append(f"Q ({q['worker']}): {q['question']}\nA: {a['answer']}\n")
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

def serve(run, poll=2):
    """The owner's terminal: show each unanswered question, read the answer, write it. Ctrl+C to stop."""
    if not os.path.exists(os.path.join(run, 'run.json')):
        print('Waiting for the builders to start...', flush=True)
        while not os.path.exists(os.path.join(run, 'run.json')):   # never create the run folder: hive run owns it
            time.sleep(poll)
    d = _dir(run); seen = set(); answered = 0; idle_note = False
    print('\nHi! The builders are at work. When they hit a decision only you can make, the question appears here.\n'
          'Each one is a real situation: pick a letter, or answer in your own words, and press Enter.\n'
          'Press Enter on an empty line to come back to a question later; Ctrl+C when you are done.', flush=True)
    try:
        while True:
            budget = _budget(d)
            for i, p in enumerate(sorted(glob.glob(os.path.join(d, 'questions', '*.json'))), 1):
                q = json.load(open(p))
                if q['id'] in seen or os.path.exists(os.path.join(d, 'answers', q['id'] + '.json')):
                    continue
                seen.add(q['id'])
                print(format_question(q, i, budget), end='', flush=True)
                ans = sys.stdin.readline().strip()
                if not ans:
                    seen.discard(q['id']); print('  OK, I will show it again shortly.', flush=True); continue
                json.dump({'id': q['id'], 'answer': ans, 'answered': int(time.time()), 'seconds': int(time.time()) - q['asked']},
                          open(os.path.join(d, 'answers', q['id'] + '.json'), 'w'))
                answered += 1; idle_note = True
                print(f"  Thanks, sent to builder {q['worker']}. ({answered} answered so far)", flush=True)
            if idle_note:
                print('\n  Waiting for the next question...', flush=True); idle_note = False
            time.sleep(poll)
    except KeyboardInterrupt:
        print(f'\nDone. You answered {answered} question(s). Thank you!')
        return 0
