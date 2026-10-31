You are the owner of a company. Your engineers are adding business functions to the company's SQL engine. How each function behaves is your company's policy, and your policy is exactly what `oracle.py` in this folder computes. Work only in this folder.

Write your complete policy as a rule sheet for the engineers, in `{DIR}/rules.json`: a JSON list of strings, one rule per string, in plain words a builder can implement and test ("Whenever ..., ..."). Name the function each rule is about.

- Cover every behaviour of every function that the one-line spec below does not already settle: every policy decision, and how each function treats NULL, empty text, zero, negative numbers and boundaries. Check each rule against `oracle.py` (run `python3`).
- Rules, not examples: do not list input-output examples or test cases. Thresholds and constants in a rule are fine.
- One decision per rule; keep each rule to one or two sentences.

The functions (what your engineers see):
{SPEC}

Reply in one line: how many rules you wrote.
