"""Stand-in for the model call in hive/explain.py (no tokens): rewrites each assumption with context and an example,
ranks them by their position, and marks the last one as something an owner cannot judge."""
import json, re, sys
prompt = sys.stdin.read()
def _out(d):
    print(json.dumps({'result': json.dumps(d)})); sys.exit(0)
if 'asked his assistant about his email' in prompt:   # hive/mail.py: the first message, by sender and subject
    frm = re.search(r'^\[1\] From: (.+)$', prompt, re.M); sub = re.search(r'^Subject: (.+)$', prompt, re.M)
    _out({'answer': f"{frm.group(1)} wrote about {sub.group(1)}." if frm else 'Nothing.', 'about': [1]})
if 'Which of these emails does he mean' in prompt:   # the message whose sender he names
    said = prompt.split('told his assistant: "')[1].split('"')[0]
    froms = re.findall(r'^\[(\d+)\] From: (.+)$', prompt, re.M)
    pick = next((int(k) for k, f in froms if any(w in f for w in re.findall(r'[A-Z][a-z]+', said))), 0)
    _out({'number': pick})
if 'wants to reply to this email' in prompt:   # a draft that carries what he asked to say
    said = prompt.split('His words: "')[1].split('"')[0]
    _out({'body': 'Hi, ' + (said.split('saying', 1)[1].strip() if 'saying' in said else said) + '\nThanks'})
if 'asked his assistant about his calendar' in prompt:   # the first event line
    evs = prompt.split('His events:\n')[1].split('\n\n')[0].splitlines()
    _out({'answer': f"{len(evs)} events: " + '; '.join(evs) if evs and evs[0] != '(nothing)' else 'Nothing on.'})
if 'asked his assistant about his payments' in prompt:   # the exact sums, as given
    _out({'answer': prompt.split('sums worked out exactly below):\n')[1].split('\n\n')[0]})
if 'would settle the new question completely' in prompt:   # duplicate questions: the same text is the same decision
    earlier = dict(re.findall(r'^(\d+)\. (.+)$', prompt.split('New question:')[0], re.M))
    new = prompt.split('New question: ')[1].split('\n')[0].strip()
    same = next((int(n) for n, q in earlier.items() if q.strip() == new), None)
    print(json.dumps({'result': json.dumps({'same': same})}))
    sys.exit(0)
if 'List every function it names explicitly' in prompt:   # Gate 84: the goal's stated interfaces (none here)
    print(json.dumps({'result': json.dumps({'functions': []})}))
    sys.exit(0)
if 'How many independent parts does it have' in prompt:   # the law's estimate of parallel work: fees and payouts
    print(json.dumps({'result': json.dumps({'parts': ['fees', 'payouts']})}))
    sys.exit(0)
if 'decisions the code for this feature must take' in prompt:   # the interview's plan: what the code must decide
    print(json.dumps({'result': json.dumps({'decisions': [{'case': 'A tip is paid', 'default': 'the usual fee'},
                                                          {'case': 'A fee is paid late', 'default': 'a reminder'}]})}))
    sys.exit(0)
if 'short interview with a busy' in prompt:   # the interview: two situations
    print(json.dumps({'result': json.dumps({'situations': [
        {'situation': 'Asha tips a creator Rs 500 after a great post.', 'options': ['No fee on a tip', 'The usual 10% fee']},
        {'situation': 'A brand pays the fee late by 3 days.', 'options': ['Remind them', 'Charge a late fee']}]})}))
    sys.exit(0)
if 'Amend his rule as he now means it' in prompt:   # keeps the shown rule and adds his correction
    shown = prompt.split('as it will be built:\n')[1].split('\n\nHe replied: ')[0]
    reply = prompt.split('He replied: ')[1].split('\n\nAmend his rule')[0]
    print(json.dumps({'result': json.dumps({'rule': f'{shown} Amended: {reply}'})}))
    sys.exit(0)
if 'Write his rule as one clear sentence' in prompt:
    print(json.dumps({'result': json.dumps({'rule': 'A late fee is charged only after 7 days.'})}))
    sys.exit(0)
if 'His newest message:' in prompt and 'What does he mean?' in prompt:   # the listener: read in context
    said = prompt.split('His newest message: "')[1].split('"\n')[0]
    history = prompt.split('(oldest first):')[1].split('His newest message:')[0]
    low = said.lower().strip(' !.')
    asked = [l for l in history.splitlines() if l.startswith('Hive: ') and 'Shall I build this?' in l]
    last_build = (history.split('Shall I build this?')[-1].strip().splitlines() or [''])[0] if asked else ''
    confirmed = low in ('yes', 'go ahead', 'yes build it', 'do it', 'build again') or 'already told you' in low
    if low == 'build again':   # points back to the last thing he asked to build
        owner = [l for l in history.splitlines() if l.startswith('Owner: ') and 'build' in l.lower()]
        if owner:
            asked, last_build = owner, owner[-1].split(':', 2)[-1].strip()
    intent = ('build' if confirmed and asked or low.startswith('make ') or low.startswith('a page')
              else 'cloud_on' if 'move to the cloud' in low else 'cloud_off' if 'delete the cloud' in low
              else 'change' if 'changed my mind' in low or low.startswith('actually') else 'status' if 'status' in low
              else 'greeting' if low in ('hi', 'hello', 'hey hive') else 'reply')
    rule = (said.split(':', 1)[-1].strip() if intent == 'change' else
            (last_build if confirmed else said) if intent == 'build' else '')
    about = low.startswith(('how do', 'how does', 'what happens when'))   # a question about his product
    print(json.dumps({'result': json.dumps({'intent': 'reply' if about else intent, 'rule': rule,
                                            'confirmed': bool(confirmed and asked), 'about_product': about})}))
    sys.exit(0)
if 'Write read-only SQL to answer it' in prompt:   # hive/access.py: one count from the first database listed
    db = re.search(r'^\[([^\]]+)\] \(db\)', prompt, re.M)
    sql = 'DELETE FROM orders' if 'DROP-ME' in prompt else "SELECT COUNT(*) AS orders FROM orders WHERE status = 'paid'"
    print(json.dumps({'result': json.dumps({'queries': [{'source': 'db' if 'KIND-NAME' in prompt else db.group(1), 'sql': sql}] if db and 'EMPTY-ME' not in prompt else []})}))
    sys.exit(0)
if 'Answer his question from his own data' in prompt:   # the last number the data shows, said plainly
    data = prompt.split('What his data shows:')[1].split('Answer him in')[0]
    nums = re.findall(r'^(\d+)\s*$', data, re.M)
    print(json.dumps({'result': json.dumps({'answer': f'{nums[-1]} paid orders so far.' if nums else
                                            'Your data does not show that.', 'found': bool(nums)})}))
    sys.exit(0)
if 'lasting facts does this give' in prompt:   # hive/onboard.py: name and facts from his description
    said = prompt.split('to his new assistant: "')[1].split('"\n')[0]
    name = re.search(r'\b(Sunny Shop|Tiny Notes)\b', said)
    print(json.dumps({'result': json.dumps({'name': name.group(1) if name else '',
                                            'facts': [s.strip() + '.' for s in re.split(r'[.;]', said) if s.strip()][:6]})}))
    sys.exit(0)
if 'Which earlier rulings does this replace' in prompt:
    print(json.dumps({'result': json.dumps({'replaces': [1] if 'late' in prompt.split('He now says:')[1] else []})}))
    sys.exit(0)
if 'contradict each other' in prompt:   # the contradiction check: decisions 1 and 2 clash when the owner's words say so
    clash = 'CONFLICT-ME' in prompt
    print(json.dumps({'result': json.dumps({'conflicts': [{'a': 1, 'b': 2, 'question': 'Should a missing price hide the day total?',
                      'option_a': 'Hide the total', 'option_b': 'Total from the others'}] if clash else []})}))
    sys.exit(0)
ids = [i for i in re.findall(r'"id": "([^"]+)"', prompt) if i != '...']
items = [{'id': i, 'context': f'In the shop report (item {k}).', 'example': f'For example, Asha with 3 orders.',
          'options': [{'label': 'Count once', 'text': 'count each order once'}, {'label': 'Count every time', 'text': 'count it every time it appears'}] if k == 0 else [{'label': 'Hide it', 'text': 'hide it from the report'}],
          'recommend': 1 if k == 0 else 0, 'advice': "I'd go with counting each order once." if k == 0 else "I'd keep it.", 'impact': 3 if k == 0 else 1, 'owner_can_judge': k < len(ids) - 1}
         for k, i in enumerate(ids)]
print(json.dumps({'result': json.dumps({'summary': 'A report that adds up daily shop orders.', 'items': items})}))
