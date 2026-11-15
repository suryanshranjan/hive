"""Gate 114 (PREDICTIONS.md): the fixes flown for real, part by part, on the owner's real phone and AWS.
  python gates/gate114/flight114.py aws-renew   A: the expired AWS sign-in renewed from his phone
  python gates/gate114/flight114.py limit       B: hive cloud --limit, then its rights checked with AWS's --dry-run
  python gates/gate114/flight114.py cycle       C: make, reach and delete a t3.small as hive-builder
  python gates/gate114/flight114.py fast        D: 10 replies timed, fast path vs Claude Code (needs hive llm api)
Results go to gates/gate114/results/<part>.json. His AWS account number is masked; nothing from his accounts is kept."""
import json, os, re, shlex, statistics, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
from hive import cloud_aws, explain, logins, telegram

OUT = os.path.join(HERE, 'results'); os.makedirs(OUT, exist_ok=True)
MASK = lambda s: re.sub(r'\b\d{12}\b', '…' + '0' * 4, str(s))
TECH = re.compile(r'\b(cli|token|profile|sts|iam|credential|oauth|stdin|subprocess)\b', re.I)

def save(part, data):
    json.dump(json.loads(MASK(json.dumps(data))), open(os.path.join(OUT, part + '.json'), 'w'), indent=1)
    print(MASK(json.dumps(data, indent=1)))

def aws(args, profile=None):
    cmd = shlex.split(cloud_aws.AWS) + args + ['--output', 'json'] + (['--profile', profile] if profile else [])
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr)

class Watched(telegram.Channel):
    """His real chat, with what Hive sent and when, for scoring."""
    sent = []
    def send(self, text, *a, **k):
        Watched.sent.append({'t': time.time(), 'text': text}); return super().send(text, *a, **k)
    def edit(self, mid, text, html=False):
        Watched.sent.append({'t': time.time(), 'edit': mid, 'text': text}); return super().edit(mid, text, html)

def chat():
    cfg = telegram.load()
    if not cfg:
        sys.exit('No phone connected (hive telegram setup).')
    if telegram.busy_elsewhere():
        sys.exit('Another Hive process is reading the chat; stop the listener first.')
    ch = Watched(cfg); ch.drain()
    return ch

def aws_renew():
    os.environ['HIVE_AWS_PROFILE'] = ''   # the CLI's own login: the one that expired
    before = logins.ok('aws')
    ch, t0 = chat(), time.time()
    done = logins.ensure(ch, 'aws', poll=5)
    link = next((m for m in Watched.sent if 'https://' in m['text']), None)
    save('aws_renew', {'expired_before': not before, 'renewed': done, 'works_now': logins.ok('aws'),
                       'link_after_s': round(link['t'] - t0, 1) if link else None, 'minutes': round((time.time() - t0) / 60, 1),
                       'technical_words': sorted({w.lower() for m in Watched.sent for w in TECH.findall(m['text'])}),
                       'messages': [m['text'][:300] for m in Watched.sent]})

def limit():
    t0 = time.time()
    rc = cloud_aws.limit('', ask=lambda q: 'yes')
    region = subprocess.run(shlex.split(cloud_aws.AWS) + ['configure', 'get', 'region', '--profile', 'hive'],
                            capture_output=True, text=True).stdout.strip()
    _, who = aws(['sts', 'get-caller-identity'], 'hive')
    ami = json.loads(aws(['ssm', 'get-parameter', '--name', cloud_aws.UBUNTU], 'hive')[1] or '{}').get('Parameter', {}).get('Value')
    _, desc = aws(['ec2', 'describe-instances', '--filters', 'Name=tag:Name,Values=barternow-staging'])   # as root: his machine
    theirs = re.findall(r'"InstanceId": "(i-[0-9a-f]+)"', desc)
    tag = lambda kind: f'ResourceType={kind},Tags=[{{Key=hive,Value=gate114}}]'
    run = lambda size, tagged: ['ec2', 'run-instances', '--dry-run', '--image-id', ami or 'ami-0', '--instance-type', size,
                                '--count', '1'] + (['--tag-specifications', tag('instance')] if tagged else [])
    allowed = {   # must come back "would have succeeded"
        't3.small tagged hive': run('t3.small', True),
        'key pair tagged hive': ['ec2', 'create-key-pair', '--dry-run', '--key-name', 'g114-dry', '--tag-specifications', tag('key-pair')],
        'firewall tagged hive': ['ec2', 'create-security-group', '--dry-run', '--group-name', 'g114-dry', '--description', 'g114',
                                 '--tag-specifications', tag('security-group')],
    }
    refused = {   # must come back refused
        'delete barternow-staging': ['ec2', 'terminate-instances', '--dry-run', '--instance-ids'] + (theirs[:1] or ['i-0']),
        'stop barternow-staging': ['ec2', 'stop-instances', '--dry-run', '--instance-ids'] + (theirs[:1] or ['i-0']),
        'list IAM users': ['iam', 'list-users'],
        'a machine with no hive tag': run('t3.small', False),
        'a c5.4xlarge tagged hive': run('c5.4xlarge', True),
    }
    res = {'limit_rc': rc, 'answers_as': who.strip()[-120:], 'region': region, 'ubuntu_found': bool(ami),
           'their_machine_found': bool(theirs), 'allowed': {}, 'refused': {}, 'seconds': round(time.time() - t0)}
    for name, args in allowed.items():
        _, out = aws(args, 'hive'); res['allowed'][name] = 'DryRunOperation' in out or out.strip()[-200:]
    for name, args in refused.items():
        _, out = aws(args, 'hive')
        res['refused'][name] = bool(re.search(r'UnauthorizedOperation|AccessDenied|not authorized', out)) or out.strip()[-200:]
    save('limit', res)

def _all_tagged():
    _, out = aws(['resourcegroupstaggingapi', 'get-resources', '--tag-filters', 'Key=hive'])   # as root: what is left
    _, inst = aws(['ec2', 'describe-instances', '--filters', 'Name=tag-key,Values=hive',
                   'Name=instance-state-name,Values=pending,running,stopping,stopped'])
    return re.findall(r'"ResourceARN": "([^"]+)"', out), re.findall(r'"InstanceId": "(i-[0-9a-f]+)"', inst)

def cycle():
    _, before = aws(['ec2', 'describe-instances', '--filters', 'Name=tag:Name,Values=barternow-staging',
                     '--query', 'Reservations[].Instances[].[InstanceId,State.Name,LaunchTime]'])
    repo = tempfile.mkdtemp(prefix='g114-')
    for c in (['init', '-q'], ['commit', '-q', '--allow-empty', '-m', 'g114']):
        subprocess.run(['git', '-C', repo] + c, check=True)
    log, t0 = [], time.time()
    rc_new = cloud_aws.new(repo, 't3.small', with_login=False, start=False, say=log.append)
    m = json.load(open(cloud_aws.STATE())) if os.path.exists(cloud_aws.STATE()) else {}
    up = time.time() - t0
    ssh = subprocess.run(['ssh', '-i', m.get('key', ''), '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=20',
                          f"ubuntu@{m.get('ip', '0.0.0.0')}", 'echo hive-ok'], capture_output=True, text=True) if m else None
    rc_stop = cloud_aws.stop(ask=lambda q: 'y' if q.startswith(('Delete the Hive machine', 'Power this')) else 'n',
                             say=log.append, repo=repo, relisten=False)
    time.sleep(20)
    os.environ['HIVE_AWS_PROFILE'] = ''   # checked as root, not as the login under test
    arns, live = _all_tagged()
    _, after = aws(['ec2', 'describe-instances', '--filters', 'Name=tag:Name,Values=barternow-staging',
                    '--query', 'Reservations[].Instances[].[InstanceId,State.Name,LaunchTime]'])
    hours = (time.time() - t0) / 3600
    save('cycle', {'new_rc': rc_new, 'ready_minutes': round(up / 60, 1), 'ssh': bool(ssh and 'hive-ok' in ssh.stdout),
                   'stop_rc': rc_stop, 'left_instances': live, 'left_tagged': [a for a in arns if ':instance/' not in a],
                   'barternow_unchanged': before == after, 'cost_usd': round(hours * cloud_aws.PRICE['t3.small'] + 0.01, 3),
                   'log': [MASK(x)[:200] for x in log]})

MESSAGES = ['hi', 'status', 'what can you do', 'good morning', 'are you there?', 'what did we build last?',
            'thanks', 'what time is it for you?', 'remind me what Hive is for', 'ok, talk later']

def fast():
    from hive import assistant
    if not explain.fast_on():
        sys.exit('No fast model set up: run `hive llm api` first.')
    ch, rows = chat(), []
    for arm in ('fast', 'claude_code'):
        if arm == 'claude_code':
            os.environ['HIVE_API'] = '0'
        for text in MESSAGES:
            n, t0, spent = len(Watched.sent), time.time(), explain.SPENT[0]
            ch.remember('owner', text)
            assistant.speak(ch, ROOT, f'He wrote: "{text}". Reply to it.', 'Here, sir.')
            mine = Watched.sent[n:]
            final = mine[-1]['text'] if mine else ''
            rows.append({'arm': arm, 'text': text, 'first_s': round(mine[0]['t'] - t0, 2) if mine else None,
                         'whole_s': round(mine[-1]['t'] - t0, 2) if mine else None,
                         'messages': sum(1 for x in mine if 'edit' not in x), 'finished': not final.endswith('…'),
                         'usd': round(explain.SPENT[0] - spent, 4)})
            time.sleep(2)
    med = lambda arm, k: statistics.median([r[k] for r in rows if r['arm'] == arm and r[k] is not None] or [0])
    save('fast', {'model': explain.fast_cfg().get('model') if os.environ.pop('HIVE_API', None) is not None else None,
                  'median_first_s': {a: med(a, 'first_s') for a in ('fast', 'claude_code')},
                  'median_whole_s': {a: med(a, 'whole_s') for a in ('fast', 'claude_code')},
                  'median_usd': {a: med(a, 'usd') for a in ('fast', 'claude_code')}, 'rows': rows})

if __name__ == '__main__':
    {'aws-renew': aws_renew, 'limit': limit, 'cycle': cycle, 'fast': fast}[sys.argv[1]]()
