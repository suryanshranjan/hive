#!/bin/sh
# M3 acceptance test for hive run, with fake workers (no tokens): two workers build two areas of a goal.
# usage: sh tests/test_run.sh   (needs git, python3 and pytest; run from the hive repo root)
set -u
HIVE=$(pwd); T=$(mktemp -d); export PYTHONPATH=$HIVE
fail=0; check() { if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1 (got $2, expected $3)"; fail=1; fi; }
cd $T && git init -q -b main project && cd project && git config user.email t@t && git config user.name t
printf 'from fees import fee\ndef test_fee(): assert fee(10000, 2000) == 1200\n' > test_fees.py
printf 'from payouts import payout\ndef test_payout(): assert payout(10000, 2000) == 12000\n' > test_payouts.py
python3 -m hive init --test-cmd "python3 -m pytest -q -p no:cacheprovider --junitxml=.hive/junit.xml" >/dev/null
python3 - <<'P'
import json; p = '.hive/config.json'; c = json.load(open(p)); c['areas'] = {'fees': ['test_fees*'], 'payouts': ['test_payouts*']}; json.dump(c, open(p, 'w'))
P
git add -A && git commit -qm "goal: fees and payouts (tests only)"; before=$(git rev-parse HEAD)
HIVE_WORKER_CMD="sh $HIVE/tests/fake_worker.sh" python3 -m hive run --repo $T/project --run $T/run --workers 2 \
  --goal "Implement creator fees (10% of cash plus bonus) and payouts (creator gets 100%)." > $T/run.out 2>&1
check "hive run exits cleanly" $? 0
git clone -q $T/run/up.git $T/result && cd $T/result && python3 -m pytest -q -p no:cacheprovider > /dev/null 2>&1
check "the swarm's result passes every test" $? 0
check "both workers landed" "$(git log --format=%s | grep -c '^implement ')" 2
check "no lock left behind" "$(ls current_tasks/*.txt 2>/dev/null | wc -l)" 0
check "the source repository was never touched" "$(git -C $T/project rev-parse HEAD)" "$before"
check "cost logged for every worker" "$(tail -n +2 $T/run/agents.csv | wc -l)" 2

# a usage limit mid-build: the worker waits for the reset, then picks up again in its own clone and finishes
HIVE_RESUME_MIN=1 HIVE_WORKER_CMD="sh $HIVE/tests/fake_limited_worker.sh" python3 -m hive run --repo $T/project \
  --run $T/run2 --workers 2 --goal "Implement creator fees and payouts." > $T/run2.out 2>&1
check "a run that hit the usage limit still exits cleanly" $? 0
check "it says when it will pick up again" "$(grep -c "usage limit was reached. I'll pick up again at" $T/run2.out)" 1
check "the stopped worker was told it is picking up again" "$(ls $T/run2/work/w1/.was_resumed 2>/dev/null | wc -l)" 1
check "both workers landed after the pause" "$(git -C $T/run2/up.git log --format=%s main | grep -c '^implement ')" 2
check "the cost of the stopped attempt is kept" "$(grep '^w1,' $T/run2/agents.csv | cut -d, -f7,9 | tr -d '\r')" "0.25,1"
rm -rf $T; exit $fail
