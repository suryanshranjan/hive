#!/usr/bin/env python3
"""The product owner: answers workers' questions from a private oracle, with a budget or per-function allowances.

usage:
  ask_server.py --oracle private/g8/oracle.py --port 7401 --log runs/g8/asks_T30.log --budget 30
  ask_server.py --oracle ... --port 7402 --log ... --allowance runs/g8/allowance.json   # {function: n}
  ask_server.py --oracle ... --port 7403 --log ... --budget -1                          # unlimited

A question is one SELECT returning one row of at most 3 values. Refused questions are not charged.
With --allowance, a question must name exactly one business function. Every question is logged as JSON lines.
Clients send one JSON line: {"sql": ..., "worker": ...} or {"allowance": true}."""
import argparse, importlib.util, json, os, re, socketserver, sys, threading, time

ap = argparse.ArgumentParser()
ap.add_argument('--oracle', required=True); ap.add_argument('--port', type=int, required=True)
ap.add_argument('--log', required=True); ap.add_argument('--budget', type=int, default=-1)
ap.add_argument('--allowance')
a = ap.parse_args()
sys.path[:] = [p for p in sys.path if p not in ('', os.getcwd())]
spec = importlib.util.spec_from_file_location('hive_oracle', os.path.abspath(a.oracle))
oracle = importlib.util.module_from_spec(spec); spec.loader.exec_module(oracle)
names = set(oracle.SCALARS) | ({oracle.AGGREGATE[0]} if getattr(oracle, 'AGGREGATE', None) else set())
allow = json.load(open(a.allowance)) if a.allowance else None
used_total = 0; used = {f: 0 for f in names}; lock = threading.Lock()

class H(socketserver.StreamRequestHandler):
    def handle(self):
        global used_total
        try:
            req = json.loads(self.rfile.readline().decode())
        except Exception:
            self.wfile.write(b'{"error":"bad request"}\n'); return
        if req.get('allowance'):
            with lock:
                resp = ({f: {'allowance': allow[f], 'used': used[f]} for f in sorted(names)} if allow
                        else {'budget': a.budget, 'used': used_total})
            self.wfile.write((json.dumps(resp) + '\n').encode()); return
        sql, who, charged = req.get('sql', ''), req.get('worker', '?'), False
        fs = {f for f in names if re.search(r'\b' + f + r'\s*\(', sql, re.I)}
        with lock:
            if a.budget >= 0 and used_total >= a.budget:
                resp = {'error': f'question budget exhausted ({a.budget} questions for the whole team)'}
            elif allow is not None and len(fs) != 1:
                resp = {'error': 'a question must be about exactly one of the business functions'}
            elif allow is not None and used[next(iter(fs))] >= allow[next(iter(fs))]:
                f = next(iter(fs)); resp = {'error': f'the allowance for {f} is used up ({allow[f]} questions)'}
            else:
                try:
                    rows = oracle.connect().execute(sql).fetchall()
                    if len(rows) != 1 or len(rows[0]) > 3:
                        resp = {'error': 'a question must return exactly one row of at most 3 values'}
                    else:
                        used_total += 1; charged = True
                        for f in fs: used[f] += 1
                        resp = {'answer': list(rows[0])}
                        if a.budget >= 0: resp['questions_left'] = a.budget - used_total
                except Exception as e:
                    resp = {'error': f'{type(e).__name__}: {e}'}
            with open(a.log, 'a') as fh:
                fh.write(json.dumps(dict(t=int(time.time()), worker=who, sql=sql, resp=resp, charged=charged)) + '\n')
        self.wfile.write((json.dumps(resp) + '\n').encode())

socketserver.ThreadingTCPServer.allow_reuse_address = True
print(f'product owner on 127.0.0.1:{a.port} ({len(names)} functions)', flush=True)
socketserver.ThreadingTCPServer(('127.0.0.1', a.port), H).serve_forever()
