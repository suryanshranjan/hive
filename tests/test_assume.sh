#!/bin/sh
# The assumption review: workers record defaults in plain words, the owner marks the wrong ones (no tokens).
# usage: sh tests/test_assume.sh   (needs python3; run from the hive repo root)
set -u
HIVE=$(pwd); T=$(mktemp -d); export PYTHONPATH=$HIVE HIVE_RUN=$T/run HIVE_WORKER=w2
fail=0; check() { if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1 (got $2, expected $3)"; fail=1; fi; }
python3 -c "from hive import owner; t = owner.setup('$T/run', None, 0, True); assert 'hive assume' in t and 'hive ask' not in t"
check "setup tells workers to record assumptions, and not to ask when the budget is 0" $? 0
python3 -m hive assume "If a creator has not entered their city, they are still shown for campaigns that require a city." >/dev/null
check "a plain assumption is recorded" $? 0
python3 -m hive assume "If creator.city is null, hardGates() returns eligible: true." >/dev/null
check "a code-worded assumption is refused" $? 5
python3 -m hive assume "If a deal is cut by Rs 500, both sides must accept again." >/dev/null
check "a second plain assumption is recorded" $? 0
check "workers can list them" "$(python3 -m hive assumptions | grep -c '^- (w2)')" 2
printf 'No, a creator without a city is left out when a city is required.\n\n' | python3 -m hive review --run $T/run > $T/review.out 2>&1
check "review exits cleanly" $? 0
check "one correction, one kept" "$(grep -c 'The owner says' $T/run/owner/corrections.md)" 1
check "the correction carries the owner's words" "$(grep -c 'left out when a city is required' $T/run/owner/corrections.md)" 1
check "both reviews are recorded" "$(ls $T/run/owner/reviews | wc -l | tr -d ' ')" 2
rm -rf $T; exit $fail
