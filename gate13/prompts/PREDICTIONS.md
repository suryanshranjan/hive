# Gate 13 predictions, registered before the rules exist (Oct 27 2026)

**Question.** Gate 12 found a floor: about a fifth of the errors were never fixed, however many questions builders got, because they sat at decisions no builder thought to probe. Builders choose where to point their questions, and they cannot point at what they cannot imagine. The product owner wrote the decisions and knows where they are. **If the owner points, one worked example per decision, does that beat the same number of answers at points the builders chose?**

**Design (one command: `python3 lab/run_gate.py lab/experiments/g13_tour.json`).**
- **Rules.** A fresh independent rule-giver, Gate 12's brief plus one addition (`gate13/prompts/rulegiver_brief.md`): `DECISION_EXAMPLES`, one example per declared decision, none of them a TYPICAL or EDGE input. Decisions per function: 1, 2, 3 and 4, five functions each, so 50 examples in all. `run_gate.py` checks counts and disjointness and edits nothing.
- **The tour.** The 50 examples become visible tests (`<function>_tour_<n>.json`, up to 3 calls each) in the starting repo of teams T and TQ only. The hidden suite draws only on TYPICAL and EDGE inputs, so no hidden test is copied. A team that hardcodes tour inputs gains nothing hidden.
- **Teams** (3 builders each, same prompt, ask texts in `lab/experiments/g13_ask_texts.md`):
  - **N0:** no tour, no questions.
  - **T:** tour, no questions (50 answered values chosen by the owner).
  - **Q:** no tour; 17 questions for the whole team, up to 51 answered values chosen by the builders.
  - **TQ:** tour plus 17 questions.
- **Hidden suite.** 25 tests per function (seed 13200000), 70% edge calls.
- **Analysis.** Registered as code: `gate13/referee/analyze.py`. fixed_X = edge calls right in X minus right in N0.

| # | Prediction |
| --- | --- |
| M1 | Owner-chosen points beat builder-chosen points of the same number: fixed_T / fixed_Q ≥ 1.3 |
| M2 | Tour plus questions breaks the questions-only ceiling: TQ fixes ≥ 0.80 of N0's edge errors (Gate 12's Q4, with 80 questions: 0.76) |
| M3 | The tour reaches what questions do not: of edge calls wrong in both N0 and Q, T gets ≥ 0.50 right |
| M4 | Treatment delivered: Q and TQ each use ≥ 15 of 17 questions; T and TQ pass every tour test at the end |
| M5 | Rules not guessable: N0 below 70% hidden |

Kills and decision rules:
- **fixed_T ≤ fixed_Q:** owner pointing is no better than builder pointing. Drop the decision tour; the floor needs another explanation.
- **M1 and M3 both hold:** make the decision tour the first step of Hive's intent interface. The next problem becomes how an owner produces one cheaply.
- **T passes its tour tests but M3 fails:** one example per decision pins a point, not a rule (Gate 4's lesson). Next, test 2 examples per decision.

**No pre-flight simulation.** No earlier gate measured a tour, so there is no noise model for T. For scale: Gate 11's 30-question head-to-head ratio had a 95% interval of 1.00 to 1.78 around 1.25.

**Honest prior.** M1 about 70%, M3 about 55%, M2 about 50%.

**Cost.** About $11 at list price; about 10 minutes.
