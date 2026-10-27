# Gate 3

Three steps, each answering an open question from Gate 2:

1. **Protocol v2** (done). Claims name test categories, and landings are guarded. `tools/claim.py` and `tools/land.py` are tested against overlap, a simultaneous race, a regression and a duplicate definition.
2. **Scale** (done; hidden replay pending). The Gate 2 project with protocol v2 at 12 workers and at 8; the 24-worker swarm was capped at 8. See `RESULTS.md`.
3. **Intent bandwidth** (built, not yet run). Swarms add 20 business functions whose rules were invented for this test, so no model can know them. Workers see a one-line spec and 2 happy-path examples per function. A "product owner" server answers questions with the intended result. Three swarms of 3 workers differ only in how many questions they may ask: 0, 30, or unlimited. A hidden suite of 500 tests (70% edge cases) scores each swarm.

## Step 3 status

The intent test has been started twice and stopped twice:

- **Attempt 1** was stopped by a usage limit about 3 minutes in.
- **Attempt 2** was stopped by the user about 3 minutes in.

Neither counts. Their data is kept in `../sealed/`. The repos, clones and question budgets have been reset to clean.

What is kept out of plain sight until step 3 has run:

- `referee/oracle.py`: the private intent.
- The hidden suite (regenerate it with `python3 referee/gen3.py hidden <dir> 900000` once the oracle is unsealed).
- The question logs.
- The aborted attempts.

All of these are in `../sealed/gate3_intent.tgz.enc`; the user holds the password. They are sealed so that no agent working in this repository can read the intended answers before the test.

## Files

| Path | Contents |
| --- | --- |
| `tools/` | `claim.py`, `land.py`, `ask_template.py` (the question client, rendered per arm) |
| `referee/` | `gen3.py` (test generator for step 3), `ask_server.py` (the product-owner server: one SELECT of up to 3 values per question, budgeted) |
| `prompts/` | Exact worker prompts for steps 2 and 3, and the predictions registered before launch |
| `seed_scale.bundle` | Starting repo for step 2 (Gate 2 seed plus protocol v2) |
| `seed_intent.bundle` | Starting repo for step 3 (finished Gate 2 engine, the 20-function spec, 40 example tests) |
| `swarms/`, `logs/`, `results/` | Step 2 histories, event logs, tokens |
