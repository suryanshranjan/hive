# Gate 42 predictions: a rule sheet complete by construction

Registered Oct 29 2026, before the rules exist. Gate 38 is untouched: no founder, no Telegram, none of its files.

## Why this test

Three wind-tunnel runs (Gates 39–41) show:
- Builders given the owner's complete rule sheet pass 750 of 750 hidden tests and break nothing.
- Hive's interview delivers about half the decisions whole. Its questions miss some decisions, and a question about one case returns an answer about that case.

Any first build already decides every case, including the unusual ones nobody asked about. So a sheet written from the built code is **complete by construction**. The owner then does not have to recall his rules. He only marks the rules that are not his policy and says each one right. This turns elicitation, which misses, into verification. Its remaining limit is the owner's attention, which this gate does not test: the owner here is synthetic.

## Setup

- **Rules and suites:** a fresh independent rule-giver (Gate 39's brief: 10 functions, 25 declared decisions). Visible seed 42100; hidden 250 tests (seed 42200000), never committed.
- **Stage 1:** N0 builds (3 builders, spec and examples only).
- **The code sheet:**
  - **D.** A describer agent reads and runs N0's built code (never the oracle) and writes every behaviour as a plain rule (`prompts/describer_brief.md`).
  - **C.** In a fresh terminal, the synthetic owner sees D through Hive's own `interview.confirm_sheet`. He marks the wrong rules and says each one right (amended, not replaced), then adds anything missing. The result is C.
- **Stage 2 teams** (3 builders each, fresh from the starting repo, no questions):
  - **H:** the rule sheet from one interview as shipped.
  - **C:** the corrected code sheet.
  - **R:** the owner's complete sheet (fourth replication).
- **Judge** (before stage 2 builds): for each declared decision, how D, C, H and R state it.
- **Analysis:** `referee/analyze.py`, committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| C1 | D addresses (right, partly or wrongly) ≥ 90% of the 25 decisions: the code sheet is complete by construction | 65% |
| C2 | C states ≥ 85% of decisions right, and H ≤ 60% | 50% |
| C3 | C − H ≥ +10 points hidden | 55% |
| C4 | C ≥ 90% hidden | 45% |
| C5 | R ≥ 95% | 80% |
| C6 | Of the decisions D states wrongly or partly, the review makes ≥ 80% right in C | 60% |
| C7 | N0 below 65% | 85% |
| Kill | C ≤ H: a corrected code sheet is no better than the interview | 20% |

## Decision rules

- **C − H ≥ +5:** Hive's hand-over becomes "here is what the first build does, as rules; mark what is not your policy". The corrected sheet then drives a fix round. The next test is a real owner reading such a sheet: its length (expected 50 to 80 rules) is the risk, because Gates 30–35 found real owners do not audit long lists of builder decisions well.
- **C1 fails:** the describer misses behaviours, so "complete by construction" needs a better describer before it can ship.

## Cost and limits

- About $7: 12 builders, the describer, one interview, the owner's review, the documenter and the judge.
- One run per team. The owner is synthetic and reads every rule carefully, so this is the mechanism's ceiling, not a person's result.
