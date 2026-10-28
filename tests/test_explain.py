"""The plain-words step and its backup model, with no network and no real key: Claude fails, a stand-in
OpenAI-compatible endpoint (like NVIDIA NIM) answers; with neither, the owner is never handed the raw list.
usage: python3 tests/test_explain.py   (run from the hive repo root)"""
import http.server, json, os, sys, tempfile, threading
sys.path.insert(0, os.getcwd())
from hive import explain

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))

seen = {}
class Endpoint(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        seen['auth'], seen['model'] = self.headers.get('Authorization'), body['model']
        seen['prompt'] = body['messages'][0]['content']
        reply = {'summary': 'A report that adds up daily shop orders.', 'items': [
            {'id': 'a1', 'context': 'The shop sees this on every report.', 'example': 'Asha has 3 orders.',
             'advice': "I'd keep it.", 'alternative': '', 'impact': 3, 'owner_can_judge': True}]}
        out = json.dumps({'choices': [{'message': {'content': 'Here you go: ' + json.dumps(reply)}}]}).encode()
        self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
        self.wfile.write(out)
    def log_message(self, *a):
        pass

srv = http.server.HTTPServer(('127.0.0.1', 0), Endpoint)
threading.Thread(target=srv.serve_forever, daemon=True).start()
home = tempfile.mkdtemp()
explain.CMD = 'false'   # Claude's login has expired
explain.BACKUP = os.path.join(home, 'llm.json')
assumptions = [{'id': 'a1', 'text': 'If the numerator is missing, the rate is null.'}]

d = tempfile.mkdtemp()
try:
    explain.plan(d, 'combine metrics', assumptions); raised = False
except RuntimeError:
    raised = True
check('with no model reachable, nothing is shown to the owner', raised, True)
check('and nothing is cached, so the next try can succeed', os.path.exists(os.path.join(d, 'explained.json')), False)

json.dump({'base_url': f'http://127.0.0.1:{srv.server_port}/v1', 'api_key': 'test-key', 'model': 'meta/llama-3.3-70b-instruct'},
          open(explain.BACKUP, 'w'))
summary, shown, aside = explain.plan(d, 'combine metrics', assumptions)
check('when Claude fails, the backup model puts it in plain words', (summary, shown[0]['text']),
      ('A report that adds up daily shop orders.', 'The shop sees this on every report. Asha has 3 orders.'))
check('the suggestion comes through', shown[0]['advice'], "I'd keep it.")
check('the key and model went to the endpoint', (seen['auth'], seen['model']), ('Bearer test-key', 'meta/llama-3.3-70b-instruct'))
check('the plain words are cached for this build', os.path.exists(os.path.join(d, 'explained.json')), True)

d2 = tempfile.mkdtemp()
explain.plan(d2, 'combine metrics', assumptions, rulings=['A late post is never paid less.'])
check("the owner's earlier rulings reach the model, to judge where he is likely to differ",
      ("earlier rulings" in seen['prompt'], 'A late post is never paid less.' in seen['prompt'], '"differs"' in seen['prompt']),
      (True, True, True))
srv.shutdown()
sys.exit(fail)
