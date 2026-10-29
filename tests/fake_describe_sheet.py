"""Stand-in for the code-sheet describer that does write a sheet (no tokens): two rules, as plain words."""
import json, re, sys
prompt = sys.stdin.read()
out = re.search(r'Write (\S+): a JSON list', prompt).group(1)
json.dump(['Fees: the fee is 10 percent of the cash plus any bonus.', 'Payouts: the creator gets the cash plus the bonus.'],
          open(out, 'w'))
print('{"result": "2 rules"}')
