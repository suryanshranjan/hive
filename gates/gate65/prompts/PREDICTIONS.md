# Gate 65 predictions: an Opus spotter for Hive's own judgement call

Registered Oct 30 2026, before the run. Asked for by the user ("Go on", after "a stronger model for Hive's own judgement calls, not the builders"). Synthetic owner only.

## Why this test

- **Builders:** model choice does not matter for them. On intent-bound jobs every model guesses the owner's rules the same way (Gate 62). On hard engineering, cheaper models are not cheaper per job, and an Opus planner does not help (Gate 64).
- **The spotter:** Hive's spotter is one model call per build, and its picks are what found the owner's decisions (Gates 58, 63). It asks "what would a business owner decide differently here?", which is judgement, not engineering. A stronger model may pick cases that matter more. It costs one call, not a team.

## Setup

- From Gate 60's records, for both rule sets (g60a: Gate 55's rules; g60b: the fresh set): the same N0 build, sheet D, the owner's list review SL, policy and owner brief.
- **CS:** SL, then the spot checks Gate 60's spotter wrote (the default model, Sonnet).
- **CO:** SL, then the spot checks an Opus spotter writes now, from the same code with the same brief (`claude -p --model opus`).
- **Both arms:**
  - cases on every function, untouched ones first (Gate 63's hand-over);
  - a fresh owner session each;
  - each correction applied alone and re-shown (Gate 58's machinery).
- A judge labels D, SL, CS, CO and R together.
- 3 fresh builders build each of CS and CO from Gate 60's starting repo, probed on Gate 60's hidden suite.

Driver `referee/run65.py`, analysis `referee/analyze.py`, both committed now.

## Predictions (pooled over both runs, 50 decisions)

| # | Prediction | Odds |
| --- | --- | --- |
| K1 | CO states ≥ 3 more decisions right than CS | 35% |
| K2 | Hidden CO ≥ CS + 3 | 35% |
| K3 | The Opus spotter writes at most 1.3× as many cases (it does not win by asking more) | 60% |
| K4 | CO spoils at most 1 decision SL had right | 70% |

## Decision rules

- **Ship:** K1 and K2 hold. Hive's spotter runs on Opus (one call per build).
- **Kill:** CO is no better than CS on decisions and on hidden. The spotter stays on the default model.

## Limits

- One owner session and one build per arm per rule set, with a synthetic skimmer. Owner noise alone can move a few decisions.
- About $15.
