"""Product owner with a fixed allowance of questions per function (Gate 6, randomized-allowance team).
usage: ask_server_quota.py <port> <allowance.json> <log path>
A question is one SELECT about exactly one of the business functions, returning one row of at most 3 values.
It is refused, uncharged, if it names no business function or several, or if that function's allowance is used up.
A request {"allowance": true} returns every function's allowance and how much of it has been used."""
import json, os, re, socketserver, sys, threading, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oracle
port, allow, logp = int(sys.argv[1]), json.load(open(sys.argv[2])), sys.argv[3]
names = set(oracle.SCALARS) | {oracle.AGGREGATE[0]}
used = {f: 0 for f in names}; lock = threading.Lock()
class H(socketserver.StreamRequestHandler):
    def handle(self):
        try:
            req = json.loads(self.rfile.readline().decode())
        except Exception:
            self.wfile.write(b'{"error":"bad request"}\n'); return
        who = req.get('worker', '?')
        if req.get('allowance'):
            with lock:
                resp = {f: {'allowance': allow[f], 'used': used[f]} for f in sorted(names)}
            self.wfile.write((json.dumps(resp) + '\n').encode()); return
        sql = req.get('sql', ''); charged = False
        fs = {f for f in names if re.search(r'\b' + f + r'\s*\(', sql, re.I)}
        with lock:
            if len(fs) != 1:
                resp = {'error': 'a question must be about exactly one of the business functions'}
            else:
                f = fs.pop()
                if used[f] >= allow[f]:
                    resp = {'error': f'the allowance for {f} is used up ({allow[f]} questions)'}
                else:
                    try:
                        rows = oracle.connect().execute(sql).fetchall()
                        if len(rows) != 1 or len(rows[0]) > 3:
                            resp = {'error': 'a question must return exactly one row of at most 3 values'}
                        else:
                            used[f] += 1; charged = True
                            resp = {'answer': list(rows[0]), 'allowance_left_for_' + f: allow[f] - used[f]}
                    except Exception as e:
                        resp = {'error': f'{type(e).__name__}: {e}'}
            open(logp, 'a').write(json.dumps(dict(t=int(time.time()), worker=who, sql=sql, resp=resp, charged=charged)) + '\n')
        self.wfile.write((json.dumps(resp) + '\n').encode())
socketserver.ThreadingTCPServer.allow_reuse_address = True
socketserver.ThreadingTCPServer(('127.0.0.1', port), H).serve_forever()
