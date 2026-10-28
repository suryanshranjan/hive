#!/bin/sh
# hive cloud with a local folder standing in for the cloud machine (no network, no tokens).
# usage: sh tests/test_cloud.sh   (needs git and python3; run from the hive repo root)
set -u
python3 -c '' 2>/dev/null && PY=python3 || PY=python; export PY   # Windows has python, not python3
[ "$PY" = python ] && export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.autocrlf GIT_CONFIG_VALUE_0=false   # Windows: test repos keep LF
HIVE=$(pwd -W 2>/dev/null || pwd); T=$(mktemp -d); TW=$(cd "$T" && (pwd -W 2>/dev/null || pwd)); export PYTHONPATH=$HIVE HOME=$T USERPROFILE="$TW" T
fail=0; check() { if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1 (got $2, expected $3)"; fail=1; fi; }
cd "$T" || exit 1
git init -q -b main project && cd project && git config user.email t@t && git config user.name t
printf 'def test_one(): assert 1\n' > test_one.py && printf '.env\n' > .gitignore && git add -A && git commit -qm init
echo 'SECRET=do-not-send' > .env
$PY -c "from hive import memory; memory.add('.', 'A late post is paid in full.')"
mkdir -p $T/.hive && printf '{"token": "x", "chat_id": 1}' > $T/.hive/telegram.json
echo "# draft" >> test_one.py   # an edit to a tracked file: real unsaved work (untracked caches are ignored)
$PY -m hive cloud --to $T/box --no-start > $T/dirty.txt 2>&1
check "unsaved work is refused (only committed work goes)" "$(grep -c 'Commit them first' $T/dirty.txt)" 1
git checkout -q test_one.py
$PY -m hive cloud --to $T/box --no-start > $T/go.txt 2>&1
check "it reports success" "$?" 0
P=$T/box/hive-cloud/project
check "the project arrives on its branch" "$(git -C $P rev-parse --abbrev-ref HEAD)" main
check "the owner's rulings and Telegram link go with it" \
  "$(ls $T/box/hive-cloud/.hive/rules/*.json | wc -l | tr -d ' ') $(test -f $T/box/hive-cloud/.hive/telegram.json && echo yes)" "1 yes"
check ".env and the Claude login stay behind" "$(test -f $P/.env && echo sent || echo kept) $(test -d $T/box/hive-cloud/.claude && echo sent || echo kept)" "kept kept"
check "it says how to log in there" "$(grep -c 'run .claude. once' $T/go.txt)" 1
git -C $P checkout -q -b hive/refund-page && echo "x" > $P/refund.py && git -C $P add refund.py && git -C $P -c user.name=h -c user.email=h@h commit -qm "built in the cloud"
$PY -m hive cloud pull --from $T/box > $T/pull.txt 2>&1
check "pull brings the cloud's result branch back, without touching main" \
  "$(git branch --list 'hive/*' | tr -d ' ') $(git rev-parse --abbrev-ref HEAD)" "hive/refund-page main"
# one step: `hive cloud --new` makes a machine on the owner's AWS account (a stand-in aws; a local folder for the machine)
export HIVE_AWS="$PY $HIVE/tests/fake_aws.py"   # a stand-in aws, run by Python (Windows runs no shell scripts as programs)
export FAKE_AWS_LOG=$T/aws.log HIVE_NO_RELISTEN=1
printf '[["owner", "build: a ratings page"]]' > $T/.hive/conversation.json
HIVE_CLOUD_LOCAL=$T/box2 HIVE_MY_IP=198.51.100.7 $PY -m hive cloud --new --no-start > $T/new.txt 2>&1
check "--new makes the machine and moves the project there" "$? $(git -C $T/box2/hive-cloud/project rev-parse --abbrev-ref HEAD)" "0 main"
check "it says what it costs and how to delete it" "$(grep -c 'an hour while it runs). .hive cloud --stop. deletes it' $T/new.txt)" 1
check "only this machine's IP may log in, with a key kept private" \
  "$(grep -c 'authorize-security-group-ingress .*--cidr 198.51.100.7/32' $T/aws.log) $(stat -c %a $T/.hive/cloud/*.pem)" "1 600"
check "the machine sets itself up on first boot (Claude Code included)" \
  "$(grep -c 'run-instances .*--user-data file://' $T/aws.log) $(grep -c 'claude-code' $T/.hive/cloud/*.boot.sh)" "1 1"
printf 'n\n' | $PY -m hive cloud --stop > $T/keep.txt 2>&1
check "--stop asks first, and keeps the machine on no" "$(grep -c 'Kept.' $T/keep.txt) $(grep -c terminate $T/aws.log)" "1 0"
P2=$T/box2/hive-cloud/project
git -C $P2 checkout -q -b hive/ratings && echo x > $P2/ratings.py && git -C $P2 add ratings.py
git -C $P2 -c user.name=h -c user.email=h@h commit -qm "built in the cloud" && git -C $P2 checkout -q main
check "the conversation went to the cloud with Hive" "$(grep -c 'a ratings page' $T/box2/hive-cloud/.hive/conversation.json)" 1
$PY - <<'P'
import json, glob, os
T = os.environ['T']
r = glob.glob(T + '/box2/hive-cloud/.hive/rules/*.json')[0]; d = json.load(open(r))
d.append({'text': 'Ratings show after both sides review.', 'kind': 'owner', 'when': '2026-10-29', 'feature': ''})
json.dump(d, open(r, 'w'))
c = T + '/box2/hive-cloud/.hive/conversation.json'; h = json.load(open(c)); h.append(['owner', 'said in the cloud']); json.dump(h, open(c, 'w'))
P
printf 'y\n' | $PY -m hive cloud --stop > $T/stop.txt 2>&1
check "--stop brings the cloud's work back to this computer before deleting" "$(git branch --list 'hive/ratings' | tr -d ' *')" "hive/ratings"
check "and the rules and conversation from the cloud come home too"   "$($PY -m hive rules | grep -c 'Ratings show after both sides review') $(grep -c 'said in the cloud' $T/.hive/conversation.json)" "1 1"
check "--stop deletes the machine, its firewall rule and its key; nothing is left" \
  "$(grep -c 'terminate-instances --instance-ids i-0hive' $T/aws.log) $(grep -c 'delete-security-group --group-id sg-0hive' $T/aws.log) $(grep -c 'delete-key-pair' $T/aws.log) $(ls $T/.hive/cloud | wc -l | tr -d ' ')" "1 1 1 0"
rm -rf $T; exit $fail
