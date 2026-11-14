"""A test deploy on his own cloud machine (the owner: "a feature shipped can use the same instance: deploy it there, test
it as a static web page, then delete it as required, so it is just a test deploy").

When he says "send me a link" and no hosting service is set up, Hive can put the build's pages on the AWS machine it
uses for the cloud (made for the purpose if there is none), at a secret address, for at most two hours. "Take it down"
(or the two hours) stops it, and a machine made only for the test is deleted, so nothing keeps billing. His live
product is never touched. Static pages for now: an index.html at the top, or in public/, dist/, build/ or out/.

The machine's port 8080 is opened to the internet while the test runs (a phone's address cannot be known in
advance), so the address carries a random secret and the server stops by itself after two hours."""
import json, os, re, secrets, shutil, subprocess, tempfile, time

from . import cloud, cloud_aws

PORT = 8080
HOURS = 2
STATE = lambda: os.path.join(os.path.expanduser('~'), '.hive', 'trydeploy.json')
TAKE_DOWN = re.compile(r"\b(take (it|that|the (test|preview|link|page)) (down|off)|take down (the )?(test|preview|link|page)|"
                       r"(i'?m|i am) done (with it|testing|checking)|done testing|remove the (test|preview)|"
                       r"delete the (test|preview)( machine)?|stop the (test|preview))\b")

def state():
    try:
        return json.load(open(STATE()))
    except (OSError, ValueError):
        return {}

def _save(st):
    os.makedirs(os.path.dirname(STATE()), exist_ok=True)
    json.dump(st, open(STATE(), 'w'), indent=1)

def static_root(code):
    """Where his pages are in the build: '' (the top), 'public', 'dist', 'build' or 'out'; None if no index.html."""
    for sub in ('', 'public', 'dist', 'build', 'out', 'site'):
        if os.path.exists(os.path.join(code, sub, 'index.html')):
            return sub
    return None

def _machine():
    try:
        return json.load(open(cloud_aws.STATE()))
    except (OSError, ValueError):
        return None

def _open_port(m):
    try:
        cloud_aws._aws(['ec2', 'authorize-security-group-ingress', '--group-id', m['group'], '--protocol', 'tcp',
                        '--port', str(PORT), '--cidr', '0.0.0.0/0'], m.get('profile'), m.get('region'))
    except RuntimeError as e:
        if 'Duplicate' not in str(e) and 'already exists' not in str(e):
            raise

def _close_port(m):
    try:
        cloud_aws._aws(['ec2', 'revoke-security-group-ingress', '--group-id', m['group'], '--protocol', 'tcp',
                        '--port', str(PORT), '--cidr', '0.0.0.0/0'], m.get('profile'), m.get('region'))
    except Exception:
        pass

def _export(repo, branch):
    """The build's files (no history), as a tar file. Returns (tar path, folder with the files)."""
    work = tempfile.mkdtemp(prefix='hive_try_')
    tar = os.path.join(work, 'site.tar')
    p = subprocess.run(['git', '-C', repo, 'archive', '--format=tar', '-o', tar, branch], capture_output=True, text=True)
    if p.returncode:
        shutil.rmtree(work, ignore_errors=True)
        return None, None
    files = os.path.join(work, 'files'); os.makedirs(files)
    subprocess.run(['tar', '-xf', tar, '-C', files], capture_output=True)
    return tar, files

def up(repo, branch, say=print, new_machine=None, target=None):
    """Put this branch's pages up for a test. Returns {'ok', 'url', 'say', 'made'}. new_machine() makes the machine
    when there is none (its return code); target(m) gives the machine to copy to (tests pass stand-ins)."""
    tar, files = _export(repo, branch)
    if not tar:
        return {'ok': False, 'say': "I couldn't find that build to put up."}
    try:
        sub = static_root(files)
        if sub is None:
            return {'ok': False, 'say': "This build isn't a set of plain web pages (there's no index.html), so I can't "
                                        "put it up as a quick test yet. Screenshots will have to do, or set up a host."}
        made = False
        m = _machine()
        if not m or not m.get('ip'):
            say('No cloud machine yet: making one for the test (about 5 minutes).')
            rc = (new_machine or (lambda: cloud_aws.new(repo, with_login=False, start=False, say=say)))()
            m = _machine()
            if rc != 0 or not m or not m.get('ip'):
                return {'ok': False, 'say': "I couldn't make the test machine on your AWS account just now."}
            made = True
        _open_port(m)
        t = target(m) if target else cloud.Target(f"ubuntu@{m['ip']}", m['key'])
        token = secrets.token_urlsafe(12)
        root = 'hive-try'
        t.run(f'pkill -f "http.server {PORT}" || true; rm -rf {root}; mkdir -p {root}/{token}', check=False)
        t.put(tar, f'{root}/site.tar')
        t.run(f'tar -xf {root}/site.tar -C {root}/{token} && rm {root}/site.tar')
        t.run(f'cd {root} && (nohup timeout {HOURS * 3600} python3 -m http.server {PORT} --bind 0.0.0.0 '
              f'> server.log 2>&1 &)')
        url = f"http://{m['ip']}:{PORT}/{token}/" + (f'{sub}/' if sub else '')
        _save({'url': url, 'ip': m['ip'], 'branch': branch, 'started': time.time(),
               'until': time.time() + HOURS * 3600, 'made_machine': made or state().get('made_machine', False)})
        return {'ok': True, 'url': url, 'made': made, 'say': ''}
    finally:
        shutil.rmtree(os.path.dirname(tar), ignore_errors=True)

def down(repo, delete_machine=None, target=None):
    """Stop the test: the server stops, its files go, the port closes; a machine made only for the test is deleted.
    Returns what happened, in plain words."""
    st = state()
    if not st:
        return "There's no test page up right now."
    m = _machine()
    if m and m.get('ip'):
        try:
            t = target(m) if target else cloud.Target(f"ubuntu@{m['ip']}", m['key'])
            t.run(f'pkill -f "http.server {PORT}" || true; rm -rf hive-try', check=False)
        except Exception:
            pass
        _close_port(m)
    os.remove(STATE())
    if st.get('made_machine') and m:
        rc = (delete_machine or (lambda: cloud_aws.stop(ask=lambda q: 'y' if q.startswith('Delete the Hive machine')
                                                        else 'n', say=lambda *a: None, repo=repo, relisten=False)))()
        return ("The test page is down, and the test machine is deleted: nothing is left running or billing." if rc == 0
                else "The test page is down, but I couldn't delete the test machine; on your computer, `hive cloud "
                     "--stop` does it.")
    return "The test page is down. Your cloud machine stays, as it was before."

def expired():
    st = state()
    return bool(st) and time.time() > st.get('until', 0)
