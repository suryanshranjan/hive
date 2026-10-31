# Gate 68 results: builders who ask, a swarm against one agent, and the hand-over after, Nov 1 2026

**Question** (Gate 66's registered next step, under the user's "hive needs to surpass everything"). When builders can ask the owner, does Hive's swarm match one agent? And does Hive's hand-over still add anything after a build whose builders asked?

**Answer.**
- **The swarm matched one agent exactly, and the hand-over added almost nothing.** The registered rule fired: after a build whose builders asked the owner, Hive skips the long hand-over.

| Pooled over 2 fresh rule sets | Hidden pass | Owner's load per run | Cost per run |
| --- | --- | --- | --- |
| One builder, asks first (CQ) | 98.4% | 18.5 questions | $0.31 |
| **Hive's 3 builders, ask first, share answers (SQ)** | **98.4%** | 24.5 questions | $0.70 |
| SQ, then Hive's hand-over and a fresh build (SQH) | 100.0% | 24.5 questions + 57.5 review replies | $1.97 |

SQ − CQ = 0.0. SQH − SQ = +1.6 (95% CI 0.0 to +4.8).

- **Asking first is now near-perfect in the wind tunnel.**
  - Gate 66: 93%. Here: 96.8% and 100%.
  - The code sheet written from SQ's build already stated 23 and 25 of 25 decisions right before any review.
- **The hand-over found one remaining slip, in one run** (96.8 → 100%), at the price of 56–59 more owner replies. In the other run there was nothing to find.
- **Three builders asked a third more questions than one** (24.5 vs 18.5) despite reading each other's answers, and cost twice as much. On a job of this size their speed did not matter: both finished in 1–2 minutes.

## Setup

- **Rules:** two fresh rule sets (g68a, g68b; published after scoring in `referee/oracle_g68*.py`).
- **The owner:** Gate 66's owner on call, now able to list his answers so far (`ask_owner.py --answers`, like `hive answers`). He skims when reviewing.
- **Builders:** told to ask him about every open business decision before building each function. SQ's builders were also told to read the answers so far first.
- **SQH:** Hive's hand-over as shipped after Gate 63, on SQ's build, then 3 fresh builders from the corrected sheet.
- Predictions pushed before the run (`9afd71c`). Builders $3.39 in all.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| Q1 | SQ ≥ CQ − 3 | **Held:** 0.0 |
| Q2 | SQH ≥ SQ + 3 | **Failed:** +1.6 |
| Q3 | SQ asks ≤ 1.5× CQ's questions | **Held:** 1.32× |
| Registered rule | Q2 fails: skip the long hand-over after a build whose builders asked | **Fired** |

## What changes in Hive

1. **Builders ask first.** When the owner can answer, Hive's builders are told to ask him about every business decision the goal leaves open for an area *before* building it. They read the team's answers first (`hive owner` text, `hive/owner.py`). The question budget rises from 4 to 10 per builder (Gate 68's swarm asked about 8 each). The plain-language rules for questions stay; they came from the real founder (Gates 25–26).
2. **No long hand-over after a build he answered.** If the builders asked him at least 3 questions, `hive start` delivers with "They asked you N questions while building, and your answers are built in" and skips the code sheet and spot checks. The threshold of 3 is untested: Gate 68's builds asked 11–26.
3. **Overnight builds keep the hand-over** until Gate 70 (questions saved for the morning) is scored.

## Limits

- A synthetic owner who answers consistently from his policy. A real founder's answers drift (Gates 36–38). Concrete outcomes may matter more for him, which this gate cannot show.
- One run per arm per rule set.

## Files

`prompts/` (owner, builder and judge briefs; predictions).

`referee/`:
- `review68.py`, `owner_server.py` (now with `--answers`), `ask_owner.py`, `analyze.py`;
- the published rule sets.

`results/g68a/`, `results/g68b/`:
- every question and answer;
- the hand-over's sheets and labels;
- probes, agents and run logs.
