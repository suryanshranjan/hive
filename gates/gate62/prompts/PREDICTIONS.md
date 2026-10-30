# Gate 62 predictions: a second build from a different model (mechanical, no owner)

Registered Oct 30 2026, before the run. A follow-up to Gate 60 under the user's "Run the tests as required". No owner, no Telegram.

## Why this test

Gate 60's two wings failed because both builds came from the same model and shared their wrong guesses. Where the first build was wrong, the second disagreed only 19% of the time. A second build from a different model might guess differently, and Hive can already mix agents (Gate 47). Whether such a build finds the owner's decisions is a mechanical question, answerable without any owner, and an owner test is worth running only if the answer is yes.

## Setup

- For each of Gate 60's runs (g60a: Gate 55's rules; g60b: the fresh set), three more builds from its starting repo, with the same prompt and no owner, 3 builders each:
  - **So:** Sonnet, the default builder model (Gate 60's N0 and B were Sonnet), as the same-model replicate;
  - **Op:** Opus;
  - **Ha:** Haiku.
- Each build runs Gate 60's 300 prober calls (`gates/gate60/referee/wings.py`).
- **recall:** of the calls where Gate 60's N0 differs from the policy, the share where the wing's result differs from N0's.
- **precision:** of the calls where the wing differs from N0, the share where N0 is wrong.
- Pooled over both runs. Driver `referee/run62.py`, analysis `referee/analyze.py`, both committed now.

Codex and Gemini are not installed in this lab, so the other models are Claude models of different sizes. Their builds are less independent than another vendor's.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| G1 | Haiku's recall ≥ 0.35 | 45% |
| G2 | Opus's recall ≥ the Sonnet replicate's + 0.10 | 30% |
| G3 | The Sonnet replicate's recall is within 0.10 of Gate 60's B | 70% |
| G4 | Every wing with recall ≥ 0.35 has precision ≥ 0.50 | 40% |

## Decision rules

- **Go:** an Opus or Haiku wing reaches recall ≥ 0.50 with precision ≥ 0.50. Then an owner test of two wings, with that model as the second build, is worth registering.
- **Stop:** no wing reaches recall 0.35. Then two wings are not worth an owner test with Claude models. A second vendor (Codex on the owner's machine) remains the one untested option.

## Limits

- One build per model per rule set. The prober's calls are Gate 60's (written from the spec alone).
- About $10, most of it Opus.
