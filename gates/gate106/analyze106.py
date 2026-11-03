"""Gate 106: score the flights.
- Found: a blind judge reads the plan (titles, why, what was seen) and the private list of what holds this goal back,
  and says which of the 3 the plan addresses.
- Built: the private checks (private/g106/checks.py) on the delivered product: which of the 3 are removed.
- His effort: the owner's messages (the goal, taps, answers). His questions: a judge says, for each, whether only the
  owner could answer it (else the product or common sense could have).
- Plain words: technical words in what Hive sent him.
usage (lab): python3 gates/gate106/analyze106.py"""
import glob, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
PRIV = os.path.join(ROOT, 'private', 'g106'); OUT = os.path.join(HERE, 'results')
sys.path.insert(0, PRIV)
import checks

TECH = re.compile(r"\b(html|css|javascript|js|json|api|endpoint|database|branch|commit|merge|repo|function|component|"
                  r"div|class|selector|regex|deploy|backend|frontend|pytest|unit test|\w+\.(html|py|css|js))\b", re.I)

def ask(prompt):
    r = subprocess.run(['claude', '-p', prompt, '--output-format', 'json'], capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=300)
    t = json.loads(r.stdout)['result']
    return json.loads(t[t.index('{'):t.rindex('}') + 1])

def main():
    B = json.load(open(os.path.join(PRIV, 'blockers.json')))
    rows = {}
    for f in sorted(glob.glob(os.path.join(OUT, 'g[123][AB].json'))):
        r = json.load(open(f)); g = r['cell'][:2]
        steps = (r.get('plan') or {}).get('steps') or []
        listing = '\n'.join(f"{k}. {s['title']}: {s['why']} (seen: {s.get('seen', '')})" for k, s in enumerate(steps, 1))
        found = ask("A product plan, and three problems that hold back a business goal. For each problem, does the plan "
                    "address it (a step that would remove or clearly reduce it)? Judge only by what the plan says.\n\n"
                    f"Goal: {B[g]['goal']}\n\nPlan:\n{listing or '(no plan)'}\n\nProblems:\n" +
                    ''.join(f'{k}. {b}\n' for k, b in enumerate(B[g]['blockers'], 1)) +
                    '\nReply with JSON only: {"addressed": [true|false, true|false, true|false]}')['addressed'] if steps else [False] * 3
        prod = os.path.join(OUT, r['cell'] + '_product')
        built = checks.check(g, prod) if os.path.isdir(prod) else [False] * 3
        owner_only = []
        for q in r.get('questions', []):
            owner_only.append(bool(ask("A shop owner's assistant, which can read the shop's product code and pages, asked "
                                       f"the owner this:\n{q['question']}\nOptions: {q['options']}\n\nCould only the owner "
                                       "answer it (a business decision: an amount, a promise, what can wait), or could the "
                                       "product, its pages or common sense have settled it? Reply with JSON only: "
                                       '{"owner_only": true|false}')['owner_only']))
        to_him = [m['text'] for m in r['hive_messages'] if not m['photo']]
        tech = sorted({w.group(0).lower() for t in to_him for w in TECH.finditer(t)})
        rows[r['cell']] = {'found': found, 'built': built, 'owner_messages': len(r['owner_messages']),
                           'questions': len(r.get('questions', [])), 'owner_only': owner_only, 'tech_words': tech,
                           'photos': sum(1 for m in r['hive_messages'] if m['photo']), 'tests': r['tests'], 'ran': r['ran'],
                           'minutes': r['minutes'], 'cost': round(r['plan_cost'] + r['builders_cost'], 2),
                           'steps': [s['title'] for s in steps]}
        x = rows[r['cell']]
        print(f"{r['cell']}: found {sum(found)}/3 {found}, built {sum(built)}/3 {built}, owner msgs {x['owner_messages']}, "
              f"questions {x['questions']} owner-only {sum(owner_only)}, tech {tech}, photos {x['photos']}, tests {x['tests']}, "
              f"{x['ran']}, {x['minutes']} min, ${x['cost']}\n   steps: {x['steps']}")
    json.dump(rows, open(os.path.join(OUT, 'summary.json'), 'w'), indent=1, ensure_ascii=False)

if __name__ == '__main__':
    main()
