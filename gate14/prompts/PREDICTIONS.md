# Gate 14 predictions, registered before the rules exist (Oct 27 2026)

**Question.** Gate 13's decision tour (one owner example per policy decision) lifted hidden correctness from 57.8% to 89.4%, but it is one run on one rule set. Its failure mode was over-generalization: shown one leniency ("dashes are stripped"), builders loosened neighbouring rules (27 edge calls broken). Two questions:
1. Does the tour's advantage replicate on a new rule-giver?
2. Does pairing each decision with a **contrast**, a nearby input the decision does not cover, stop the stretching?

**Design (one command: `python3 lab/run_gate.py lab/experiments/g14_contrast.json`).**
- **Rules.** A fresh independent rule-giver: Gate 13's brief plus `CONTRAST_EXAMPLES` (`gate14/prompts/rulegiver_brief.md`): one contrast per decision, close to its example but not covered by it. Decisions per function: 1, 2, 3 and 4, five functions each. `run_gate.py` checks that tour and contrast inputs are disjoint from TYPICAL, EDGE and each other, and edits nothing.
- **Teams** (3 builders each, no questions, same prompt):
  - **N0:** no tour.
  - **T:** the tour (50 examples).
  - **TC:** the tour plus 50 contrasts.
- **Hidden suite.** 25 tests per function (seed 14200000), 70% edge calls, drawn only from TYPICAL and EDGE.
- **Analysis.** Registered as code: `gate14/referee/analyze.py`. broken_X = edge calls right in N0 but wrong in X.

| # | Prediction |
| --- | --- |
| C1 | The tour replicates: T − N0 ≥ +20 points hidden (Gate 13: +31.6) |
| C2 | Contrasts stop the stretching: broken_TC ≤ 0.5 × broken_T (untestable if broken_T < 10) |
| C3 | Contrasts do not cost correctness: TC hidden ≥ T hidden |
| C4 | Treatment delivered: T and TC pass all their tour (and contrast) tests at the end |
| C5 | Rules not guessable: N0 below 70% hidden |

Kills and decision rules:
- **C1 fails (T − N0 < +10):** Gate 13's tour result was specific to its rule set. Demote the tour from "step one" to "promising".
- **C2 holds:** contrasts become part of the tour format (each decision ships as an example and a contrast).
- **C2 fails and C3 fails:** contrasts add nothing. Over-generalization is left to questions (Gate 13: tour plus questions broke 15).

**Confound, stated before the run.** TC sees 100 examples against T's 50, so a higher TC score partly reflects more examples. C2 targets the mechanism (calls broken, not total score), which is less affected by that.

**No pre-flight simulation.** One prior tour run exists. Its broken count (27) suggests C2 can be tested; Gate 13's per-function noise is the only reference.

**Honest prior.** C1 about 80%; C2 about 45%; C3 about 70%.

**Cost.** About $8 at list price; about 10 minutes.
