#!/usr/bin/env python3
"""Build a new intent experiment from a private oracle: starting repo, visible examples, hidden suite.

usage: new_intent_gate.py --name g8 --oracle private/g8/oracle.py [--visible-seed 8100] [--hidden-seed 8200000]

Writes:
  runs/<name>/seed/          the starting repo: the finished SQL engine, claim/land tools, the oracle's one-line spec
                             in README, 2 visible example tests per function (typical calls only)
  runs/<name>/example.txt    two typical calls, for the {EXAMPLE} placeholder in ask texts
  private/<name>/hidden/     the hidden suite (25 tests per function, 70% edge calls). Never commit it.
The oracle must follow the Gate 5/6 contract (see lab/intent.py). Keep it under private/ until the run is scored."""
import argparse, glob, json, os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lab'))
import intent

def sh(*args, cwd=None):
    r = subprocess.run(list(args), cwd=cwd, capture_output=True, text=True)
    if r.returncode: sys.exit(f'failed: {" ".join(args)}\n{r.stderr}')
    return r.stdout

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', required=True); ap.add_argument('--oracle', required=True)
    ap.add_argument('--visible-seed', type=int, default=8100); ap.add_argument('--hidden-seed', type=int, default=8200000)
    a = ap.parse_args()
    o = intent.load_oracle(a.oracle); g = intent.Gen(o)
    run = os.path.join(ROOT, 'runs', a.name); seed = os.path.join(run, 'seed'); os.makedirs(run, exist_ok=True)
    # SQL-engine test categories (the 1,340 tests that must keep passing), read from the Gate 3 scale seed
    tmp = tempfile.mkdtemp(); sh('git', 'clone', '-q', os.path.join(ROOT, 'gates', 'gate3', 'seed_scale.bundle'), tmp)
    sql_cats = {json.load(open(f))['category'] for f in glob.glob(os.path.join(tmp, 'tests', 'visible', '*.json'))}
    shutil.rmtree(tmp)
    # base: the finished engine with tools and README (Gate 6 seed); drop that gate's business functions
    shutil.rmtree(seed, ignore_errors=True); sh('git', 'clone', '-q', os.path.join(ROOT, 'gates', 'gate6', 'seed.bundle'), seed)
    sh('git', 'remote', 'remove', 'origin', cwd=seed)
    if sh('git', 'log', '-1', '--format=%s', cwd=seed).startswith('Business functions project'):
        sh('git', 'reset', '-q', '--soft', 'HEAD~1', cwd=seed)
    for f in glob.glob(os.path.join(seed, 'tests', 'visible', '*.json')):
        if json.load(open(f))['category'] not in sql_cats: os.remove(f)
    intent.cmd_tests(a.oracle, 'visible', os.path.join(seed, 'tests', 'visible'), a.visible_seed)
    intent.cmd_tests(a.oracle, 'hidden', os.path.join(ROOT, 'private', a.name, 'hidden'), a.hidden_seed)
    rows = []
    for name in g.CATS:
        sig, desc = o.SPEC[name].split(':', 1); desc = desc.strip()
        if name == g.AGG and 'aggregate' not in desc.lower(): desc = desc.rstrip('.') + ' (an aggregate).'
        rows.append(f'| `{sig.strip()}` | {desc} |')
    rp = os.path.join(seed, 'README.md'); s = open(rp).read()
    i, j = s.index('| Function | Spec from the product team |'), s.index('`tools/ask.py` tells you')
    s = s[:i] + '| Function | Spec from the product team |\n| --- | --- |\n' + '\n'.join(rows) + '\n\n' + s[j:]
    s = s.replace('20 business functions', f'{len(g.CATS)} business functions')
    open(rp, 'w').write(s)
    sh('git', 'add', '-A', cwd=seed)
    sh('git', '-c', 'user.name=hive', '-c', 'user.email=hive@local', 'commit', '-q', '-m',
       f'Business functions project ({a.name}): {len(g.CATS)} functions spec and example tests', cwd=seed)
    f0 = sorted(o.SCALARS)[0]; t = o.TYPICAL[f0]
    open(os.path.join(run, 'example.txt'), 'w').write(f'SELECT {g.call(f0, t[0])}, {g.call(f0, t[1])}')
    print('seed:', seed); print('example:', open(os.path.join(run, 'example.txt')).read())
    print('hidden suite:', os.path.join(ROOT, 'private', a.name, 'hidden'), '(never commit)')

if __name__ == '__main__':
    main()
