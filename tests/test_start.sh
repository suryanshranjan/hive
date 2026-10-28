#!/bin/sh
# hive start, end to end with stand-in builders (no tokens): one conversation from a goal to a tested branch.
# usage: sh tests/test_start.sh   (needs git, python3 and pytest; run from the hive repo root)
set -u
HIVE=$(pwd); T=$(mktemp -d); export PYTHONPATH=$HIVE HOME=$T HIVE_WORKER_CMD="sh $HIVE/tests/fake_assuming_worker.sh"
fail=0; check() { if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1 (got $2, expected $3)"; fail=1; fi; }
cd $T && git init -q -b main project && cd project && git config user.email t@t && git config user.name t
printf 'from fees import fee\ndef test_fee(): assert fee(10000, 2000) == 1200\n' > test_fees.py
printf 'from payouts import payout\ndef test_payout(): assert payout(10000, 2000) == 12000\n' > test_payouts.py
printf '__pycache__/\n.pytest_cache/\n' > .gitignore
git add -A && git commit -qm "tests for fees and payouts"; before=$(git rev-parse HEAD)
# the owner: types the goal, then corrects the one assumption in the review
printf 'Implement creator fees and payouts.\nNo: with no bonus, the fee is 10 percent of the cash.\n' | \
  python3 -m hive start --workers 2 > $T/out.txt 2>&1
check "hive exits cleanly" $? 0
check "it found the tests on its own" "$(grep -c 'Your tests: pytest. 2 tests, 0 passing' $T/out.txt)" 1
check "it narrated the builders' work" "$(grep -c 'landed: implement' $T/out.txt)" 3
check "it asked the owner about the assumption" "$(grep -c "assumption your description didn't cover" $T/out.txt)" 1
check "the correction went to a fix round" "$(grep -c 'Sending the builders back to fix 1 thing' $T/out.txt)" 1
check "the result is handed over as a branch" "$(git branch --list 'hive/*' | wc -l | tr -d ' ')" 1
check "the owner's branch was not touched" "$(git rev-parse main)" "$before"
git checkout -q $(git branch --list 'hive/*' | tr -d ' *') && python3 -m pytest -q -p no:cacheprovider >/dev/null 2>&1
check "the handed-over branch passes every test" $? 0
check "it reported every test passing" "$(grep -c '2 tests, all passing' $T/out.txt)" 1
# overnight: no questions, no review until morning; then `hive morning` reviews, fixes and updates the same branch
cd $T/project && git checkout -q main && git branch -D -q $(git branch --list 'hive/*' | tr -d ' *')
printf 'Implement creator fees and payouts.\n' | python3 -m hive start --workers 2 --overnight > $T/night.txt 2>&1
check "overnight run exits cleanly" $? 0
check "overnight run asks nothing and hands over a branch" "$(git branch --list 'hive/*' | wc -l | tr -d ' ')" 1
check "it tells the owner to come back with hive morning" "$(grep -c 'hive morning' $T/night.txt)" 1
night=$(git rev-parse $(git branch --list 'hive/*' | tr -d ' *'))
printf 'No: with no bonus, the fee is 10 percent of the cash.\n' | python3 -m hive morning > $T/morning.txt 2>&1
check "morning review exits cleanly" $? 0
check "morning greets and fixes the correction" "$(grep -c -e 'Welcome back' -e 'Sending the builders back to fix 1 thing' $T/morning.txt)" 2
[ "$(git rev-parse $(git branch --list 'hive/*' | tr -d ' *'))" != "$night" ]
check "the same branch was updated with the fix" $? 0
check "nothing is left for a second morning" "$(python3 -m hive morning | grep -c 'nothing left')" 1
rm -rf $T; exit $fail
