# The only difference between the three teams: this paragraph of the builder prompt

{EXAMPLE} is filled in after the rules exist by a fixed rule: two typical calls of the alphabetically first scalar function.

## N0 (no questions)
There is no product owner on this project: `tools/ask.py` will tell you so. Work from the spec and the examples.

## N30f (30 free questions, the control; same text as Gates 4 and 5)
A product owner answers questions through `tools/ask.py "{EXAMPLE}"`: one SELECT returning one row of up to 3 values per question, answered with the intended result. Your whole team of 3 shares a budget of 30 questions, so spend them where the spec is most ambiguous.

## NQ (randomized allowance per function)
A product owner answers questions through `tools/ask.py "{EXAMPLE}"`: one SELECT about exactly one of the 20 functions, returning one row of up to 3 values, answered with the intended result. The product owner has set a fixed allowance of questions for each function (0, 1 or 3); `tools/ask.py --allowance` shows every function's allowance and how much has been used. Before you land a function, use its full allowance on the cases where its intended behaviour is least clear.
