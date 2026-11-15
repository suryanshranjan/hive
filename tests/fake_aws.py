"""A stand-in for the AWS command line (no account, no cost): records each call, replies like AWS would."""
import json, os, sys

args = sys.argv[1:]
open(os.environ['FAKE_AWS_LOG'], 'a').write(' '.join(args) + '\n')
cmd = ' '.join(a for a in args[:2])
replies = {
    'sts get-caller-identity': {'Account': '123456789012'},
    'ec2 create-key-pair': {'KeyMaterial': '-----BEGIN OPENSSH PRIVATE KEY-----\nstand-in\n-----END OPENSSH PRIVATE KEY-----\n'},
    'ec2 create-security-group': {'GroupId': 'sg-0hive'},
    'ssm get-parameter': {'Parameter': {'Value': 'ami-0ubuntu'}},
    'ec2 run-instances': {'Instances': [{'InstanceId': 'i-0hive'}]},
    'ec2 describe-instances': {'Reservations': [{'Instances': [{'PublicIpAddress': '203.0.113.9'}]}]},
}
if os.environ.get('FAKE_AWS_EXPIRED') and cmd != 'configure get':   # expired credentials: every call fails
    sys.stderr.write('An error occurred (ExpiredToken): The security token included in the request is expired\n')
    sys.exit(255)
if cmd == 'ec2 describe-instances' and os.environ.get('FAKE_AWS_STOPPED') and 'start-instances' not in open(os.environ['FAKE_AWS_LOG']).read():
    print(json.dumps({'Reservations': [{'Instances': [{'State': {'Name': 'stopped'}}]}]}))   # powered off from the phone
    sys.exit(0)
if cmd == 'ec2 describe-instances' and 'terminate' in open(os.environ['FAKE_AWS_LOG']).read():
    print(json.dumps({'Reservations': [{'Instances': [{'PublicIpAddress': '203.0.113.9', 'State': {'Name': 'terminated'}}]}]}))
    sys.exit(0)
if cmd == 'sts get-caller-identity':   # who is signed in: the limited user under --profile hive, else root or a user
    prof = args[args.index('--profile') + 1] if '--profile' in args else ''
    arn = ('arn:aws:iam::123456789012:user/hive-builder' if prof == 'hive' else
           'arn:aws:iam::123456789012:root' if os.environ.get('FAKE_AWS_ROOT') else 'arn:aws:iam::123456789012:user/owner')
    print(json.dumps({'Account': '123456789012', 'Arn': arn})); sys.exit(0)
if cmd == 'iam get-user' and 'iam create-user' not in open(os.environ['FAKE_AWS_LOG']).read():
    sys.stderr.write('An error occurred (NoSuchEntity): The user with name hive-builder cannot be found.\n'); sys.exit(254)
if cmd == 'iam list-access-keys':
    print(json.dumps({'AccessKeyMetadata': [{'AccessKeyId': 'AKIAOLD'}] if os.environ.get('FAKE_AWS_OLDKEY') else []})); sys.exit(0)
if cmd == 'iam create-access-key':
    print(json.dumps({'AccessKey': {'AccessKeyId': 'AKIANEW', 'SecretAccessKey': 'secret-new'}})); sys.exit(0)
if cmd == 'configure get':
    print('ap-south-1')
elif cmd in replies:
    print(json.dumps(replies[cmd]))
