You are the product owner at a mid-sized company. Your engineering team is adding 20 business functions to the company's SQL engine: 19 scalar functions and 1 aggregate. Each function's exact behaviour is company policy, decided by you. Engineers will see only a one-line description and a few typical examples, and will have to discover the rest.

Write the policy as a Python module at `{DIR}/oracle.py`. Work only in `{DIR}`: do not read any other directory or file on this machine. Use only the Python standard library.

Requirements:
1. 20 functions on varied business topics of your choosing (money, dates, text, codes, ratings, scheduling, and so on). Each takes 1 to 3 SQL values (integer, real, text or NULL) and returns an integer, real, text or NULL. Deterministic: no randomness, no current date or time, no environment.
2. Each function's typical behaviour must be learnable from its one-line description plus two or three typical examples. Beyond that, each function must carry a set number of specific policy decisions of your own that a competent engineer could not know from the description and the typical examples: exactly 5 functions carry 1 decision, 5 carry 2, 5 carry 3 and 5 carry 4 (the aggregate counts as one of the 20). Decide for yourself which functions get which count, where the decisions are and what they say. A decision is one independent choice (for example a rounding rule, a cap, how one kind of invalid input is treated); do not split one choice into several or merge several into one. Never raise an error for any input in your lists below; return a value.
3. The one-line descriptions must read like a real product spec: say what the function is for, without revealing the policy decisions.
4. Exactly one function is an aggregate (a class with `step(value)` and `finalize()`) taking 1 argument.
5. Module contents, with these exact names:
   - `SPEC`: dict name → `'name(arg1, arg2): one-line description'`
   - `SCALARS`: dict name → (python function, number of args) for the 19 scalars
   - `AGGREGATE`: tuple (name, class)
   - `TYPICAL`: dict scalar name → list of at least 4 argument tuples showing typical use (none of them may touch your policy decisions)
   - `EDGE`: dict scalar name → list of 6 to 10 argument tuples a careful QA engineer would test for this function, covering every one of your policy decisions and other tricky cases
   - `AGG_TYPICAL`: list of at least 3 lists of input values (typical use); `AGG_EDGE`: list of 5 to 8 lists of input values (tricky cases, covering the aggregate's policy decisions)
   - `DECISIONS`: dict name → list of short labels, one per policy decision of that function (1 to 4 labels, matching requirement 2). This list is kept private.
   - `DECISION_EXAMPLES`: dict name → list with one example per policy decision, in the same order as `DECISIONS`, each showing that decision at work. For a scalar, an argument tuple; for the aggregate, a list of input values. None of them may appear in `TYPICAL`, `EDGE`, `AGG_TYPICAL` or `AGG_EDGE`.
   - `HANDBOOK`: a string, the company's internal policy handbook for these functions, written in prose the way a real one is: organised by business topic rather than function by function, with some background and history. Of the 50 policy decisions, state exactly 20 clearly, mention 15 only vaguely (hint at the rule without its exact threshold, format or value), and leave 15 out entirely, as real handbooks do. Never quote any input from `TYPICAL`, `EDGE` or `DECISION_EXAMPLES`.
   - `HANDBOOK_STATUS`: dict name → list with one of `'clear'`, `'vague'` or `'omitted'` per decision, in the same order as `DECISIONS`. This list is kept private.
   - `connect()`: returns `sqlite3.connect(':memory:', isolation_level=None)` with every scalar registered via `create_function(name, nargs, fn, deterministic=True)` and the aggregate via `create_aggregate(name, 1, cls)`.
   Argument values are int, float, str or None only. Function names are lowercase letters, digits and underscores, and must not be the name of any built-in SQLite function.
6. Self-check before you finish: through `connect()`, run `SELECT name(args)` for every TYPICAL, EDGE and DECISION_EXAMPLES tuple, and run the aggregate on every list (`CREATE TABLE m (id INTEGER, v)`, insert the values, `SELECT name(v) FROM m`). Make sure nothing raises, outputs are int, float, str or None, and repeated runs agree.

Reply in at most 3 lines: the 20 function names and whether the self-check passed. Do not describe your policy decisions in the reply.
