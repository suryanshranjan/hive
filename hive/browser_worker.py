"""JSON-lines browser worker, launched only inside the dedicated browser container."""
import argparse
import ipaddress
import json
import socket
import sys
from urllib.parse import urlparse


def origin(url):
    parsed = urlparse(url)
    return f'{parsed.scheme}://{parsed.netloc}'


def allowed(url, local_origins=()):
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
        return False
    if origin(url) in local_origins:
        return True
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == 'https' else 80))
        return bool(addresses) and all(ipaddress.ip_address(item[4][0]).is_global for item in addresses)
    except (OSError, ValueError):
        return False


class Browser:
    def __init__(self, profile, local_origins=(), sandbox=True):
        from playwright.sync_api import sync_playwright
        self.local_origins = local_origins
        self.playwright = sync_playwright().start()
        try:
            self.context = self.playwright.chromium.launch_persistent_context(
                profile, headless=True, chromium_sandbox=sandbox, accept_downloads=False,
                service_workers='block', viewport={'width': 1280, 'height': 900})
        except Exception:
            self.playwright.stop()
            raise
        self.context.set_default_timeout(10000)
        self.context.route('**/*', lambda route: route.continue_() if allowed(route.request.url, self.local_origins)
                           else route.abort('blockedbyclient'))
        self.context.route_web_socket('**/*', lambda ws: ws.close())
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        self.page.on('dialog', lambda dialog: dialog.dismiss())
        self.context.on('page', self._new_page)

    def _new_page(self, page):
        # A click must not silently switch the controlled page or authorize popup work.
        if page != self.page:
            page.close()

    def snapshot(self):
        return {'url': self.page.url, 'title': self.page.title(),
                'text': self.page.locator('body').inner_text(timeout=5000)[:8000],
                'elements': self.page.locator('a,button,input,textarea,select').evaluate_all('''els => els.slice(0,80).map(e => ({
                    tag:e.tagName.toLowerCase(), id:e.id, name:e.name || '', type:e.type || '',
                    text:(e.innerText || e.getAttribute('aria-label') || e.getAttribute('placeholder') || '').slice(0,120),
                    href:e.tagName === 'A' ? e.getAttribute('href') : undefined
                }))''')}

    def execute(self, operation, args):
        if operation == 'open':
            if not allowed(args['url'], self.local_origins):
                raise ValueError('Only public HTTP(S) URLs or explicitly allowed local origins can be opened.')
            self.page.goto(args['url'], wait_until='domcontentloaded', timeout=20000)
        elif operation in ('click', 'fill', 'press'):
            if args['url'] != self.page.url:
                raise ValueError('The page changed after this action was proposed. Inspect it again.')
            target = self.page.locator(args['selector'])
            if target.count() != 1:
                raise ValueError('The selector must identify exactly one element.')
            if operation == 'click': target.click(timeout=15000)
            elif operation == 'fill': target.fill(args['text'])
            elif operation == 'press': target.press(args['key'])
            self.page.wait_for_timeout(150)
        elif operation != 'inspect':
            raise ValueError('Unsupported browser operation')
        return self.snapshot()

    def close(self):
        self.context.close()
        self.playwright.stop()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', default='/profile')
    parser.add_argument('--allow-local-origin', action='append', default=[])
    args = parser.parse_args()
    browser = Browser(args.profile, args.allow_local_origin)
    try:
        for line in sys.stdin:
            request = {}
            try:
                request = json.loads(line)
                result = {'id': request['id'], 'status': 'done',
                          'data': browser.execute(request['operation'], request.get('args', {}))}
            except Exception as exc:
                # Raw browser exceptions can include form fields and page content.
                result = {'id': request.get('id'), 'status': 'failed', 'error': type(exc).__name__}
            print(json.dumps(result, ensure_ascii=False), flush=True)
    finally:
        browser.close()


if __name__ == '__main__':
    main()
