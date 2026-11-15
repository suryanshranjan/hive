"""Fast replies with a model API key, any provider, with no network and no real key: a stand-in chat-completions
endpoint (OpenAI's shape) streams a reply; the owner's chat shows the first words early and the whole reply at the end,
edited in place, and Hive's record of the conversation keeps only the final words. Without a key nothing changes.
usage: python3 tests/test_fast.py   (run from the hive repo root)"""
import http.server, json, os, sys, tempfile, threading, time
sys.path.insert(0, os.getcwd())
home = tempfile.mkdtemp()
os.environ['HOME'] = os.environ['USERPROFILE'] = home
os.environ.pop('ANTHROPIC_API_KEY', None); os.environ.pop('HIVE_EXPLAIN_CMD', None); os.environ.pop('HIVE_API', None)
from hive import explain, assistant

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))

# 1. the part of a reply written so far
check('partial: not started', explain.partial_field('{"rep'), '')
check('partial: mid-word', explain.partial_field('{"reply": "Good morn'), 'Good morn')
check('partial: escapes', explain.partial_field('{"reply": "He said \\"yes\\" \\u20b9 5'), 'He said "yes" ₹ 5')
check('partial: an escape half written', explain.partial_field('{"reply": "Pay \\u20'), 'Pay ')
check('partial: finished', explain.partial_field('{"reply": "Done.", "x": 1}'), 'Done.')

# 2. no key: off, and every chain goes on as before
explain.FAST = os.path.join(home, 'fast.json')
check('no key: off', explain.fast_on(), False)
check('no key: _ask_api steps aside', explain._ask_api('x'), None)

REPLY = 'Good morning, sir. Nothing has changed since last night, and the build is still green.'
seen = {}
class Endpoint(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        seen.update(auth=self.headers.get('Authorization'), model=body['model'], stream=body.get('stream'))
        text = json.dumps({'reply': REPLY})
        if not body.get('stream'):
            out = json.dumps({'choices': [{'message': {'content': text}}]}).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
            self.wfile.write(out); return
        self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
        for k in range(0, len(text), 6):   # six characters at a time, slowly, like a model writing
            piece = {'choices': [{'delta': {'content': text[k:k + 6]}}]}
            self.wfile.write(b'data: ' + json.dumps(piece).encode() + b'\n\n'); self.wfile.flush()
            time.sleep(0.05)
        self.wfile.write(b'data: [DONE]\n\n')
    def log_message(self, *a):
        pass

srv = http.server.HTTPServer(('127.0.0.1', 0), Endpoint)
threading.Thread(target=srv.serve_forever, daemon=True).start()
json.dump({'provider': 'openai', 'api_key': 'sk-test', 'model': 'some-model',
           'base_url': f'http://127.0.0.1:{srv.server_port}/v1'}, open(explain.FAST, 'w'))

# 3. any provider: one plain question, and one streamed
check('key: on', explain.fast_on(), True)
check('ask: answered', explain._ask_api('hi'), {'reply': REPLY})
check('ask: the key and model were sent', (seen['auth'], seen['model'], seen['stream']), ('Bearer sk-test', 'some-model', False))
parts = []
got = explain.stream_json('hi', parts.append)
check('stream: whole reply', got, {'reply': REPLY})
check('stream: arrived in pieces', len(parts) > 5 and parts[-1] == REPLY and parts[0] != REPLY, True)

# 4. in the owner's chat: early words, edits, the final text, and a clean record
class Chat:
    def __init__(self):
        self.log, self.history, self.n = [], [], 0
    def send(self, text, html=False, **k):
        self.n += 1; self.log.append(('send', self.n, text, time.time())); self.history.append(('hive', text)); return self.n
    def edit(self, mid, text, html=False):
        self.log.append(('edit', mid, text, time.time())); self.history[-1] = ('hive', text); return True
    def typing(self):
        pass

assistant.STREAM_EVERY = 0.2
ch, t0 = Chat(), time.time()
assistant._speak_streamed(ch, 'hi', 'fallback line')
sends = [x for x in ch.log if x[0] == 'send']; edits = [x for x in ch.log if x[0] == 'edit']
check('chat: one message, not several', len(sends), 1)
check('chat: first words before the end', sends[0][2] != '🐝 ' + REPLY and sends[0][2].endswith('…'), True)
check('chat: edited as it was written', len(edits) >= 2, True)
check('chat: final text in place', edits[-1][2], '🐝 ' + REPLY)
check('chat: record keeps the final words only', ch.history, [('hive', '🐝 ' + REPLY)])
print(f'     (first words after {sends[0][3] - t0:.2f} s, whole reply after {edits[-1][3] - t0:.2f} s)')

# 5. a provider that fails: the plain line, never silence
json.dump({'provider': 'openai', 'api_key': 'sk-test', 'model': 'm', 'base_url': 'http://127.0.0.1:9/v1'},
          open(explain.FAST, 'w'))
explain._ask_claude = lambda p: None   # no Claude Code in this test
ch = Chat()
assistant._speak_streamed(ch, 'hi', 'fallback line')
check('down: the fallback line', [x[2] for x in ch.log], ['fallback line'])

# 6. an Anthropic key goes through Anthropic's SDK (a stand-in server speaks its streaming events)
class Messages(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        seen.update(key=self.headers.get('x-api-key') or (self.headers.get('Authorization') or '').replace('Bearer ', ''), model=body['model'], effort=body.get('output_config'),
                    stream=body.get('stream'))
        text = json.dumps({'reply': REPLY})
        msg = {'id': 'msg_1', 'type': 'message', 'role': 'assistant', 'model': body['model'], 'content': [],
               'stop_reason': None, 'stop_sequence': None, 'usage': {'input_tokens': 1000, 'output_tokens': 0}}
        if not body.get('stream'):
            msg.update(content=[{'type': 'text', 'text': text}], stop_reason='end_turn',
                       usage={'input_tokens': 1000, 'output_tokens': 40})
            out = json.dumps(msg).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
            self.wfile.write(out); return
        self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
        def ev(name, data):
            self.wfile.write(f'event: {name}\ndata: {json.dumps(data)}\n\n'.encode()); self.wfile.flush()
        ev('message_start', {'type': 'message_start', 'message': msg})
        ev('content_block_start', {'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'text', 'text': ''}})
        for k in range(0, len(text), 8):
            ev('content_block_delta', {'type': 'content_block_delta', 'index': 0,
                                       'delta': {'type': 'text_delta', 'text': text[k:k + 8]}})
            time.sleep(0.03)
        ev('content_block_stop', {'type': 'content_block_stop', 'index': 0})
        ev('message_delta', {'type': 'message_delta', 'delta': {'stop_reason': 'end_turn', 'stop_sequence': None},
                             'usage': {'output_tokens': 40}})
        ev('message_stop', {'type': 'message_stop'})
    def log_message(self, *a):
        pass

try:
    import anthropic  # noqa: F401
    asrv = http.server.HTTPServer(('127.0.0.1', 0), Messages)
    threading.Thread(target=asrv.serve_forever, daemon=True).start()
    os.environ['ANTHROPIC_BASE_URL'] = f'http://127.0.0.1:{asrv.server_port}'
    os.remove(explain.FAST); os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-test'
    explain.SPENT[0] = 0.0
    check('anthropic: on from the key alone', explain.fast_on(), True)
    check('anthropic: answered', explain._ask_api('hi'), {'reply': REPLY})
    check('anthropic: key, default model, low effort', (seen['key'], seen['model'], seen['effort']),
          ('sk-ant-test', 'claude-opus-5-5', {'effort': 'low'}))
    parts = []
    check('anthropic: streamed', explain.stream_json('hi', parts.append), {'reply': REPLY})
    check('anthropic: in pieces', len(parts) > 5 and parts[-1] == REPLY, True)
    check('anthropic: spend counted ($4 in, $20 out a million)', round(explain.SPENT[0], 4), round(2 * (1000 * 4 + 40 * 20) / 1e6, 4))
    os.environ.pop('ANTHROPIC_API_KEY')
except ImportError:
    print('skip anthropic: the SDK is not installed (pip install "hive-swarm[api]")')

# 7. a test or experiment that names its reader is never sent to the fast model
os.environ['HIVE_EXPLAIN_CMD'] = 'true'
check('named reader: off', explain.fast_on(), False)
sys.exit(fail)
