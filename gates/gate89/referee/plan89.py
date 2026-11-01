"""Gate 89: how many business decisions the interview's planner finds (hive.interview.decisions), 3 calls per goal:
the 10 Django issues' summaries (Gate 86; technical, should be 0) and business goals (should stay >= 5).
usage: python3 plan89.py <hive checkout> <out.json>"""
import json, os, sys
sys.path.insert(0, sys.argv[1])
from hive import interview
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'gates', 'gate86', 'referee')); sys.path.insert(0, os.path.join(ROOT, 'gates', 'gate85', 'referee'))
import swe86, run86
ids = json.load(open(os.path.join(ROOT, 'private', 'g86', 'valid.json')))
goals = {i: run86.goal_text(next(x for x in swe86.instances() if x['instance_id'] == i), False) for i in ids}
src = open(os.path.join(ROOT, 'gates', 'gate85', 'referee', 'flight85.py')).read()
goals['tiny_shop'] = eval('(' + src.split('GOAL = (')[1].split('OWNER =')[0].strip())
goals['invoices'] = ("Add late fees to invoices: `late_fee(invoice, days_late)` in `billing/fees.py`, returning the fee in whole "
                     "rupees, and `remind(invoice, days_late)` returning which reminder to send, if any.")
out = {g: [len(interview.decisions(t)) for _ in range(3)] for g, t in goals.items()}
json.dump(out, open(sys.argv[2], 'w'), indent=1); print(json.dumps(out))
