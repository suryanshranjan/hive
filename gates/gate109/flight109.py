"""Gate 109: the cloud paths on real AWS (PREDICTIONS.md). Run on the owner's laptop, signed in to AWS, after the
predictions are pushed:   python gates/gate109/flight109.py <path to the Dabba Days project>

"I'm sleepy" with a build running -> moved to a new t3.small -> the cloud copy restarts the work -> a test deploy at a
private link -> "take it down" -> the machine deleted with the work brought home. Whatever happens, the flight ends
by checking AWS itself, and deletes the machine by hand if anything is left."""
import json, os, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'tests'))
from hive import assistant, cloud, cloud_aws, telegram, trydeploy
from test_telegram_fake import FakeTelegram, ME, tap

OUT = os.path.join(HERE, 'results'); os.makedirs(OUT, exist_ok=True)
GOAL = ("On the plans page (plans.html), add one line under the heading 'Choose your plan': 'Not sure? Try a week of "
        "lunches for ₹500.' Add a test in test_dabba.py that checks the line is there. Change nothing else.")
log, t0 = {'steps': []}, time.time()

def note(step, **kw):
    kw.update(step=step, minute=round((time.time() - t0) / 60, 1))
    log['steps'].append(kw); print(json.dumps(kw, ensure_ascii=False)[:600], flush=True)
    json.dump(log, open(os.path.join(OUT, 'flight.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

def aws(*args):
    m = json.load(open(cloud_aws.STATE())) if os.path.exists(cloud_aws.STATE()) else {}
    return subprocess.run(['aws', *args, '--region', m.get('region') or 'ap-south-1', '--output', 'json'],
                          capture_output=True, text=True)

def target():
    m = json.load(open(cloud_aws.STATE()))
    return m, cloud.Target(f"ubuntu@{m['ip']}", m['key'])

def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except Exception as e:
        return None, repr(e)[:200]

def main(proj):
    proj = os.path.abspath(proj)
    made = {}
    try:
        # 1-2. "I'm sleepy" with a build running; he taps the cloud
        stand_in = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(3600)'])
        assistant.BUILD.clear()
        assistant.BUILD.update(proc=stand_in, goal=GOAL, started=time.time(), log=os.path.join(OUT, 'standin.log'),
                               stopped=False)
        fake = FakeTelegram([tap('awy|cloud')])
        ch = telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake)
        def to_cloud(repo, on, login=True):
            if not on:
                return 1
            t = time.time()
            rc = cloud_aws.new(repo, size='t3.small', with_login=login)
            made['minutes'] = round((time.time() - t) / 60, 1)
            made['standin_alive_during_move'] = stand_in.poll() is None
            return rc
        r = assistant.away(ch, proj, "I'm sleepy, shutting my laptop", poll=1, cloud=to_cloud)
        time.sleep(2)
        note('move', result=r, minutes=made.get('minutes'), standin_alive_during_move=made.get('standin_alive_during_move'),
             standin_stopped_after=stand_in.poll() is not None, told=[m['text'][:200] for m in fake.sent])
        if r != 'moved':
            return
        # 3-4. the cloud copy picks the work up and builds it
        m, t = target()
        start, done = time.time(), None
        while time.time() - start < 25 * 60:
            p = t.run('cat ~/hive-cloud/listen.log 2>/dev/null | tail -5; echo ---; ls ~/.hive/runs 2>/dev/null; echo ---; '
                      'pgrep -f "hive start" >/dev/null && echo BUILDING || echo IDLE; echo ---; '
                      'for f in ~/.hive/runs/*/state.json; do python3 -c "import json,sys; s=json.load(open(sys.argv[1])); '
                      'print(s.get(\'name\'), \'|\', s.get(\'check\'), \'|\', s.get(\'cost\'))" "$f"; done 2>/dev/null; '
                      'echo ---; free -m | head -2', check=False)
            out = p.stdout
            if 'IDLE' in out and '|' in out.split('---')[3]:
                done = out; break
            time.sleep(30)
        note('cloud_build', finished=done is not None, waited_minutes=round((time.time() - start) / 60, 1),
             cloud_state=(done or out)[-1500:])
        # 5. a test deploy of his pages on the same machine; the laptop opens the private link
        up = trydeploy.up(proj, 'HEAD')
        code, body = fetch(up['url']) if up.get('ok') else (None, up.get('say'))
        secret = up['url'].rstrip('/').split('/')[-1] if up.get('ok') else ''
        note('test_deploy', ok=up.get('ok'), url_secret_len=len(secret), status=code, has_home_page='Dabba Days' in (body or ''),
             made_machine=up.get('made'))
        # 6. "take it down"
        said = trydeploy.down(proj)
        code2, _ = fetch(up['url']) if up.get('ok') else (None, '')
        sg = json.loads(aws('ec2', 'describe-security-groups', '--group-ids', m['group']).stdout or '{}')
        ports = [pp.get('FromPort') for g in sg.get('SecurityGroups', []) for pp in g.get('IpPermissions', [])]
        note('take_down', said=said, status_after=code2, port_8080_open=8080 in ports, machine_kept='stays' in said)
    finally:
        # 7. delete the machine, bringing every branch home; then check AWS itself
        if os.path.exists(cloud_aws.STATE()):
            m = json.load(open(cloud_aws.STATE()))
            rc = cloud_aws.stop(ask=lambda q: 'y' if q.startswith('Delete the Hive machine') else 'n', repo=proj,
                                relisten=False)
            branches = subprocess.run(['git', '-C', proj, 'branch', '-a'], capture_output=True, text=True).stdout
            inst = json.loads(aws('ec2', 'describe-instances', '--instance-ids', m['instance']).stdout or '{}')
            states = [i['State']['Name'] for r_ in inst.get('Reservations', []) for i in r_['Instances']]
            sg_left = aws('ec2', 'describe-security-groups', '--group-ids', m['group']).returncode == 0
            key_left = aws('ec2', 'describe-key-pairs', '--key-names', m.get('key_name', 'none')).returncode == 0
            if states and states[0] not in ('terminated', 'shutting-down'):   # the kill: delete by hand
                aws('ec2', 'terminate-instances', '--instance-ids', m['instance'])
            hours = (time.time() - t0) / 3600
            note('delete', rc=rc, hive_branches=[b.strip() for b in branches.splitlines() if 'hive/' in b],
                 instance_state=states, firewall_rule_left=sg_left, key_left=key_left,
                 machine_dollars=round(hours * 0.0224, 3), total_minutes=round((time.time() - t0) / 60, 1))

if __name__ == '__main__':
    main(sys.argv[1])
