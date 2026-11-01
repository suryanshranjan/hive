#!/bin/sh
# M2 acceptance test for hive's area claims, on a throwaway repository with two areas.
# usage: sh tests/test_claims.sh   (needs git, python3 and pytest; run from the hive repo root)
set -u
python3 -c '' 2>/dev/null && PY=python3 || PY=python; export PY   # Windows has python, not python3
[ "$PY" = python ] && export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.autocrlf GIT_CONFIG_VALUE_0=false   # Windows: test repos keep LF
HIVE=$(pwd -W 2>/dev/null || pwd); T=$(mktemp -d); TW=$(cd "$T" && (pwd -W 2>/dev/null || pwd)); export HIVE_GUARD_CACHE=$T/cache; export PYTHONPATH=$HIVE
fail=0; check() { if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1 (exit $2, expected $3)"; fail=1; fi; }
cd "$T" || exit 1
git init -q -b main seed && cd seed && git config user.email t@t && git config user.name t
echo "def fee(x): return x // 10" > fees.py && echo "from fees import fee
def test_fee(): assert fee(100) == 10" > test_fees.py
$PY -m hive init --test-cmd "$PY -m pytest -q -p no:cacheprovider --junitxml=.hive/junit.xml" >/dev/null
$PY - <<'P'
import json; p = '.hive/config.json'; c = json.load(open(p)); c['areas'] = {'fees': ['test_fees*'], 'payouts': ['test_payouts*'], 'refunds': ['test_refunds*']}; json.dump(c, open(p, 'w'))
P
printf '__pycache__/\n' >> .gitignore; git add -A && git commit -qm seed && git clone -q --bare . $T/up.git && cd $T
for w in a b c; do git clone -q up.git $w; git -C $w config user.email $w@t; git -C $w config user.name $w; done
cd $T/a && $PY -m hive claim fa fees "fee rules" >/dev/null; check "first claim on an area succeeds" $? 0
cd $T/b && $PY -m hive claim fb fees,payouts "fees again" >/dev/null; check "overlapping claim refused" $? 1
cd $T/b && $PY -m hive claim pb payouts "payout rules" >/dev/null; check "claim on a free area succeeds" $? 0
cd $T/c && $PY -m hive claim zz chargebacks "unknown" >/dev/null; check "unknown area refused" $? 4
# a real race: c and d claim the same free area at the same moment; exactly one may hold it
git clone -q $T/up.git $T/d; git -C $T/d config user.email d@t; git -C $T/d config user.name d
(cd $T/c && $PY -m hive claim rc refunds "refunds c" >/dev/null; echo $? > $T/rc) &
(cd $T/d && $PY -m hive claim rd refunds "refunds d" >/dev/null; echo $? > $T/rd) &
wait
wins=$(( ($(cat $T/rc) == 0) + ($(cat $T/rd) == 0) )); check "exactly one of two racing claims wins" $wins 1
cd $T/a && git pull -q --rebase origin main && n=$(grep -l "refunds" current_tasks/*.txt | wc -l); check "exactly one lock on refunds on the shared branch" $n 1
cd $T/a && $PY -m hive areas | grep -q "payouts *held by pb"; check "areas shows who holds payouts" $? 0
# landing releases the lock: a finishes fees and lands; b can then claim fees
cd $T/a && echo "def fee(x): return x // 10  # rule: 10%" > fees.py && $PY -m hive land fa "fee rule comment" >/dev/null; check "landing succeeds" $? 0
cd $T/b && $PY -m hive claim fb2 fees "fees after release" >/dev/null; check "area free again after landing" $? 0
# Gate 81: a builder with no lock of that name cannot land; one claim holds at most an even share of the areas
cd $T/c && git pull -q --rebase origin main && echo "def extra(): return 1" > extra.py && $PY -m hive land nolock "built without a claim" >/dev/null; check "landing without a lock refused" $? 9
cd $T/c && git checkout -q -- . 2>/dev/null; rm -f extra.py
mkdir -p $T/run && echo '{"workers": 3}' > $T/run/run.json
cd $T/c && git pull -q --rebase origin main && HIVE_RUN=$T/run $PY -m hive claim greedy fees,payouts "two of three areas, three builders" >/dev/null; check "a claim beyond an even share refused" $? 1
# Gate 82: within a run, an area that landed shows as landed, not free, and is not claimed again without --again
cd $T && git init -q -b main s2 && cd s2 && git config user.email t@t && git config user.name t && echo "def test_ok(): pass" > test_ok.py
$PY -m hive init --test-cmd "$PY -m pytest -q -p no:cacheprovider --junitxml=.hive/junit.xml" >/dev/null
$PY -c "import json; p = '.hive/config.json'; c = json.load(open(p)); c['areas'] = {'x': [], 'y': []}; json.dump(c, open(p, 'w'))"
printf '__pycache__/\n' >> .gitignore; git add -A && git commit -qm s2 && git clone -q --bare . $T/up2.git
for w in p q; do git clone -q $T/up2.git $T/$w; git -C $T/$w config user.email $w@t; git -C $T/$w config user.name $w; done
mkdir -p $T/run2 && echo '{"workers": 2}' > $T/run2/run.json; export HIVE_RUN=$T/run2
cd $T/p && $PY -m hive claim px x "x" >/dev/null && echo "x = 1" > x.py && $PY -m hive land px "x built" >/dev/null; check "p lands area x" $? 0
cd $T/q && git pull -q --rebase origin main && $PY -m hive claim qx x "x again" >/dev/null; check "a landed area is not claimed again" $? 1
cd $T/q && $PY -m hive areas | grep -q "x *landed by p"; check "areas shows it as landed" $? 0
cd $T/q && $PY -m hive claim --again qx2 x "fix a wrong case in x" >/dev/null; check "--again claims it to fix it" $? 0
# Gate 90: the business builder may claim a landed area, and beyond an even share
echo '{"workers": 2, "business_builder": "w2"}' > $T/run2/run.json
cd $T/q && echo "x = 2" > x.py && $PY -m hive land qx2 "x fixed" >/dev/null; git pull -q --rebase origin main
HIVE_WORKER=w1 $PY -m hive claim qnot x,y "x again and y" >/dev/null; check "another builder still may not" $? 1
HIVE_WORKER=w2 $PY -m hive claim qbiz x,y "fill placeholders in x, and y" >/dev/null; check "the business builder claims a landed area and more than a share" $? 0
unset HIVE_RUN
rm -rf $T; exit $fail
