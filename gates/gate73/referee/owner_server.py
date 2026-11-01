#!/usr/bin/env python3
"""Gate 73: Gate 72's owner on call (queued, a person's pace, one question at a time), plus Hive's repeated-question rule
when --dedupe is given: a new question that asks the same decision as an earlier one (prompts/same_brief.md, one model
call) is not put to him; it gets the earlier one's answer. Duplicates are logged in <log>.dupes.

usage: owner_server.py --port P --policy <pre.json> --log <file.jsonl> [--min-seconds S] [--dedupe]
requests: {"question": q, "worker": w} -> {"id": i}; {"get": i} -> {"answer": a or null}; {"answers": true} -> all so far"""
import argparse, json, os, queue, socketserver, subprocess, threading, time

HERE = os.path.dirname(os.path.abspath(__file__)); CMD = ['claude', '-p', '--output-format', 'json']
P = os.path.join(os.path.dirname(HERE), 'prompts')

def model(prompt):
    p = subprocess.run(CMD, input=prompt, capture_output=True, text=True, timeout=300, cwd='/tmp')
    try:
        d = json.loads(p.stdout); return (d.get('result') or '').strip(), float(d.get('total_cost_usd') or 0)
    except Exception:
        return '', 0.0

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--port', type=int, required=True); ap.add_argument('--policy', required=True)
    ap.add_argument('--log', required=True); ap.add_argument('--min-seconds', type=float, default=0); ap.add_argument('--dedupe', action='store_true')
    a = ap.parse_args()
    R = json.load(open(a.policy))['R']
    brief = open(os.path.join(P, 'owner_qa.md')).read().replace('{POLICY}', '\n'.join(f'- {r}' for r in R))
    same_brief = open(os.path.join(P, 'same_brief.md')).read()
    Q = queue.Queue(); asked, answers, alias, lock, dlock = {}, {}, {}, threading.Lock(), threading.Lock()
    def owner():
        while True:
            qid = Q.get(); q = asked[qid]; t0 = time.time()
            ans, cost = model(brief.replace('{QUESTION}', q['question']))
            time.sleep(max(0.0, a.min_seconds - (time.time() - t0)))
            ans = ans or 'Use your judgement on that one.'
            with lock:
                answers[qid] = ans
                open(a.log, 'a').write(json.dumps(dict(t=int(t0), worker=q['worker'], question=q['question'], answer=ans, cost=cost,
                                                       waited=round(time.time() - q['t'], 1))) + '\n')
    threading.Thread(target=owner, daemon=True).start()
    def enqueue(question, worker):
        with dlock:   # one at a time, so questions asked together are compared with each other
            with lock:
                earlier = [i for i in asked if i not in alias]
            same = None
            if a.dedupe and earlier:
                txt, _ = model(same_brief.replace('{EARLIER}', '\n'.join(f'{n}. {asked[i]["question"]}' for n, i in enumerate(earlier, 1)))
                               .replace('{NEW}', question))
                try:
                    n = json.loads(txt[txt.index('{'):txt.rindex('}') + 1]).get('same')
                    same = earlier[n - 1] if isinstance(n, int) and 1 <= n <= len(earlier) else None
                except Exception:
                    same = None
            with lock:
                qid = str(len(asked) + 1); asked[qid] = dict(question=question[:2000], worker=worker, t=time.time())
                if same:
                    alias[qid] = same
                    open(a.log + '.dupes', 'a').write(json.dumps(dict(worker=worker, question=question, same_as=asked[same]['question'])) + '\n')
                else:
                    Q.put(qid)
            return qid
    class H(socketserver.StreamRequestHandler):
        def handle(self):
            try:
                req = json.loads(self.rfile.readline())
            except Exception:
                return
            if 'question' in req:
                out = {'id': enqueue(str(req.get('question', '')), req.get('worker'))}
            else:
                with lock:
                    if req.get('answers'):
                        own = [i for i in asked if i not in alias]
                        done = '\n'.join(f"Q: {asked[i]['question']}\nA: {answers[i]}" for i in own if i in answers)
                        wait = '\n'.join(f"Q: {asked[i]['question']}\n(he has not answered yet)" for i in own if i not in answers)
                        out = {'answer': '\n'.join(x for x in (done, wait) if x) or 'No questions asked yet.'}
                    else:
                        out = {'answer': answers.get(alias.get(req.get('get'), req.get('get')))}
            self.wfile.write((json.dumps(out) + '\n').encode())
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(('127.0.0.1', a.port), H) as s:
        s.serve_forever()

if __name__ == '__main__':
    main()
