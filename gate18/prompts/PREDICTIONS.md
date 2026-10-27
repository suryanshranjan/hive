# Gate 18 predictions, registered before the run (Oct 27 2026)

**Question.** Gates 13 to 17 showed that owner-given worked examples (a decision tour) carry intent far better than builder questions. But every rule set there was written by an agent. **Does the tour still work on a real company's rules?** Gate 7's company (Company X, anonymous) is the only real rule set this lab has. With 15 builder questions on it, Gate 7 reached 49.6% hidden.

**Design (`python3 lab/run_gate.py lab/experiments/g18_real.json --oracle <private wrapper>`).**
- **Rules.** Gate 7's 10 real business functions, as confirmed by the user (the founder) against the company's documents. They are kept outside this repo, wrapped privately for the lab's runner. No rule-giver runs.
- **Tour.** Gate 7's QA edge cases, which the user checked row by row in a check table, are split in half per function by a fixed shuffle (`random.Random(18000)`): **56 cases** become visible tour tests for teams T and TQ; **60** stay as the hidden edge inputs. 5 of the 60 hidden inputs (8%) are strict near copies of a tour input (equal after removing case, spaces and dashes, or numbers within 1%). This is reported, not hidden.
- **What "owner-chosen" means here.** These cases were drafted by an agent in Gate 7 and confirmed by the owner, not chosen by the owner. That is weaker than Gates 13 to 17's tours, which the owner wrote directly.
- **Specs.** Gate 7's original one-line specs are not available, so the specs are new and written neutrally: purpose and argument names only, with no rule, threshold or list of allowed values. They were written by an agent that knows the rules; any leakage would help every team equally.
- **Teams** (3 builders each): **N0** (nothing); **T** (tour); **Q** (19 questions for the team, up to 57 values, matched to the tour's 56); **TQ** (tour plus 19 questions).
- **Hidden suite.** 25 tests per function (seed 18200000), 70% edge calls from the held-out half.
- **Privacy.** Only aggregate numbers are committed: hidden pass, paired differences, counts. The oracle, specs, probes, questions, answers, logs and swarm histories stay private. The analysis code (`gate18/referee/analyze.py`) prints aggregates only.

| # | Prediction |
| --- | --- |
| R1 | The tour works on real rules: T − N0 ≥ +20 points |
| R2 | Owner-confirmed points beat builder-chosen points of the same size: fixed_T / fixed_Q ≥ 1.3 |
| R3 | Tour plus questions passes Gate 7's best by far: TQ ≥ 75% hidden (Gate 7: 49.6%) |
| R4 | Treatment delivered: Q and TQ each use ≥ 17 of 19 questions; T and TQ pass every tour test |
| R5 | Rules not guessable: N0 below 70% hidden |

Kills and decision rules:
- **T − N0 < +10:** the tour does not carry a real company's intent. Gates 13 to 17 were an artefact of agent-written rules.
- **R1 and R3 hold:** the decision tour is confirmed on real rules, and Hive's intent interface leads with owner-confirmed examples.

**Honest prior.** R1 about 75%; R2 about 60%; R3 about 55%. Real rules have been harder to guess (Gate 7's no-question team: 32.8%).

**Cost.** About $9 at list price; about 10 minutes.
