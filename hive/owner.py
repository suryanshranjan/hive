"""The owner session: the owner's intent reaches a running swarm (Gates 13-24: owner examples plus questions).

Inside a run (HIVE_RUN set by `hive run`):
  workers:  hive ask "<question>"     ask the owner; blocks until answered; prints the answer
            hive answers              every question answered so far in this run (read before asking)
  owner:    hive owner --run <run>    answer pending questions in a terminal, as they arrive

Files under <run>/owner/: examples.md (the owner's worked examples, also put in every worker's prompt),
budget.json ({"questions": N}), questions/<id>.json, answers/<id>.json. Every answer is a ruling on that input:
the worker who asked encodes it as a test before landing."""
import glob, json, os, sys, time

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
        text += ("\n## Asking the owner\nThe owner answers questions live: `python3 -m hive ask \"<one concrete question, "
                 "ideally a specific input and what it should do>\"` blocks until they answer. First read "
                 "`python3 -m hive answers` (all answers so far). " + (f"The team has {questions} questions in all. " if questions else '') +
                 "Ask about what the goal and examples leave open. Every answer is a ruling on that input: encode it as a "
                 "test before you land, and do not stretch it into rules it does not state.\n")
    return text

def ask(question, timeout_min=30):
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

def serve(run, poll=2):
    """The owner's terminal: show each unanswered question, read the answer, write it. Ctrl+C to stop."""
    if not os.path.exists(os.path.join(run, 'run.json')):
        print('waiting for the run to start...', flush=True)
        while not os.path.exists(os.path.join(run, 'run.json')):   # never create the run folder: hive run owns it
            time.sleep(poll)
    d = _dir(run); seen = set()
    print('Answering questions for this run. Type the answer and press Enter; Ctrl+C to stop.', flush=True)
    try:
        while True:
            for p in sorted(glob.glob(os.path.join(d, 'questions', '*.json'))):
                q = json.load(open(p))
                if q['id'] in seen or os.path.exists(os.path.join(d, 'answers', q['id'] + '.json')):
                    continue
                seen.add(q['id'])
                print(f"\n[{q['worker']}] {q['question']}", flush=True)
                ans = sys.stdin.readline().strip()
                if not ans:
                    seen.discard(q['id']); continue
                json.dump({'id': q['id'], 'answer': ans, 'answered': int(time.time()), 'seconds': int(time.time()) - q['asked']},
                          open(os.path.join(d, 'answers', q['id'] + '.json'), 'w'))
                print('  saved.', flush=True)
            time.sleep(poll)
    except KeyboardInterrupt:
        return 0
