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
if cmd == 'ec2 describe-instances' and 'terminate' in open(os.environ['FAKE_AWS_LOG']).read():
    print(json.dumps({'Reservations': [{'Instances': [{'PublicIpAddress': '203.0.113.9', 'State': {'Name': 'terminated'}}]}]}))
    sys.exit(0)
if cmd == 'configure get':
    print('ap-south-1')
elif cmd in replies:
    print(json.dumps(replies[cmd]))
