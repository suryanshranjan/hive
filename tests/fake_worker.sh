#!/bin/sh
# A stand-in for a headless coding agent (no tokens): reads the prompt, claims one area, implements it, lands.
# Worker w1 builds fees, w2 builds payouts. Prints a Claude-style JSON result so hive can log cost.
cat > /dev/null
case "$HIVE_WORKER" in w1) area=fees; code='def fee(cash, bonus=0): return round((cash + bonus) * 0.10, 2)';;
                       *)  area=payouts; code='def payout(cash, bonus=0): return cash + bonus';; esac
python3 -m hive claim "$HIVE_WORKER-$area" "$area" "build $area" >&2 || { echo '{"total_cost_usd": 0, "result": "claim refused"}'; exit 0; }
echo "$code" > "$area.py"
python3 -m hive land "$HIVE_WORKER-$area" "implement $area" >&2
echo "{\"total_cost_usd\": 0, \"usage\": {\"input_tokens\": 0}, \"result\": \"landed $area (exit $?)\"}"
