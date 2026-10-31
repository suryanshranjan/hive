# Gate 70 results: overnight, questions saved for the morning, Nov 1 2026

**Question** (following Gate 66, under the user's "go on and on"). When the owner is away overnight, builders cannot ask him. Is it better for them to record their questions for his morning, than for Hive to hand him the finished build to review?

**Answer.**
- **Yes, by a wide margin. All three predictions held, and the ship rule fired.**

| Overnight, pooled over 2 fresh rule sets | Hidden pass | Owner reads (characters) |
| --- | --- | --- |
| Night build as shipped, no questions (N0) | 34.0% | – |
| Night build recording questions (QN), before any answer | 39.4% | – |
| Hive's morning hand-over of N0, then a fresh build (HV) | 75.0% | 34,475 |
| **His morning answers to QN's questions, then a fresh build (QA)** | **94.2%** | **8,830** |

QA − HV = **+19.2** (95% CI +10.2 to +28.2), at 0.26× the owner's reading.

- **The night builds recorded 27 and 32 questions** in plain business words: "Shift pay: overtime starts after how many hours in a week, and at what multiple of the hourly rate (we assumed after 40 hours at 1.5x)?" He answered each in a sentence or two.
- **His answers stated the policy almost whole.** The judge found 23 and 25 of 25 decisions right in his Q&A, against 14 and 14 in the hand-over's corrected sheet.
- **The same pattern as Gates 66 and 68:** answering a question gets his rule; reviewing a finished build gets what a skimmer notices.

## Setup

- **Rules:** two fresh rule sets (g70a, g70b; published after scoring in `referee/oracle_g70*.py`). Predictions pushed before the run (`3e106d2`).
- **The owner:** Gate 66's person model. He answered recorded questions one at a time (`prompts/owner_qa.md`) and skimmed when reviewing.
- **N0 and QN:** 3 builders each, overnight. QN was told to record a question for every open business decision (`referee/queue_question.py`), build its best guess, and keep going.
- **HV:** Hive's hand-over as shipped (code sheet, list review, spot checks of every function), then 3 fresh builders.
- **QA:** 3 fresh builders given his morning answers.
- Builders cost $5.34 in all.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| M1 | QA ≥ HV + 10 | **Held:** +19.2 |
| M2 | QA's owner reads ≤ 0.3× HV's | **Held:** 0.26× |
| M3 | QA ≥ QN + 15 | **Held:** +54.8 |
| Ship | M1 and M2 | **Fired** |

## What changes in Hive

`hive start --overnight` now runs the builders in "questions for the morning" mode (`hive/owner.py`):
- `hive ask` records the question and returns at once;
- builders are told to record a question for every open business decision, build their best guess, and keep going;
- `hive answers` lists what teammates have recorded.

When the build is done:
- **Phone connected:** Hive sends the questions one at a time and he taps or types.
- **Otherwise:** he types `hive morning` and answers them in the terminal.
- **Then:** a fix round builds his answers in (`start._answer_and_fix`), and the branch is updated. No hand-over follows (Gate 68).

Builders still record assumptions, so a night that recorded no question falls back to the old morning review.

## Limits

- A synthetic owner who answers consistently from his policy. A real founder's answers drift (Gates 36–38).
- QA's builders started fresh from the starting repo. The product's fix round changes the night build instead.
- The phone version of the morning questions reuses the live-question bridge (`telegram.bridge_questions`), which has its own tests. The new morning call through it is not yet tested end to end.

## Files

`prompts/` (owner, builder and judge briefs; predictions).

`referee/`:
- `review70.py`, `queue_question.py`, `analyze.py`;
- the published rule sets.

`results/g70a/`, `results/g70b/`:
- the recorded questions (`queue_QN.jsonl`);
- his answers, the hand-over's sheets and labels (`sheet.json`);
- probes, agents and run logs.
