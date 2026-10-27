# The only difference between the teams: this paragraph of the builder prompt

{EXAMPLE} is filled in by lab/new_intent_gate.py: two typical calls of the alphabetically first scalar function.
T and TQ start from a repo with the owner's decision tour added as visible tests; N0 and Q do not.

## N0 (no questions, no tour)
There is no product owner to ask on this project: `tools/ask.py` will tell you so. Work from the spec and the examples.

## T (decision tour, no questions)
The product owner has confirmed worked examples of the company's policy for every function, as visible tests named `tests/visible/<function>_tour_<n>.json`. Each shows the policy at work on a case that needs care; work out the rules behind them. There is no product owner to ask on this project: `tools/ask.py` will tell you so.

## Q (19 questions, no tour)
A product owner answers questions through `tools/ask.py "{EXAMPLE}"`: one SELECT about exactly one of the 10 functions, returning one row of up to 3 values, answered with the intended result. The team has 19 questions in all; `tools/ask.py --allowance` shows how many are left. Spend them on the cases where intended behaviour is least clear.

## TQ (decision tour and 19 questions)
The product owner has confirmed worked examples of the company's policy for every function, as visible tests named `tests/visible/<function>_tour_<n>.json`. Each shows the policy at work on a case that needs care; work out the rules behind them. A product owner answers questions through `tools/ask.py "{EXAMPLE}"`: one SELECT about exactly one of the 10 functions, returning one row of up to 3 values, answered with the intended result. The team has 19 questions in all; `tools/ask.py --allowance` shows how many are left. Spend them on the cases where intended behaviour is least clear.
