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
import json, os, re, shlex, subprocess, time, urllib.request

from . import cloud, memory

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
    cmd = shlex.split(AWS) + args + ['--output', 'json'] + (['--profile', profile] if profile else []) + (['--region', region] if region else [])
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
    region = region or subprocess.run(shlex.split(AWS) + ['configure', 'get', 'region'] + (['--profile', profile] if profile else []),
                                      capture_output=True, text=True).stdout.strip() or 'ap-south-1'
    slug = re.sub(r'[^a-z0-9]+', '-', (memory.project_name(repo) or cloud._project(repo)).lower()).strip('-')[:30] or 'project'
    name = f"hive-{slug}-{int(time.time()) % 100000}"   # named after his startup in the AWS console
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
        if os.name == 'nt':   # chmod does nothing on Windows, and Windows' ssh refuses a key others can read
            user = os.environ.get('USERNAME', '')
            subprocess.run(['icacls', m['key'], '/inheritance:r', '/grant:r', f'{user}:F'], capture_output=True)
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

MARK = os.environ.get('HIVE_CLOUD_MARK', '/var/lib/hive-ready')   # made by FIRST_BOOT: this is a machine --new made
SHUTDOWN = os.environ.get('HIVE_SHUTDOWN_CMD', 'sudo shutdown -h +1')   # a minute's grace: the phone gets its reply first

def power_off_here(ask=input, say=print):
    """From the phone, on the cloud machine itself. It holds no AWS keys (on purpose), so it cannot delete itself; but it
    can power itself off. That ends the hourly bill, and its disk keeps every branch until his computer's
    `hive cloud --stop` starts it again, brings everything home and deletes it (the owner: delete it from the phone,
    and no development may be lost). Returns 9 when powering off, 8 mid-build, 5 when this is not such a machine."""
    if not os.path.exists(MARK):
        say("There is no Hive machine made from this computer to delete."); return 5
    if subprocess.run("pgrep -f '[h]ive start' >/dev/null", shell=True).returncode == 0:
        say('A build is still running here: powering off now would lose it. Wait for it, or stop it first.'); return 8
    if ask("Power this cloud machine off? Its disk keeps everything until your computer's `hive cloud --stop` brings it "
           "home and deletes it. [y/N] > ").strip().lower() not in ('y', 'yes'):
        say('Kept.'); return 0
    if subprocess.run(SHUTDOWN, shell=True).returncode != 0:
        say('I could not power this machine off.'); return 7
    say('Powering off in a minute. Its disk keeps everything; on your computer, `hive cloud --stop` brings it home '
        'and deletes the machine.')
    return 9

def _wake(m, say=print):
    """A machine powered off from the phone is started again, so its work can come home before it is deleted."""
    p, r = m.get('profile'), m.get('region')
    st = _aws(['ec2', 'describe-instances', '--instance-ids', m['instance']], p, r, check=False)
    inst = (st.get('Reservations') or [{}])[0].get('Instances', [{}])[0]
    state = inst.get('State', {}).get('Name')
    if state not in ('stopped', 'stopping'):
        return
    say('  It was powered off from your phone; starting it again to bring its work home (about a minute)...')
    if state == 'stopping':
        _aws(['ec2', 'wait', 'instance-stopped', '--instance-ids', m['instance']], p, r)
    _aws(['ec2', 'start-instances', '--instance-ids', m['instance']], p, r)
    _aws(['ec2', 'wait', 'instance-running', '--instance-ids', m['instance']], p, r)
    desc = _aws(['ec2', 'describe-instances', '--instance-ids', m['instance']], p, r)
    old, m['ip'] = m.get('ip'), desc['Reservations'][0]['Instances'][0]['PublicIpAddress']   # new address after a restart
    json.dump(m, open(STATE(), 'w'), indent=1)
    cfg = os.path.join(os.path.expanduser('~'), '.hive', 'cloud.json')
    if os.path.exists(cfg) and old and json.load(open(cfg)).get('to', '').endswith('@' + old):   # only where it pointed there
        c = json.load(open(cfg)); c['to'] = f"ubuntu@{m['ip']}"; json.dump(c, open(cfg, 'w'), indent=1)
    if not os.environ.get('HIVE_CLOUD_LOCAL'):
        t = cloud.Target(f"ubuntu@{m['ip']}", m.get('key'))
        for _ in range(30):
            if t.run('true', check=False).returncode == 0:
                break
            time.sleep(5)

def stop(ask=input, say=print, repo='.', relisten=True):
    """Bring the work done in the cloud back to this computer, then delete the machine `hive cloud --new` made, with its
    key and firewall rule (the owner: "when we close the instance, the development must come back to local")."""
    if not os.path.exists(STATE()):   # e.g. asked on the cloud machine itself, which never holds the owner's AWS keys
        return power_off_here(ask, say)
    m = json.load(open(STATE()))
    what = m.get('instance') or m.get('name')
    if ask(f"Delete the Hive machine {what}? Everything built there comes back to this computer first. [y/N] > "
           ).strip().lower() not in ('y', 'yes'):
        say('Kept.'); return 0
    if m.get('instance') and m.get('ip'):
        try:
            _wake(m, say)
        except Exception as e:
            say(f"  I could not start it again to bring its work home ({e}); I kept it. Check your AWS login (aws login), "
                "then run `hive cloud --stop` again."); return 7
    if m.get('ip') and os.path.isdir(os.path.join(repo, '.git')):   # nothing built there may be lost (the owner)
        local = os.environ.get('HIVE_CLOUD_LOCAL')
        t = cloud.Target(local or f"ubuntu@{m['ip']}", None if local else m.get('key'))
        if cloud.building(t):   # a build still running there: never delete it mid-way
            say('A build is still running there. I kept the machine: wait for it to finish (I will tell you), or stop it '
                'with "stop the build", then run `hive cloud --stop` again.'); return 8
        say('  Bringing everything back first (every branch, the build records, your rules and our conversation)...')
        if cloud.pull(repo, say=say, verify=True) != 0:
            if ask("  Not everything came back, so the machine is kept. To delete it anyway and LOSE that work, type "
                   "DELETE > ").strip() != 'DELETE':
                say('Kept. Run `hive cloud pull` to try again, then `hive cloud --stop`.'); return 6
        if _on_github(repo) and ask("  Also push the result branches (hive/...) to your GitHub, as a second copy? [y/N] > "
                                   ).strip().lower() in ('y', 'yes'):
            r = subprocess.run(['git', '-C', repo, 'push', '-q', 'origin', 'refs/heads/hive/*:refs/heads/hive/*'],
                               capture_output=True, text=True)
            say('  Pushed the result branches to GitHub.' if r.returncode == 0 else
                f"  Could not push to GitHub ({r.stderr.strip()[:200]}); your copy here is complete anyway.")
    p, r = m.get('profile'), m.get('region')
    failed = []   # every step is checked: --stop once said "Deleted" while expired credentials had deleted nothing
    if m.get('instance'):
        say(f"  Deleting {m['instance']}...")
        try:
            _aws(['ec2', 'terminate-instances', '--instance-ids', m['instance']], p, r)
            _aws(['ec2', 'wait', 'instance-terminated', '--instance-ids', m['instance']], p, r)
            state = _aws(['ec2', 'describe-instances', '--instance-ids', m['instance']], p, r)
            gone = state.get('Reservations', [{}])[0].get('Instances', [{}])[0].get('State', {}).get('Name') == 'terminated'
            if not gone and state:
                failed.append(f"the machine {m['instance']} is not terminated yet")
        except Exception as e:
            failed.append(f"the machine {m['instance']}: {e}")
    if m.get('group') and not failed:   # the firewall rule can only go once the machine is gone
        try:
            _aws(['ec2', 'delete-security-group', '--group-id', m['group']], p, r)
        except Exception as e:
            failed.append(f"the firewall rule {m['group']}: {e}")
    if m.get('key_name') and not failed:
        try:
            _aws(['ec2', 'delete-key-pair', '--key-name', m['key_name']], p, r)
        except Exception as e:
            failed.append(f"the key {m['key_name']}: {e}")
    if failed:   # keep the record, so --stop can be run again; never claim what did not happen
        say("I could NOT delete everything, so it may still be running and billing:\n  - " + '\n  - '.join(failed) +
            "\nCheck your AWS login (aws login), then run `hive cloud --stop` again.")
        return 7
    for f in (m.get('key'), os.path.join(HOME(), m['name'] + '.boot.sh'), STATE()):
        if f and os.path.exists(f):
            os.remove(f)
    cfg = os.path.join(os.path.expanduser('~'), '.hive', 'cloud.json')
    if os.path.exists(cfg) and json.load(open(cfg)).get('to', '').endswith(m.get('ip', '-')):
        os.remove(cfg)
    say("Deleted: the machine, its key and its firewall rule. Nothing is left running.")
    if relisten:
        _home(repo, say)
    return 0

def _home(repo, say=print):
    """Hive is back on this computer: start listening on his Telegram again and tell him, so his phone has no gap."""
    from . import telegram
    cfg = telegram.load()
    if not cfg or os.environ.get('HIVE_NO_RELISTEN'):
        return
    import sys
    log = os.path.join(os.path.expanduser('~'), '.hive', 'listen.log')
    kw = {'creationflags': 0x00000008 | 0x00000200} if os.name == 'nt' else {'start_new_session': True}   # outlives this
    subprocess.Popen([sys.executable, '-m', 'hive', 'listen'], cwd=os.path.abspath(repo), stdout=open(log, 'a'),
                     stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, **kw)
    say("Hive is back on this computer and listening on your Telegram (log: ~/.hive/listen.log).")
    try:
        telegram.Channel(cfg).send("🏠 <b>I'm back on your computer.</b> Everything built in the cloud is here, and so "
                                   "is our conversation. Carry on whenever you like.", html=True)
    except Exception:
        pass

def _on_github(repo):
    """True when the project's origin is on GitHub (then the results can be pushed there as a second copy)."""
    url = subprocess.run(['git', '-C', repo, 'remote', 'get-url', 'origin'], capture_output=True, text=True).stdout
    return 'github.com' in url
