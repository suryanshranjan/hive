# The only difference between the three teams: this paragraph of the builder prompt

{EXAMPLE} is filled in after the rules exist, by a fixed rule: two typical calls of the alphabetically first scalar function.

## D0 (no questions)
There is no product owner on this project: `tools/ask.py` will tell you so. Work from the spec and the examples.

## D30f (30 free questions, the control; same text as Gate 4's R30)
A product owner answers questions through `tools/ask.py "{EXAMPLE}"`: one SELECT returning one row of up to 3 values per question, answered with the intended result. Your whole team of 3 shares a budget of 30 questions, so spend them where the spec is most ambiguous.

## D30d (30 questions, defaults first)
A product owner answers questions through `tools/ask.py "{EXAMPLE}"`: one SELECT returning one row of up to 3 values per question, answered with the intended result. Your whole team of 3 shares a budget of 30 questions. Spend them defaults-first: a product team's own rules usually differ from convention in exactly the cases you would otherwise settle by habit. So for each function you take on, use your first question on those cases: NULL in an argument, an extreme or out-of-range value, and an unknown or malformed input. Only after that, ask about whatever else looks ambiguous.
