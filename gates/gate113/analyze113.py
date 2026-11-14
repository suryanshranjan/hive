"""Gate 113: score the flight against the private answer key (kept outside this repo).

usage: python3 gates/gate108/analyze113.py <answers.json> [results/transcript.json]
Prints each prediction's evidence; the human read of the transcript decides O1, O3 and O5 (printed for reading)."""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
key = json.load(open(sys.argv[1], encoding='utf-8'))
tr = json.load(open(sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'results', 'transcript.json'), encoding='utf-8'))
steps = {s['step']: s for s in tr['steps']}

def said(step):
    return '\n'.join(steps.get(step, {}).get('hive', []))

def numbers(text):
    """Every number in the text, commas and the rupee sign dropped ('Rs 4,85,800' and '₹485,800' -> 485800)."""
    return {int(n.replace(',', '')) for n in re.findall(r'\d[\d,]*', text) if n.replace(',', '').isdigit()}

def right(answer, text):
    if isinstance(answer, (int, float)):
        return int(answer) in numbers(text)
    name = re.match(r'(.+?) \((\d+)\)$', str(answer))
    return bool(name) and name.group(1).lower() in text.lower()

print('O1 onboarding:', steps.get('onboard', {}).get('result'), '| script left:', steps.get('onboard', {}).get('script_left'))
for line in steps.get('onboard', {}).get('hive', []):
    print('   ', line[:220].replace('\n', ' '))
ok = 0
print('\nO2 data answers:')
for k, q in enumerate(key['questions'], 1):
    text = said(f'q{k}')
    r = right(q['answer'], text)
    ok += r
    print(f"  q{k} {'RIGHT' if r else 'WRONG'} key={q['answer']!r} | {steps.get(f'q{k}', {}).get('result')} | {text[-260:].replace(chr(10), ' ')}")
print(f'  -> {ok} of {len(key["questions"])} right (R2 fires at >= 8; kill under 6)')
print('\nO3 hidden rule (key:', key['hidden']['answer'], ')')
print('  ', said('techs').replace('\n', ' ')[:900])
print('\nO4 screens:')
for s in ('screen1', 'screen2', 'screen3'):
    photos = [h for h in steps.get(s, {}).get('hive', []) if '[photo' in h]
    print(f'  {s}: {len(photos)} photo(s):', [p[:70].replace(chr(10), ' ') for p in photos])
print('\nO5 plan (planted:', key['planted_problems'], ')')
for st in (tr.get('summary', {}).get('plan') or []):
    print('  -', st.get('title'), '|', (st.get('why') or '')[:200])
print('\nO6:', tr.get('summary'))
