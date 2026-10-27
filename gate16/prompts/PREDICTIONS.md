# Gate 16 predictions, registered before the rules exist (Oct 27 2026)

**Question.** Gate 15 built a tour from a policy handbook: an extractor agent picked inputs and the owner answered them (80.6% hidden, against 92.6% for the owner's own tour). The gap sits at decisions nobody wrote down. **Does the full stack (handbook, extracted tour and builder questions together) close it?** This is the candidate intent interface for owners who have documents rather than a list of their decisions.

**Design (one command: `python3 lab/run_gate.py lab/experiments/g16_stack.json`).**
- **Rules and extractor.** As in Gate 15 (same rule-giver brief and extractor brief), with a fresh independent rule-giver and new seeds. The handbook states 20 of 50 decisions clearly, 15 vaguely and leaves 15 out (declared privately). The copy rule is unchanged: extractor picks equal to a TYPICAL or EDGE input are dropped.
- **Teams** (3 builders each, same prompt):
  - **N0:** nothing.
  - **X:** the extracted tour (replicates Gate 15's X).
  - **HX:** the handbook and the extracted tour.
  - **HXQ:** the handbook, the extracted tour and 17 questions for the team.
- **Hidden suite.** 25 tests per function (seed 16200000), 70% edge calls.
- **Analysis.** Registered as code: `gate16/referee/analyze.py`.

| # | Prediction |
| --- | --- |
| S1 | The full stack reaches 90% hidden: HXQ ≥ 90% |
| S2 | The handbook adds to the extracted tour: HX − X ≥ +3 points |
| S3 | Questions add to handbook and tour: HXQ − HX ≥ +3 points |
| S4 | The extracted tour replicates: X − N0 ≥ +25 points (Gate 15: +36) |
| S5 | The stack closes the floor: on functions with an omitted decision, HXQ fixes ≥ 0.85 of N0's edge errors (Gate 15's X: 0.70) |
| S6 | Treatment delivered: HXQ uses ≥ 15 of 17 questions; every team passes its visible tests |
| S7 | Rules not guessable: N0 below 70% hidden |

Kills and decision rules:
- **HXQ < 85% and HXQ ≤ HX:** stacking does not close the floor. Unwritten decisions need the owner's own knowledge, so the interface must start by drawing the owner's decision list out of them.
- **S1 and S5 hold:** the documented-owner interface is complete enough: handbook + extracted examples answered by the owner + builder questions, with answers as tests.
- **S2 fails (HX ≤ X):** do not ship the handbook alongside the examples; the examples carry it.

**No pre-flight simulation.** One prior run of X (Gate 15). Two-point differences are inside single-run noise (Gate 15's paired intervals were about ±10), so S2 and S3 are weak tests on their own.

**Honest prior.** S1 about 50%; S2 about 50%; S3 about 60%; S4 about 75%; S5 about 45%.

**Cost.** About $11 at list price; about 12 minutes.
