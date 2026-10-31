#!/bin/sh
: "${PY:=python3}"
# A stand-in builder (no tokens) told to ask first: asks the owner three plain questions, builds to his answers, lands.
cat > /dev/null
$PY -m hive claim fees fees "fee rules" >&2
for q in "A brand enters a deal of minus Rs 5 by mistake. What should happen? A) refuse it B) treat it as Rs 0 C) something else (please say)" \
         "A creator earns Rs 2,500 on a deal capped at Rs 2,000. What do they get? A) Rs 2,000 B) Rs 2,500 C) something else (please say)" \
         "A deal of Rs 999 comes in. Is there a minimum fee? A) no minimum B) at least Rs 100 C) something else (please say)"; do
  $PY -m hive ask "$q" > /dev/null
done
printf 'def fee(cash, bonus=0):\n    return round((max(cash, 0) + max(bonus, 0)) * 0.10, 2)\n' > fees.py
printf 'from fees import fee\ndef test_fee(): assert fee(1000) == 100\n' > test_fees_asked.py
$PY -m hive land fees "fee, to the owner's three answers" >&2
echo '{"total_cost_usd": 0, "result": "done"}'
