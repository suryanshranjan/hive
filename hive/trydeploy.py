"""A test deploy on his own cloud machine (the owner: "a feature shipped can use the same instance: deploy it there, test
it as a static web page, then delete it as required, so it is just a test deploy").

When he says "send me a link" and no hosting service is set up, Hive can put the build's pages on the AWS machine it
uses for the cloud (made for the purpose if there is none), at a secret address, for at most two hours. The server
times out on the host. Telegram offers cleanup of the port and dedicated machine for fresh approval.
Static pages require an index.html at the top, or in public/, dist/, build/ or out/.

The machine's port 8080 is opened to the internet while the test runs (a phone's address cannot be known in
advance), so the address carries a random secret and the server stops by itself after two hours."""
import hashlib, json, os, re, secrets, subprocess, tarfile, tempfile, threading, time
from pathlib import Path

from . import actions, cloud, cloud_aws, deploy, projects

PORT = 8080
HOURS = 2
_PAGE_LOCK = threading.Lock()
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
    folder = os.path.dirname(STATE())
    os.makedirs(folder, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=folder, delete=False) as out:
        json.dump(st, out)
    os.replace(out.name, STATE())


def _machine_id(m):
    return {key: m.get(key) for key in ('instance', 'ip', 'group', 'region', 'profile')}


def target_snapshot(repo):
    """Bind the action to this project, this page generation and this machine."""
    page = state()
    if page.get('project', projects.path(repo)) != projects.path(repo):
        raise ValueError('The current test page belongs to another project.')
    current = _machine()
    if current is not None and not current.get('ip'):
        raise ValueError('The cloud machine record is incomplete. Check it before changing the preview.')
    machine = _machine_id(current or {})
    if page and (not machine['ip'] or page.get('ip') != machine['ip']
                 or page.get('machine', machine) != machine):
        raise ValueError('The recorded test machine has changed. Check the page and cloud machine.')
    page_id = hashlib.sha256(json.dumps(page, sort_keys=True).encode()).hexdigest() if page else ''
    return {'machine': machine, 'page': page_id, 'delete_machine': bool(page.get('made_machine'))}


def cloud_binding(machine):
    profile = machine['profile'] or cloud_aws.default_profile()
    try:
        region = machine['region'] or cloud_aws.default_region(profile)
        account = cloud_aws._aws(['sts', 'get-caller-identity'], profile, region).get('Account')
    except (OSError, RuntimeError):
        account = None
    if not account:
        raise ValueError('I could not check the AWS account. Check the AWS login before confirming.')
    return {'account': account, 'region': region, 'profile': profile}


def publish_approved(repo, args):
    with _PAGE_LOCK:
        if target_snapshot(repo) != args['target']:
            return {'ok': False, 'say': 'The test target changed. Request a new preview.'}
        binding = cloud_binding(args['target']['machine'])
        if binding != args['cloud']:
            return {'ok': False, 'say': 'The AWS account or region changed. Request a new preview.'}
        return up(repo, args['sha'], say=lambda *a: None, binding=binding)


def remove_approved(repo, args):
    with _PAGE_LOCK:
        try:
            if (not args['target']['page'] or target_snapshot(repo) != args['target']
                    or cloud_binding(args['target']['machine']) != args['cloud']):
                return actions.ActionResult('needs_input', 'The test page changed. Check the current page.')
        except ValueError as exc:
            return actions.ActionResult('needs_input', str(exc))
        return actions.ActionResult('succeeded', down(repo))

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
    cloud_aws._aws(['ec2', 'revoke-security-group-ingress', '--group-id', m['group'], '--protocol', 'tcp',
                    '--port', str(PORT), '--cidr', '0.0.0.0/0'], m.get('profile'), m.get('region'))

def _export(repo, branch):
    """The build's files (no history), as a tar file. Returns (tar path, folder with the files)."""
    work = tempfile.mkdtemp(prefix='hive_try_')
    tar = os.path.join(work, 'site.tar')
    p = subprocess.run(['git', '-C', repo, 'archive', '--format=tar', '-o', tar, branch], capture_output=True, text=True)
    if p.returncode:
        deploy.remove(work)
        return None, None
    files = Path(work, 'files').resolve()
    files.mkdir()
    try:
        with tarfile.open(tar) as archive:
            if hasattr(tarfile, 'data_filter'):
                archive.extractall(files, filter='data')
            else:  # Python versions before extraction filters were backported.
                for member in archive:
                    if not ((member.isfile() or member.isdir()) and (files / member.name).resolve().is_relative_to(files)):
                        raise ValueError('Unsupported preview asset.')
                    archive.extract(member, files)
        # Package the validated tree. All file and directory links must stay inside
        # the build when Chromium requests them on the remote preview machine.
        root = files.resolve()
        if any(not path.resolve().is_relative_to(root) for path in files.rglob('*')):
            raise ValueError('Unsupported preview asset.')
        with tarfile.open(tar, 'w') as checked:
            checked.add(files, arcname='.')
    except (OSError, RuntimeError, ValueError, tarfile.TarError):
        deploy.remove(work)
        raise ValueError('The preview could not be packaged with all assets confined to the build.') from None
    return tar, files

# "[h]ttp" so the pattern does not match this command's own shell (Gate 109: `pkill -f "http.server 8080"` killed the
# shell running it, before the folder for the pages was made, and the test page never went up)
SIZE = 't3.small'   # plain pages need little; the owner asked for t3.small (Gate 109)
STOP_SERVER = f'pkill -f "[h]ttp.server {PORT}" || true'

def up(repo, branch, say=print, new_machine=None, target=None, binding=None):
    """Put this branch's pages up for a test. Returns {'ok', 'url', 'say', 'made'}. new_machine() makes the machine
    when there is none (its return code); target(m) gives the machine to copy to (tests pass stand-ins)."""
    try:
        tar, files = _export(repo, branch)
    except ValueError as exc:
        return {'ok': False, 'say': str(exc)}
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
            options = {k: binding[k] for k in ('profile', 'region')} if binding else {}
            rc = (new_machine or (lambda: cloud_aws.new(repo, size=SIZE, with_login=False, start=False, say=say, **options)))()
            m = _machine()
            if rc != 0 or not m or not m.get('ip'):
                raise RuntimeError('The outcome of creating the test machine is unconfirmed.')
            made = True
        started = time.time()
        page = {'branch': branch, 'ip': m['ip'], 'machine': _machine_id(m), 'project': projects.path(repo),
                'cloud': binding, 'started': started, 'until': started + HOURS * 3600,
                'made_machine': made or state().get('made_machine', False)}
        _save(page)  # Preserve the cleanup target even if publishing loses its response.
        _open_port(m)
        t = target(m) if target else cloud.Target(f"ubuntu@{m['ip']}", m['key'])
        token = secrets.token_urlsafe(12)
        # The server's own folder (www) holds only the secret folder and a blank index.html, so the bare address
        # shows a blank page, never a listing that names the secret; its log lives outside what is served (audit, Nov 15).
        root, www = 'hive-try', 'hive-try/www'
        t.run(STOP_SERVER, check=False)
        t.run(f'rm -rf {root} && mkdir -p {www}/{token} && printf "<!doctype html><title></title>" > {www}/index.html')
        t.put(tar, f'{root}/site.tar')
        t.run(f'tar -xf {root}/site.tar -C {www}/{token} && rm {root}/site.tar')
        t.run(f'cd {root} && (nohup timeout {HOURS * 3600} python3 -m http.server {PORT} --bind 0.0.0.0 --directory www '
              f'> server.log 2>&1 &)')
        url = f"http://{m['ip']}:{PORT}/{token}/" + (f'{sub}/' if sub else '')
        _save(dict(page, url=url))
        return {'ok': True, 'url': url, 'made': made, 'say': ''}
    finally:
        deploy.remove(os.path.dirname(tar))

def down(repo, delete_machine=None, target=None):
    """Stop the test: the server stops, its files go, the port closes; a machine made only for the test is deleted.
    Returns what happened, in plain words."""
    st = state()
    if not st:
        return "There's no test page up right now."
    m = _machine()
    target_snapshot(repo)
    t = target(m) if target else cloud.Target(f"ubuntu@{m['ip']}", m['key'])
    t.run(STOP_SERVER + '; rm -rf hive-try')
    _close_port(m)
    if st.get('made_machine'):
        rc = (delete_machine or (lambda: cloud_aws.stop(ask=lambda q: 'y' if q.startswith('Delete the Hive machine')
                                                        else 'n', say=lambda *a: None, repo=repo, relisten=False)))()
        if rc != 0:
            raise RuntimeError('Test machine deletion is unconfirmed.')
    if os.path.exists(STATE()):  # cloud_aws.stop also clears the page on confirmed deletion
        os.remove(STATE())
    if st.get('made_machine'):
        return "The test page is down, and the test machine is deleted: nothing is left running or billing."
    return "The test page is down. Your cloud machine stays, as it was before."

def expired():
    st = state()
    return bool(st) and time.time() > st.get('until', 0)
