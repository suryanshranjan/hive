"""Gate 109, attempt 2b: the test page again on real AWS, after the fix (attempt 2's first command on the machine killed
its own shell, so the pages never went up). Same predictions: A3 (the private link answers 200 with his home page, a
secret of >= 16 characters), A4 (afterwards the link no longer answers; port 8080 closed), and the kill (nothing left
billing). As Hive does it for a founder with no cloud machine: a t3.small made only for the test, deleted on "take it
down". Run on the owner's laptop, signed in to AWS:   python gates/gate109/flight109b.py <Dabba Days project> <branch>"""
import json, os, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
from hive import cloud_aws, trydeploy

OUT = os.path.join(HERE, 'results'); os.makedirs(OUT, exist_ok=True)
log, t0 = {'steps': []}, time.time()

def note(step, **kw):
    kw.update(step=step, minute=round((time.time() - t0) / 60, 1))
    log['steps'].append(kw); print(json.dumps(kw, ensure_ascii=False)[:600], flush=True)
    json.dump(log, open(os.path.join(OUT, 'flight_b.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

def aws(m, *args):
    return subprocess.run(['aws', *args, '--region', m.get('region') or 'ap-south-1', '--output', 'json'],
                          capture_output=True, text=True)

def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except Exception as e:
        return None, repr(e)[:200]

def main(proj, branch):
    proj = os.path.abspath(proj); m = {}
    try:
        up = trydeploy.up(proj, branch)
        m = json.load(open(cloud_aws.STATE())) if os.path.exists(cloud_aws.STATE()) else {}
        code, body, plans = None, up.get('say'), ''
        if up.get('ok'):
            for _ in range(10):   # the server takes a moment to start
                code, body = fetch(up['url'])
                if code == 200:
                    break
                time.sleep(3)
            _, plans = fetch(up['url'] + 'plans.html')
        secret = up['url'].rstrip('/').split('/')[-1] if up.get('ok') else ''
        note('test_deploy', ok=up.get('ok'), made_machine=up.get('made'), size=m.get('size') or m.get('type'),
             url_secret_len=len(secret), status=code, has_home_page='Dabba Days' in (body or ''),
             plans_has_trial_line='Try a week of lunches' in (plans or ''), said=up.get('say'))
        said = trydeploy.down(proj)
        code2, _ = fetch(up['url']) if up.get('ok') else (None, '')
        note('take_down', said=said, status_after=code2)
    finally:
        if os.path.exists(cloud_aws.STATE()):   # take-down did not delete it: delete it here
            m = json.load(open(cloud_aws.STATE()))
            note('leftover_machine', rc=cloud_aws.stop(ask=lambda q: 'y', repo=proj, relisten=False))
        if m.get('instance'):
            inst = json.loads(aws(m, 'ec2', 'describe-instances', '--instance-ids', m['instance']).stdout or '{}')
            states = [i['State']['Name'] for r_ in inst.get('Reservations', []) for i in r_['Instances']]
            types = [i['InstanceType'] for r_ in inst.get('Reservations', []) for i in r_['Instances']]
            if states and states[0] not in ('terminated', 'shutting-down'):   # the kill: delete by hand
                aws(m, 'ec2', 'terminate-instances', '--instance-ids', m['instance'])
            note('delete', instance_state=states, instance_type=types,
                 firewall_rule_left=aws(m, 'ec2', 'describe-security-groups', '--group-ids', m['group']).returncode == 0,
                 key_left=aws(m, 'ec2', 'describe-key-pairs', '--key-names', m.get('key_name', 'none')).returncode == 0,
                 machine_dollars=round((time.time() - t0) / 3600 * 0.0224, 3), total_minutes=round((time.time() - t0) / 60, 1))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
