# The only difference between the teams: this paragraph of the builder prompt

T starts from a repo with the owner's decision tour added as visible tests; N0, H and R do not.
H and R are not written here: gates/gate39/referee/wind_tunnel.py appends them to runs/g39/ask_texts.md after the
interview, as "There is no product owner to ask..." plus the rules in exactly the words Hive gives its builders
(hive.interview.instructions). H's rules come from Hive's interview with the synthetic owner; R's are the owner's
complete rule sheet.

## N0 (nothing extra)
There is no product owner to ask on this project: `tools/ask.py` will tell you so. Work from the spec and the examples.

## T (owner's decision tour)
The product owner has written a decision tour: for every function, one worked example per company policy decision, as visible tests named `tests/visible/<function>_tour_<n>.json`. Each shows one decision at work; work out the rule behind it. There is no product owner to ask on this project: `tools/ask.py` will tell you so.
