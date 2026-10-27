You are F1-founder. You work alone, first. After you finish, 6 other workers will build **minisql** (a small SQL engine in Python that must behave exactly like SQLite) in parallel. They never message each other or you; they coordinate only through the git repository, so the structure you leave in the code is how they will coordinate.

Your clone: `/tmp/claude-0/-home-claude/8c8904c7-77e6-5db5-9267-c0fd993e2759/scratchpad/gate1/work3/F1-founder` (git identity set; remote `origin`; branch `main`).
Event log: `/tmp/claude-0/-home-claude/8c8904c7-77e6-5db5-9267-c0fd993e2759/scratchpad/gate1/logs3/F1-founder.log`
Work only inside your clone. Do not read any other directory.

Read `README.md`, the top of `run_tests.py`, and the code in `minisql/`. `python3 run_tests.py tests/visible` shows 210 tests in 14 categories. Never edit anything under `tests/`.

## Your one task: the shared foundation
In a previous run without you, six workers spent their first minutes blocked on the expression parser and then collided on the same few lines (the keyword list, `select()`, `evaluate()`). Build what everything depends on, and shape the code so the 14 categories can be added independently:

1. A complete expression layer with SQLite precedence: literals, column refs (qualified and not), unary minus/NOT, arithmetic with SQLite integer/real semantics, `||`, comparisons, AND/OR/NOT with three-valued logic, IS [NOT] NULL, BETWEEN, IN (list), LIKE, and function-call syntax `NAME(args)` including `COUNT(*)` and `COUNT(DISTINCT x)`.
2. Extension points so later features touch shared files as little as possible, for example a scalar-function registry, an aggregate hook, keyword registration that does not require editing one shared list, and a statement-dispatch table.
3. A short "How to extend" section in `README.md` saying where each kind of feature should go.

Do NOT implement the 14 categories themselves beyond what the expression layer naturally gives (no ORDER BY, GROUP BY, joins, subqueries, CASE, UPDATE/DELETE, DISTINCT, aggregate functions). Keep all currently passing tests passing.

Log `echo "$(date +%s) CLAIM foundation" >> /tmp/claude-0/-home-claude/8c8904c7-77e6-5db5-9267-c0fd993e2759/scratchpad/gate1/logs3/F1-founder.log` when you start. When done, commit with message `Foundation: expression layer and extension points`, push to `origin main`, and log `echo "$(date +%s) LAND foundation <visible pass count>" >> /tmp/claude-0/-home-claude/8c8904c7-77e6-5db5-9267-c0fd993e2759/scratchpad/gate1/logs3/F1-founder.log`. Stop after landing, or after 15 minutes.

Reply in at most 6 lines: what you built, the extension points, and the visible pass count after landing.