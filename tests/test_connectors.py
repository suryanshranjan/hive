"""Real official MCP client against a loopback Streamable HTTP fixture server."""
import copy
import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

sys.path.insert(0, os.getcwd())
from hive import connectors, tools


class ConnectorTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.schema = {'type': 'object', 'properties': {'q': {'type': 'string'}}, 'required': ['q']}
        self.error = False
        case = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def respond(self, code, result=None):
                body = json.dumps(result).encode() if result else b''
                self.send_response(code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers(); self.wfile.write(body)
            def do_GET(self): self.respond(405)
            def do_DELETE(self): self.respond(200)
            def do_POST(self):
                request = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                case.calls.append((request, self.headers.get('Authorization')))
                if 'id' not in request:
                    self.respond(202); return
                method = request['method']
                if method == 'initialize':
                    result = {'protocolVersion': request['params']['protocolVersion'], 'capabilities': {'tools': {}},
                              'serverInfo': {'name': 'fixture', 'version': '1'}}
                elif method == 'tools/list':
                    second = request.get('params', {}).get('cursor') == 'page-two'
                    result = {'tools': [{'name': 'record' if second else 'lookup', 'description': 'Fixture tool',
                                          'inputSchema': case.schema, 'annotations': {'readOnlyHint': True}}]}
                    if not second: result['nextCursor'] = 'page-two'
                elif method == 'tools/call':
                    result = {'content': [{'type': 'text', 'text': 'found:' + request['params']['arguments']['q']}],
                              'isError': case.error}
                else:
                    raise AssertionError(method)
                self.respond(200, {'jsonrpc': '2.0', 'id': request['id'], 'result': result})
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close); self.addCleanup(self.server.shutdown)
        self.entry = {'url': f'http://127.0.0.1:{self.server.server_port}/mcp', 'token_env': 'HIVE_FIXTURE_MCP_TOKEN',
                      'read_tools': ['lookup']}
        token = patch.dict(os.environ, {'HIVE_FIXTURE_MCP_TOKEN': 'fixture-only'})
        token.start(); self.addCleanup(token.stop)

    def discover(self):
        self.entry['tools'] = connectors.request(self.entry, 'discover')
        return self.entry['tools']

    def test_discovery_pagination_auth_and_real_call(self):
        self.assertEqual([t['name'] for t in self.discover()], ['lookup', 'record'])
        result = connectors.request(self.entry, 'call', 'lookup', {'q': 'invoice'})
        self.assertEqual(result['content'][0]['text'], 'found:invoice')
        self.assertTrue(all(auth == 'Bearer fixture-only' for _, auth in self.calls))
        self.assertEqual(sum(req['method'] == 'tools/call' for req, _ in self.calls), 1)

    def test_server_read_hint_cannot_authorize_writes(self):
        self.discover()
        with patch.object(connectors, 'config', return_value={'fixture': self.entry}):
            catalog = {t.name: t for t in connectors.catalog('.')}
            self.assertEqual(catalog['mcp.fixture.lookup'].risk, tools.READ)
            self.assertEqual(catalog['mcp.fixture.record'].risk, tools.EXTERNAL)
            self.assertEqual(catalog['mcp.fixture.lookup'].call({'q': 'x'})['status'], 'done')
            self.error = True
            self.assertEqual(catalog['mcp.fixture.record'].call({'q': 'x'})['status'], 'unknown')

    def test_schema_drift_is_rejected_before_call(self):
        self.discover()
        self.schema = dict(copy.deepcopy(self.schema), required=['q', 'recipient'])
        with self.assertRaises(Exception): connectors.request(self.entry, 'call', 'record', {'q': 'x'})
        self.assertFalse(any(req['method'] == 'tools/call' for req, _ in self.calls))

    def test_reconfigured_endpoint_invalidates_existing_tool(self):
        self.discover()
        config = {'fixture': self.entry}
        with patch.object(connectors, 'config', side_effect=lambda: config):
            tool = connectors.catalog('.')[0]
            config['fixture']['token_env'] = ''
            with self.assertRaises(tools.Refused): tool.call({'q': 'x'})

    def test_endpoint_validation(self):
        for url in ('http://example.com/mcp', 'file:///etc/passwd', 'https://user:secret@example.com/mcp'):
            with self.assertRaises(ValueError): connectors._url(url)


if __name__ == '__main__':
    unittest.main()
