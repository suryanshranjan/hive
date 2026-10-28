#!/bin/sh
: "${PY:=python3}"
# A stand-in worker for the owner-session test (no tokens): reads its prompt, asks the owner one question,
# encodes the answer as a test, lands, then tries a second question (the budget is 1).
prompt=$(cat)
echo "$prompt" | grep -q "fee(10000, 2000) -> 1200" && echo ok > "$HIVE_RUN/saw_examples"
$PY -m hive answers > "$HIVE_RUN/answers_before.txt"
$PY -m hive claim fees fees "fee rules" >&2
$PY -m hive ask "What should fee(-5) do? Return null or throw 400?" > /dev/null; echo $? > "$HIVE_RUN/jargon_ask_exit"
answer=$($PY -m hive ask "A brand enters a deal of minus Rs 5 by mistake. What should happen? A) refuse the deal B) treat it as Rs 0 C) something else (please say)" | grep '^ANSWER:' | cut -c9-)
echo "$answer" > "$HIVE_RUN/got_answer"
printf 'def fee(cash, bonus=0):\n    if cash < 0 or bonus < 0:\n        raise ValueError("negative amount")\n    return round((cash + bonus) * 0.10, 2)\n' > fees.py
printf 'import pytest\nfrom fees import fee\ndef test_owner_answer_negative(): \n    with pytest.raises(ValueError): fee(-5)\n' > test_fees_owner.py
$PY -m hive land fees "fee; owner: negative raises ValueError" >&2
$PY -m hive ask "Is a bonus capped?" > /dev/null; echo $? > "$HIVE_RUN/second_ask_exit"
echo '{"total_cost_usd": 0, "result": "done"}'
