#!/bin/sh
# hive doctor and the installed `hive` command (no tokens: the Claude login probe is skipped).
# usage: sh tests/test_doctor.sh   (needs git, python3 and pip; run from the hive repo root)
set -u
HIVE=$(pwd); T=$(mktemp -d); export HOME=$T
fail=0; check() { if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1 (got $2, expected $3)"; fail=1; fi; }
python3 -m venv $T/venv >/dev/null 2>&1 && $T/venv/bin/pip install -q $HIVE >/dev/null 2>&1
check "it installs with pip and gives a hive command" "$(test -x $T/venv/bin/hive && echo yes)" yes
cd $T && git init -q -b main project && cd project && git config user.email t@t && git config user.name t
printf 'def test_one(): assert 1\n' > test_one.py && git add -A && git commit -qm init
$T/venv/bin/python -c "from hive import doctor; import sys; sys.exit(doctor.main('.', claude_probe=False))" > $T/ok.txt 2>&1
code=$?
check "the installed package finds its tests and templates" "$(grep -c 'tests found (pytest)' $T/ok.txt)" 1
check "with only optional extras missing, it says all set" "$code $(grep -c 'All set' $T/ok.txt)" "0 1"
check "the installed package carries the worker template" "$(ls $T/venv/lib/python3*/site-packages/hive/templates/worker.md | wc -l | tr -d ' ')" 1
printf 'n\nn\n' | $T/venv/bin/python -c "from hive import doctor; import sys; sys.exit(doctor.setup('.', claude_probe=False))" > $T/setup.txt 2>&1
check "hive setup checks, offers the extras one at a time, and ends ready" \
  "$? $(grep -c 'on your phone, through Telegram' $T/setup.txt) $(grep -c 'All set. Type' $T/setup.txt)" "0 1 1"
echo "x" > notes.txt
$T/venv/bin/python -c "from hive import doctor; import sys; sys.exit(doctor.main('.', claude_probe=False))" > $T/dirty.txt 2>&1
check "unsaved changes are reported with how to fix them" "$(grep -c 'Commit or stash' $T/dirty.txt)" 1
rm -rf $T; exit $fail
