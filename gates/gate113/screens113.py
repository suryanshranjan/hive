"""Gate 113, R4 again: the flight's home had no screenshot browser (PLAYWRIGHT_BROWSERS_PATH was left out at launch, as
lab/QUEUE.md says a clean home needs), and Hive said so plainly. The same three requests, with the browser found.

usage (lab): HOME=/home/node/f113 PLAYWRIGHT_BROWSERS_PATH=/home/node/.cache/ms-playwright python3 gates/gate113/screens113.py"""
import glob, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
import flight113 as f
from hive import assistant, telegram

repo = next(p for p in glob.glob(os.path.join(f.HOME, 'hive-projects', '*')) if os.path.isdir(os.path.join(p, '.git')))
phone = f.Phone(); ch = telegram.Channel({'chat_id': 1, 'token': 'x', 'address': 'sir'}, api=phone); ch.listener = True
out = []
for n, text in (('screen1', 'show me the services page on desktop'), ('screen2', 'and on tablet?'),
                ('screen3', 'show me the booking page on every screen')):
    phone.step = n; t = time.time()
    r = assistant.handle(ch, repo, text, poll=1)
    out.append({'step': n, 'said': text, 'result': r, 'seconds': round(time.time() - t, 1),
                'hive': [m['text'][:300] + (f" [photo {os.path.basename(m['file'] or '')}]" if m['photo'] else '')
                         for m in phone.sent if m['step'] == n]})
    print(n, r, sum(m['photo'] for m in phone.sent if m['step'] == n), 'photo(s)', flush=True)
json.dump(out, open(os.path.join(f.OUT, 'screens_rerun.json'), 'w'), indent=1, ensure_ascii=False)
