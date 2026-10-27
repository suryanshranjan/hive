#!/bin/sh
# M4 acceptance test for the owner session, with a fake worker and a scripted owner (no tokens).
# usage: sh tests/test_owner.sh   (needs git, python3 and pytest; run from the hive repo root)
set -u
HIVE=$(pwd); T=$(mktemp -d); export PYTHONPATH=$HIVE
fail=0; check() { if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1 (got $2, expected $3)"; fail=1; fi; }
cd $T && git init -q -b main project && cd project && git config user.email t@t && git config user.name t
printf 'from fees import fee\ndef test_fee(): assert fee(10000, 2000) == 1200\n' > test_fees.py
python3 -m hive init --test-cmd "python3 -m pytest -q -p no:cacheprovider --junitxml=.hive/junit.xml" >/dev/null
python3 - <<'P'
import json; p = '.hive/config.json'; c = json.load(open(p)); c['areas'] = {'fees': ['test_fees*']}; json.dump(c, open(p, 'w'))
P
printf '__pycache__/\n' >> .gitignore; git add -A && git commit -qm "goal: fees"
printf -- '- fee(10000, 2000) -> 1200   (10%% of cash plus bonus)\n' > $T/examples.md
# the owner: answers the first question that appears, through the real `hive owner` loop
(sleep 8; echo "Negative amounts are invalid: raise ValueError."; sleep 30) | python3 -m hive owner --run $T/run > $T/owner.out 2>&1 &
OWNER=$!
HIVE_WORKER_CMD="sh $HIVE/tests/fake_asking_worker.sh" python3 -m hive run --repo $T/project --run $T/run --workers 1 \
  --goal "Implement creator fees (fees.py)." --examples $T/examples.md --questions 1 > $T/run.out 2>&1
check "hive run exits cleanly" $? 0
kill $OWNER 2>/dev/null
check "the owner's examples were in the worker's prompt" "$(cat $T/run/saw_examples 2>/dev/null)" ok
check "the worker got the owner's answer" "$(cat $T/run/got_answer)" "Negative amounts are invalid: raise ValueError."
check "the answer was recorded with its response time" "$(ls $T/run/owner/answers/*.json | wc -l)" 1
check "the second question was refused (budget 1)" "$(cat $T/run/second_ask_exit)" 3
git clone -q $T/run/up.git $T/result && cd $T/result && python3 -m pytest -q -p no:cacheprovider > /dev/null 2>&1
check "the answer became a passing test on the shared branch" "$?.$(ls test_fees_owner.py 2>/dev/null)" "0.test_fees_owner.py"
rm -rf $T; exit $fail
