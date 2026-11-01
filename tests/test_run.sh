#!/bin/sh
# M3 acceptance test for hive run, with fake workers (no tokens): two workers build two areas of a goal.
# usage: sh tests/test_run.sh   (needs git, python3 and pytest; run from the hive repo root)
set -u
python3 -c '' 2>/dev/null && PY=python3 || PY=python; export PY   # Windows has python, not python3
[ "$PY" = python ] && export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.autocrlf GIT_CONFIG_VALUE_0=false   # Windows: test repos keep LF
HIVE=$(pwd -W 2>/dev/null || pwd); T=$(mktemp -d); TW=$(cd "$T" && (pwd -W 2>/dev/null || pwd)); export PYTHONPATH=$HIVE
fail=0; check() { if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1 (got $2, expected $3)"; fail=1; fi; }
cd "$T" || exit 1
git init -q -b main project && cd project && git config user.email t@t && git config user.name t
printf 'from fees import fee\ndef test_fee(): assert fee(10000, 2000) == 1200\n' > test_fees.py
printf 'from payouts import payout\ndef test_payout(): assert payout(10000, 2000) == 12000\n' > test_payouts.py
$PY -m hive init --test-cmd "$PY -m pytest -q -p no:cacheprovider --junitxml=.hive/junit.xml" >/dev/null
$PY - <<'P'
import json; p = '.hive/config.json'; c = json.load(open(p)); c['areas'] = {'fees': ['test_fees*'], 'payouts': ['test_payouts*']}; json.dump(c, open(p, 'w'))
P
git add -A && git commit -qm "goal: fees and payouts (tests only)"; before=$(git rev-parse HEAD)
HIVE_WORKER_CMD="sh $HIVE/tests/fake_worker.sh" $PY -m hive run --repo $T/project --run $T/run --workers 2 \
  --goal "Implement creator fees (10% of cash plus bonus) and payouts (creator gets 100%)." > $T/run.out 2>&1
check "hive run exits cleanly" $? 0
git clone -q $T/run/up.git $T/result && cd $T/result && $PY -m pytest -q -p no:cacheprovider > /dev/null 2>&1
check "the swarm's result passes every test" $? 0
check "both workers landed" "$(git log --format=%s | grep -c '^implement ')" 2
check "no lock left behind" "$(ls current_tasks/*.txt 2>/dev/null | wc -l)" 0
check "the source repository was never touched" "$(git -C $T/project rev-parse HEAD)" "$before"
check "cost logged for every worker" "$(tail -n +2 $T/run/agents.csv | wc -l)" 2
check "the phone's board of builders: each one's agent, finished, with its process recorded"   "$($PY -c "import json; b = json.load(open('$TW/run/builders.json')); print(sorted((k, v['agent'], v['state'], v['pid'] > 0) for k, v in b.items()))")"   "[('w1', 'custom', 'finished', True), ('w2', 'custom', 'finished', True)]"

# a usage limit mid-build: the worker waits for the reset, then picks up again in its own clone and finishes
HIVE_RESUME_MIN=1 HIVE_WORKER_CMD="sh $HIVE/tests/fake_limited_worker.sh" $PY -m hive run --repo $T/project \
  --run $T/run2 --workers 2 --goal "Implement creator fees and payouts." > $T/run2.out 2>&1
check "a run that hit the usage limit still exits cleanly" $? 0
check "it says when it will pick up again" "$(grep -c "usage limit was reached. I'll pick up again at" $T/run2.out)" 1
check "the stopped worker was told it is picking up again" "$(ls $T/run2/work/w1/.was_resumed 2>/dev/null | wc -l)" 1
check "both workers landed after the pause" "$(git -C $T/run2/up.git log --format=%s main | grep -c '^implement ')" 2
check "the cost of the stopped attempt is kept" "$(grep '^w1,' $T/run2/agents.csv | cut -d, -f8,10 | tr -d '\r')" "0.25,1"

# an expired login: it says to log in again, keeps trying, and carries on once it works
FAKE_STOP=auth HIVE_RESUME_MIN=1 HIVE_LOGIN_WAIT=1 HIVE_WORKER_CMD="sh $HIVE/tests/fake_limited_worker.sh" $PY -m hive run   --repo $T/project --run $T/run3 --workers 2 --goal "Implement creator fees and payouts." > $T/run3.out 2>&1
check "an expired login is not the end: it says so, then carries on"   "$? $(grep -c "login has expired. Run claude and log in again" $T/run3.out) $(git -C $T/run3/up.git log --format=%s main | grep -c '^implement ')" "0 1 2"
# Gate 74: with the owner there and 3 or more builders, one builder owns his decisions; the others build the rest
cd $T/project && $PY -c "from hive import swarm; swarm.prepare('$TW/project', '$TW/runsplit', 3, 'Implement creator fees.', 40, None, 30)"
check "the last builder owns the owner's decisions and asks him; the others build the rest and do not ask" \
  "$(grep -c 'Your role: the business builder' $T/runsplit/prompts/w3.md) $(grep -c 'Your role: build the rest' $T/runsplit/prompts/w1.md) $(grep -c 'hive ask' $T/runsplit/prompts/w1.md)" "1 1 0"
$PY -c "from hive import swarm; swarm.prepare('$TW/project', '$TW/runsolo', 2, 'Implement creator fees.', 40, None, 30)"
check "with 2 builders nobody is split" "$(grep -c 'Your role' $T/runsolo/prompts/w1.md $T/runsolo/prompts/w2.md | grep -c ':0')" 2
cd $T/project && $PY -c "from hive import swarm; swarm.prepare('$TW/project', '$TW/runnight', 3, 'Implement creator fees.', 40, None, 'later')"
check "overnight: no split unless HIVE_SPLIT_OVERNIGHT=1 (Gate 77, under test)" "$(grep -c 'Your role' $T/runnight/prompts/w3.md)" 0
cd $T/project && HIVE_SPLIT_OVERNIGHT=1 $PY -c "from hive import swarm; swarm.prepare('$TW/project', '$TW/runnight2', 3, 'Implement creator fees.', 40, None, 'later')"
check "overnight split: w3 records systematically, w1 records nothing" \
  "$(grep -c 'record his questions systematically' $T/runnight2/prompts/w3.md) $(grep -c 'Do not record questions yourself' $T/runnight2/prompts/w1.md) $(grep -c 'hive ask' $T/runnight2/prompts/w1.md)" "1 1 0"
rm -rf $T; exit $fail
