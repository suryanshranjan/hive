"""Gate 111: the founder's choice of always-on machine, on real AWS (PREDICTIONS.md). Run on the owner's laptop, AWS
signed in, the Telegram link copied to ~/.hive/telegram.json:   python gates/gate111/flight111.py <Dabba Days project>"""
import json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'tests'))
from hive import assistant, cloud, cloud_aws, telegram
from test_telegram_fake import FakeTelegram, ME, tap

OUT = os.path.join(HERE, 'results'); os.makedirs(OUT, exist_ok=True)
log, t0 = {'steps': []}, time.time()

def note(step, **kw):
    kw.update(step=step, minute=round((time.time() - t0) / 60, 1))
    log['steps'].append(kw); print(json.dumps(kw, ensure_ascii=False)[:800], flush=True)
    json.dump(log, open(os.path.join(OUT, 'flight.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

def aws(m, *args):
    return subprocess.run(['aws', *args, '--region', m.get('region') or 'ap-south-1', '--output', 'json'],
                          capture_output=True, text=True)

def to_cloud(repo, on, login=True, size='t3.small'):   # as `hive listen` wires it (hive/__main__.py)
    return cloud_aws.new(repo, size=size, with_login=login) if on else cloud_aws.stop(
        ask=lambda q: 'y' if q.startswith(('Delete the Hive machine', 'Power this')) else 'n', repo=repo, relisten=False)

def say(script, words, proj):
    fake = FakeTelegram(script)
    ch = telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake)
    return assistant.handle(ch, proj, words, poll=1, cloud=to_cloud), [m['text'] for m in fake.sent]

def main(proj):
    proj = os.path.abspath(proj); m = {}
    try:
        t = time.time()
        r, told = say([tap('cld|yes')], 'Keep running when my laptop is off, move to the cloud', proj)
        m = json.load(open(cloud_aws.STATE())) if os.path.exists(cloud_aws.STATE()) else {}
        inst = json.loads(aws(m, 'ec2', 'describe-instances', '--instance-ids', m['instance']).stdout or '{}') if m else {}
        types = [i['InstanceType'] for x in inst.get('Reservations', []) for i in x['Instances']]
        note('move', result=r, minutes=round((time.time() - t) / 60, 1), offer=told[0][:700],
             offer_has_prices=('$23 a month' in told[0], '$72 a month' in told[0], 'this computer' in told[0].lower()),
             aws_type=types, remembered=cloud_aws.preferred(), told_last=told[-1][:200])
        if m.get('ip'):
            tg = cloud.Target(f"ubuntu@{m['ip']}", m['key'])
            time.sleep(20)
            p = tg.run("pgrep -af '[h]ive listen' | head -3; echo ---; tail -3 ~/hive-cloud/listen.log", check=False)
            note('always_on', listener_running='hive listen' in p.stdout.split('---')[0], seen=p.stdout[-600:])
    finally:
        if os.path.exists(cloud_aws.STATE()):
            m = json.load(open(cloud_aws.STATE()))
            r, told = say([tap('cld|yes')], 'delete the cloud machine', proj)
            note('delete_said', result=r, told=told[-1][:200])
        if m.get('instance'):
            inst = json.loads(aws(m, 'ec2', 'describe-instances', '--instance-ids', m['instance']).stdout or '{}')
            states = [i['State']['Name'] for x in inst.get('Reservations', []) for i in x['Instances']]
            if states and states[0] not in ('terminated', 'shutting-down'):   # the kill: delete by hand
                aws(m, 'ec2', 'terminate-instances', '--instance-ids', m['instance'])
            note('delete', instance_state=states,
                 firewall_rule_left=aws(m, 'ec2', 'describe-security-groups', '--group-ids', m['group']).returncode == 0,
                 key_left=aws(m, 'ec2', 'describe-key-pairs', '--key-names', m.get('key_name', 'none')).returncode == 0,
                 machine_dollars=round((time.time() - t0) / 3600 * (0.0224 + 0.005), 3),
                 total_minutes=round((time.time() - t0) / 60, 1))
        try:
            os.remove(cloud_aws.CHOICE())   # the flight's choice is not his
        except OSError:
            pass

if __name__ == '__main__':
    main(sys.argv[1])
