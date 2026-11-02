# Gate 97 predictions: a lean reader for Hive's own calls (Gap 3)

Registered Nov 2 2026, before the flights. The user: "Hive's own model calls still cost 4–10× the builders' … Fix it."

## Why this test

- **Hive's own spend has been 4–10× the builders'.** About 75% of it goes to reading the owner's words (`settled_by`, `_amend`, `understand`, `_rule`).
- **Measured before registering** (`claude -p`, the same reading prompt, 5 calls each):
  - **As Hive calls it** (Claude Code's full coding-agent setup, in the project folder): **$0.050 a call**. Every call re-caches about 11,000 tokens of system prompt and tool definitions.
  - **Lean** (no tools, a one-line system prompt, run in an empty folder): **$0.005 a call**, the same model (Claude Sonnet 5.5), the same effort, and the same answer on every call.
- **Not the model:** Gates 87 and 91 cut cost by switching to Haiku and lost accuracy twice. This keeps Sonnet 5.5 and removes only the coding-agent overhead, which a reading task does not use.

## The change (on main with this registration)

- `hive/explain.py`'s default reader:

  `claude -p --output-format json --tools '' --system-prompt 'You read what a business owner and his builders wrote, and answer exactly in the JSON you are asked for.'`

  It runs in an empty temporary folder.
- `HIVE_EXPLAIN_CMD` still overrides it.
- The code-reading steps (the code sheet's describer, the spot-check finder) keep their tools.
- All test suites pass.

## Setup

- Gates 95–96's live flights, five more, on main with this change. Compared with Gates 95–96's ten flights (the same code with the old reader).
- Driver `referee/flight97.py`, analysis `referee/analyze.py`, committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| E1 | Hive's own spend, mean per flight, ≤ 0.3× Gates 95–96's | 80% |
| E2 | pass^1 ≥ 0.8 | 75% |
| E3 | Median hidden ≥ 26 | 75% |
| E4 | Median owner prompts ≤ 1.2× Gates 95–96's | 75% |
| E5 | pass^5 | 45% |

## Decision rules

- **Claim (E1, E2 and E3):** the lean reader stays the default.
- **E2 or E3 fails:** the short system prompt changed how the readings come out. Find the step (spend by step and the transcripts), and give it the old setup back.

## Limits

- Five flights against ten, with a synthetic owner. About $15.
