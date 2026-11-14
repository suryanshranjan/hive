"""Gate 108: can a founder run his company through Hive? Dabba Days, flown on a fake Telegram with real Claude.

The founder onboards ("set me up", business path, a scripted founder: his words are fixed so the run is repeatable),
asks how his cooks are paid, asks 10 questions about his figures, asks for screens, then gives a growth goal and
answers Hive's questions from a short brief (a simulated founder). Everything both ways is kept in
results/transcript.json; scoring against the private answer key is done by analyze108.py.

usage (lab, clean home with the Dabba Days data at ~/dabba-data):
    HOME=/home/node/f108 python3 gates/gate108/flight108.py"""
import glob, json, os, re, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
from hive import assistant, doctor, explain, start, telegram

HOME = os.path.expanduser('~'); OUT = os.path.join(HERE, 'results'); os.makedirs(OUT, exist_ok=True)
DATA = os.path.join(HOME, 'dabba-data')
BRIEF = """You run Dabba Days, a monthly lunchbox subscription in Bengaluru: home cooks in six areas make lunch, delivered
to office workers by 1 pm, Monday to Friday. Plans: Veg Basic Rs 2,400, Veg Plus Rs 3,000, Non-veg Rs 3,400 a month,
20 lunches each. About 200 subscribers since August; you want 500 by March. Most sign-ups come from Instagram and
referrals. You are busy: you answer briefly. You would accept a cheap trial week if it brings people in, and you know
most office workers do not have a GST number."""

def owner(question, options):
    ask = (f"You are this business owner:\n{BRIEF}\n\nYour assistant asks you on your phone:\n{question}\n" +
           (''.join(f'{k}. {o}\n' for k, o in enumerate(options)) + '\nReply with JSON only: {"pick": <number>}'
            if options else '\nReply with JSON only: {"say": "<your short answer>"}'))
    r = subprocess.run(['claude', '-p', ask, '--output-format', 'json'], capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=300)
    t = json.loads(r.stdout)['result']; j = json.loads(t[t.index('{'):t.rindex('}') + 1])
    return int(j.get('pick', 0)) if options else str(j.get('say', 'Keep it simple.'))

YES = ('pln|all', 'bld|yes', 'shp|yes', 'stp|yes')

class Phone:
    """The fake Telegram. Scripted replies go first, in order, whenever Hive waits; otherwise the simulated founder
    taps the obvious yes or answers from his brief. Everything both ways is kept."""
    def __init__(self):
        self.sent, self.uid, self.done, self.log, self.step, self.script = [], 0, set(), [], 0, []
    def __call__(self, method, **p):
        import html as H
        if method in ('sendMessage', 'sendPhoto'):
            kb = (p.get('reply_markup') or {}).get('inline_keyboard', [])
            m = {'step': self.step, 'text': H.unescape(re.sub(r'<[^>]+>', '', p.get('text', p.get('caption', '')))),
                 'photo': method == 'sendPhoto', 'file': p.get('_upload', (None, None))[1] if method == 'sendPhoto' else None,
                 'buttons': [b['callback_data'] for r in kb for b in r], 'labels': [b['text'] for r in kb for b in r],
                 't': time.time()}
            self.sent.append(m); self.log.append(('hive', m['text'][:2000] + (' [photo]' if m['photo'] else '')))
            return {'message_id': len(self.sent)}
        if method in ('answerCallbackQuery', 'sendChatAction'):
            return True
        if method == 'getChat':
            return {'first_name': 'Ravi'}
        if method == 'getUpdates':
            if p.get('timeout') == 0:
                return []
            self.uid += 1
            if self.script:
                kind, val = self.script.pop(0)
                if kind == 'tap':
                    self.log.append(('owner', f'[tap] {val}'))
                    return [{'update_id': self.uid, 'callback_query': {'id': str(self.uid), 'data': val,
                             'message': {'message_id': len(self.sent), 'chat': {'id': 1}}}}]
                self.log.append(('owner', val))
                return [{'update_id': self.uid, 'message': {'message_id': 900 + self.uid, 'chat': {'id': 1}, 'text': val}}]
            for k in range(len(self.sent) - 1, -1, -1):
                m = self.sent[k]
                if k in self.done or not (m['buttons'] or m['text'].startswith('❓')):
                    continue
                self.done.add(k)
                yes = [d for d in m['buttons'] if d in YES]
                if yes:
                    return self._tap(yes[0], k, m['labels'][m['buttons'].index(yes[0])])
                if m['buttons'] and not m['buttons'][0].startswith(('pm|', 'onb|')):
                    pick = owner(m['text'], m['labels']); return self._tap(m['buttons'][pick], k, m['labels'][pick])
                said = owner(m['text'], [])
                self.log.append(('owner', said))
                return [{'update_id': self.uid, 'message': {'message_id': 900 + self.uid, 'chat': {'id': 1}, 'text': said}}]
            time.sleep(0.5)
            return []
        if method == 'getFile':
            return {'file_path': 'x'}
        raise AssertionError(method)
    def _tap(self, data, k, label):
        self.log.append(('owner', f'[tap] {label}'))
        return [{'update_id': self.uid, 'callback_query': {'id': str(self.uid), 'data': data,
                 'message': {'message_id': k + 1, 'chat': {'id': 1}}}}]

def settle(limit=2400):
    t0 = time.time()
    while time.time() - t0 < limit:
        p = assistant.BUILD.get('proc')
        if not assistant.PLAN.get('running') and (p is None or p.poll() is not None):
            break
        time.sleep(5)
    time.sleep(12)

QUESTIONS = ['How many active subscribers do we have right now?',
             'How many new subscribers signed up in October?',
             'How many subscribers cancelled in October?',
             'Which cook had the most complaints in October?',
             'How much skip credit did we give in October?',
             'What is our refund total this month?',
             'What was our revenue from subscriptions in October?',
             'Which plan is most popular among active subscribers?',
             'Which area has the most active subscribers?',
             'How much did we pay our cooks in October, bonuses included?']

def main():
    origin = os.path.join(HOME, 'github', 'dabba-days.git')
    for d in (origin, os.path.join(HOME, 'hive-projects')):
        shutil.rmtree(d, ignore_errors=True)
    os.makedirs(os.path.dirname(origin), exist_ok=True)
    subprocess.run(['git', 'clone', '-q', '--bare', os.path.join(HOME, 'dabba-days-src'), origin], check=True)
    repo = doctor.fetch_repo(origin)   # hive up --repo <address>
    calls = {'n': 0}
    real = explain.ask_json
    def counted(prompt):
        calls['n'] += 1
        return real(prompt)
    explain.ask_json = counted
    phone = Phone(); ch = telegram.Channel({'chat_id': 1, 'token': 'x', 'address': 'sir'}, api=phone)
    ch.listener = True   # as hive listen runs it
    assistant.CURRENT['ch'] = ch
    t_all = time.time(); steps = []
    def say(n, text, wait=False, script=()):
        phone.step = n; phone.script = list(script); phone.log.append(('owner', text)); t0 = time.time(); r = None
        try:
            r = assistant.handle(ch, repo, text, poll=1, apply_build=start.apply_ruling,
                                 start_build=lambda rp, goal, interview=True: assistant.background_build(rp, goal, interview=interview))
        except Exception as e:
            r = f'CRASH {e!r}'
        if wait:
            settle()
        steps.append({'step': n, 'said': text, 'result': r, 'minutes': round((time.time() - t0) / 60, 1),
                      'script_left': len(phone.script),
                      'hive': [m['text'][:2500] + (f" [photo {os.path.basename(m['file'] or '')}]" if m['photo'] else '')
                               for m in phone.sent if m['step'] == n]})
        print(f'step {n}: {r} ({steps[-1]["minutes"]} min)', flush=True)
        json.dump({'steps': steps, 'transcript': phone.log}, open(os.path.join(OUT, 'transcript.json'), 'w'), indent=1,
                  ensure_ascii=False)
    say('hello', 'hi')
    say('onboard', 'set me up', script=[
        ('tap', 'onb|who|business'),
        ('say', 'Dabba Days. Home cooks make lunch and we deliver it to office workers in Bengaluru, Monday to Friday. '
                'Our customers are people working in offices in six areas.'),
        ('tap', 'onb|skip|2'),
        ('say', f'here is our database {os.path.join(DATA, "dabba.db")}'),
        ('say', 'done'),
        ('say', f'our policy [document: {os.path.join(DATA, "docs", "policy.md")} | policy.md]'),
        ('say', 'done'),
        ('tap', 'onb|skip|5')])
    say('cooks', 'How are our cooks paid?')
    for k, q in enumerate(QUESTIONS, 1):
        say(f'q{k}', q)
    say('screen1', 'show me the plans page on desktop')
    say('screen2', 'and on tablet?')
    say('screen3', 'show me the sign up page on every screen')
    say('goal', 'I want more office workers subscribing', wait=True)
    spent = sum(json.load(open(h)).get('cost', 0) or 0 for h in glob.glob(os.path.join(assistant.RUNS, '*', 'state.json')))
    summary = {'minutes': round((time.time() - t_all) / 60, 1), 'builders_cost': round(spent, 2),
               'plan_cost': assistant.PLAN.get('cost', 0), 'reader_calls': calls['n'],
               'plan': assistant.PLAN.get('steps')}
    json.dump({'steps': steps, 'transcript': phone.log, 'summary': summary}, open(os.path.join(OUT, 'transcript.json'), 'w'),
              indent=1, ensure_ascii=False)
    print('done', summary, flush=True)

if __name__ == '__main__':
    main()
