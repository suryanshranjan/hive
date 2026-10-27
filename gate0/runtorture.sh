#!/bin/bash
CCC=$1; DIR=$2; OUT=$3; LIST=$4; export CCC DIR; TMP=$(mktemp -d); export TMP
xargs -P 2 -I{} bash -c 'n={}; c="$DIR/$n"; bin="$TMP/$n.bin"; if timeout 10 "$CCC" -w -o "$bin" "$c" >/dev/null 2>&1 && timeout 5 "$bin" >/dev/null 2>&1; then echo "$n PASS"; else echo "$n FAIL"; fi' < "$LIST" 2>/dev/null | sort > "$OUT"
rm -rf "$TMP"
