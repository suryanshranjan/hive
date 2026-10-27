# The only difference between the teams: this paragraph of the builder prompt

{EXAMPLE} is filled in by lab/new_intent_gate.py. Both teams use the content-keyed cached guard (gates/gate23/tools/land.py).

## N0 (no tour, no questions)
There is no product owner to ask on this project: `tools/ask.py` will tell you so. Work from the spec and the examples.

## V1 (Hive v1 intent interface: decision tour and 17 questions)
The product owner has written a decision tour: for every function, one worked example per company policy decision, as visible tests named `tests/visible/<function>_tour_<n>.json`. Each shows one decision at work; work out the rule behind it. A product owner answers questions through `tools/ask.py "{EXAMPLE}"`: one SELECT about exactly one of the 20 functions, returning one row of up to 3 values, answered with the intended result. The team has 17 questions in all; `tools/ask.py --allowance` shows how many are left. Spend them on the cases where intended behaviour is least clear.
