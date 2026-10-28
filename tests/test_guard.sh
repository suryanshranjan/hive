#!/bin/sh
# M1 acceptance test for hive's runner-agnostic guard, on a throwaway pytest repository.
# usage: sh tests/test_guard.sh   (needs git, python3 and pytest; run from the hive repo root)
set -u
python3 -c '' 2>/dev/null && PY=python3 || PY=python; export PY   # Windows has python, not python3
[ "$PY" = python ] && export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.autocrlf GIT_CONFIG_VALUE_0=false   # Windows: test repos keep LF
HIVE=$(pwd); T=$(mktemp -d); export HIVE_GUARD_CACHE=$T/cache; export PYTHONPATH=$HIVE
fail=0; check() { if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1 (exit $2, expected $3)"; fail=1; fi; }
cd $T && git init -q -b main seed && cd seed && git config user.email t@t && git config user.name t
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
rm -rf $T; exit $fail
