#!/usr/bin/env python3
"""Gate 72: the synthetic owner on call at a person's pace, answering one question at a time from a queue. A builder's
question is queued at once; ask_owner.py waits for its answer at most 90 s (a builder's command is cut off at 2 minutes:
Gate 71's swarm lost answers that way), then says it is queued, and the builder works on something else meanwhile.

usage: owner_server.py --port P --policy <pre.json with "R"> --log <file.jsonl> [--min-seconds S]
requests (one JSON line): {"question": q, "worker": w} -> {"id": i}; {"get": i} -> {"answer": a or null};
{"answers": true} -> every answered question so far, and the ones still waiting"""
import argparse, json, os, queue, socketserver, subprocess, threading, time

HERE = os.path.dirname(os.path.abspath(__file__)); CMD = ['claude', '-p', '--output-format', 'json']

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--port', type=int, required=True); ap.add_argument('--policy', required=True)
    ap.add_argument('--log', required=True); ap.add_argument('--min-seconds', type=float, default=0); a = ap.parse_args()
    R = json.load(open(a.policy))['R']
    brief = open(os.path.join(os.path.dirname(HERE), 'prompts', 'owner_qa.md')).read().replace('{POLICY}', '\n'.join(f'- {r}' for r in R))
    Q = queue.Queue(); asked, answers, lock = {}, {}, threading.Lock()
    def owner():   # one person: one question at a time, in the order asked
        while True:
            qid = Q.get(); q = asked[qid]; t0 = time.time()
            p = subprocess.run(CMD, input=brief.replace('{QUESTION}', q['question']), capture_output=True, text=True, timeout=300, cwd='/tmp')
            try:
                d = json.loads(p.stdout); ans, cost = (d.get('result') or '').strip(), float(d.get('total_cost_usd') or 0)
            except Exception:
                ans, cost = '', 0.0
            time.sleep(max(0.0, a.min_seconds - (time.time() - t0)))
            ans = ans or 'Use your judgement on that one.'
            with lock:
                answers[qid] = ans
                open(a.log, 'a').write(json.dumps(dict(t=int(t0), worker=q['worker'], question=q['question'], answer=ans, cost=cost,
                                                       waited=round(time.time() - q['t'], 1))) + '\n')
    threading.Thread(target=owner, daemon=True).start()
    class H(socketserver.StreamRequestHandler):
        def handle(self):
            try:
                req = json.loads(self.rfile.readline())
            except Exception:
                return
            with lock:
                if req.get('answers'):
                    done = '\n'.join(f"Q: {asked[i]['question']}\nA: {answers[i]}" for i in asked if i in answers)
                    wait = '\n'.join(f"Q: {asked[i]['question']}\n(he has not answered yet)" for i in asked if i not in answers)
                    out = {'answer': '\n'.join(x for x in (done, wait) if x) or 'No questions asked yet.'}
                elif 'get' in req:
                    out = {'answer': answers.get(req['get'])}
                else:
                    qid = f"{len(asked) + 1}"; asked[qid] = dict(question=str(req.get('question', ''))[:2000], worker=req.get('worker'), t=time.time())
                    Q.put(qid); out = {'id': qid}
            self.wfile.write((json.dumps(out) + '\n').encode())
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(('127.0.0.1', a.port), H) as s:
        s.serve_forever()

if __name__ == '__main__':
    main()
