"""Gate 105: measure how a page looks, by role, at phone size (390x844): the header's colour, the heading's size and
colour, the amount's colour, the card's corners, the button's colour, width and shape, the page colour behind the
heading. Works on any page with those roles (the starting page, a reference from another brand, a builder's result).
The expected values for each target are private until the gate is scored; this file only measures.
usage: python3 measure105.py <folder with index.html> [heading regex] [amount regex] [button regex] [brand regex]"""
import json, math, os, socket, subprocess, sys, time

JS = r"""([hd, amt, btn, brand]) => {
  const clear = c => c === 'rgba(0, 0, 0, 0)' || c === 'transparent';
  const bg = el => { while (el) { const c = getComputedStyle(el).backgroundColor; if (!clear(c)) return c; el = el.parentElement; }
                     return 'rgb(255, 255, 255)'; };
  const find = re => { re = new RegExp(re, 'i'); let hit = null;
    for (const el of document.body.querySelectorAll('*')) {
      if (!re.test(el.textContent) || ['SCRIPT', 'STYLE'].includes(el.tagName)) continue;
      if ([...el.children].some(k => re.test(k.textContent))) continue;   // the deepest element holding it
      const r = el.getBoundingClientRect(); if (r.width && r.height) { hit = el; break; } }
    return hit; };
  const out = {};
  const h1 = find(hd), a = find(amt), b = find(btn), top = document.querySelector('header') || find(brand);
  if (top) out.header_bg = bg(top);
  if (h1) { const s = getComputedStyle(h1); out.h1_size = parseFloat(s.fontSize); out.h1_color = s.color; out.page_bg = bg(h1); }
  if (a) { out.reward_color = getComputedStyle(a).color;
    let c = a.parentElement;   // the card: the first box around the amount that is drawn (a colour, a border or a shadow)
    while (c && c !== document.body) { const s = getComputedStyle(c);
      if (!clear(s.backgroundColor) || s.boxShadow !== 'none' || parseFloat(s.borderTopWidth) > 0) break; c = c.parentElement; }
    out.card_radius = c && c !== document.body ? parseFloat(getComputedStyle(c).borderTopLeftRadius) : 0; }
  if (b) { let el = b; while (el.parentElement && el.parentElement.textContent.trim() === el.textContent.trim()) el = el.parentElement;
    const s = getComputedStyle(el), r = el.getBoundingClientRect();
    out.button_bg = bg(el); out.button_width = r.width / document.documentElement.clientWidth;
    out.button_radius = parseFloat(s.borderTopLeftRadius); out.button_height = r.height; }
  out.text = document.body.innerText;
  return out; }"""

def _port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p

def measure(folder, roles=('Invite a creator', '₹\\s?500', 'invite link', 'Sunny Shop'), shot=None):
    from playwright.sync_api import sync_playwright
    port = _port()
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=folder,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(0.8)
        with sync_playwright() as p:
            b = p.chromium.launch(); pg = b.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=2)
            pg.goto(f'http://127.0.0.1:{port}/', wait_until='networkidle')
            out = pg.evaluate(JS, list(roles))
            if shot:
                pg.screenshot(path=shot, full_page=True)
            b.close()
        return out
    finally:
        srv.kill(); srv.wait()

def rgb(c):
    if c.startswith('#'):
        return tuple(int(c[k:k + 2], 16) for k in (1, 3, 5))
    return tuple(float(x) for x in c[c.index('(') + 1:c.index(')')].split(',')[:3])

def dist(a, b):
    return math.dist(rgb(a), rgb(b))

COLOUR, SIZE = 45, 3   # a colour within 45 (RGB distance), a size within 3 px

def score(m, checks):
    """[(check, matched, measured)] for one page against one target's checks."""
    out = []
    for name, want in checks:
        if name.endswith('_bg') or name.endswith('_color'):
            got = m.get(name); ok = got is not None and dist(got, want) <= COLOUR
            got = f'{got} (distance {dist(got, want):.0f})' if got else None
        elif name == 'h1_size':
            got = m.get('h1_size'); ok = got is not None and abs(got - want) <= SIZE
        elif name == 'card_radius_max':
            got = m.get('card_radius'); ok = got is not None and got <= want
        elif name == 'card_radius_min':
            got = m.get('card_radius'); ok = got is not None and got >= want
        elif name == 'button_full':
            got = m.get('button_width'); ok = got is not None and got >= 0.7
        elif name == 'button_pill':
            got = m.get('button_radius'); ok = got is not None and got >= m.get('button_height', 99) / 2 - 1
        else:
            raise ValueError(name)
        out.append((name, bool(ok), got))
    return out

if __name__ == '__main__':
    print(json.dumps(measure(sys.argv[1], tuple(sys.argv[2:6]) if len(sys.argv) > 5 else
                             ('Invite a creator', '₹\\s?500', 'invite link', 'Sunny Shop')), indent=1, ensure_ascii=False))
