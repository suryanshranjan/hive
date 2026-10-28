# The only difference between the teams: this paragraph of the builder prompt

T starts from a repo with the owner's decision tour added as visible tests; N0, H, K and R do not.
H, K and R are not written here: gates/gate41/referee/wind_tunnel.py appends them to runs/g41/ask_texts.md after the
interview, as "There is no product owner to ask..." plus the rules in exactly the words Hive gives its builders
(hive.interview.instructions). H gets the rule sheet from one interview as shipped; K gets the same sheet plus his answer to each situation kept whole (instructions(rules, rulings)); R gets the owner's complete rule sheet.

## N0 (nothing extra)
There is no product owner to ask on this project: `tools/ask.py` will tell you so. Work from the spec and the examples.

## T (owner's decision tour)
The product owner has written a decision tour: for every function, one worked example per company policy decision, as visible tests named `tests/visible/<function>_tour_<n>.json`. Each shows one decision at work; work out the rule behind it. There is no product owner to ask on this project: `tools/ask.py` will tell you so.
