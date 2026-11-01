#!/usr/bin/env python3
"""One map of the lab and the product, made with graphify (`pip install graphifyy`; https://graphify.com).

It joins the two scopes of this repo:
- **the product's code** (hive/, lab/, tests/): graphify reads it from its syntax, on this computer, at no cost;
- **the research**: one node per gate (its result from BRAIN.md's evidence log), with edges, all read from the repo text
  (graphify's label EXTRACTED; nothing is guessed):
    gate -> gate          `builds_on`     a gate's RESULTS.md names an earlier gate
    gate -> code file     `shipped_in`    docs/research_to_product.md lists the file for that gate's finding
    code -> gate          `justified_by`  a line in the code cites the gate (the function around that line)

usage: python3 lab/graphify_lab.py [--out runs/lab_map]
then, for example (G=runs/lab_map/graphify-out/graph.json):
    graphify explain "Gate 74" --graph $G          what it found, what it built on, where it is in the code
    graphify explain "split_roles()" --graph $G    a function, and the gates behind it
    graphify path "Gate 66" "settle_duplicates()" --graph $G
    graphify affected "Gate 70" --relation justified_by --depth 1 --graph $G   the code that cites that gate
The map is rebuilt from the repo each time and never committed."""
import argparse, glob, json, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = re.compile(r'\bGates? (\d+)(?:\s*[-–]\s*(\d+))?')

def gates_in(text):
    out = set()
    for a, b in GATE.findall(text):
        a = int(a); b = int(b) if b else a
        if b - a <= 20:
            out.update(range(a, b + 1))
    return out

def tool():
    t = os.environ.get('HIVE_GRAPHIFY') or shutil.which('graphify')
    if not t:
        sys.exit('graphify is not installed: pip install graphifyy')
    return t

def evidence():
    """BRAIN.md's evidence log: gate number -> (what ran, result)."""
    rows = {}
    for line in open(os.path.join(ROOT, 'BRAIN.md')).read().splitlines():
        m = re.match(r'\| Gate (\d+)[a-z]? \| [^|]* \| ([^|]*) \| ([^|]*) \|', line)
        if m:
            rows.setdefault(int(m.group(1)), (m.group(2).strip(), m.group(3).strip()))
    return rows

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default=os.path.join(ROOT, 'runs', 'lab_map')); a = ap.parse_args()
    g = tool(); src = os.path.join(a.out, 'src')
    shutil.rmtree(a.out, ignore_errors=True)
    for d in ('hive', 'lab', 'tests'):
        shutil.copytree(os.path.join(ROOT, d), os.path.join(src, d), ignore=shutil.ignore_patterns('__pycache__'))
    subprocess.run([g, 'extract', src, '--code-only'], check=True, capture_output=True)
    gp = os.path.join(src, 'graphify-out', 'graph.json'); G = json.load(open(gp))
    nodes = {n['id']: n for n in G['nodes']}; links = G['links']
    ev = evidence(); added = {'gates': 0, 'builds_on': 0, 'shipped_in': 0, 'justified_by': 0}

    def gate(k):
        nid = f'gate_{k}'
        if nid not in nodes:
            ran, res = ev.get(k, ('', ''))
            res_path = f'gates/gate{k}/RESULTS.md'
            nodes[nid] = dict(id=nid, label=f'Gate {k}', norm_label=f'gate {k}', file_type='document', _origin='hive-lab',
                              source_file=res_path if os.path.exists(os.path.join(ROOT, res_path)) else 'BRAIN.md',
                              source_location='L1', what_ran=ran, result=res, community=None)
            if res:   # its result, as its own node: "Gate 74" must stay an exact name for explain and path
                fid = f'gate_{k}_result'
                nodes[fid] = dict(id=fid, label=f'Result of gate {k}: ' + (res[:160] + '…' if len(res) > 160 else res),
                                  norm_label=f'result of gate {k}', file_type='document', _origin='hive-lab',
                                  source_file='BRAIN.md', source_location='L1', community=None)
                links.append(dict(source=nid, target=fid, relation='found', confidence='EXTRACTED', confidence_score=1.0,
                                  weight=1.0, _origin='hive-lab', source_file='BRAIN.md', source_location='L1'))
            added['gates'] += 1
        return nid

    def link(s, t, rel, where, line):
        links.append(dict(source=s, target=t, relation=rel, confidence='EXTRACTED', confidence_score=1.0, weight=1.0,
                          _origin='hive-lab', source_file=where, source_location=f'L{line}'))
        added[rel] += 1

    for k in sorted(ev):
        gate(k)
    for p in sorted(glob.glob(os.path.join(ROOT, 'gates', 'gate*', 'RESULTS.md'))):
        k = int(re.search(r'gate(\d+)', p).group(1)); rel = os.path.relpath(p, ROOT)
        for j in sorted(gates_in(open(p).read()) - {k}):
            if j < k:
                link(gate(k), gate(j), 'builds_on', rel, 1)
    files = {n['source_file']: nid for nid, n in nodes.items() if n.get('source_file') and n.get('label') == os.path.basename(n['source_file'])}
    rtp = os.path.join(ROOT, 'docs', 'research_to_product.md')
    for i, line in enumerate(open(rtp).read().splitlines(), 1):
        cells = [c.strip() for c in line.split('|')]
        if len(cells) >= 6 and cells[2] and 'Gate' in cells[2]:
            for f in re.findall(r'`([\w./-]+\.(?:py|md|sh))', cells[4]):
                if f in files:
                    for k in gates_in(cells[2]):
                        link(gate(k), files[f], 'shipped_in', 'docs/research_to_product.md', i)
    import ast
    callables = {(n['source_file'], n['label']): nid for nid, n in nodes.items() if n.get('_callable') and n.get('source_file')}
    for f in sorted(set(n['source_file'] for n in nodes.values() if str(n.get('source_file', '')).endswith('.py'))):
        path = os.path.join(ROOT, f)
        if not os.path.exists(path) or f == 'lab/graphify_lab.py':
            continue
        body = open(path).read(); spans = []   # (start, end, name) of every function and class, innermost last
        for d in ast.walk(ast.parse(body)):
            if isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                spans.append((d.lineno, d.end_lineno, d.name + ('()' if not isinstance(d, ast.ClassDef) else '')))
        seen = set()
        for i, line in enumerate(body.splitlines(), 1):
            if 'Gate' not in line:
                continue
            inside = sorted((s0, nm) for s0, e0, nm in spans if s0 <= i <= e0)
            who = next((callables[(f, nm)] for _, nm in reversed(inside) if (f, nm) in callables), None) or files.get(f)
            for k in gates_in(line):
                if who and (who, k) not in seen:
                    seen.add((who, k)); link(who, gate(k), 'justified_by', f, i)
    G['nodes'] = list(nodes.values()); G['links'] = links
    json.dump(G, open(gp, 'w'))
    subprocess.run([g, 'cluster-only', src, '--no-label', '--no-viz'], check=True, capture_output=True)
    shutil.move(os.path.join(src, 'graphify-out'), os.path.join(a.out, 'graphify-out')); shutil.rmtree(src)
    print(f"{a.out}/graphify-out: {len(nodes)} nodes, {len(links)} edges; added {added}")
    print(f'try: graphify explain "Gate 74" --graph {a.out}/graphify-out/graph.json')

if __name__ == '__main__':
    main()
