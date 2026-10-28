"""hive cloud --new / --stop: one command makes a cloud machine for Hive on the owner's own AWS account, and one deletes
it, so nothing is left running (and billing).

  hive cloud --new [--size t3.large] [--region ap-south-1] [--profile name] [--no-login]
                       make the machine, then move the project; the Claude login goes too, so builders work there
  hive cloud --stop                                                           delete the machine, its key and firewall

It uses the AWS command line (`aws`), logged in on this machine. What it makes, all tagged `hive`:
- a key pair, kept at ~/.hive/cloud/<name>.pem (only this machine can log in);
- a firewall rule (security group) that lets SSH in from this machine's current IP address only;
- one Ubuntu 24.04 machine that installs git, Python, Node.js and Claude Code by itself on first boot.
Then the project moves there exactly as with `hive cloud --to` (only committed work; never .env files or keys)."""
import json, os, subprocess, time, urllib.request

from . import cloud

AWS = os.environ.get('HIVE_AWS', 'aws')
HOME = lambda: os.path.join(os.path.expanduser('~'), '.hive', 'cloud')
STATE = lambda: os.path.join(HOME(), 'machine.json')
UBUNTU = '/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id'
PRICE = {'t3.medium': 0.045, 't3.large': 0.09, 't3.xlarge': 0.18, 'm7i.large': 0.11, 'm7i.xlarge': 0.22}   # $/hour, about
FIRST_BOOT = """#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y git python3-venv python3-pip curl ca-certificates
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt-get install -y nodejs
npm install -g @anthropic-ai/claude-code
touch /var/lib/hive-ready
"""

def _aws(args, profile=None, region=None, check=True):
    cmd = [AWS] + args + ['--output', 'json'] + (['--profile', profile] if profile else []) + (['--region', region] if region else [])
    p = subprocess.run(cmd, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"aws {' '.join(args[:2])}: {p.stderr.strip()[:300]}")
    try:
        return json.loads(p.stdout) if p.stdout.strip() else {}
    except ValueError:
        return {}

def _my_ip():
    if os.environ.get('HIVE_MY_IP'):
        return os.environ['HIVE_MY_IP']
    with urllib.request.urlopen('https://checkip.amazonaws.com', timeout=15) as r:
        return r.read().decode().strip()

def new(repo='.', size='t3.large', region=None, profile=None, with_login=True, start=True, say=print):
    """Make a machine on the owner's AWS account, wait until it is ready, and move the project there."""
    if os.path.exists(STATE()):
        m = json.load(open(STATE()))
        say(f"You already have a Hive machine ({m['instance']} at {m['ip']}). Moving the project there; "
            "`hive cloud --stop` deletes it.")
        return cloud.go(repo, f"ubuntu@{m['ip']}", with_login, start, say, key=m['key'])
    try:
        who = _aws(['sts', 'get-caller-identity'], profile)
    except (RuntimeError, FileNotFoundError):
        say("I need the AWS command line, logged in to your account: install it (aws.amazon.com/cli), then run "
            "`aws configure` or `aws login`, and try again."); return 2
    region = region or subprocess.run([AWS, 'configure', 'get', 'region'] + (['--profile', profile] if profile else []),
                                      capture_output=True, text=True).stdout.strip() or 'ap-south-1'
    name = f"hive-{cloud._project(repo)}-{int(time.time()) % 100000}"
    say(f"Making a cloud machine for Hive on AWS account {who.get('Account', '?')} ({region}, {size}, about "
        f"${PRICE.get(size, 0.1):.2f} an hour while it runs). `hive cloud --stop` deletes it.")
    os.makedirs(HOME(), exist_ok=True)
    m = {'name': name, 'region': region, 'profile': profile, 'size': size}
    try:
        key = _aws(['ec2', 'create-key-pair', '--key-name', name, '--key-type', 'ed25519', '--tag-specifications',
                    f'ResourceType=key-pair,Tags=[{{Key=hive,Value={name}}}]'], profile, region)
        m['key'] = os.path.join(HOME(), name + '.pem')
        with open(m['key'], 'w') as f:
            f.write(key['KeyMaterial'])
        os.chmod(m['key'], 0o600)
        m['key_name'] = name
        json.dump(m, open(STATE(), 'w'), indent=1)   # from here on, --stop can clean up whatever was made
        sg = _aws(['ec2', 'create-security-group', '--group-name', name, '--description', 'Hive: SSH from the owner only',
                   '--tag-specifications', f'ResourceType=security-group,Tags=[{{Key=hive,Value={name}}}]'], profile, region)
        m['group'] = sg['GroupId']; json.dump(m, open(STATE(), 'w'), indent=1)
        _aws(['ec2', 'authorize-security-group-ingress', '--group-id', m['group'], '--protocol', 'tcp', '--port', '22',
              '--cidr', f'{_my_ip()}/32'], profile, region)
        ami = _aws(['ssm', 'get-parameter', '--name', UBUNTU], profile, region)['Parameter']['Value']
        boot = os.path.join(HOME(), name + '.boot.sh')
        open(boot, 'w').write(FIRST_BOOT)
        run = _aws(['ec2', 'run-instances', '--image-id', ami, '--instance-type', size, '--key-name', name,
                    '--security-group-ids', m['group'], '--user-data', f'file://{boot}',
                    '--block-device-mappings', 'DeviceName=/dev/sda1,Ebs={VolumeSize=30,VolumeType=gp3}',
                    '--tag-specifications', f'ResourceType=instance,Tags=[{{Key=Name,Value={name}}},{{Key=hive,Value={name}}}]'],
                   profile, region)
        m['instance'] = run['Instances'][0]['InstanceId']; json.dump(m, open(STATE(), 'w'), indent=1)
        say(f"  Machine {m['instance']} is starting...")
        _aws(['ec2', 'wait', 'instance-running', '--instance-ids', m['instance']], profile, region)
        desc = _aws(['ec2', 'describe-instances', '--instance-ids', m['instance']], profile, region)
        m['ip'] = desc['Reservations'][0]['Instances'][0]['PublicIpAddress']; json.dump(m, open(STATE(), 'w'), indent=1)
    except Exception as e:
        say(f"  That did not work: {e}\n  Run `hive cloud --stop` to delete anything that was made.")
        return 1
    local = os.environ.get('HIVE_CLOUD_LOCAL')   # tests: a local folder stands in for the machine
    target = local or f"ubuntu@{m['ip']}"
    if not local:
        say('  Setting itself up (git, Python, Node.js, Claude Code); this takes about 3 minutes...')
        t = cloud.Target(target, m['key'])
        for _ in range(60):
            if t.run('test -f /var/lib/hive-ready', check=False).returncode == 0:
                break
            time.sleep(10)
        else:
            say("  It did not finish setting itself up in 10 minutes. `hive cloud --stop` deletes it."); return 1
    say(f"  Ready at {m['ip']}.")
    return cloud.go(repo, target, with_login, start, say, key=None if local else m['key'])

def stop(ask=input, say=print):
    """Delete the machine `hive cloud --new` made, with its key and firewall rule."""
    if not os.path.exists(STATE()):   # e.g. asked on the cloud machine itself, which never holds the owner's AWS keys
        say("There is no Hive machine made from this computer to delete."); return 5
    m = json.load(open(STATE()))
    what = m.get('instance') or m.get('name')
    if ask(f"Delete the Hive machine {what} and everything on it? Bring results back first with `hive cloud pull`. "
           "[y/N] > ").strip().lower() not in ('y', 'yes'):
        say('Kept.'); return 0
    p, r = m.get('profile'), m.get('region')
    if m.get('instance'):
        _aws(['ec2', 'terminate-instances', '--instance-ids', m['instance']], p, r, check=False)
        say(f"  Deleting {m['instance']}...")
        _aws(['ec2', 'wait', 'instance-terminated', '--instance-ids', m['instance']], p, r, check=False)
    if m.get('group'):
        _aws(['ec2', 'delete-security-group', '--group-id', m['group']], p, r, check=False)
    if m.get('key_name'):
        _aws(['ec2', 'delete-key-pair', '--key-name', m['key_name']], p, r, check=False)
    for f in (m.get('key'), os.path.join(HOME(), m['name'] + '.boot.sh'), STATE()):
        if f and os.path.exists(f):
            os.remove(f)
    cfg = os.path.join(os.path.expanduser('~'), '.hive', 'cloud.json')
    if os.path.exists(cfg) and json.load(open(cfg)).get('to', '').endswith(m.get('ip', '-')):
        os.remove(cfg)
    say("Deleted: the machine, its key and its firewall rule. Nothing is left running.")
    return 0
