#!/bin/sh
# M2 acceptance test for hive's area claims, on a throwaway repository with two areas.
# usage: sh tests/test_claims.sh   (needs git, python3 and pytest; run from the hive repo root)
set -u
HIVE=$(pwd); T=$(mktemp -d); export HIVE_GUARD_CACHE=$T/cache; export PYTHONPATH=$HIVE
fail=0; check() { if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1 (exit $2, expected $3)"; fail=1; fi; }
cd $T && git init -q -b main seed && cd seed && git config user.email t@t && git config user.name t
echo "def fee(x): return x // 10" > fees.py && echo "from fees import fee
def test_fee(): assert fee(100) == 10" > test_fees.py
python3 -m hive init --test-cmd "python3 -m pytest -q -p no:cacheprovider --junitxml=.hive/junit.xml" >/dev/null
python3 - <<'P'
import json; p = '.hive/config.json'; c = json.load(open(p)); c['areas'] = {'fees': ['test_fees*'], 'payouts': ['test_payouts*'], 'refunds': ['test_refunds*']}; json.dump(c, open(p, 'w'))
P
printf '__pycache__/\n' >> .gitignore; git add -A && git commit -qm seed && git clone -q --bare . $T/up.git && cd $T
for w in a b c; do git clone -q up.git $w; git -C $w config user.email $w@t; git -C $w config user.name $w; done
cd $T/a && python3 -m hive claim fa fees "fee rules" >/dev/null; check "first claim on an area succeeds" $? 0
cd $T/b && python3 -m hive claim fb fees,payouts "fees again" >/dev/null; check "overlapping claim refused" $? 1
cd $T/b && python3 -m hive claim pb payouts "payout rules" >/dev/null; check "claim on a free area succeeds" $? 0
cd $T/c && python3 -m hive claim zz chargebacks "unknown" >/dev/null; check "unknown area refused" $? 4
# a real race: c and d claim the same free area at the same moment; exactly one may hold it
git clone -q $T/up.git $T/d; git -C $T/d config user.email d@t; git -C $T/d config user.name d
(cd $T/c && python3 -m hive claim rc refunds "refunds c" >/dev/null; echo $? > $T/rc) &
(cd $T/d && python3 -m hive claim rd refunds "refunds d" >/dev/null; echo $? > $T/rd) &
wait
wins=$(( ($(cat $T/rc) == 0) + ($(cat $T/rd) == 0) )); check "exactly one of two racing claims wins" $wins 1
cd $T/a && git pull -q --rebase origin main && n=$(grep -l "refunds" current_tasks/*.txt | wc -l); check "exactly one lock on refunds on the shared branch" $n 1
cd $T/a && python3 -m hive areas | grep -q "payouts *held by pb"; check "areas shows who holds payouts" $? 0
# landing releases the lock: a finishes fees and lands; b can then claim fees
cd $T/a && echo "def fee(x): return x // 10  # rule: 10%" > fees.py && python3 -m hive land fa "fee rule comment" >/dev/null; check "landing succeeds" $? 0
cd $T/b && python3 -m hive claim fb2 fees "fees after release" >/dev/null; check "area free again after landing" $? 0
rm -rf $T; exit $fail
