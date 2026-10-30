You are preparing quick spot checks for a busy business owner. The folder `{BASE}` is a git repository: a SQL engine in Python (`minisql/`) to which engineers have just added the business functions below. Read it and run it, but do not change anything in it. Do not read any other folder on this machine.

**Cover every function below**, not only the most striking choices: for each function, find the choices the code made that a business owner might not expect or might decide differently (boundaries and cut-offs, rounding, caps and minimums, what happens in each business situation, inputs that are wrong in a way the business would care about, and what it returns for an empty or missing value). For each function write **at least 2 and at most 5** spot checks, one choice each. For each, pick one concrete case, **run the engine on it**, and write what actually comes out.

Write `{OUT}/spots.json`: a JSON list of objects, grouped by function, the most important first within each:
`{"function": "...", "setup": [], "call": "SELECT late_fee(10000, 31)", "got": <the value the engine returned>, "say": "..."}`, where `setup` lists the SQL statements that create and fill any table the call reads (for the aggregate function; empty otherwise), so the call can be run again on a fresh connection
where `say` is one sentence in plain business words, with names and amounts, ending with the outcome, for example: "Ravi's 100-rupee invoice is paid 31 days late: the late fee comes to 2 rupees." No code words in `say`.

The functions (as the product team specified them):
{SPEC}

Reply in one line: how many spot checks you wrote, and for how many functions.
