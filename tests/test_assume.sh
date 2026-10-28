#!/bin/sh
# The assumption review: workers record defaults in plain words, the owner marks the wrong ones (no tokens).
# usage: sh tests/test_assume.sh   (needs python3; run from the hive repo root)
set -u
python3 -c '' 2>/dev/null && PY=python3 || PY=python; export PY   # Windows has python, not python3
[ "$PY" = python ] && export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.autocrlf GIT_CONFIG_VALUE_0=false   # Windows: test repos keep LF
HIVE=$(pwd -W 2>/dev/null || pwd); T=$(mktemp -d); TW=$(cd "$T" && (pwd -W 2>/dev/null || pwd)); export PYTHONPATH=$HIVE HIVE_RUN=$T/run HIVE_WORKER=w2
fail=0; check() { if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1 (got $2, expected $3)"; fail=1; fi; }
$PY -c "from hive import owner; t = owner.setup('$T/run', None, 0, True); assert 'hive assume' in t and 'hive ask' not in t"
check "setup tells workers to record assumptions, and not to ask when the budget is 0" $? 0
$PY -m hive assume "If a creator has not entered their city, they are still shown for campaigns that require a city." >/dev/null
check "a plain assumption is recorded" $? 0
$PY -m hive assume "If creator.city is null, hardGates() returns eligible: true." >/dev/null
check "a code-worded assumption is refused" $? 5
$PY -m hive assume "If a deal is cut by Rs 500, both sides must accept again." >/dev/null
check "a second plain assumption is recorded" $? 0
$PY -m hive assume --technical "termsChange() throws TypeError when cashPaise is not a BigInt." >/dev/null
check "a technical choice is recorded for engineers, code words allowed" $? 0
check "workers can list them" "$($PY -m hive assumptions | grep -c '^- (w2)')" 3
$PY -c "from hive import owner; t = owner.setup('$T/run2', None, 5, True); assert 'beyond the one asked' in t"
check "with questions on, workers must record any answer they stretch" $? 0
printf 'No, a creator without a city is left out when a city is required.\n\n' | $PY -m hive review --run $T/run > $T/review.out 2>&1
check "review exits cleanly" $? 0
check "one correction, one kept" "$(grep -c 'The owner says' $T/run/owner/corrections.md)" 1
check "the correction carries the owner's words" "$(grep -c 'left out when a city is required' $T/run/owner/corrections.md)" 1
check "only the two business defaults reached the owner" "$(ls $T/run/owner/reviews | wc -l | tr -d ' ')" 2
check "the technical choice went to the engineers' list" "$(grep -c 'TypeError' $T/run/owner/technical_assumptions.md)" 1
# undo: the owner keeps #1, then types undo at #2, changes #1, and keeps #2
export HIVE_RUN=$T/run3
$PY -m hive assume "If a creator has no city, they are still shown." >/dev/null; sleep 0.01
$PY -m hive assume "If a deal is cut by Rs 500, both must accept again." >/dev/null
printf '
undo
No, leave them out.

' | $PY -m hive review --run $T/run3 > $T/undo.out 2>&1
check "undo brings the last decision back" "$(grep -c 'Here it is again' $T/undo.out)" 1
check "the changed answer replaced the first one" "$(grep -c 'leave them out' $T/run3/owner/corrections.md)" 1
rm -rf $T; exit $fail
