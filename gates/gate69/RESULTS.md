# Gate 69 results: does Hive need less of the owner the more he uses it, when builders ask? Nov 1 2026

**Question** (following Gates 66–68, under the user's "go on and on"). With builders who ask, intent flows through questions. Across three features of one business, do kept answers, and house rules distilled from them, cut the questions later builds need while staying as right?

**Answer.**
- **No. Neither rule fired.** All four predictions failed.

| Features 2 and 3 pooled | Questions he answered | Hidden pass (mean) |
| --- | --- | --- |
| F: fresh each feature (Hive as shipped) | 41 | 95.6% |
| M: earlier answers kept | 39 | 95.6% |
| C: answers plus house rules | 34 | 89.6% |

- **Asking already gets nearly everything, from scratch.** Feature 1, built by builders who asked 14 questions, passed 125 of 125 hidden tests. The same feature through Gate 67's hand-over passed 73.6%. With so little left to gain, memory has little to save.
- **House rules saved a few questions and cost correctness.** C asked 17% fewer, but builders applied the general rules where the function had its own decision, and lost 6 points. The distilled rules were accurate ("rounded up to the next whole unit, never half-up"; "a boundary value belongs to the lower band"). They were stretched where they did not apply, as rulings were in Gate 41.
- **Kept answers alone changed nothing** (39 vs 41 questions; 95.6% each). Builders asked about each new function's own decisions, which earlier answers do not settle.

## Setup

- Gate 67's business (published), with new draws (seeds 69101–69103, 69200000–69400000).
- 3 builders per build, told to ask first and to read the answers given so far. Each arm had its own owner on call (Gate 68's server).
- No hand-over: each build was scored directly.
- Feature 1 was shared; F, M and C branched from feature 2.
- Predictions pushed before the run (`7e014e7`). Builders cost $3.54.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| A1 | C asks ≤ 0.7× F's questions | **Failed:** 0.83× |
| A2 | M asks ≤ 0.85× F's | **Failed:** 0.95× |
| A3 | C's hidden ≥ F's − 2 | **Failed:** −6.0 |
| A4 | C's hidden ≥ F's + 3 | **Failed:** −6.0 |
| Ship / Kill | | **Neither fired** (C asked 0.83×, under the kill's 0.85×) |

## What it means

1. **No product change.** Hive does not carry answers across builds, and does not distil house rules. Gates 67 and 69 agree: neither memory nor house rules compounded.
2. **Hive's long-run edge over a one-shot agent is not memory.** With asking builders, each feature costs the owner about 14–22 short questions and comes out at 90–100%. What is left to win is his time per question and his trust, not correctness.

## Files

`prompts/` (house-rule brief for answers, predictions), `referee/` (`run69.py`, `analyze.py`).

`results/`:
- every feature's questions and answers, house rules in, and score (`feature_*.json`, `owner_*.jsonl`);
- probes, agents and the run log.
