"""Replay every first-parent commit of upstream main against the visible and hidden suites.
usage: evaluate.py <upstream.git> <hidden_dir> <out.json> [extra hidden dirs...]
Writes per-commit: hash, author, time, subject, visible pass, hidden pass (+ per-test results)."""
import json, os, subprocess, sys, tempfile

up, hidden, out = (os.path.abspath(x) for x in sys.argv[1:4])
extra = [os.path.abspath(x) for x in sys.argv[4:]]
here = os.path.dirname(os.path.abspath(__file__))
log = subprocess.run(['git', '-C', up, 'log', '--first-parent', '--reverse', '--format=%H|%an|%ct|%s', 'main'],
                     capture_output=True, text=True).stdout.strip().splitlines()
wt = tempfile.mkdtemp()
subprocess.run(['git', 'clone', '-q', up, wt], check=True)
rows = []
for line in log:
    h, an, ct, subj = line.split('|', 3)
    subprocess.run(['git', '-C', wt, 'checkout', '-q', '-f', h], check=True)
    rec = dict(hash=h, author=an, t=int(ct), subject=subj)
    for name, suite in [('visible', os.path.join(wt, 'tests/visible')), ('hidden', hidden)] + [(f'hidden{i+2}', d) for i, d in enumerate(extra)]:
        if not os.path.isdir(suite):
            continue
        jf = os.path.join(wt, f'.res_{name}.json')
        # run the repo's own runner at this commit, against the given suite, in a fresh process
        runner = os.path.join(wt, '_ref_runner.py')  # the referee's own runner, never the repo's copy
        open(runner, 'w').write(open(os.path.join(here, 'ref_runner.py')).read())
        subprocess.run([sys.executable, '-I', runner, suite, '--json', jf], cwd=wt, capture_output=True, timeout=900)
        os.remove(runner)
        try:
            res = json.load(open(jf))
        except Exception:
            res = {}
        rec[name] = sum(res.values()); rec[name + '_n'] = len(res); rec[name + '_res'] = res
    rows.append(rec)
    print(f"{an:10s} {subj[:60]:60s} vis {rec.get('visible')}/{rec.get('visible_n')} hid {rec.get('hidden')}/{rec.get('hidden_n')}", flush=True)
json.dump(rows, open(out, 'w'))
