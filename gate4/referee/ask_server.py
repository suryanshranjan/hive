"""Product owner: answers one question at a time against the private intent (oracle.py).
usage: ask_server.py <port> <budget or -1 for unlimited> <log path>
A question is one SQL SELECT returning one row of at most 3 values; anything else is refused uncharged."""
import json, socketserver, sys, threading, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oracle
port, budget, logp = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
used = 0; lock = threading.Lock()
class H(socketserver.StreamRequestHandler):
    def handle(self):
        global used
        try:
            req = json.loads(self.rfile.readline().decode())
            sql, who = req.get('sql', ''), req.get('worker', '?')
        except Exception:
            self.wfile.write(b'{"error":"bad request"}\n'); return
        with lock:
            if budget >= 0 and used >= budget:
                resp = {'error': f'question budget exhausted ({budget} questions for the whole team)'}; charged = False
            else:
                try:
                    rows = oracle.connect().execute(sql).fetchall()
                    if len(rows) != 1 or len(rows[0]) > 3:
                        resp = {'error': 'a question must return exactly one row of at most 3 values'}; charged = False
                    else:
                        used += 1; charged = True
                        resp = {'answer': list(rows[0]), 'questions_left': None if budget < 0 else budget - used}
                except Exception as e:
                    resp = {'error': f'{type(e).__name__}: {e}'}; charged = False
            open(logp, 'a').write(json.dumps(dict(t=int(time.time()), worker=who, sql=sql, resp=resp, charged=charged)) + '\n')
        self.wfile.write((json.dumps(resp) + '\n').encode())
socketserver.ThreadingTCPServer.allow_reuse_address = True
socketserver.ThreadingTCPServer(('127.0.0.1', port), H).serve_forever()
