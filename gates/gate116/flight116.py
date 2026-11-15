"""Gate 116 (PREDICTIONS.md): does the picture still beat words when the picture is messy, as founders really send them?
Gate 105 (clean screenshots): picture 18/18 measured checks, words 13/18. Here each private target (a Kite Market page)
is given to Hive's fix round on Sunny Shop's invite page four ways:
  C  the clean phone screenshot          "Make the invite page look like this. [photo: clean.png]"
  F  a phone photo of it on a laptop     "... [photo: photo.jpg]"   (tilt, glare, blur, warm cast, noise, JPEG 45)
  S  a busy real-site screenshot         "... [photo: busy.png]"    (status bar, promo strip, 3 other buttons, cookie bar)
  W  his words                           "Make the invite page look like this: <a founder's description>"
Then the delivered page is measured by role (measure116.py) and scored against the private checks.
usage: python gates/gate116/flight116.py [t4 t5 t6]   (private inputs: private/g116/, made by make_targets.py)"""
import json, os, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
os.environ['HIVE_CONTRACT_CHECK'] = '0'   # no interfaces in this goal; the check would only spend
from hive import screens, start
import measure116 as M

PRIV = os.path.join(ROOT, 'private', 'g116')
OUT = os.path.join(HERE, 'results'); os.makedirs(OUT, exist_ok=True)
WORK = os.path.join(tempfile.gettempdir(), 'g116')
GOAL = ("Sunny Shop's invite page (index.html): a creator is invited to Sunny Shop, with the reward of Rs 500 each "
        "(shown as ₹500), the 'Copy invite link' button and the three steps.")
TEST = '''import pathlib, re
H = pathlib.Path(__file__).with_name('index.html').read_text(encoding='utf-8')
def test_heading(): assert 'Invite a creator' in H
def test_brand(): assert 'Sunny Shop' in H
def test_reward(): assert '₹500' in H
def test_button(): assert re.search(r'Copy invite link', H)
def test_steps(): assert H.count('<li') >= 3
'''
CMD = f'"{sys.executable}" -m pytest -q --junitxml=.hive/junit.xml'
DESCRIBE = ("You run a small online shop. Open the picture {p}: it is a page from another site that you like. Write the "
            "message you would type on your phone to your developer, asking them to make your own invite page look like "
            "it. Describe how it looks in your own plain words, 2 to 4 sentences. No colour codes, no pixel numbers, and "
            "don't mention that site's name or its wording. Reply with the message only.")
PICTURE = {'C': 'clean.png', 'F': 'photo.jpg', 'S': 'busy.png'}

def sh(*a, cwd=None):
    return subprocess.run(a, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')

def words_for(t):   # Gate 105's describer, on the clean picture: what he would type having seen the page itself
    path = os.path.join(PRIV, f'words_{t}.json')
    if not os.path.exists(path):
        r = sh(shutil.which('claude') or 'claude', '-p', DESCRIBE.format(p=os.path.join(PRIV, t, 'clean.png')),
               '--allowedTools', 'Read', '--output-format', 'json', cwd=os.path.join(PRIV, t))
        j = json.loads(r.stdout)
        json.dump({'words': j['result'].strip(), 'cost': float(j.get('total_cost_usd') or 0)}, open(path, 'w'), indent=1,
                  ensure_ascii=False)
    return json.load(open(path))['words']

def shop(home):
    """The starting build: the invite page with its tests, as a finished build's shared branch."""
    repo = os.path.join(home, 'shop'); os.makedirs(os.path.join(repo, '.hive')); os.makedirs(os.path.join(repo, 'current_tasks'))
    shutil.copy(os.path.join(PRIV, 'base', 'index.html'), repo)
    open(os.path.join(repo, 'test_page.py'), 'w', encoding='utf-8').write(TEST)
    json.dump({'test_cmd': CMD, 'snapshot_links': [], 'branch': 'main', 'junit': '.hive/junit.xml', 'areas': {}},
              open(os.path.join(repo, '.hive', 'config.json'), 'w'), indent=1)
    open(os.path.join(repo, 'current_tasks', '.keep'), 'w').close()
    open(os.path.join(repo, '.gitignore'), 'w').write('.hive/junit.xml\n__pycache__/\n.pytest_cache/\n')
    g = lambda *a: sh('git', '-C', repo, *a)
    g('init', '-q', '-b', 'main'); g('add', '.'); g('-c', 'user.name=owner', '-c', 'user.email=o@x', 'commit', '-qm', 'the invite page')
    final = os.path.join(home, 'build'); os.makedirs(final)
    sh('git', 'clone', '-q', '--bare', repo, os.path.join(final, 'up.git'))
    return repo, final

def cell(t, arm):
    name = f'{t}{arm}'; home = os.path.join(WORK, name)
    if os.path.exists(os.path.join(OUT, name + '.json')):
        print(name, 'done already'); return
    rule = (f"Make the invite page look like this. [photo: {os.path.join(PRIV, t, PICTURE[arm])}]" if arm in PICTURE
            else 'Make the invite page look like this: ' + words_for(t))
    if os.path.exists(home):
        start._rmtree(home)
    os.makedirs(home)
    repo, final = shop(home)
    state = dict(repo=repo, branch='main', name=f'g116-{name}', home=home, test_cmd=CMD, links=[], goal=GOAL,
                 technical=True, minutes=15, before=start.run_tests(repo, CMD), started=time.time(), b='main', final=final,
                 check='', code=0, cost=0.0, spent0=0.0)
    t0 = time.time()
    rc = start.apply_ruling(state, rule)
    mins = (time.time() - t0) / 60
    result = os.path.join(home, 'result')
    shot = os.path.join(OUT, name + '.png')
    try:
        got = screens.take(result, ['/'], os.path.join(home, 'shots'))   # the product's own camera
        shutil.copy(got[0][1], shot)
    except Exception as e:
        print('screens.take failed:', e); M.measure(result, shot=shot)
    m = M.measure(result)
    checks = json.load(open(os.path.join(PRIV, t, 'checks.json')))
    sc = M.score(m, checks)
    after = start.run_tests(result, CMD)
    json.dump({'cell': name, 'target': t, 'arm': arm, 'rc': rc, 'minutes': round(mins, 1), 'cost': round(state['cost'], 3),
               'matched': sum(1 for x in sc if x[1]), 'of': len(sc), 'score': sc,
               'tests': f'{sum(after.values())}/{len(after)}', 'kept_words': all(w in m.get('text', '') for w in
               ('Invite a creator', 'Sunny Shop', '₹500', 'Copy invite link')),
               'other_brand': 'Kite Market' in m.get('text', '') or '₹250' in m.get('text', ''),
               'measured': {k: v for k, v in m.items() if k != 'text'}, 'rule': rule.replace(PRIV, 'private/g116')},
              open(os.path.join(OUT, name + '.json'), 'w'), indent=1, ensure_ascii=False)
    print(f'{name}: {sum(1 for x in sc if x[1])}/{len(sc)}  rc {rc}, {mins:.1f} min, ${state["cost"]:.2f}', flush=True)

if __name__ == '__main__':
    targets = sys.argv[1:] or ['t4', 't5', 't6']
    os.makedirs(WORK, exist_ok=True)
    for t in targets:
        print(t, 'words:', words_for(t), flush=True)
    for t in targets:
        for arm in ('C', 'F', 'S', 'W'):
            cell(t, arm)
