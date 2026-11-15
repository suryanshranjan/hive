"""Gate 120 referee: the plan reader (hive/router.py) against the one-intent reader (assistant.CLASSIFY), on Gate 59's
independent 130-message exam (first step = intent), and on chains.jsonl (the whole plan).
  python gates/gate120/run120.py exam     both readers on the exam, same model, same run
  python gates/gate120/run120.py chains   the plan reader on the chains
Writes gates/gate120/results_<part>.json. The model is the one Hive uses (explain.ask_json), as in Gate 59."""
import json, os, statistics, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from hive import assistant, explain, router

def recent(history):
    return '\n'.join(f"{'Owner' if w == 'owner' else 'Hive'}: {t}" for w, t in history) or '(nothing yet)'

class Chat:
    def __init__(self, history):
        self.h = history
    def recent(self, n=10):
        return recent(self.h[-n:])

def timed(fn):
    s0, t0 = explain.SPENT[0], time.time()
    out = fn()
    return out, time.time() - t0, explain.SPENT[0] - s0

def exam():
    items = [json.loads(l) for l in open(os.path.join(ROOT, 'gates', 'gate59', 'exam.jsonl'), encoding='utf-8')]
    rows = []
    for it in items:
        a, ta, ca = timed(lambda: assistant.read(Chat(it['history']), it['text']))
        b, tb, cb = timed(lambda: router.plan(recent(it['history']), it['text']))
        first = b['steps'][0]['tool'] if b['steps'] else 'none'
        rows.append({'id': it['id'], 'lang': it.get('lang'), 'want': it['intent'], 'one': a.get('intent'),
                     'plan': first, 'plan_steps': len(b['steps']), 'sec_one': round(ta, 2), 'sec_plan': round(tb, 2),
                     'usd_one': round(ca, 5), 'usd_plan': round(cb, 5)})
        print(it['id'], it['intent'], a.get('intent'), first, flush=True)
    n = len(rows)
    out = {'n': n, 'one': sum(r['one'] == r['want'] for r in rows), 'plan': sum(r['plan'] == r['want'] for r in rows),
           'plan_multi': sum(r['plan_steps'] > 1 for r in rows),
           'median_sec': {'one': statistics.median(r['sec_one'] for r in rows), 'plan': statistics.median(r['sec_plan'] for r in rows)},
           'usd': {'one': round(sum(r['usd_one'] for r in rows), 3), 'plan': round(sum(r['usd_plan'] for r in rows), 3)},
           'rows': rows}
    for lang in ('en', 'hi', 'mix'):
        sub = [r for r in rows if r['lang'] == lang]
        out[f'{lang}'] = {'n': len(sub), 'one': sum(r['one'] == r['want'] for r in sub), 'plan': sum(r['plan'] == r['want'] for r in sub)}
    return out

def chains():
    items = [json.loads(l) for l in open(os.path.join(ROOT, 'gates', 'gate120', 'chains.jsonl'), encoding='utf-8')]
    rows = []
    for it in items:
        b, tb, cb = timed(lambda: router.plan(recent(it['history']), it['text']))
        got = [s['tool'] for s in b['steps']]
        ok = got == it['steps'] or got in (it.get('alt') or [])
        ref_ok = None
        if it.get('ref'):
            step, arg = it['ref']
            later = [s for s in b['steps'][1:] if arg in s['args']]
            ref_ok = any(f'${step}' in json.dumps(s['args'][arg]) for s in later)
        rows.append({'id': it['id'], 'want': it['steps'], 'got': got, 'ok': ok, 'ref_ok': ref_ok, 'args': [s['args'] for s in b['steps']],
                     'sec': round(tb, 2), 'usd': round(cb, 5)})
        print(it['id'], ok, got, flush=True)
    ch = [r for r in rows if r['id'].startswith('c')]; co = [r for r in rows if r['id'].startswith('k')]
    refs = [r['ref_ok'] for r in rows if r['ref_ok'] is not None]
    return {'chains_ok': sum(r['ok'] for r in ch), 'chains': len(ch), 'controls_ok': sum(r['ok'] for r in co),
            'controls': len(co), 'refs_ok': sum(refs), 'refs': len(refs), 'rows': rows}

if __name__ == '__main__':
    part = (sys.argv[1:] or ['exam'])[0]
    got = exam() if part == 'exam' else chains()
    json.dump(got, open(os.path.join(ROOT, 'gates', 'gate120', f'results_{part}.json'), 'w', encoding='utf-8'), indent=1,
              ensure_ascii=False)
    print(json.dumps({k: v for k, v in got.items() if k != 'rows'}, indent=1))
