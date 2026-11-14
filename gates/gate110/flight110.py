"""Gate 110: a real host from the phone (PREDICTIONS.md). Run on the owner's laptop, Vercel signed in, Vercel's tool
uninstalled first:   python gates/gate110/flight110.py <Dabba Days project with Gate 109's build branch>

"we're on Vercel" -> "send me a link" -> "put it live" (refused: not merged) -> his engineer merges -> "put it live", yes
-> "undo that", yes -> everything deleted. Whatever happens, the flight ends by deleting the test project and checking
that his own project was not touched."""
import json, os, shutil, stat, subprocess, sys, tempfile, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'tests'))
from hive import assistant, deploy, logins, memory, telegram
from test_telegram_fake import FakeTelegram, ME, tap

NAME = 'hive-test-dabba-days'
BUILD = 'on-plans-page-plans-1114-2144'
LINE = 'Try a week of lunches'
OUT = os.path.join(HERE, 'results'); os.makedirs(OUT, exist_ok=True)
log, t0 = {'steps': []}, time.time()

def note(step, **kw):
    kw.update(step=step, minute=round((time.time() - t0) / 60, 1))
    log['steps'].append(kw); print(json.dumps(kw, ensure_ascii=False)[:700], flush=True)
    json.dump(log, open(os.path.join(OUT, 'flight.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

def vercel(*args):
    exe = shutil.which('vercel')
    return subprocess.run([exe, *args], capture_output=True, text=True, encoding='utf-8', errors='replace') if exe else None

def projects():
    p = vercel('project', 'ls', '--format', 'json')
    try:
        return {x['name']: x.get('updatedAt') for x in json.loads(p.stdout).get('projects', [])}
    except Exception:
        return {}

def fetch(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'hive-flight'}), timeout=20) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, ''
    except Exception as e:
        return None, repr(e)[:200]

def wait_for(url, want, minutes=5):
    """The production address, until it shows (want=True) or stops showing (want=False) the trial line."""
    t, last = time.time(), (None, '')
    while time.time() - t < minutes * 60:
        last = fetch(url)
        if last[0] == 200 and (LINE in last[1]) == want:
            break
        time.sleep(10)
    return last

RAW = []   # what Vercel's tool printed, each time (attempt 1 could not tell why the preview link was the main address)
_real_run = deploy._run
def _logged_run(cmd, cwd, timeout=900):
    p = _real_run(cmd, cwd, timeout)
    RAW.append({'cmd': cmd, 'rc': p.returncode, 'stdout': (p.stdout or '')[-800:], 'stderr': (p.stderr or '')[-1500:]})
    return p
deploy._run = _logged_run

def say(fake_script, words):
    fake = FakeTelegram(fake_script)
    ch = telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake)
    r = assistant.handle(ch, repo, words, poll=1)
    return r, [m['text'] for m in fake.sent]

def git(*a):
    return subprocess.run(['git', '-C', repo, '-c', 'user.name=engineer', '-c', 'user.email=e@e', *a],
                          capture_output=True, text=True)

def main(src):
    global repo
    before = projects()   # empty when Vercel's tool is not installed yet: taken again after "we're on Vercel"
    work = tempfile.mkdtemp(prefix='hive110_')
    repo = os.path.join(work, NAME)
    subprocess.run(['git', 'clone', '-q', os.path.abspath(src), repo], check=True)
    git('branch', f'hive/{BUILD}', f'origin/hive/{BUILD}')
    assistant.RUNS = os.path.join(work, 'runs'); home = os.path.join(assistant.RUNS, BUILD); os.makedirs(home)
    json.dump({'repo': repo, 'name': BUILD, 'branch': 'main', 'goal': "Add a ₹500 trial-week line to the plans page",
               'check': '10 tests, all passing.', 'home': home,
               'test_cmd': f'"{sys.executable}" -m pytest -q --junitxml=.hive/junit.xml'},
              open(os.path.join(home, 'state.json'), 'w', encoding='utf-8'))
    note('setup', vercel_installed_before=bool(shutil.which('vercel')), projects_before=before)
    prod = f'https://{NAME}.vercel.app'
    plans = prod + '/plans.html'   # the trial line is on the plans page (attempt 1 looked at the home page)
    try:
        # 1. "we're on Vercel": the tool installed by Hive, the sign-in checked, connected
        r, told = say([], "we're on Vercel")
        before = before or projects()
        note('connect', result=r, told=told, installed_now=bool(shutil.which('vercel')), signed_in=logins.ok('vercel'),
             projects_before=before)
        # 2. "send me a link"
        # attempt 3: new on Vercel, Hive asks first (its first version goes live); he says yes
        t = time.time(); r, told = say([tap('fst|yes')], 'send me a link')
        link = next((w for w in told[-1].split() if '.vercel.app' in w), None)
        live_after_preview = fetch(plans)
        code, body = fetch(link) if link else (None, '')
        pcode, pbody = fetch(link.rstrip('/') + '/plans.html') if link else (None, '')
        note('preview', result=r, minutes=round((time.time() - t) / 60, 1), link=link, status=code,
             has_home_page='Dabba Days' in body, plans_status=pcode, link_shows_build=LINE in pbody,
             is_main_address=bool(link) and link.rstrip('/') == prod, project_made=NAME in projects(),
             named_code='code' in projects(), told=[x[:300] for x in told], asked_first=any("isn't on Vercel yet" in x for x in told),
             live_status=live_after_preview[0], live_shows_unmerged_build=LINE in live_after_preview[1], vercel_said=RAW[-3:])
        # 3. "put it live" before the merge
        r, told = say([], 'put it live')
        code0, body0 = fetch(plans)
        note('live_unmerged', result=r, told=told[-1][:300], prod_status=code0, prod_has_line=LINE in body0)
        # 4. his engineer merges (as a pull request would); "put it live", yes
        m = git('merge', '--no-ff', '-q', '-m', 'Merge the trial-week line', f'hive/{BUILD}')
        t = time.time(); r, told = say([tap('liv|yes')], 'put it live')
        asked = any('Put it live on' in x for x in told)
        code1, body1 = wait_for(plans, True)
        note('live', merge_rc=m.returncode, result=r, asked_first=asked, minutes=round((time.time() - t) / 60, 1),
             prod_status=code1, prod_has_line=LINE in body1, told=told[-1][:300], vercel_said=RAW[-1:])
        # 5. "undo that", yes
        t = time.time(); r, told = say([tap('und|yes')], 'undo that')
        code2, body2 = wait_for(plans, False)
        note('undo', result=r, minutes=round((time.time() - t) / 60, 1), prod_status=code2, prod_has_line=LINE in body2,
             told=told[-1][:300])
    finally:
        # 6. delete everything this flight made; check his own project is untouched
        rm = vercel('project', 'rm', NAME, '--confirm-name', NAME) if NAME in projects() else None
        after = projects()
        key = os.path.join(deploy.DIR, memory.project_key(repo) + '.json')
        if os.path.exists(key):
            os.remove(key)
        shutil.rmtree(work, onerror=lambda f, p, e: (os.chmod(p, stat.S_IWRITE), f(p)))   # git's read-only files
        note('delete', rm_rc=rm.returncode if rm else None, rm_said=(rm.stdout + rm.stderr)[-200:] if rm else '',
             test_project_left=NAME in after, projects_after=after,
             others_untouched=all(after.get(k) == v for k, v in before.items()),
             host_record_left=os.path.exists(key), work_left=os.path.exists(work),
             total_minutes=round((time.time() - t0) / 60, 1), vercel_said_all=RAW)

if __name__ == '__main__':
    main(sys.argv[1])
