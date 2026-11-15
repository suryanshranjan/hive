"""Gate 117 (PREDICTIONS.md): only a phone, on real Render. Does the same thing the Deploy to Render button does, through
Render's API, so it can be timed and deleted cleanly:
  python gates/gate117/render117.py up       make the worker (render.yaml's settings) and wait for its first deploy
  python gates/gate117/render117.py logs     the service's recent log lines (secrets never printed)
  python gates/gate117/render117.py down     delete the service and its disk (nothing left billing)
Keys come from ~/.hive/render_test.env (RENDER_API_KEY, TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY), never from the repo.
Results: gates/gate117/results/flight.json."""
import json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'results'); os.makedirs(OUT, exist_ok=True)
ENV = os.path.join(os.path.expanduser('~'), '.hive', 'render_test.env')
STATE = os.path.join(os.path.expanduser('~'), '.hive', 'render_test_service.json')
API = 'https://api.render.com/v1'

def keys():
    out = {}
    for line in open(ENV, encoding='utf-8-sig'):
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.split('=', 1); out[k.strip()] = v.strip().strip('"').strip("'")
    for k in ('RENDER_API_KEY', 'TELEGRAM_BOT_TOKEN', 'ANTHROPIC_API_KEY'):
        if not out.get(k):
            sys.exit(f'{k} is missing from {ENV}')
    return out

def secrets_out(text, k):
    for v in k.values():
        if v and len(v) > 8:
            text = text.replace(v, '••••')
    return text

def render(k, method, path, body=None):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': f"Bearer {k['RENDER_API_KEY']}", 'Accept': 'application/json',
                                          'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        sys.exit(f'Render said {e.code} on {method} {path}: {secrets_out(e.read().decode()[:600], k)}')

def log(**kw):
    path = os.path.join(OUT, 'flight.json')
    data = json.load(open(path)) if os.path.exists(path) else {'steps': []}
    kw['t'] = time.strftime('%H:%M:%S'); data['steps'].append(kw)
    json.dump(data, open(path, 'w'), indent=1); print(json.dumps(kw))

def bot_name(k):
    with urllib.request.urlopen(f"https://api.telegram.org/bot{k['TELEGRAM_BOT_TOKEN']}/getMe", timeout=30) as r:
        return json.load(r)['result']['username']

def up():
    k = keys()
    if os.path.exists(STATE):
        sys.exit(f'A test service already exists ({json.load(open(STATE))["id"]}); run "down" first.')
    owners = render(k, 'GET', '/owners?limit=20')
    owner = (owners[0].get('owner') or owners[0])['id']
    body = {'type': 'background_worker', 'name': 'hive-g117', 'ownerId': owner,
            'repo': 'https://github.com/suryanshranjan/hive', 'branch': 'main', 'autoDeployTrigger': 'off',
            'envVars': [{'key': 'TELEGRAM_BOT_TOKEN', 'value': k['TELEGRAM_BOT_TOKEN']},
                        {'key': 'ANTHROPIC_API_KEY', 'value': k['ANTHROPIC_API_KEY']}],
            'serviceDetails': {'runtime': 'docker', 'plan': 'standard', 'region': 'singapore',
                               'envSpecificDetails': {'dockerfilePath': './deploy/render/Dockerfile', 'dockerContext': '.'},
                               'disk': {'name': 'hive-data', 'mountPath': '/data', 'sizeGB': 10}}}
    t0 = time.time()
    got = render(k, 'POST', '/services', body)
    svc = got.get('service') or got
    json.dump({'id': svc['id'], 'owner': owner, 'made': t0}, open(STATE, 'w'))
    log(step='made', service=svc['id'], plan='standard (1 CPU, 2 GB)', disk_gb=10, region='singapore')
    while True:
        time.sleep(20)
        deps = render(k, 'GET', f"/services/{svc['id']}/deploys?limit=1")
        d = (deps[0].get('deploy') or deps[0]) if deps else {}
        st = d.get('status', '?')
        print(f'  {int(time.time() - t0)} s: {st}', flush=True)
        if st in ('live', 'build_failed', 'update_failed', 'canceled', 'deactivated', 'pre_deploy_failed'):
            log(step='deploy', status=st, minutes=round((time.time() - t0) / 60, 1)); break
        if time.time() - t0 > 2400:
            log(step='deploy', status='still ' + st + ' after 40 min'); break
    if st == 'live':
        log(step='ready', say_hi_to='@' + bot_name(k))

def logs():
    k, s = keys(), json.load(open(STATE))
    q = urllib.parse.urlencode({'ownerId': s['owner'], 'resource': s['id'], 'limit': 100, 'direction': 'backward'})
    got = render(k, 'GET', '/logs?' + q)
    for line in reversed(got.get('logs', [])):
        print(secrets_out(f"{line.get('timestamp', '')[11:19]} {line.get('message', '')}", k)[:300])

def down():
    k = keys()
    if not os.path.exists(STATE):
        print('No test service recorded.'); return
    s = json.load(open(STATE))
    render(k, 'DELETE', f"/services/{s['id']}")
    left = [x for x in render(k, 'GET', '/services?limit=50') if (x.get('service') or x).get('name') == 'hive-g117']
    log(step='deleted', service=s['id'], left=len(left), hours=round((time.time() - s['made']) / 3600, 2))
    os.remove(STATE)

if __name__ == '__main__':
    {'up': up, 'logs': logs, 'down': down}[sys.argv[1]]()
