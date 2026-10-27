#!/bin/bash
CCC=$1; SUITE=$2; OUT=$3; export CCC; TMP=$(mktemp -d); export TMP
ls "$SUITE"/*.c | xargs -P 2 -I{} bash -c 'c={}; n=$(basename "$c"); bin="$TMP/$n.bin"; if timeout 20 "$CCC" -o "$bin" "$c" >/dev/null 2>&1 && timeout 10 "$bin" > "$TMP/$n.out" 2>/dev/null && cmp -s "$TMP/$n.out" "$c.expected"; then echo "$n PASS"; else echo "$n FAIL"; fi' | sort > "$OUT"
rm -rf "$TMP"
