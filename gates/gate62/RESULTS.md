# Gate 62 results: a second build from a different model, Oct 30 2026

**Question** (follow-up to Gate 60, under the user's "Run the tests as required"). Two Sonnet builds of the same spec share most of their wrong guesses, so their disagreements miss the owner's decisions (Gate 60). Does a build from a different model disagree with the first build where the first build is wrong? Mechanical, no owner.

**Answer.**
- **No. The stop rule fired.** No second build disagreed with the first on more than a quarter of its errors. Even three extra builds together (Sonnet, Opus, Haiku) reached 29%.

| Second build (pooled over 2 rule sets, 243 calls where N0 was wrong) | Disagrees with N0 where N0 is wrong (recall) | N0 wrong where they disagree (precision) | Disagreements |
| --- | --- | --- | --- |
| Gate 60's B (Sonnet) | 0.19 | 0.61 | 77 |
| Sonnet again (So) | 0.12 | 0.51 | 55 |
| **Opus (Op)** | **0.25** | 0.66 | 91 |
| Haiku (Ha) | 0.20 | 0.58 | 85 |
| Any of So, Op, Ha | 0.29 | 0.63 | 111 |

- **Opus disagrees most** (twice the Sonnet replicate: 0.25 vs 0.12), and Haiku no more than Sonnet. A stronger model guesses differently a little more often, but three builds of three sizes still agree on 71% of the first build's errors.
- **The owner's rules are not where builders split.** A rule a builder cannot guess from the spec ("platinum from 20,000 points", "a 500-cent minimum") is guessed the same natural way by every model. Disagreement measures how ambiguous the spec is to a builder, not how far the builder is from the owner.
- **Correctness:** the extra builds pass about as many hidden calls as N0 (426–473 of 700 against 443–484). No model reads the owner's mind.

## Setup

- For each of Gate 60's runs (g60a: Gate 55's rules; g60b: the fresh set), three more builds from its starting repo, with the same builder prompt and no owner, 3 builders each: Sonnet (the default builder model), Opus and Haiku (`claude -p --model …`).
- Each build ran Gate 60's 300 prober calls (written from the spec alone). Recall and precision are measured against Gate 60's N0, scored by the policy.
- Predictions pushed before the run (`cd8b716`).
- Builder cost: Sonnet $1.20, Opus about $3.3, Haiku $0.20.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| G1 | Haiku's recall ≥ 0.35 | **Failed:** 0.20 |
| G2 | Opus's recall ≥ the Sonnet replicate's + 0.10 | **Held:** 0.25 vs 0.12 |
| G3 | The Sonnet replicate within 0.10 of Gate 60's B | **Held:** 0.12 vs 0.19 |
| G4 | Every wing with recall ≥ 0.35 has precision ≥ 0.50 | **Held, vacuously:** no wing reached 0.35 |
| Go | | **Did not fire** |
| Stop | No wing reaches recall 0.35 | **Fired** |

## Disclosed: a referee fault, and the rescoring

- **The fault:** the first scoring of each run stopped at the hidden-suite probe. The oracle path was relative and the probe runs from `/`.
- **What was rescored:** every build had finished, so scoring was rerun with no rebuild (`G62_SCORE_ONLY=1`), after making the path absolute.
- **A premature rescore:** for g62b, scoring was first rerun while one Opus builder was still running. A rescore after it finished gave the same numbers, and those are reported.
- **Lost costs:** three concurrent launches overwrote one another's cost files, so builder costs are summed from the run logs. One Opus builder's final reply was not recorded, but its 3 functions landed.
- **One change to the analysis after the run:** `analyze.py` now also reads the gzipped copies in `results/`. Its logic is unchanged.

## What it means

1. **Two wings is closed for Claude models.** A second build costs money and finds about a fifth of what is wrong. The spotter, which asks "what would a business owner decide differently", stays (Gates 58, 60).
2. **A second vendor (Codex, Gemini) is the one untested option.** Given how uniformly three model sizes guess, the evidence points against it. Not worth the owner's time without a mechanical test like this one first.

## Limits

- One build per model per rule set, and the prober's 300 calls.
- All models are from one vendor.

## Files

`prompts/PREDICTIONS.md`.

`referee/`: `run62.py` and `analyze.py`.

`results/g62a/`, `results/g62b/`:
- every build's output on the 300 calls (`out_*.json.gz`), with the policy's outputs;
- hidden-call counts (`results.json`);
- run logs.
