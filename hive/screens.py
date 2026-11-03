"""Screenshots of what was built, for the owner's phone (the owner: "if Hive created a frontend, it shares the screenshot
on my phone; I say what's off, or send a reference: make it like this"). A founder judges a screen by looking at it.

Hive starts the product the way its project says (`serve_cmd` in .hive/config.json, else `npm run dev`/`npm start` from
package.json, else a plain file server for a folder with index.html), opens it in a headless browser (Playwright,
optional: pip install playwright && playwright install chromium), and photographs each page at phone size."""
import json, os, re, socket, subprocess, sys, tempfile, time, urllib.request

PHONE = {'width': 390, 'height': 844}   # how he will see it, on his phone

class Unavailable(RuntimeError):
    """Screenshots cannot be taken on this machine (no browser, or the product would not start)."""

def available():
    try:
        import playwright.sync_api  # noqa: F401
        return True
    except ImportError:
        return False

def is_frontend(repo):
    """A project with something to look at: a web page, or a package with a dev server."""
    if os.path.exists(os.path.join(repo, 'index.html')) or glob_any(repo, ('public/index.html', 'src/index.html', 'app/page.tsx',
                                                                            'pages/index.tsx', 'pages/index.js', 'src/App.tsx', 'src/App.jsx')):
        return True
    scripts = _scripts(repo)
    return bool(scripts.get('dev') or scripts.get('start'))

LOOK = re.compile(r"\b(design|style|styling|look|looks|colou?rs?|fonts?|typography|layout|spacing|theme|dark mode|"
                  r"ui|header|button|redo|restyle|redesign|make it like|like this|prettier|nicer)\b|\[photo: |his picture:")
LOGIC = re.compile(r"\b(refunds?|pay(ment|out)?s?|charge|discounts?|points|orders?|checkout|calculate|logic|api|database|"
                   r"emails?|login|signup|sign up|stock|tax|invoice|rules?)\b")

def is_look_job(goal, repo):
    """A job about how his product looks, not how it works ("redo this page in their style", a picture he sent): no
    business decisions to ask him about, one builder, and the screenshots are the review (the owner: "for a UI change
    Jarvis shouldn't give me situations; tell me about the page simply")."""
    g = (goal or '').lower()
    return is_frontend(repo) and bool(LOOK.search(g)) and not LOGIC.search(re.sub(r'\(his picture:[^)]*\)', '', g))

LOOK_NOTE = ("\n\n# How to work on the look\n\nThis job is about how the page looks; keep what it says and does. If he names "
             "another website, fetch it (curl its HTML and its CSS files) and take its look: colours, fonts, spacing, "
             "shapes of cards and buttons, layout. Never take its logo, name, wording or images: the page stays his. "
             "Check your work by its appearance at phone width.\n")

def glob_any(repo, rels):
    return any(os.path.exists(os.path.join(repo, r)) for r in rels)

def _scripts(repo):
    try:
        return json.load(open(os.path.join(repo, 'package.json'))).get('scripts') or {}
    except (OSError, ValueError):
        return {}

def _port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
    return port

def _command(repo):
    """(command, url or None): how this project serves its pages. The url is found in the output when None."""
    try:
        cfg = json.load(open(os.path.join(repo, '.hive', 'config.json')))
    except (OSError, ValueError):
        cfg = {}
    if cfg.get('serve_cmd'):
        return cfg['serve_cmd'], cfg.get('serve_url')
    scripts = _scripts(repo)
    for name in ('dev', 'start'):
        if scripts.get(name):
            port = _port()   # a fixed free port, passed the ways common servers accept it
            return f'npm run {name} -- --port {port}', f'http://127.0.0.1:{port}'
    root = repo if os.path.exists(os.path.join(repo, 'index.html')) else next(
        (os.path.join(repo, d) for d in ('public', 'src', 'dist', 'build') if os.path.exists(os.path.join(repo, d, 'index.html'))), None)
    if root:
        port = _port()
        return f'"{sys.executable}" -m http.server {port} --bind 127.0.0.1 --directory "{root}"', f'http://127.0.0.1:{port}'
    raise Unavailable("I couldn't tell how to start your product to look at it. Tell me once with "
                      "`serve_cmd` in .hive/config.json (for example \"npm run dev\").")

def _wait(url, proc, seconds=90):
    t0 = time.time()
    while time.time() - t0 < seconds:
        if proc.poll() is not None:
            raise Unavailable('your product stopped as it started, so there is nothing to look at yet')
        try:
            urllib.request.urlopen(url, timeout=3); return True
        except Exception:
            time.sleep(1)
    raise Unavailable(f'your product did not answer at {url} within {seconds} seconds')

def _stop(proc):
    try:
        if os.name == 'nt':
            subprocess.run(['taskkill', '/F', '/T', '/PID', str(proc.pid)], capture_output=True)
        else:
            os.killpg(proc.pid, 15)
    except Exception:
        proc.kill()

def take(code_dir, pages=('/',), out_dir=None, size=PHONE):
    """Photograph these pages of the product in code_dir at phone size. Returns [(page, png path)]. Raises Unavailable
    with a plain reason when it cannot (no browser here, or the product would not start)."""
    if not available():
        raise Unavailable("I can't take screenshots on this machine yet (run: pip install playwright, then playwright "
                          "install chromium).")
    cmd, url = _command(code_dir)
    out_dir = out_dir or tempfile.mkdtemp(prefix='hive_screens_')
    os.makedirs(out_dir, exist_ok=True)
    log = open(os.path.join(out_dir, 'server.log'), 'w')
    proc = subprocess.Popen(cmd, shell=True, cwd=code_dir, stdout=log, stderr=subprocess.STDOUT,
                            start_new_session=os.name != 'nt')
    try:
        if not url:   # read the address the server printed
            for _ in range(90):
                m = re.search(r'https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0):\d+', open(log.name, errors='replace').read())
                if m:
                    url = m.group(0).replace('0.0.0.0', '127.0.0.1'); break
                time.sleep(1)
            if not url:
                raise Unavailable("your product started but didn't say where to find it")
        _wait(url, proc)
        from playwright.sync_api import sync_playwright
        shots = []
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch()
            except Exception as e:   # Playwright without its browser (found in Gate 105: a clean home has none)
                if "doesn't exist" in str(e) or 'Executable' in str(e):
                    raise Unavailable("I can't take screenshots on this machine yet: the browser isn't installed "
                                      "(run: playwright install chromium).") from None
                raise
            page = browser.new_page(viewport=size, device_scale_factor=2)
            for k, path in enumerate(pages, 1):
                page.goto(url.rstrip('/') + '/' + path.lstrip('/'), wait_until='networkidle', timeout=30000)
                png = os.path.join(out_dir, f'{k:02d}_{re.sub(r"[^a-z0-9]+", "_", path.lower()).strip("_") or "home"}.png')
                page.screenshot(path=png, full_page=True)
                shots.append((path, png))
            browser.close()
        return shots
    finally:
        _stop(proc); log.close()

def pages_of(goal, repo):
    """The pages worth showing: the paths the goal names ("/pricing"), else the home page."""
    found = re.findall(r'(?<![\w/])(/[a-z0-9][a-z0-9/_-]*)', goal or '')
    found = [f for f in dict.fromkeys(found) if not f.startswith(('/home/', '/tmp/', '/usr/'))][:4]
    return found or ['/']
