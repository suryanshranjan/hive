You are documenting what a piece of software does, so that its busy business owner can check it at a glance. The folder `{BASE}` is a git repository: a SQL engine in Python (`minisql/`) to which engineers have just added the business functions below. Read it and run it, but do not change anything in it. Do not read any other folder on this machine.

Write `{OUT}/rules.json`: a JSON list of strings, one rule per string, in plain words a business owner can check ("Whenever ..., ..."), each naming its function.

- Write only the **business choices** the code makes: amounts, rates, cut-offs and boundaries, rounding, caps and minimums, what happens in each business situation, and what the customer or staff sees when an input is wrong in a way the business would care about (for example an impossible date or an unknown code).
- Leave out mechanics a business owner would not rule on (NULL in gives NULL out, numbers given as text, extra spaces), unless the code does something a business would find surprising.
- One choice per rule, with one concrete example. At most 30 rules in all; if there are more choices, keep the ones a wrong guess would cost the business most.
- Check each rule by running the engine (for example `cd {BASE} && python3 -c "import minisql; ..."`).

The functions (as the product team specified them):
{SPEC}

Reply in one line: how many rules you wrote.
