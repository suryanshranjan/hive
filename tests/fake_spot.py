"""Stand-in for the spotter (no tokens): checks it works in a copy of the built code, then writes two spot checks."""
import json, os, re, sys
prompt = sys.stdin.read()
out = re.search(r'Write (\S+): a JSON list', prompt).group(1)
code = re.search(r'The folder (\S+) holds', prompt).group(1)
assert os.path.isdir(code) and 'hive_spots_' in code, code
parts = re.findall(r'^- (.+)$', prompt.split('The parts:')[1].split('Write ')[0], re.M)
json.dump([{'part': p, 'say': f'{p}: for Ravi, 10,000 rupees of cash and a 2,000 bonus come to 1,200.'} for p in parts],
          open(out, 'w'))
print('{"result": "%d spot checks"}' % len(parts))
