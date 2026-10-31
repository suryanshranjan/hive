#!/usr/bin/env python3
"""Gate 68 (from Gate 66): the synthetic owner on call. Builders ask in plain words (ask_owner.py); a headless Claude, holding the owner's
policy as prose and the brief in prompts/owner_qa.md, types his answer. One question at a time; every exchange is logged.

usage: owner_server.py --port P --policy <pre.json with "R"> --log <file.jsonl>"""
import argparse, json, os, socketserver, subprocess, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
CMD = ['claude', '-p', '--output-format', 'json']
LOCK = threading.Lock()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--port', type=int, required=True); ap.add_argument('--policy', required=True)
    ap.add_argument('--log', required=True); a = ap.parse_args()
    R = json.load(open(a.policy))['R']
    brief = open(os.path.join(os.path.dirname(HERE), 'prompts', 'owner_qa.md')).read().replace('{POLICY}', '\n'.join(f'- {r}' for r in R))
    class H(socketserver.StreamRequestHandler):
        def handle(self):
            try:
                req = json.loads(self.rfile.readline())
                if req.get('answers'):   # every question answered so far, so builders do not ask twice (hive answers)
                    done = [json.loads(x) for x in open(a.log)] if os.path.exists(a.log) else []
                    self.wfile.write((json.dumps({'answer': '\n'.join(f"Q: {x['question']}\nA: {x['answer']}" for x in done)
                                                  or 'No questions answered yet.'}) + '\n').encode()); return
                q = str(req.get('question', ''))[:2000]
            except Exception:
                self.wfile.write(b'{"answer": "Sorry, I could not read that."}\n'); return
            with LOCK:   # one question at a time, as one person answers
                t0 = time.time()
                p = subprocess.run(CMD, input=brief.replace('{QUESTION}', q), capture_output=True, text=True, timeout=300, cwd='/tmp')
                try:
                    d = json.loads(p.stdout); ans, cost = (d.get('result') or '').strip(), float(d.get('total_cost_usd') or 0)
                except Exception:
                    ans, cost = '', 0.0
                ans = ans or 'Use your judgement on that one.'
                open(a.log, 'a').write(json.dumps(dict(t=int(t0), worker=req.get('worker'), question=q, answer=ans, cost=cost,
                                                       seconds=round(time.time() - t0, 1))) + '\n')
            self.wfile.write((json.dumps({'answer': ans}) + '\n').encode())
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(('127.0.0.1', a.port), H) as s:
        s.serve_forever()

if __name__ == '__main__':
    main()
