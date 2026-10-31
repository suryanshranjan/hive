#!/bin/sh
: "${PY:=python3}"
# A stand-in night builder (no tokens): the owner is away, so it records two questions for his morning, builds its best
# guess and lands. In the fix round it builds his answers in.
prompt=$(cat)
$PY -m hive claim fees fees "fee rules" >&2
if echo "$prompt" | grep -q "The owner's answers"; then
  echo "$prompt" | grep -q "Rs 0" && echo built > "$HIVE_RUN/answers_seen"
  printf 'def fee(cash, bonus=0):\n    return round((max(cash, 0) + max(bonus, 0)) * 0.10, 2)\n' > fees.py
  printf 'from fees import fee\ndef test_owner_negative(): assert fee(-5) == 0\n' > test_fees_morning.py
  $PY -m hive land fees "fee: negative counts as Rs 0, as the owner answered" >&2
else
  $PY -m hive answers > "$HIVE_RUN/answers_listing.txt"
  $PY -m hive ask "A brand enters a deal of minus Rs 5 by mistake. What should happen? A) refuse it B) treat it as Rs 0 C) something else (please say)" > "$HIVE_RUN/ask_out.txt"
  $PY -m hive ask "A deal of Rs 999 comes in. Is there a minimum fee? A) no minimum B) at least Rs 100 C) something else (please say)" > /dev/null
  printf 'def fee(cash, bonus=0):\n    return round((cash + bonus) * 0.10, 2)\n' > fees.py
  printf 'from fees import fee\ndef test_fee(): assert fee(1000) == 100\n' > test_fees_night.py
  $PY -m hive land fees "fee, best guess; two questions recorded for the owner" >&2
fi
echo '{"total_cost_usd": 0, "result": "done"}'
