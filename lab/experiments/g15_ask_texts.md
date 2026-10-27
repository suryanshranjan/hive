# The only difference between the teams: this paragraph of the builder prompt

{EXAMPLE} is filled in by lab/new_intent_gate.py: two typical calls of the alphabetically first scalar function.
T and X get the same text: T's examples are the owner's own decision tour, X's are the owner's answers at inputs an extractor picked from the handbook. H gets the handbook.

## N0 (nothing extra)
There is no product owner to ask on this project: `tools/ask.py` will tell you so. Work from the spec and the examples.

## T (owner's decision tour)
The product owner has written worked examples of the company's policy decisions, as visible tests named `tests/visible/<function>_tour_<n>.json`. Each shows a decision at work; work out the rule behind it. There is no product owner to ask on this project: `tools/ask.py` will tell you so.

## H (policy handbook)
The product team's policy handbook for these functions is in `HANDBOOK.md`; read it before you implement a function. There is no product owner to ask on this project: `tools/ask.py` will tell you so.

## X (owner's answers at handbook-derived inputs)
The product owner has written worked examples of the company's policy decisions, as visible tests named `tests/visible/<function>_tour_<n>.json`. Each shows a decision at work; work out the rule behind it. There is no product owner to ask on this project: `tools/ask.py` will tell you so.
