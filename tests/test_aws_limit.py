"""A limited AWS login for Hive, with a stand-in AWS command line (no account, no cost): signed in as root, Hive says so
plainly; `hive cloud --limit` makes the user hive-builder with only Hive's rights, saves it as the profile 'hive', and
every later AWS call uses it. The policy only reaches resources tagged hive.
usage: python3 tests/test_aws_limit.py   (run from the hive repo root)"""
import json, os, sys, tempfile
sys.path.insert(0, os.getcwd())
home = tempfile.mkdtemp()
os.environ['HOME'] = os.environ['USERPROFILE'] = home
log = os.path.join(home, 'aws.log'); open(log, 'w').close()
os.environ['FAKE_AWS_LOG'] = log
os.environ['HIVE_AWS'] = f'"{sys.executable}" "{os.path.join(os.getcwd(), "tests", "fake_aws.py")}"'
os.environ.pop('HIVE_AWS_PROFILE', None)
from hive import cloud_aws

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))
calls = lambda: open(log).read().splitlines()

# 1. the policy: everything that changes or deletes is limited to Hive's tagged things; no IAM, no other service
pol = cloud_aws.POLICY['Statement']
acts = [a for s in pol for a in (s['Action'] if isinstance(s['Action'], list) else [s['Action']])]
check('policy: no IAM, S3 or wildcard rights', [a for a in acts if a.startswith(('iam:', 's3:')) or '*' in a], [])
destroy = next(s for s in pol if s['Sid'] == 'OnlyOurs')
check('policy: delete/stop only tagged hive', ('ec2:TerminateInstances' in destroy['Action'], destroy['Condition']),
      (True, {'Null': {'aws:ResourceTag/hive': 'false'}}))
run = next(s for s in pol if s['Sid'] == 'RunSmallTagged')
check('policy: machines only tagged, only the sizes Hive offers', run['Condition']['StringLike']['ec2:InstanceType'],
      ['t3.*', 'm7i.large', 'm7i.xlarge'])
for size in cloud_aws.PRICE:
    if not (size.startswith('t3.') or size in ('m7i.large', 'm7i.xlarge')):
        check(f'policy covers the offered size {size}', False, True)

# 2. root: said plainly, before anything is made
os.environ['FAKE_AWS_ROOT'] = '1'
check('root: recognised', cloud_aws.is_root(cloud_aws._aws(['sts', 'get-caller-identity'])), True)
check('a user: not root', cloud_aws.is_root({'Arn': 'arn:aws:iam::1:user/x'}), False)

# 3. --limit: asks first; "no" makes nothing
said = []
check('limit: no means nothing', cloud_aws.limit(say=said.append, ask=lambda q: 'no'), 1)
check('limit: no IAM call after a no', [c for c in calls() if c.startswith('iam')], [])

# 4. --limit: yes makes the user, its rights and key, and switches Hive to it
os.environ['FAKE_AWS_OLDKEY'] = '1'
open(log, 'w').close()
check('limit: yes', cloud_aws.limit(say=said.append, ask=lambda q: 'yes'), 0)
c = calls()
check('limit: user made', any(x.startswith('iam create-user --user-name hive-builder') for x in c), True)
check('limit: rights attached', any(x.startswith('iam put-user-policy --user-name hive-builder --policy-name hive-only') for x in c), True)
check('limit: old key retired', any(x.startswith('iam delete-access-key') and 'AKIAOLD' in x for x in c), True)
check('limit: key saved to profile hive', sorted(x.split()[2] for x in c if x.startswith('configure set') and '--profile hive' in x),
      ['aws_access_key_id', 'aws_secret_access_key', 'region'])
check('limit: secret never in Hive\'s files', 'secret-new' in open(cloud_aws.LIMITED()).read(), False)
check('limit: Hive now uses it', cloud_aws.default_profile(), 'hive')
n = len(calls())
who = cloud_aws._aws(['sts', 'get-caller-identity'])
check('later calls: as hive-builder', (who['Arn'].endswith('/hive-builder'), '--profile hive' in calls()[n]), (True, True))
check('later calls: not root', cloud_aws.is_root(who), False)

# 5. run twice: the user is reused, not made again
before = len(calls())
cloud_aws.limit(say=said.append, ask=lambda q: 'yes')
check('again: no second user', any(x.startswith('iam create-user') for x in calls()[before:]), False)
check("again: run with the CLI's own login, not the limited one", all('--profile hive' not in x for x in calls()[before:]
      if x.startswith('iam')), True)
print('     ' + said[-1])
sys.exit(fail)
