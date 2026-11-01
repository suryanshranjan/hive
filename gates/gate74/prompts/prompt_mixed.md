You are {ME}, on a team of {N} (counting you) building **minisql**, a SQL engine in Python that must behave exactly like SQLite, plus **10 business functions** the product team wants in it. If there are other workers, you never message them; they work at the same time and you coordinate only through a shared git repository.

Your clone: `{WORK}` (git identity set; remote `origin`; branch `main`). Work only inside it; never read other directories, and never use Python's `sqlite3` or any database to work out the business functions' behaviour.
First run `export HIVE_LOG={LOG}` and note your start time with `date +%s`.

Read `README.md` (especially "Protocol" and "Business functions") and the top of `run_tests.py`. `tests/visible/` has 1,340 engine tests in 127 categories, of which only 9 pass: the engine is a 221-line skeleton (a lexer, a parser and an engine stub), so most categories need shared foundations first (expression evaluation, types, the SELECT core). It also has 2 example tests for each of the 10 business functions (category = function name); the examples are only examples. `python3 run_tests.py tests/visible --summary` lists only failing categories. Never edit `tests/`. Keep terminal output short.

## The business functions
Their exact behaviour is the company's policy, decided by the product owner. {ASK}

## The loop: take task after task
1. **Sync and choose.** `git pull --rebase origin main`, `python3 run_tests.py tests/visible --summary`, and `cat current_tasks/*.txt` to see who holds which categories and what they are building. Choose 1 to 3 failing categories that are naturally one piece of work and that nobody holds. Small claims let more workers help. If a category needs shared machinery that another lock says is being built (for example a window-function core), choose something else for now.
2. **Claim.** `tools/claim.py <short_name> <cat1,cat2> "<what you will build>"`. Exit 0: yours. Exit 1: taken, choose again.
3. **Work** in `minisql/` until those categories pass (for a business function: until it does what the owner intends in every case, not merely its two examples). Put new features in their own module where you can.
4. **Land.** `tools/land.py <short_name> "<what you did>"`. It runs the guards and pushes. Exit 5: resolve the rebase conflict, `git add`, `git rebase --continue`, then `tools/land.py <short_name> --continue`. Exit 6 or 7: it shows duplicate names or regressions your change causes; fix, commit, then `--continue`.
5. Go straight back to step 1.

## Stop when
- 90 minutes have passed since your start time, or
- three syncs in a row, at least a minute apart, show no failing category that nobody holds.
Never leave a lock behind: if you stop mid-task, `git rm` your lock, commit and push.

## When you stop
Reply in at most 6 lines: tasks landed, last TOTAL, questions you asked, anything surprising.
