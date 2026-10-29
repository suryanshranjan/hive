#!/bin/sh
# M1 acceptance test for hive's runner-agnostic guard, on a throwaway pytest repository.
# usage: sh tests/test_guard.sh   (needs git, python3 and pytest; run from the hive repo root)
set -u
python3 -c '' 2>/dev/null && PY=python3 || PY=python; export PY   # Windows has python, not python3
[ "$PY" = python ] && export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.autocrlf GIT_CONFIG_VALUE_0=false   # Windows: test repos keep LF
HIVE=$(pwd -W 2>/dev/null || pwd); T=$(mktemp -d); TW=$(cd "$T" && (pwd -W 2>/dev/null || pwd)); export HIVE_GUARD_CACHE=$T/cache; export PYTHONPATH=$HIVE
fail=0; check() { if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1 (exit $2, expected $3)"; fail=1; fi; }
cd "$T" || exit 1
git init -q -b main seed && cd seed && git config user.email t@t && git config user.name t
cat > calc.py <<'P'
def add(a, b):
    return a + b
P
cat > test_calc.py <<'P'
from calc import add
def test_add(): assert add(2, 3) == 5
P
$PY -m hive init --test-cmd "$PY -m pytest -q --junitxml=.hive/junit.xml" >/dev/null
git add -A && git commit -qm seed && git clone -q --bare . $T/up.git && cd $T
for w in a b; do git clone -q up.git $w; git -C $w config user.email $w@t; git -C $w config user.name $w; done
# 1. a clean change lands
cd $T/a && printf 'def mul(a, b):\n    return a * b\n' >> calc.py && printf 'from calc import mul\ndef test_mul(): assert mul(2, 3) == 6\n' > test_mul.py
$PY -m hive land mul "add mul" >/dev/null; check "clean change lands" $? 0
# 2. a change that breaks a passing test is refused
cd $T/b && git pull -q --rebase origin main && sed -i 's/return a + b/return a - b/' calc.py
$PY -m hive land breaker "break add" >/dev/null; check "regression refused" $? 7
git rebase --abort 2>/dev/null; git reset -q --hard origin/main
# 3. a new duplicate definition is refused
printf 'def add(a, b):\n    return 0\n' >> calc.py
$PY -m hive land dup "duplicate add" >/dev/null; check "duplicate definition refused" $? 6
git rebase --abort 2>/dev/null; git reset -q --hard origin/main
# 4. a lock commit changes no code, so the next lander reuses main's cached results
mkdir -p current_tasks && echo "b: x" > current_tasks/x.txt && git add current_tasks/x.txt && git commit -qm "Lock: x" && git push -q origin HEAD:main
hits() { cat $HIVE_GUARD_CACHE/*/stats.log 2>/dev/null | grep -c hit; }
before=$(hits)
cd $T/a && git pull -q --rebase origin main && printf '\ndef sub(a, b):\n    return a - b\n' >> calc.py
$PY -m hive land sub "add sub" >/dev/null; check "lands after a lock commit" $? 0
after=$(hits)
check "main's results came from the cache" $((after > before)) 1
# 5. a secret or a dependency folder is never committed
cd $T/a && git pull -q --rebase origin main && echo "API_KEY=abc" > .env && echo "x = 1" > extra.py
$PY -m hive land leak "with a .env" >/dev/null; check "secret file refused" $? 8
test -z "$(git log origin/main --name-only --format= | grep -x .env)"; check ".env never reached the shared branch" $? 0
# 6. team notes (Gates 43-44): a note rides in the landing's commit and others read it
rm -f .env; git checkout -q -- . 2>/dev/null; git reset -q --hard origin/main
printf '\ndef neg(a):\n    return -a\n' >> calc.py
$PY -m hive land neg "add neg" --note "calc.py now has neg(); use it instead of 0 - x" >/dev/null; check "a landing with a team note" $? 0
cd $T/b && $PY -m hive notes | grep -q "a: calc.py now has neg()"; check "the other builder reads the note" $? 0
# 7. a collision shows the recent notes, and once this swarm collides often, switches notes on
export HIVE_RUN=$T/run; mkdir -p $HIVE_RUN; printf '1 LAND\n2 CONFLICT\n3 LAND\n4 CONFLICT\n5 LAND\n6 LAND\n' > $HIVE_RUN/landings.log
git pull -q --rebase origin main; sed -i 's/return -a/return 0 - a/' calc.py   # b edits neg's line, uncommitted
cd $T/a && sed -i 's/return -a/return -1 * a/' calc.py && $PY -m hive land neg2 "neg as a product" >/dev/null   # a lands first
cd $T/b && out=$($PY -m hive land clash "neg as a difference" 2>&1); code=$?
check "a rebase conflict is reported" $code 5
echo "$out" | grep -q "Recent team notes"; check "the conflict shows recent team notes" $? 0
echo "$out" | grep -q "Team notes are now on"; check "frequent collisions switch notes on" $? 0
git rebase --abort 2>/dev/null; unset HIVE_RUN
# 8. what a builder commits itself, with plain git, is checked too (Gate 38: its own commit carried node_modules)
git reset -q --hard origin/main && mkdir -p node_modules && echo x > node_modules/pkg.js && printf '\ndef sq(a):\n    return a * a\n' >> calc.py
git add -f node_modules calc.py && git commit -qm "sq, with dependencies" && $PY -m hive land sq "sq" >/dev/null 2>&1
git fetch -q origin; check "a dependency folder in the builder's own commit stays off the shared branch" \
  "$(git ls-tree -r --name-only origin/main | grep -c node_modules) $(git show origin/main:calc.py | grep -c 'def sq')" "0 1"
git reset -q --hard origin/main && echo "TOKEN=abc" > .env && git add -f .env && git commit -qm "a secret"
$PY -m hive land secret "secret" >/dev/null 2>&1; check "a secret in the builder's own commit is refused" $? 8
rm -rf $T; exit $fail
