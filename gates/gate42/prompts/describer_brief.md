You are documenting what a piece of software does, so that its owner can check it. The folder `{BASE}` is a git repository: a SQL engine in Python (`minisql/`) to which engineers have just added the business functions below. Read it and run it, but do not change anything in it. Do not read any other folder on this machine.

Write `{OUT}/rules.json`: a JSON list of strings, one rule per string, in plain words a business owner can check ("Whenever ..., ..."), each naming its function.

- For every function, describe everything the code does: its normal calculation, and how it treats NULL, empty text, text where a number is expected, zero, negative numbers, boundaries, unusual formats, letter case, spaces, separators and rounding. Describe what the code actually does, even where it looks odd.
- Check each rule by running the engine (for example `cd {BASE} && python3 -c "import minisql; ..."`, or the way `run_tests.py` runs queries).
- One behaviour per rule, one or two sentences each. Business words, no code.

The functions (as the product team specified them):
{SPEC}

Reply in one line: how many rules you wrote.
