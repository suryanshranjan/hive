"""Stand-in for the model call in hive/explain.py (no tokens): rewrites each assumption with context and an example,
ranks them by their position, and marks the last one as something an owner cannot judge."""
import json, re, sys
prompt = sys.stdin.read()
if 'Classify it.' in prompt:   # the listener: what kind of message is this?
    said = prompt.split('"')[1]
    low = said.lower()
    intent = ('change' if 'changed my mind' in low or low.startswith('actually') else 'status' if 'status' in low
              else 'greeting' if low.strip(' !.') in ('hi', 'hello', 'hey hive') else 'other')
    print(json.dumps({'result': json.dumps({'intent': intent, 'rule': said.split(':', 1)[-1].strip() if intent == 'change' else ''})}))
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
