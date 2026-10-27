# The only difference between the teams: this paragraph of the builder prompt

{EXAMPLE} is filled in by lab/new_intent_gate.py: two typical calls of the alphabetically first scalar function.
T starts from a repo with the owner's decision tour; TC from one with the tour and a contrast per decision; N0 from neither.

## N0 (no tour)
There is no product owner to ask on this project: `tools/ask.py` will tell you so. Work from the spec and the examples.

## T (decision tour)
The product owner has written a decision tour: for every function, one worked example per company policy decision, as visible tests named `tests/visible/<function>_tour_<n>.json`. Each shows one decision at work; work out the rule behind it. There is no product owner to ask on this project: `tools/ask.py` will tell you so.

## TC (decision tour with contrasts)
The product owner has written a decision tour: for every function, one worked example per company policy decision, as visible tests named `tests/visible/<function>_tour_<n>.json`. Each shows one decision at work; work out the rule behind it. Each decision also has a contrast example, `tests/visible/<function>_contrast_<n>.json`: a nearby input the decision does not cover, which follows the function's ordinary behaviour. Use the pair to see where each rule stops. There is no product owner to ask on this project: `tools/ask.py` will tell you so.
