#!/bin/sh
# hive doctor and the installed `hive` command (no tokens: the Claude login probe is skipped).
# usage: sh tests/test_doctor.sh   (needs git, python3 and pip; run from the hive repo root)
set -u
python3 -c '' 2>/dev/null && PY=python3 || PY=python; export PY   # Windows has python, not python3
[ "$PY" = python ] && export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.autocrlf GIT_CONFIG_VALUE_0=false   # Windows: test repos keep LF
HIVE=$(pwd -W 2>/dev/null || pwd); T=$(mktemp -d); TW=$(cd "$T" && (pwd -W 2>/dev/null || pwd)); export HOME=$T USERPROFILE="$TW"
mkdir -p $T/bin && printf '#!/bin/sh\necho OK\n' > $T/bin/claude && chmod +x $T/bin/claude
export PATH="$(cd $T/bin && pwd):$PATH"   # a stand-in Claude Code (the login probe is skipped)
[ "$PY" = python ] && printf '@echo OK\r\n' > $T/bin/claude.cmd   # Windows finds programs by extension
fail=0; check() { if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1 (got $2, expected $3)"; fail=1; fi; }
$PY -m venv $T/venv >/dev/null 2>&1
B=$T/venv/bin; [ -d $T/venv/Scripts ] && B=$T/venv/Scripts   # Windows keeps a venv's programs in Scripts
mkdir -p $T/src && cp -r $HIVE/hive $HIVE/pyproject.toml $HIVE/README.md $HIVE/LICENSE $T/src/   # pip builds in a copy, never in the repo
PIP_CACHE_DIR=$T/pipcache $B/python -m pip install -q $T/src >/dev/null 2>&1
check "it installs with pip and gives a hive command" "$(test -x $B/hive -o -f $B/hive.exe && echo yes)" yes
cd "$T" || exit 1
git init -q -b main project && cd project && git config user.email t@t && git config user.name t
printf 'def test_one(): assert 1\n' > test_one.py && git add -A && git commit -qm init
$B/python -c "from hive import doctor; import sys; sys.exit(doctor.main('.', claude_probe=False))" > $T/ok.txt 2>&1
code=$?
check "the installed package finds its tests and templates" "$(grep -c 'tests found (pytest)' $T/ok.txt)" 1
check "with only optional extras missing, it says all set" "$code $(grep -c 'All set' $T/ok.txt)" "0 1"
check "the installed package carries the worker template" "$(ls $T/venv/lib/python3*/site-packages/hive/templates/worker.md $T/venv/Lib/site-packages/hive/templates/worker.md 2>/dev/null | wc -l | tr -d ' ')" 1
printf 'n\nn\n' | $B/python -c "from hive import doctor; import sys; sys.exit(doctor.setup('.', claude_probe=False))" > $T/setup.txt 2>&1
check "hive setup checks, offers the extras one at a time, and ends ready" \
  "$? $(grep -c 'on your phone, through Telegram' $T/setup.txt) $(grep -c 'All set. Type' $T/setup.txt)" "0 1 1"
echo "# x" >> test_one.py   # an edit to a tracked file (untracked caches are ignored)
$B/python -c "from hive import doctor; import sys; sys.exit(doctor.main('.', claude_probe=False))" > $T/dirty.txt 2>&1
check "unsaved changes are reported with how to fix them" "$(grep -c 'Commit or stash' $T/dirty.txt)" 1
rm -rf $T; exit $fail
