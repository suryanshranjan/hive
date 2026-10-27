# Gate 15 predictions, registered before the rules exist (Oct 27 2026)

**Question.** The decision tour works (Gates 13, 14: 89–96% hidden), but every tour so far came from an owner that could list its own decisions. A real owner has documents and habits, not a list. **Can a tour be built from a policy handbook, which states some decisions clearly, some vaguely and leaves some out? And is it better to turn the handbook into owner-answered examples, or to hand the handbook to the builders?**

**Design (one command: `python3 lab/run_gate.py lab/experiments/g15_handbook.json`).**
- **Rules.** A fresh independent rule-giver: Gate 13's brief plus a prose `HANDBOOK` (`gates/gate15/prompts/rulegiver_brief.md`). Of the 50 decisions, 20 are stated clearly, 15 vaguely and 15 not at all; each decision's status is declared privately in `HANDBOOK_STATUS`. Not edited.
- **Extractor.** A separate headless agent sees only the handbook and the one-line spec (`gates/gate15/prompts/extractor_brief.md`). It picks at most 50 inputs, each meant to show one decision. The owner (oracle) answers them, and the answers become visible tests. Inputs equal to a TYPICAL or EDGE input are dropped, the rule the owner's tour also obeys.
- **Teams** (3 builders each, no questions):
  - **N0:** nothing.
  - **T:** the owner's own decision tour (upper bound).
  - **H:** the handbook (`HANDBOOK.md`).
  - **X:** the owner's answers at the extractor's inputs. Same ask text as T.
- **Hidden suite.** 25 tests per function (seed 15200000), 70% edge calls.
- **Analysis.** Registered as code: `gates/gate15/referee/analyze.py`.

| # | Prediction |
| --- | --- |
| X1 | A handbook-derived tour keeps at least half of the owner's tour gain: X − N0 ≥ 0.5 × (T − N0) |
| X2 | Owner-answered examples beat reading the handbook: X ≥ H |
| X3 | The owner's own knowledge still matters: T − X ≥ +5 points |
| X4 | Omitted decisions are the remaining floor: X fixes ≥ 0.15 more of N0's edge errors on functions with no omitted decision than on functions with at least one |
| X5 | Treatment delivered: the extracted tour keeps ≥ 40 inputs; every team passes its visible tests |
| X6 | Rules not guessable: N0 below 70% hidden |

Kills and decision rules:
- **X − N0 < 0.25 × (T − N0):** extraction fails. A tour needs an owner who can list their own decisions, and Hive's intent step must start with eliciting that list from a person.
- **X1 and X2 hold:** the intent interface's first step becomes "an extractor turns the owner's documents into examples, and the owner answers them".
- **H ≥ T − 5:** the handbook alone nearly matches the tour. Writing things down is what matters, and the example format adds little.

**No pre-flight simulation.** This is the first extractor run.

**Honest prior.** X1 about 55%; X2 about 55%; X3 about 75%; X4 about 60%.

**Cost.** About $10 at list price (rule-giver, extractor, 12 builders); about 12 minutes.
