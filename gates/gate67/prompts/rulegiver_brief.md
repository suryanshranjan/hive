You are the owner of one mid-sized business (choose its trade: a shop, a clinic, a logistics firm, a school…). Over the next three weeks your engineering team will add **15 business functions** to the company's SQL engine, **5 per week** (feature 1, feature 2, feature 3). Each function's exact behaviour is company policy, decided by you. Engineers see only a one-line description and a few typical examples, and must discover the rest.

Like any real business, yours has **house conventions**: a few ways of doing things that you apply everywhere, in every part of the business, and that an engineer would not guess (for example, how money is rounded, how a missing or unreadable value is treated, how a boundary day counts, how a name is capitalized). Every one of them should surprise a competent engineer: never the default most engineers would pick.

Write the policy as a Python module at `{DIR}/oracle.py`. Work only in `{DIR}`: do not read any other directory or file on this machine. Use only the Python standard library.

Requirements:
1. **15 scalar functions** (no aggregate), on varied topics within your one business. Each takes 1 to 3 SQL values (integer, real, text or NULL) and returns an integer, real, text or NULL. Deterministic: no randomness, no current date or time.
2. **5 house conventions.** Each convention applies to at least 4 functions, and those functions span **all three features**. Apply each convention identically wherever it applies.
3. **Each function** also carries 1 or 2 policy decisions of its own (not a convention), that a competent engineer could not know from its description and typical examples. In total each function has 2 to 4 decisions (conventions plus its own). A decision is one independent choice.
4. Typical behaviour must be learnable from the one-line description plus two or three typical examples. Never raise an error for any input in your lists below; return a value.
5. The one-line descriptions read like a real product spec: what the function is for, without revealing any decision or convention.
6. Module contents, with these exact names:
   - `SPEC`: dict name → `'name(arg1, arg2): one-line description'`
   - `SCALARS`: dict name → (python function, number of args), all 15
   - `FEATURES`: dict `'f1'`, `'f2'`, `'f3'` → list of 5 function names (each function in exactly one feature)
   - `CONVENTIONS`: list of 5 short labels, one per house convention
   - `TYPICAL`: dict name → list of at least 4 argument tuples showing typical use (none may touch a decision or convention)
   - `EDGE`: dict name → list of 6 to 10 argument tuples a careful QA engineer would test, covering every decision and convention that applies to the function
   - `DECISIONS`: dict name → list of short labels, one per decision of that function. A convention's label is written exactly as `'convention: <its label from CONVENTIONS>'`; the function's own decisions are plain labels. Kept private.
   - `DECISION_EXAMPLES`: dict name → list with one argument tuple per decision, in the same order as `DECISIONS`, showing it at work; none may appear in `TYPICAL` or `EDGE`.
   - `connect()`: returns `sqlite3.connect(':memory:', isolation_level=None)` with every function registered via `create_function(name, nargs, fn, deterministic=True)`.
   Argument values are int, float, str or None only. Names are lowercase letters, digits and underscores, never a built-in SQLite function name.
7. Self-check before you finish: through `connect()`, run `SELECT name(args)` for every TYPICAL, EDGE and DECISION_EXAMPLES tuple. Nothing may raise; outputs are int, float, str or None; repeated runs agree; every convention is used by at least 4 functions spanning all three features.

Reply in at most 4 lines: the business, the 15 function names by feature, and whether the self-check passed. Do not describe your decisions or conventions in the reply.
