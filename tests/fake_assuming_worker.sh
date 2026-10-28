#!/bin/sh
: "${PY:=python3}"
# Like fake_worker.sh, but w1 also records one assumption for the owner's review (no tokens).
prompt=$(cat)
case "$HIVE_WORKER" in w1) area=fees; code='def fee(cash, bonus=0): return round((cash + bonus) * 0.10, 2)';;
                       *)  area=payouts; code='def payout(cash, bonus=0): return cash + bonus';; esac
$PY -m hive claim "$HIVE_WORKER-$area-$$" "$area" "build $area" >&2 || { echo '{"total_cost_usd": 0.01, "result": "claim refused"}'; exit 0; }
echo "$code" > "$area.py"
[ "$HIVE_WORKER" = w1 ] && echo "$prompt" | grep -q "Recording your assumptions" && \
  $PY -m hive assume "If a creator has no bonus, the fee is still taken on the cash alone." >&2
$PY -m hive land "$HIVE_WORKER-$area-$$" "implement $area" >&2
[ "$HIVE_WORKER" = w1 ] && echo "$prompt" | grep -q "Record each change as built" && \
  $PY -m hive assume "As built: with no bonus, the fee is 10 percent of the cash." >&2
echo '{"total_cost_usd": 0.01, "usage": {"input_tokens": 0}, "result": "done"}'
