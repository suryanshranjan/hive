You are preparing quick spot checks for a busy business owner. The folder `{BASE}` is a git repository: a SQL engine in Python (`minisql/`) to which engineers have just added the business functions below. Read it and run it, but do not change anything in it. Do not read any other folder on this machine.

Find the places where the code made a choice a business owner might not expect or might decide differently: boundaries and cut-offs (the day a period ends, a tier's exact start), rounding, caps and minimums, what happens in each business situation, and inputs that are wrong in a way the business would care about. For each such choice, pick one concrete case, **run the engine on it**, and write what actually comes out.

Write `{OUT}/spots.json`: a JSON list of at most 30 objects, the most important first:
`{"function": "...", "call": "SELECT late_fee(10000, 31)", "got": <the value the engine returned>, "say": "..."}`
where `say` is one sentence in plain business words, with names and amounts, ending with the outcome, for example: "Ravi's 100-rupee invoice is paid 31 days late: the late fee comes to 2 rupees." No code words in `say`.

The functions (as the product team specified them):
{SPEC}

Reply in one line: how many spot checks you wrote.
