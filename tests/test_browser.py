"""Real Chromium fixture test. Run inside hive-browser:1 with --network none.

The only allowed private origin is this test's in-container loopback web server.
"""
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.getcwd())
from hive.browser_worker import Browser, allowed


class BrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_GET(self):
                if self.path.startswith('/save'):
                    cls.saved += 1
                    body = b'<html><title>Saved</title><body>Saved once.</body></html>'
                elif self.path.startswith('/login'):
                    body = b'<form>Private login screen<input type="password"></form>'
                else:
                    body = b'''<html><title>Fixture</title><body><h1>Local form</h1>
                    <form action="/save"><input id="name" name="name"><input id="secret" type="hidden" value="hidden-secret">
                    <button id="save">Save</button></form><button class="many">A</button><button class="many">B</button>
                    <script>document.cookie = 'fixture=persisted; max-age=3600; path=/';</script></body></html>'''
                self.send_response(200); self.send_header('Content-Type', 'text/html')
                self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
        cls.saved = 0
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.origin = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.browser = Browser(self.temp.name, [self.origin])
        self.addCleanup(lambda: self.browser.close())

    def test_real_form_and_private_values_masked(self):
        result = self.browser.execute('open', {'url': self.origin})
        self.assertEqual(result['title'], 'Fixture')
        self.assertNotIn('hidden-secret', json.dumps(result))
        url = result['url']
        result = self.browser.execute('fill', {'url': url, 'selector': '#name', 'text': 'Fixture Person'})
        self.assertNotIn('Fixture Person', json.dumps(result))
        self.assertEqual(self.browser.page.locator('#name').input_value(), 'Fixture Person')
        before = self.saved
        result = self.browser.execute('click', {'url': url, 'selector': '#save'})
        self.assertEqual(result['title'], 'Saved')
        self.assertEqual(self.saved, before + 1)

    def test_page_mismatch_ambiguous_selector_and_private_urls_refused(self):
        result = self.browser.execute('open', {'url': self.origin})
        with self.assertRaises(ValueError): self.browser.execute('click', {'url': 'https://example.invalid/', 'selector': '#save'})
        with self.assertRaises(ValueError): self.browser.execute('click', {'url': result['url'], 'selector': '.many'})
        for url in ('file:///etc/passwd', 'http://169.254.169.254/latest/meta-data', 'http://127.0.0.1:1/'):
            self.assertFalse(allowed(url))
            with self.assertRaises(ValueError): self.browser.execute('open', {'url': url})
        self.assertFalse(allowed('http://user:password@127.0.0.1/'))

    def test_login_screen_is_held_for_owner(self):
        result = self.browser.execute('open',{'url':self.origin+'/login'})
        self.assertTrue(result['takeover_required'])
        self.assertNotIn('Private login screen',json.dumps(result))
        with self.assertRaises(ValueError):
            self.browser.execute('fill',{'url':self.origin+'/login','selector':'input','text':'fixture'})

    def test_profile_persists_cookies_across_browser_restart(self):
        self.browser.execute('open', {'url': self.origin})
        self.browser.close()
        self.browser = Browser(self.temp.name, [self.origin])
        cookies = self.browser.context.cookies(self.origin)
        self.assertTrue(any(c['name'] == 'fixture' and c['value'] == 'persisted' for c in cookies))


if __name__ == '__main__':
    unittest.main()
