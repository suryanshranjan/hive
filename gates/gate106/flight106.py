"""Gate 106: the owner gives only the business; Hive works out what to change, and does it.

One flight = one business goal on the mock Sunny Shop Creators product (gates/gate106/shop), driven through Jarvis
exactly as from the phone: assistant.handle(goal) -> pursue (the plan in plain words, one yes, his few decisions) ->
run_plan (step 1 a build, later steps fix rounds on the same branch, each shown). The owner is simulated on a fake
Telegram: he sends only the goal, taps "Yes, do it all", and answers questions from his private policy (an LLM reading
private/g106/policy.md). Arms: A = the planner; B = the planner plus a simulated customer panel (MiroFish's idea,
re-implemented, HIVE_PLAN_PANEL=1).

usage (lab, one process per flight; the HOME is the flight's own):
  HOME=/home/node/f106/<g><arm> python3 gates/gate106/flight106.py <g1|g2|g3> <A|B>"""
import json, os, shutil, subprocess, sys, time

GOAL_ID, ARM = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
os.environ['HIVE_PLAN_PANEL'] = '1' if ARM == 'B' else '0'
os.environ['HIVE_CONTRACT_CHECK'] = '0'   # static pages: no stated interfaces
from hive import assistant, memory, start, telegram

PRIV = os.path.join(ROOT, 'private', 'g106')
GOALS = {'g1': 'I want more creators signing up this month.',
         'g2': 'Creators who join never make their first deal. Help me get more of them to a first deal.',
         'g3': 'I want more creators to invite their friends.'}
NOTES = ['Sunny Shop connects small Indian brands with Instagram creators for paid deals.',
         'Most of our creators are students and part-timers in tier-2 cities, on their phones.',
         'Creators earn on average ₹8,000 a month in their first 3 months.']
OUT = os.path.join(HERE, 'results'); os.makedirs(OUT, exist_ok=True)
CELL = GOAL_ID + ARM
HOME = os.path.expanduser('~')

def owner_answer(question, options):
    """The simulated owner, answering from his private policy: an option's index, or a few words."""
    policy = open(os.path.join(PRIV, 'policy.md'), encoding='utf-8').read()
    ask = (f"You are this business owner:\n{policy}\n\nYour assistant asks you, on your phone:\n{question}\n" +
           (''.join(f'{k}. {o}\n' for k, o in enumerate(options)) + '\nReply with JSON only: {"pick": <number>}'
            if options else '\nReply with JSON only: {"say": "<your answer in a few words>"}'))
    r = subprocess.run(['claude', '-p', ask, '--output-format', 'json'], capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=300)
    text = json.loads(r.stdout)['result']
    j = json.loads(text[text.index('{'):text.rindex('}') + 1])
    return j.get('pick', 0) if options else j.get('say', 'Keep it simple for the creator.')

class Owner:
    """A fake Telegram with the simulated owner on the other end."""
    def __init__(self):
        self.sent, self.uid, self.answered, self.owner_msgs, self.asked = [], 0, set(), [], []
    def __call__(self, method, **p):
        import html as H, re
        if method in ('sendMessage', 'sendPhoto'):
            text = p.get('text', p.get('caption', ''))
            self.sent.append({'text': H.unescape(re.sub(r'<[^>]+>', '', text)), 'photo': method == 'sendPhoto',
                              'buttons': [b['callback_data'] for row in (p.get('reply_markup') or {}).get('inline_keyboard', []) for b in row],
                              'labels': [b['text'] for row in (p.get('reply_markup') or {}).get('inline_keyboard', []) for b in row],
                              't': time.time()})
            return {'message_id': len(self.sent)}
        if method in ('answerCallbackQuery', 'sendChatAction'):
            return True
        if method == 'getChat':
            return {'first_name': 'Owner'}
        if method == 'getUpdates':
            if p.get('timeout') == 0:
                return []
            for k in range(len(self.sent) - 1, -1, -1):
                m = self.sent[k]
                if k in self.answered or not (m['buttons'] or m['text'].startswith('❓')):
                    continue
                self.answered.add(k); self.uid += 1
                if 'pln|all' in m['buttons']:
                    self.owner_msgs.append('[tap] Yes, do it all')
                    return [{'update_id': self.uid, 'callback_query': {'id': str(self.uid), 'data': 'pln|all',
                             'message': {'message_id': k + 1, 'chat': {'id': 1}}}}]
                if m['text'].startswith('❓'):
                    opts = m['labels']; got = owner_answer(m['text'], opts)
                    self.asked.append({'question': m['text'], 'options': opts, 'answer': opts[int(got)] if opts else got})
                    if opts:
                        self.owner_msgs.append(f'[tap] {opts[int(got)]}')
                        return [{'update_id': self.uid, 'callback_query': {'id': str(self.uid), 'data': m['buttons'][int(got)],
                                 'message': {'message_id': k + 1, 'chat': {'id': 1}}}}]
                    self.owner_msgs.append(got)
                    return [{'update_id': self.uid, 'message': {'message_id': 900 + self.uid, 'chat': {'id': 1}, 'text': got}}]
                self.owner_msgs.append('[unexpected buttons: ' + ','.join(m['buttons']) + ']')
            time.sleep(0.5)
            return []
        if method == 'getFile':
            return {'file_path': 'x'}
        raise AssertionError(method)

def main():
    repo = os.path.join(HOME, 'shop')
    if os.path.exists(repo):
        start._rmtree(repo)
    shutil.copytree(os.path.join(HERE, 'shop'), repo)
    g = lambda *a: subprocess.run(['git', '-C', repo, *a], capture_output=True, text=True)
    g('init', '-q', '-b', 'main'); g('add', '.'); g('-c', 'user.name=owner', '-c', 'user.email=o@x', 'commit', '-qm', 'Sunny Shop Creators')
    for n in NOTES:
        memory.add_note(repo, n)
    api = Owner()
    ch = telegram.Channel({'chat_id': 1, 'token': 'x', 'address': 'sir'}, api=api)
    t0 = time.time()
    run_plan = assistant.run_plan
    assistant.run_plan = lambda *a, **k: None   # handle starts the plan in a thread, as on his phone; here it is run
    r = assistant.handle(ch, repo, GOALS[GOAL_ID], poll=1, apply_build=start.apply_ruling)   # once, in the foreground
    assistant.run_plan = run_plan
    plan = {k: assistant.PLAN.get(k) for k in ('steps', 'answers')}
    ran = run_plan(ch, repo, start.apply_ruling) if r == 'planned' else r
    mins = (time.time() - t0) / 60
    st = assistant.latest_build(repo) or {}
    final = os.path.join(HOME, 'final')
    if os.path.exists(final):
        start._rmtree(final)
    if st.get('name'):
        subprocess.run(['git', 'clone', '-q', '-b', f"hive/{st['name']}", repo, final])
    tests = start.run_tests(final, 'python3 -m pytest -q --junitxml=.hive/junit.xml') if os.path.isdir(final) else {}
    json.dump({'cell': CELL, 'goal': GOALS[GOAL_ID], 'arm': ARM, 'handled': r, 'ran': ran, 'minutes': round(mins, 1),
               'plan': plan, 'plan_cost': assistant.PLAN.get('cost', 0), 'builders_cost': st.get('cost', 0),
               'check': st.get('check', ''), 'tests': f'{sum(tests.values())}/{len(tests)}',
               'owner_messages': [GOALS[GOAL_ID]] + api.owner_msgs, 'questions': api.asked,
               'hive_messages': [{'text': m['text'], 'photo': m['photo']} for m in api.sent],
               'final': final}, open(os.path.join(OUT, CELL + '.json'), 'w'), indent=1, ensure_ascii=False)
    if os.path.isdir(final):   # the delivered product, for the private checks and to look at
        dst = os.path.join(OUT, CELL + '_product'); shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(final, dst, ignore=shutil.ignore_patterns('.git', '__pycache__', '.pytest_cache', 'current_tasks'))
    print(f'{CELL}: {r} -> {ran}, {mins:.1f} min, plan ${assistant.PLAN.get("cost", 0):.2f}, builders ${st.get("cost", 0):.2f}, '
          f'{st.get("check", "")}, owner messages {1 + len(api.owner_msgs)}', flush=True)

if __name__ == '__main__':
    main()
