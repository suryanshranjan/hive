#!/bin/sh
# A stand-in builder that costs $3 (no tokens): for the monthly-cap test in tests/test_run.sh.
cat > /dev/null
echo '{"total_cost_usd": 3, "result": "spent"}'
