#!/bin/sh
# hive cloud with a local folder standing in for the cloud machine (no network, no tokens).
# usage: sh tests/test_cloud.sh   (needs git and python3; run from the hive repo root)
set -u
HIVE=$(pwd); T=$(mktemp -d); export PYTHONPATH=$HIVE HOME=$T
fail=0; check() { if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1 (got $2, expected $3)"; fail=1; fi; }
cd $T && git init -q -b main project && cd project && git config user.email t@t && git config user.name t
printf 'def test_one(): assert 1\n' > test_one.py && printf '.env\n' > .gitignore && git add -A && git commit -qm init
echo 'SECRET=do-not-send' > .env
python3 -c "from hive import memory; memory.add('.', 'A late post is paid in full.')"
mkdir -p $T/.hive && printf '{"token": "x", "chat_id": 1}' > $T/.hive/telegram.json
echo "draft" > notes.txt
python3 -m hive cloud --to $T/box --no-start > $T/dirty.txt 2>&1
check "unsaved work is refused (only committed work goes)" "$(grep -c 'Commit them first' $T/dirty.txt)" 1
rm notes.txt
python3 -m hive cloud --to $T/box --no-start > $T/go.txt 2>&1
check "it reports success" "$?" 0
P=$T/box/hive-cloud/project
check "the project arrives on its branch" "$(git -C $P rev-parse --abbrev-ref HEAD)" main
check "the owner's rulings and Telegram link go with it" \
  "$(ls $T/box/hive-cloud/.hive/rules/*.json | wc -l | tr -d ' ') $(test -f $T/box/hive-cloud/.hive/telegram.json && echo yes)" "1 yes"
check ".env and the Claude login stay behind" "$(test -f $P/.env && echo sent || echo kept) $(test -d $T/box/hive-cloud/.claude && echo sent || echo kept)" "kept kept"
check "it says how to log in there" "$(grep -c 'run .claude. once' $T/go.txt)" 1
git -C $P checkout -q -b hive/refund-page && echo "x" > $P/refund.py && git -C $P add refund.py && git -C $P -c user.name=h -c user.email=h@h commit -qm "built in the cloud"
python3 -m hive cloud pull --from $T/box > $T/pull.txt 2>&1
check "pull brings the cloud's result branch back, without touching main" \
  "$(git branch --list 'hive/*' | tr -d ' ') $(git rev-parse --abbrev-ref HEAD)" "hive/refund-page main"
rm -rf $T; exit $fail
