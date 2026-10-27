# The only difference between the teams: this paragraph of the builder prompt

{EXAMPLE} is filled in by lab/new_intent_gate.py: two typical calls of the alphabetically first scalar function.
S and B get the same text; only their allowances differ (set by lab/run_gate.py after N0 is scored).

## N0 (no questions)
There is no product owner on this project: `tools/ask.py` will tell you so. Work from the spec and the examples.

## S (allowance per function: 1 or 2 questions)
A product owner answers questions through `tools/ask.py "{EXAMPLE}"`: one SELECT about exactly one of the 20 functions, returning one row of up to 3 values, answered with the intended result. The product owner has set a fixed allowance of questions for each function; `tools/ask.py --allowance` shows every function's allowance and how much has been used. Before you land a function, use its full allowance on the cases where its intended behaviour is least clear.

## B (allowance per function: 0 or 3 questions)
A product owner answers questions through `tools/ask.py "{EXAMPLE}"`: one SELECT about exactly one of the 20 functions, returning one row of up to 3 values, answered with the intended result. The product owner has set a fixed allowance of questions for each function; `tools/ask.py --allowance` shows every function's allowance and how much has been used. Before you land a function, use its full allowance on the cases where its intended behaviour is least clear.
