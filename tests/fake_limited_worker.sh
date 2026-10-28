#!/bin/sh
# A stand-in worker that hits Claude's usage limit on its first try (w1 only), then is picked up again and finishes.
# The second try must be told it is picking up again; it records that in its clone.
prompt=$(cat)
if [ "$HIVE_WORKER" = w1 ] && [ ! -f .limit_seen ]; then
  touch .limit_seen
  echo "{\"is_error\": true, \"api_error_status\": 429, \"total_cost_usd\": 0.25, \"result\": \"Claude AI usage limit reached|$(( $(date +%s) + 1 ))\"}"
  exit 1
fi
case "$prompt" in *"You are picking up again"*) touch .was_resumed;; esac
echo "$prompt" | sh "$(dirname "$0")/fake_worker.sh"
