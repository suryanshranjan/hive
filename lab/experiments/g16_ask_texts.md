# The only difference between the teams: this paragraph of the builder prompt

{EXAMPLE} is filled in by lab/new_intent_gate.py: two typical calls of the alphabetically first scalar function.
X, HX and HXQ get the same worked examples (the owner's answers at inputs an extractor picked from the handbook). HX and HXQ also get the handbook; HXQ also gets 17 questions.

## N0 (nothing extra)
There is no product owner to ask on this project: `tools/ask.py` will tell you so. Work from the spec and the examples.

## X (worked examples)
The product owner has written worked examples of the company's policy decisions, as visible tests named `tests/visible/<function>_tour_<n>.json`. Each shows a decision at work; work out the rule behind it. There is no product owner to ask on this project: `tools/ask.py` will tell you so.

## HX (handbook and worked examples)
The product team's policy handbook for these functions is in `HANDBOOK.md`; read it before you implement a function. The product owner has written worked examples of the company's policy decisions, as visible tests named `tests/visible/<function>_tour_<n>.json`. Each shows a decision at work; work out the rule behind it. There is no product owner to ask on this project: `tools/ask.py` will tell you so.

## HXQ (handbook, worked examples and 17 questions)
The product team's policy handbook for these functions is in `HANDBOOK.md`; read it before you implement a function. The product owner has written worked examples of the company's policy decisions, as visible tests named `tests/visible/<function>_tour_<n>.json`. Each shows a decision at work; work out the rule behind it. A product owner answers questions through `tools/ask.py "{EXAMPLE}"`: one SELECT about exactly one of the 20 functions, returning one row of up to 3 values, answered with the intended result. The team has 17 questions in all; `tools/ask.py --allowance` shows how many are left. Spend them on the cases where intended behaviour is least clear, especially policies the handbook and the examples leave open.
