#!/bin/bash
# usage: replay.sh <index list file> <results dir>
# For each 1-based first-parent index: checkout, fast build, run external suite, record.
LIST=$1; RES=$2; mkdir -p "$RES"
WT=/tmp/claude-0/-home-claude/8c8904c7-77e6-5db5-9267-c0fd993e2759/scratchpad/repos/ccc_wt
FP=/tmp/claude-0/-home-claude/8c8904c7-77e6-5db5-9267-c0fd993e2759/scratchpad/repos/ccc_fp.txt
SUITE=/tmp/claude-0/-home-claude/8c8904c7-77e6-5db5-9267-c0fd993e2759/scratchpad/repos/c-testsuite/tests/single-exec
TOR=/tmp/claude-0/-home-claude/8c8904c7-77e6-5db5-9267-c0fd993e2759/scratchpad/gate0/runtorture.sh
TDIR=/tmp/claude-0/-home-claude/8c8904c7-77e6-5db5-9267-c0fd993e2759/scratchpad/repos/gcc_sparse/gcc/testsuite/gcc.c-torture/execute
TLIST=/tmp/claude-0/-home-claude/8c8904c7-77e6-5db5-9267-c0fd993e2759/scratchpad/gate0/torture_sub.txt
RUN=/tmp/claude-0/-home-claude/8c8904c7-77e6-5db5-9267-c0fd993e2759/scratchpad/gate0/runsuite.sh
export CARGO_PROFILE_DEV_OPT_LEVEL=1 CARGO_PROFILE_DEV_DEBUG=0
for i in $(cat "$LIST"); do
  [ -f "$RES/$i.txt" ] && continue
  H=$(sed -n "${i}p" "$FP"); T=$(git -C "$WT" log -1 --format=%ct "$H")
  git -C "$WT" checkout -q -f "$H" || { echo "$i $H $T CHECKOUT_FAIL" >> "$RES/log.txt"; continue; }
  s=$(date +%s)
  if (cd "$WT" && timeout 900 cargo build -q --bin ccc >/dev/null 2>&1) && [ -x "$WT/target/debug/ccc" ]; then
    "$RUN" "$WT/target/debug/ccc" "$SUITE" "$RES/$i.txt"
    "$TOR" "$WT/target/debug/ccc" "$TDIR" "$RES/$i.tor" "$TLIST"
    echo "$i $H $T OK $(( $(date +%s)-s ))s pass=$(grep -c PASS "$RES/$i.txt") tor=$(grep -c PASS "$RES/$i.tor")" >> "$RES/log.txt"
  else
    echo "BUILD_FAIL" > "$RES/$i.txt"; echo "$i $H $T BUILD_FAIL $(( $(date +%s)-s ))s" >> "$RES/log.txt"
  fi
done
echo DONE >> "$RES/log.txt"
