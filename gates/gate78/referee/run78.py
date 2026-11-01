#!/usr/bin/env python3
"""Gate 78: does a map of the codebase (graphify) make Hive's builders cheaper or faster on a large real codebase?
The job: sqlglot 30.27.0 (85k lines, MIT) with 12 functions emptied (pick78.py, seed 78; seed78.py builds the repo).
Arms, each 4 builders through the product (hive.swarm.prepare + launch), no owner, 30 minutes:
  H   Hive as shipped
  HM  the same, plus one map built before launch and copied into every clone (hive/codemap.py)
usage: python3 gates/gate78/referee/run78.py <H|HM> <k> [--skip-prereg-check]
Scores: the hidden suite (the 61 test methods removed from the seed, run from sqlglot's own test files) at the end and at
every landing on main; builders' cost and tokens; tool calls per builder from their transcripts (reads, searches, graphify);
any sign of a builder reaching another copy of sqlglot."""
import argparse, glob, json, os, re, shutil, subprocess, sys, tempfile, time
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'lab'))
PRIV = os.path.join(ROOT, 'private', 'g78'); SEED = os.path.join(ROOT, 'runs', 'g78_seed')
FAST = ['--ignore=tests/test_parser.py', '--ignore=tests/test_executor.py', '--ignore=tests/test_optimizer.py']
GRAPHIFY = os.environ.get('HIVE_GRAPHIFY', '/home/claude/gvenv/bin/graphify')
WORKERS, MINUTES = 4, 30

def goal(functions):
    return ("This repository is sqlglot, a SQL parser, transpiler and optimizer in pure Python (about 85,000 lines). Twelve "
            "of its functions were emptied: each now only raises NotImplementedError. Rebuild each one so that sqlglot "
            "behaves exactly as it did before, for every dialect that uses it. The tests that covered them were removed, so "
            "work out what each must do from the code around it (its callers, the helpers next to it, the other dialects) "
            "and add your own tests. Do not install, download or look at any other copy of sqlglot: work only from this "
            "repository. The emptied functions:\n" + '\n'.join(f'- `{f}`' for f in functions))

def hidden_score(code_dir, hidden):
    """Run sqlglot's original fast suite against code_dir's package; return (hidden passed, other failures)."""
    t = tempfile.mkdtemp(prefix='g78score-')
    try:
        shutil.copytree(os.path.join(code_dir, 'sqlglot'), os.path.join(t, 'sqlglot'), ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(os.path.join(PRIV, 'orig', 'tests'), os.path.join(t, 'tests'), ignore=shutil.ignore_patterns('__pycache__', 'test_sqlglotc.py'))
        for f in ('pyproject.toml', 'setup.cfg'):
            if os.path.exists(os.path.join(PRIV, 'orig', f)): shutil.copy(os.path.join(PRIV, 'orig', f), t)
        j = os.path.join(t, 'junit.xml')
        subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', 'tests', *FAST, f'--junitxml={j}'],
                       cwd=t, capture_output=True, timeout=1800, env=dict(os.environ, PYTHONPATH=t))
        if not os.path.exists(j): return 0, -1
        ok, other = set(), 0
        for tc in ET.parse(j).iter('testcase'):
            tid = f"{tc.get('classname')}::{tc.get('name')}"; bad = tc.find('failure') is not None or tc.find('error') is not None
            if tid in hidden and not bad: ok.add(tid)
            if tid not in hidden and bad: other += 1
        return len(ok), other
    finally:
        shutil.rmtree(t, ignore_errors=True)

def transcripts(work):
    d = os.path.expanduser('~/.claude/projects/' + re.sub(r'[/.]', '-', work))
    return sorted(glob.glob(os.path.join(d, '*.jsonl')))

def tool_use(work):
    c = {'Read': 0, 'Grep': 0, 'Glob': 0, 'Bash': 0, 'Edit': 0, 'Write': 0, 'graphify': 0, 'search_bash': 0, 'outside': []}
    for p in transcripts(work):
        for line in open(p, errors='replace'):
            try: e = json.loads(line)
            except Exception: continue
            msg = e.get('message') or {}
            for b in (msg.get('content') or []) if isinstance(msg.get('content'), list) else []:
                if b.get('type') != 'tool_use': continue
                name = b.get('name'); inp = json.dumps(b.get('input') or {})
                if name in c: c[name] += 1
                if name == 'Bash':
                    cmd = (b.get('input') or {}).get('command', '')
                    if 'graphify' in cmd: c['graphify'] += 1
                    if re.search(r'\b(grep|rg|find|ls|cat|sed|head|tail)\b', cmd): c['search_bash'] += 1
                if re.search(r'pip (install|download)[^"]*sqlglot|site-packages/sqlglot|private/g78|scratchpad|g78_seed|sqlglot-30', inp):
                    c['outside'].append(inp[:200])
    return c

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('arm', choices=['H', 'HM']); ap.add_argument('k'); ap.add_argument('--skip-prereg-check', action='store_true')
    a = ap.parse_args()
    if not a.skip_prereg_check:
        import run_gate; run_gate.prereg_check('gates/gate78/prompts/PREDICTIONS.md')
    from hive import swarm
    os.environ['HIVE_GRAPHIFY'] = GRAPHIFY
    H = json.load(open(os.path.join(PRIV, 'hidden.json'))); hidden = set(H['hidden'])
    run = os.path.join(ROOT, 'runs', f'g78_{a.arm}{a.k}'); shutil.rmtree(run, ignore_errors=True)
    t0 = time.time()
    swarm.prepare(SEED, run, WORKERS, goal(H['functions']), MINUTES, None, 0, False, code_map=(a.arm == 'HM'))
    prep = time.time() - t0
    t1 = time.time(); swarm.launch(run); t2 = time.time()
    final = os.path.join(run, 'final'); subprocess.run(['git', 'clone', '-q', os.path.join(run, 'up.git'), final], check=True)
    hp, other = hidden_score(final, hidden)
    log = subprocess.run(['git', 'log', '--first-parent', '--format=%H %ct %s', 'main'], cwd=final, capture_output=True, text=True).stdout.split('\n')
    land = []
    for line in reversed([l for l in log if l.strip()][:-1]):   # every commit on main after the seed, oldest first
        h, ts, subj = line.split(' ', 2)
        if subj.startswith('Lock:'): continue
        wt = tempfile.mkdtemp(prefix='g78land-')
        subprocess.run(['git', 'worktree', 'add', '-q', '--detach', wt, h], cwd=final, capture_output=True)
        p, o = hidden_score(wt, hidden)
        subprocess.run(['git', 'worktree', 'remove', '--force', wt], cwd=final, capture_output=True)
        land.append(dict(commit=h[:8], minute=round((int(ts) - t1) / 60, 1), subject=subj[:100], hidden=p, other_fail=o))
        print(f"  landing {h[:8]} at {land[-1]['minute']} min: hidden {p}/{len(hidden)}", flush=True)
    rows = list(__import__('csv').DictReader(open(os.path.join(run, 'agents.csv'))))
    tools = {r['worker']: tool_use(os.path.join(run, 'work', r['worker'])) for r in rows}
    out = dict(arm=a.arm, k=a.k, workers=WORKERS, prep_seconds=round(prep, 1), wall_minutes=round((t2 - t1) / 60, 1),
               hidden_passed=hp, hidden_total=len(hidden), other_failures=other, landings=land,
               cost=round(sum(float(r['cost_usd'] or 0) for r in rows), 2), tokens=sum(int(r['tokens'] or 0) for r in rows),
               builders=rows, tools=tools, map=os.path.exists(os.path.join(run, 'map', 'graphify-out', 'GRAPH_REPORT.md')))
    json.dump(out, open(os.path.join(run, 'result.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ('landings', 'builders', 'tools')}, indent=1))

if __name__ == '__main__':
    main()
