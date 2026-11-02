"""Stands in for the owner's-examples checker (hive/examples.py) in tests: writes the JSON its brief asks for.
FAKE_EXAMPLES_FAIL=<marker file>: report one failing example, once (the marker remembers it was reported)."""
import json, os, re, sys
brief = sys.stdin.read()
out = re.search(r'Write (\S+) as JSON', brief).group(1)
mark = os.environ.get('FAKE_EXAMPLES_FAIL')
failing = []
if mark and not os.path.exists(mark):
    open(mark, 'w').write('reported')
    failing = [{'rule': 'late fee', 'example': '31 days late: 2 rupees', 'got': '0 rupees', 'where': 'fees.late_fee'}]
json.dump({'checks': brief.count('\n') and 1, 'failing': failing}, open(out, 'w'))
print(json.dumps({'total_cost_usd': 0.01, 'result': 'ok'}))
