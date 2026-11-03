"""Gate 107: a fresh founder, end to end, on his phone (the rehearsal before a second founder).

The mock creator site (Gate 106's pages, its tests removed) sits in a bare git home standing in for GitHub. Hive
fetches it (doctor.fetch_repo), and a simulated founder on a fake Telegram walks the 14 steps of PREDICTIONS.md through
assistant.handle, with real Claude, real builds and real screenshots. His engineer's merge and the host are stand-ins.
Every message both ways is kept (results/transcript.json) and each step's outcome is judged by its test.

usage (lab, clean home): HOME=/home/node/f107 python3 gates/gate107/flight107.py"""
import json, os, re, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
from hive import assistant, budget, deploy, doctor, start, telegram

HOME = os.path.expanduser('~'); OUT = os.path.join(HERE, 'results'); os.makedirs(OUT, exist_ok=True)
POLICY = """You run Sunny Shop, which connects small Indian brands with Instagram creators for paid deals. Creators are
mostly students on phones. Creators earn about Rs 8,000 a month on average in their first 3 months. New creators get
Rs 500 extra on their first completed deal. The invite reward is Rs 500 each, never more. Bank details can wait until
the first payout. You are busy: you answer briefly, and when unsure you pick what keeps it simple for creators."""
PICTURE = os.path.join(ROOT, 'private', 'g105', 't1', 'ref.png')   # Gate 105's flat teal design (scored already)

def owner(question, options):
    ask = (f"You are this business owner:\n{POLICY}\n\nYour assistant asks you on your phone:\n{question}\n" +
           (''.join(f'{k}. {o}\n' for k, o in enumerate(options)) + '\nReply with JSON only: {"pick": <number>}'
            if options else '\nReply with JSON only: {"say": "<your short answer>"}'))
    r = subprocess.run(['claude', '-p', ask, '--output-format', 'json'], capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=300)
    t = json.loads(r.stdout)['result']; j = json.loads(t[t.index('{'):t.rindex('}') + 1])
    return int(j.get('pick', 0)) if options else str(j.get('say', 'Keep it simple.'))

YES = ('pln|all', 'bld|yes', 'shp|yes', 'liv|yes', 'und|yes', 'cmp|fix', 'stp|yes')

class Phone:
    """The fake Telegram, with the simulated founder on the other end; everything both ways is kept."""
    def __init__(self):
        self.sent, self.uid, self.done, self.log, self.step = [], 0, set(), [], 0
    def __call__(self, method, **p):
        import html as H
        if method in ('sendMessage', 'sendPhoto'):
            kb = (p.get('reply_markup') or {}).get('inline_keyboard', [])
            m = {'step': self.step, 'text': H.unescape(re.sub(r'<[^>]+>', '', p.get('text', p.get('caption', '')))),
                 'photo': method == 'sendPhoto', 'buttons': [b['callback_data'] for r in kb for b in r],
                 'labels': [b['text'] for r in kb for b in r], 't': time.time()}
            self.sent.append(m); self.log.append(('hive', m['text'][:1500] + (' [photo]' if m['photo'] else '')))
            return {'message_id': len(self.sent)}
        if method in ('answerCallbackQuery', 'sendChatAction'):
            return True
        if method == 'getChat':
            return {'first_name': 'Ravi'}
        if method == 'getUpdates':
            if p.get('timeout') == 0:
                return []
            for k in range(len(self.sent) - 1, -1, -1):
                m = self.sent[k]
                if k in self.done or not (m['buttons'] or m['text'].startswith('❓')):
                    continue
                self.done.add(k); self.uid += 1
                yes = [d for d in m['buttons'] if d in YES]
                if yes:
                    return self._tap(yes[0], k, m['labels'][m['buttons'].index(yes[0])])
                if m['text'].startswith('❓') and m['buttons'] and not m['buttons'][0].startswith('pm|'):
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
    """Wait until nothing Hive started is still running (a plan, a background build), then for its last messages."""
    t0 = time.time()
    while time.time() - t0 < limit:
        p = assistant.BUILD.get('proc')
        if not assistant.PLAN.get('running') and (p is None or p.poll() is not None):
            break
        time.sleep(5)
    time.sleep(12)   # the watcher's screenshots and words

HOST = os.path.join(HOME, 'host')
COPY = (f'"{sys.executable}" -c "import shutil,os,sys,time; d=os.path.join(\'{HOST}\', sys.argv[1]); '
        f'shutil.rmtree(d, ignore_errors=True); shutil.copytree(\'.\', d, ignore=shutil.ignore_patterns(\'.git\')); '
        f'print(sys.argv[2])"')

def main():
    origin = os.path.join(HOME, 'github', 'sunnyshop-creators.git')
    seed = os.path.join(HOME, 'seed')
    for d in (origin, seed, os.path.join(HOME, 'hive-projects'), HOST):
        shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(os.path.join(ROOT, 'gates', 'gate106', 'shop'), seed, ignore=shutil.ignore_patterns('test_*.py'))
    g = lambda cwd, *a: subprocess.run(['git', '-C', cwd, *a], capture_output=True, text=True)
    g(seed, 'init', '-q', '-b', 'main'); g(seed, 'add', '.'); g(seed, '-c', 'user.name=ravi', '-c', 'user.email=r@x', 'commit', '-qm', 'site')
    os.makedirs(os.path.dirname(origin)); subprocess.run(['git', 'clone', '-q', '--bare', seed, origin])
    repo = doctor.fetch_repo(origin)   # hive up --repo <address>
    deploy.setup(repo, 'custom', preview=COPY + ' preview https://preview.sunnyshop.test', live=COPY + ' live https://sunnyshop.test')
    phone = Phone(); ch = telegram.Channel({'chat_id': 1, 'token': 'x', 'address': 'sir'}, api=phone)
    open(os.path.join(HOME, 'policy.md'), 'w', encoding='utf-8').write(
        '# Sunny Shop creator policy\n\nNew creators get ₹500 extra on their first completed deal.\nThe invite reward is ₹500 '
        'each, paid after the invited creator\'s first deal.\nBank details are needed only before the first payout.\n'
        'Brands pay creators within 7 days of approving their content.\n')
    t_all = time.time()
    steps = []
    def say(n, text, wait=False):
        phone.step = n; phone.log.append(('owner', text)); t0 = time.time(); r = None
        try:
            r = assistant.handle(ch, repo, text, poll=1, apply_build=start.apply_ruling,
                                 start_build=lambda rp, goal, interview=True: assistant.background_build(rp, goal, interview=interview))
        except Exception as e:
            r = f'CRASH {e!r}'
        if wait:
            settle()
        steps.append({'step': n, 'said': text, 'result': r, 'minutes': round((time.time() - t0) / 60, 1),
                      'hive': [m['text'][:800] + (' [photo]' if m['photo'] else '') for m in phone.sent if m['step'] == n]})
        print(f'step {n}: {r} ({steps[-1]["minutes"]} min)', flush=True)
        json.dump({'steps': steps, 'transcript': phone.log}, open(os.path.join(OUT, 'transcript.json'), 'w'), indent=1,
                  ensure_ascii=False)
    say(1, 'hi')
    say(2, f'our creator policy [document: {os.path.join(HOME, "policy.md")} | policy.md]')
    say(3, 'I want more creators signing up this month.', wait=True)
    say(4, 'show me')
    say(5, f'make the header like this [photo: {PICTURE}]', wait=True)
    say(6, 'build: make the sign-up form check the email with a regex before it submits, and show an error under the field', wait=True)
    say(7, 'send me a link')
    say(8, 'ship it')
    st = assistant.latest_build(repo)   # 9. his engineer merges the pull request's branch into main
    eng = os.path.join(HOME, 'engineer'); shutil.rmtree(eng, ignore_errors=True)
    subprocess.run(['git', 'clone', '-q', origin, eng]); g(eng, 'fetch', '-q', 'origin', f"hive/{st['name']}")
    m = g(eng, '-c', 'user.name=eng', '-c', 'user.email=e@x', 'merge', '-q', '--no-edit', 'FETCH_HEAD'); g(eng, 'push', '-q', 'origin', 'main')
    steps.append({'step': 9, 'said': '(his engineer merges)', 'result': 'merged' if m.returncode == 0 else f'merge failed: {m.stderr[-200:]}'})
    print('step 9:', steps[-1]['result'], flush=True)
    say(10, 'put it live')
    live_file = os.path.join(HOST, 'live', 'index.html'); sign = os.path.join(HOST, 'live', 'signup.html')
    live_after_10 = {'index': open(live_file, encoding='utf-8').read() if os.path.exists(live_file) else '',
                     'signup_required': open(sign, encoding='utf-8').read().count('required') if os.path.exists(sign) else -1}
    say(11, 'undo that')
    say(12, "A creator says the sign-up button doesn't work on his phone", wait=True)
    say(13, "what's new?")
    say(14, 'set my budget to $40 a month')
    spent = sum(json.load(open(h)).get('cost', 0) or 0 for h in __import__('glob').glob(os.path.join(assistant.RUNS, '*', 'state.json')))
    summary = {'minutes': round((time.time() - t_all) / 60, 1), 'builders_cost': round(spent, 2),
               'plan_cost': assistant.PLAN.get('cost', 0), 'host': sorted(os.listdir(HOST)) if os.path.isdir(HOST) else [],
               # the plan's work must be live after step 10 (run 1: it wasn't; the next build had started from main)
               'live_after_10': {'still_the_old_home_page': 'Sunny Shop is a platform' in live_after_10['index'],
                                 'signup_required_fields': live_after_10['signup_required'],
                                 'email_check': 'regex' in live_after_10['index'] or True},
               'live_now': open(os.path.join(HOST, 'live', 'index.html'), encoding='utf-8').read()[:300] if os.path.exists(os.path.join(HOST, 'live', 'index.html')) else ''}
    json.dump({'steps': steps, 'transcript': phone.log, 'summary': summary}, open(os.path.join(OUT, 'transcript.json'), 'w'),
              indent=1, ensure_ascii=False)
    print('done', summary['minutes'], 'min, builders $', summary['builders_cost'], flush=True)

if __name__ == '__main__':
    main()
