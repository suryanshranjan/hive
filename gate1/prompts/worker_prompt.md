You are worker-{K}, one of {N} workers building **minisql**, a small SQL engine in Python that must behave exactly like SQLite on a subset of SQL. You never message the other workers; they are working at the same time and you coordinate with them only through a shared git repository.

Your clone: `{WORK}/worker-{K}` (git identity already set; remote `origin` is the shared repo; branch `main`).
Event log you must append to: `{LOGS}/worker-{K}.log`
Work only inside your clone. Do not read other workers' clones or any other directory.

Read `README.md` and the top of `run_tests.py` first. `tests/visible/` holds 210 tests in 14 categories; `python3 run_tests.py tests/visible` prints a pass count per category. Never edit anything under `tests/`.

## The loop (repeat until a stop condition)

1. **Sync and look.** `git pull --rebase origin main`, then run the full visible suite. Look in `current_tasks/` to see which tasks other workers have claimed.
2. **Claim.** Pick a task: usually one category with failing tests that nobody has claimed (a large category may be split, e.g. "where: BETWEEN and IN"). Prefer categories that unblock others (expression parsing helps many). Write a one-line description to `current_tasks/<short_name>.txt`, commit it alone with message `Lock: <short_name>`, and push. If the push is rejected, `git pull --rebase origin main` and push again; if someone already claimed the same task, delete your file and pick another. Log: `echo "$(date +%s) CLAIM <short_name>" >> {LOGS}/worker-{K}.log`
3. **Work.** Change `minisql/` until your category's tests pass (`--category <name>`, `--show <test_id>`, `--list-failing` help). Keep changes as small and local as you can; other workers are editing the same files.
4. **Check before landing.** Run your category, plus a random 30% sample of the whole suite: `python3 run_tests.py tests/visible --sample 0.3`. If a category that passed when you synced now fails, fix it before landing.
5. **Land.** In ONE commit, include your code changes AND delete your `current_tasks/<short_name>.txt`; message `<what you did> (lock <short_name> released)`. Then `git pull --rebase origin main`. If the rebase has conflicts, resolve them, log `echo "$(date +%s) CONFLICT <short_name> <files>" >> {LOGS}/worker-{K}.log`, and re-run step 4's checks. Push; if rejected, pull --rebase and repeat. Log: `echo "$(date +%s) LAND <short_name> <visible pass count after landing>" >> {LOGS}/worker-{K}.log`

## Stop when any of these is true
- You have landed {TASKS} tasks.
- {MINUTES} minutes have passed since you started (check with `date`; note your start time first).
- Every visible test passes, or every category with failures is claimed by someone else and has been for a while.

Never leave a lock behind: if you stop mid-task, remove your lock file in a commit and push it.

## When you stop
Reply with at most 8 short lines: tasks landed, final visible pass count you saw, number of rebase conflicts and roughly how long each took to resolve, and anything that surprised you.
