# Gate 17 predictions, registered before the rules exist (Oct 27 2026)

**Question.** Two versions of Hive's intent interface have been measured on different rule sets: an owner who lists their own decisions (tour + questions: 95.2%, Gate 13), and an owner who only has documents (handbook + extracted tour + questions: 83.2%, Gate 16). Gate 16 also found that the copy rule penalized the extractor by dropping its best picks. **On the same rules, with a fair copy rule, how big is the gap between the two owners?** That decides whether drawing a decision list out of a person is worth building.

**Design (one command: `python3 lab/run_gate.py lab/experiments/g17_owners.json`).**
- **Rules and extractor.** As in Gates 15 and 16 (same briefs), with a fresh independent rule-giver and new seeds: 20 decisions clear, 15 vague, 15 omitted in the handbook.
- **Fair copy rule** (`"copy_rule": "exclude_from_hidden"`, new in `run_gate.py`). Extractor picks that equal a TYPICAL or EDGE input stay in the tour. Every hidden call equal to one is removed from scoring for every team, so nothing is copied and nothing is penalized.
- **Teams** (3 builders each; ask texts `lab/experiments/g17_ask_texts.md`):
  - **N0:** nothing.
  - **X:** the extracted tour.
  - **HXQ** (documented owner): handbook, extracted tour and 17 questions.
  - **TQ** (listing owner): the owner's own decision tour and 17 questions.
- **Hidden suite.** 25 tests per function (seed 17200000), 70% edge calls.
- **Analysis.** Registered as code: `gates/gate17/referee/analyze.py`.

| # | Prediction |
| --- | --- |
| F1 | With the fair rule, the extracted tour gains more than before: X − N0 ≥ +30 points (Gates 15, 16 under the old rule: +36.0, +19.4) |
| F2 | The listing owner beats the documented owner: TQ − HXQ ≥ +5 points |
| F3 | The documented-owner stack reaches 85%: HXQ ≥ 85% |
| F4 | The listing-owner stack reaches 92%: TQ ≥ 92% (Gate 13: 95.2%) |
| F5 | Treatment delivered: HXQ and TQ each use ≥ 15 of 17 questions; every team passes its visible tests |
| F6 | Rules not guessable: N0 below 70% hidden |

Decision rules:
- **TQ − HXQ < +3:** with documents, extraction and questions, a documented owner is about as good as one who lists their decisions. Hive does not need a decision-elicitation step for owners with documents.
- **TQ − HXQ ≥ +5:** a step that draws the owner's decision list out of them is worth building and testing with people.
- **F1 fails (X − N0 < +20):** the extracted tour is weak even when fairly scored. The documented-owner interface leans on handbook and questions.

**No pre-flight simulation.** Single-run paired intervals in Gates 15 and 16 were about ±10 to ±13 points, so F2's +5 threshold can be missed by noise either way.

**Honest prior.** F1 about 55%; F2 about 60%; F3 about 50%; F4 about 70%.

**Cost.** About $11 at list price; about 12 minutes.
