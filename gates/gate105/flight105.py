"""Gate 105: does a builder given the owner's picture match it better than one given his words?

For each private target (a page from another mock brand, rendered at phone size as the picture he would send):
  - W: a separate model looks at the picture and writes what a founder would type instead (plain words, no hex codes,
       no pixel numbers); the builder gets "Make the invite page look like this: <his words>".
  - P: the builder gets "Make the invite page look like this. [photo: <the picture>]", which Hive carries into the
       code (hive/refs.py) exactly as from Telegram.
Both through Hive's own fix round on a finished build (hive/start.py apply_ruling: one builder, every test re-checked).
Then the delivered page is measured by role (measure105.py) and shot at phone size (hive/screens.py).

Runs in the lab container, clean home: HOME=/home/node/fh python3 gates/gate105/flight105.py [t1 t2 t3]
Private inputs: private/g105/<t>/ref.png and checks.json (kept out of the repo until scored)."""
import json, os, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['HIVE_CONTRACT_CHECK'] = '0'   # no interfaces in this goal; the check would only spend
from hive import screens, start
import measure105 as M

PRIV = os.path.join(ROOT, 'private', 'g105')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
WORK = os.path.join(os.path.expanduser('~'), 'g105')
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
CMD = 'python3 -m pytest -q --junitxml=.hive/junit.xml'
DESCRIBE = ("You run a small online shop. Open the picture {p}: it is a page from another site that you like. Write the "
            "message you would type on your phone to your developer, asking them to make your own invite page look like "
            "it. Describe how it looks in your own plain words, 2 to 4 sentences. No colour codes, no pixel numbers, and "
            "don't mention that site's name or its wording. Reply with the message only.")

def sh(*a, cwd=None):
    return subprocess.run(a, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')

def claude(prompt, cwd):
    r = sh('claude', '-p', prompt, '--allowedTools', 'Read', '--output-format', 'json', cwd=cwd)
    j = json.loads(r.stdout)
    return j['result'].strip(), float(j.get('total_cost_usd') or 0)

def words_for(t):
    path = os.path.join(PRIV, f'words_{t}.json')
    if not os.path.exists(path):
        text, cost = claude(DESCRIBE.format(p=os.path.join(PRIV, t, 'ref.png')), os.path.join(PRIV, t))
        json.dump({'words': text, 'cost': cost}, open(path, 'w'), indent=1, ensure_ascii=False)
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
    rule = ('Make the invite page look like this. [photo: ' + os.path.join(PRIV, t, 'ref.png') + ']' if arm == 'P'
            else 'Make the invite page look like this: ' + words_for(t))
    result = os.path.join(home, 'result')
    done = os.path.join(home, 'state.json')
    if os.path.exists(done) and os.path.isdir(result) and os.path.exists(os.path.join(home, 'minutes')):
        state = json.load(open(done)); rc = None; mins = float(open(os.path.join(home, 'minutes')).read())
        print(name, 'fix round done already: measuring it')   # (the camera failed once after a finished round)
    else:
        if os.path.exists(home):
            start._rmtree(home)
        os.makedirs(home)
        repo, final = shop(home)
        before = start.run_tests(repo, CMD)
        state = dict(repo=repo, branch='main', name=f'g105-{name}', home=home, test_cmd=CMD, links=[], goal=GOAL,
                     technical=True, minutes=15, before=before, started=time.time(), b='main', final=final, check='',
                     code=0, cost=0.0, spent0=0.0)
        t0 = time.time()
        rc = start.apply_ruling(state, rule)
        mins = (time.time() - t0) / 60
        open(os.path.join(home, 'minutes'), 'w').write(str(mins))
    os.makedirs(OUT, exist_ok=True)
    shot = os.path.join(OUT, name + '.png')
    try:
        got = screens.take(result, ['/'], os.path.join(home, 'shots'))   # the product's own camera
        shutil.copy(got[0][1], shot)
    except Exception as e:
        print('screens.take failed:', e); M.measure(result, shot=shot)
    m = M.measure(result)
    after = start.run_tests(result, CMD)
    json.dump({'cell': name, 'target': t, 'arm': arm, 'rc': rc, 'minutes': round(mins, 1), 'cost': round(state['cost'], 3),
               'check': state['check'], 'tests': f'{sum(after.values())}/{len(after)}', 'measured': m,
               'rule': rule.replace(PRIV, 'private/g105')}, open(os.path.join(OUT, name + '.json'), 'w'), indent=1, ensure_ascii=False)
    print(f'{name}: rc {rc}, {mins:.1f} min, ${state["cost"]:.2f}, {state["check"]}', flush=True)

if __name__ == '__main__':
    targets = sys.argv[1:] or ['t1', 't2', 't3']
    os.makedirs(WORK, exist_ok=True)
    for t in targets:
        print(t, 'words:', words_for(t), flush=True)
    for t in targets:
        for arm in ('P', 'W'):
            cell(t, arm)
