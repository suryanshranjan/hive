"""Gate 105: score the flights. Measured: each delivered page against its target's 6 private checks (measure105.score).
Judged: a blind model sees the reference and one page (the starting page, or a result), under neutral names, never the
arm, and scores 0-10 how closely the page's look matches the reference (ignoring the wording, which differs by brand).
usage (lab, after flight105.py): python3 gates/gate105/analyze105.py"""
import json, os, random, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import measure105 as M

PRIV = os.path.join(ROOT, 'private', 'g105'); OUT = os.path.join(HERE, 'results')
JUDGE = ("Open two pictures of phone screens: {a} is a reference design, {b} is a page. The wording and brand differ on "
         "purpose; ignore the words. Score 0 to 10 how closely the page's look matches the reference: colours (header, "
         "background, highlight, button), shapes (corners, button width and shape), type sizes and layout. 10 means it "
         "looks like the same design. Reply with JSON only: {{\"score\": <0-10>, \"why\": \"<one sentence>\"}}")

def judge(ref, page):
    d = tempfile.mkdtemp(); names = random.sample(['x7.png', 'k2.png'], 2)
    a, b = os.path.join(d, names[0]), os.path.join(d, names[1])
    shutil.copy(ref, a); shutil.copy(page, b)
    r = subprocess.run(['claude', '-p', JUDGE.format(a=a, b=b), '--allowedTools', 'Read', '--output-format', 'json'],
                       cwd=d, capture_output=True, text=True, encoding='utf-8', errors='replace')
    text = json.loads(r.stdout)['result']
    j = json.loads(text[text.index('{'):text.rindex('}') + 1])
    shutil.rmtree(d)
    return float(j['score']), j.get('why', '')

def main():
    checks = json.load(open(os.path.join(PRIV, 'checks.json')))
    base_shot = os.path.join(PRIV, 'base', 'shot.png')
    base = M.measure(os.path.join(PRIV, 'base'))
    rows, summary = [], {}
    for t in ('t1', 't2', 't3'):
        ref = os.path.join(PRIV, t, 'ref.png')
        b_meas = M.score(base, checks[t]); b_judge = judge(ref, base_shot)
        summary[t] = {'before': {'matched': sum(o for _, o, _ in b_meas), 'judge': b_judge[0]}}
        for arm in ('P', 'W'):
            f = os.path.join(OUT, f'{t}{arm}.json')
            if not os.path.exists(f):
                continue
            r = json.load(open(f)); m = r['measured']; s = M.score(m, checks[t])
            text = m.get('text', '')
            kept = all(w in text for w in ('Sunny Shop', 'Invite a creator', '₹500')) and checks['brands'][t] not in text
            jd = judge(ref, os.path.join(OUT, f'{t}{arm}.png'))
            summary[t][arm] = {'matched': sum(o for _, o, _ in s), 'judge': jd[0], 'why': jd[1], 'kept_his_words': kept,
                               'tests': r['tests'], 'cost': r['cost'], 'minutes': r['minutes'],
                               'checks': [[n, o, g] for n, o, g in s]}
            print(f"{t}{arm}: matched {summary[t][arm]['matched']}/6, judge {jd[0]}, kept his words {kept}, tests {r['tests']}, "
                  f"${r['cost']}, {r['minutes']} min")
        print(f"{t} before: matched {summary[t]['before']['matched']}/6, judge {b_judge[0]}")
    json.dump(summary, open(os.path.join(OUT, 'summary.json'), 'w'), indent=1, ensure_ascii=False)

if __name__ == '__main__':
    main()
