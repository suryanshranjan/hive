#!/bin/sh
# Builders in the sandbox (hive/sandbox.py), for real when Docker runs here: two stand-in builders, each in its own
# container, claim, build and land through the guard; they see the run folder but not ~/.hive. No tokens.
# usage: sh tests/test_sandbox.sh   (needs Docker running; skips otherwise)
set -u
python3 -c '' 2>/dev/null && PY=python3 || PY=python; export PY
[ "$PY" = python ] && export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.autocrlf GIT_CONFIG_VALUE_0=false
HIVE=$(pwd -W 2>/dev/null || pwd); T=$(mktemp -d); TW=$(cd "$T" && (pwd -W 2>/dev/null || pwd)); export PYTHONPATH=$HIVE HOME=$T USERPROFILE=$TW
fail=0; check() { if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1 (got $2, expected $3)"; fail=1; fi; }
if ! docker info >/dev/null 2>&1; then echo "skip: Docker is not running here"; rm -rf $T; exit 0; fi
mkdir -p $T/.hive && echo '{"token": "BOT-TOKEN-NOT-FOR-BUILDERS", "chat_id": 1}' > $T/.hive/telegram.json
cd "$T" && git init -q -b main project && cd project && git config user.email t@t && git config user.name t
printf 'from fees import fee\ndef test_fee(): assert fee(10000, 2000) == 1200\n' > test_fees.py
printf 'from payouts import payout\ndef test_payout(): assert payout(10000, 2000) == 12000\n' > test_payouts.py
$PY -m hive init --test-cmd "python3 -m pytest -q -p no:cacheprovider --junitxml=.hive/junit.xml" >/dev/null
$PY - <<'P'
import json; p = '.hive/config.json'; c = json.load(open(p)); c['areas'] = {'fees': ['test_fees*'], 'payouts': ['test_payouts*']}; json.dump(c, open(p, 'w'))
P
git add -A && git commit -qm "goal: fees and payouts (tests only)"
# the stand-in builder also tries to read his keys: in the sandbox there is nothing there
W='{ cat $HOME/.hive/telegram.json; cat /data/home/.hive/telegram.json; echo "$TELEGRAM_BOT_TOKEN"; env; } > leak_$HIVE_WORKER.txt 2>/dev/null; sh /opt/hive/tests/fake_worker.sh'
TELEGRAM_BOT_TOKEN=BOT-TOKEN-NOT-FOR-BUILDERS HIVE_SANDBOX=docker HIVE_SANDBOX_CUSTOM=1 HIVE_WORKER_CMD="$W" \
  $PY -m hive run --repo $T/project --run $T/run --workers 2 --goal "Implement fees and payouts." > $T/run.out 2>&1
check "the run finishes in the sandbox" "$? $(grep -c 'Builders run in a sandbox' $T/run.out)" "0 1"
git clone -q $T/run/up.git $T/result && cd $T/result
check "both builders landed from their containers" "$(git log --format=%s | grep -c '^implement ')" 2
check "the result passes every test" "$($PY -m pytest -q -p no:cacheprovider >/dev/null 2>&1; echo $?)" 0
check "his bot token never reached a builder (not in its files, not in its environment)"   "$(ls $T/run/work/w*/leak_w*.txt | wc -l | tr -d ' ') $(cat $T/run/work/w*/leak_w*.txt | grep -c BOT-TOKEN)" "2 0"
check "the board names each builder's container" "$($PY -c "import json; print(all(v.get('container', '').startswith('hive-') for v in json.load(open('$TW/run/builders.json')).values()))")" True
PFX=$($PY -c "from hive import sandbox; print(sandbox.name('$TW/run', ''))")   # this run's containers only (other runs may be going)
check "no container left running" "$(docker ps -q --filter name=$PFX | wc -l | tr -d ' ')" 0
check "the copies of the agents' logins are gone" "$(test -d $T/run/.logins && echo kept || echo gone)" gone
# A project whose tests cannot run in the image is refused in both modes.
cd $T/project && $PY -m hive init --test-cmd "no-such-tool --junit .hive/junit.xml" >/dev/null 2>&1; git commit -qam "a tool the image lacks"
HIVE_SANDBOX=docker HIVE_SANDBOX_CUSTOM=1 HIVE_WORKER_CMD="true" $PY -m hive run --repo $T/project --run $T/run2 --workers 1 --goal x > $T/run2.out 2>&1
check "required sandbox, tests can't run there: refused with the reason" "$? $(grep -c "tests don't run in the sandbox" $T/run2.out)" "1 1"
HIVE_SANDBOX_CUSTOM=1 HIVE_WORKER_CMD="true" $PY -m hive run --repo $T/project --run $T/run3 --workers 1 --goal x > $T/run3.out 2>&1
check "auto: no unsafe fallback when tests cannot run in the sandbox" "$? $(grep -c "tests don't run in the sandbox" $T/run3.out)" "1 1"
cd / && rm -rf $T; exit $fail
