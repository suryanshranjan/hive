"""Stand-in for the model call in hive/explain.py (no tokens): rewrites each assumption with context and an example,
ranks them by their position, and marks the last one as something an owner cannot judge."""
import json, re, sys
prompt = sys.stdin.read()
ids = [i for i in re.findall(r'"id": "([^"]+)"', prompt) if i != '...']
items = [{'id': i, 'context': f'In the brand report (item {k}).', 'example': f'For example, Priya with 1,000 followers.',
          'question': 'Is that what you want?', 'impact': 3 if k == 0 else 1, 'owner_can_judge': k < len(ids) - 1}
         for k, i in enumerate(ids)]
print(json.dumps({'result': json.dumps({'summary': 'A report that adds up campaign results.', 'items': items})}))
