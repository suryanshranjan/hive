# Gate 6 predictions, registered before the rules exist (Oct 27 2026, 15:25 IST)

**Why this design.** The test proposed after Gate 5 pitted "spread the budget" against free asking. Fed through our own questions-per-function table, it predicts an advantage of only 0 to 1 point of edge accuracy: free teams already reach 18 of 20 functions. One run's noise is about ±10 points, so that test could not have told us anything. Instead we measure the curve itself, with the number of questions per function **randomly assigned**. This turns the observational table (Gates 3 to 5) into an experiment.

**Rule-giver.** A new independent agent with the same neutral brief as Gate 5 (`rulegiver_brief.md`). Its rules are checked mechanically only, and not edited.

**Teams.** Three teams of 3 builders, one run each, on the same engine as Gates 3 to 5. They differ only in one paragraph of the prompt (`ask_texts.md`):
- **N0:** no questions.
- **N30f:** 30 free questions, the control.
- **NQ:** each function gets an allowance of 0, 1 or 3 questions, enforced by the product-owner server (`referee/ask_server_quota.py`). A question must be about exactly one function.

**Random assignment, fixed now.** Take the 20 function names sorted alphabetically and shuffle them with `random.Random(6000).shuffle`. The first 6 get 0 questions, the next 7 get 1, and the last 7 get 3: 28 questions in all.

**Hidden suite.** 25 tests per function (seed 6200000), 70% edge calls, from the rule-giver's own typical and edge lists. Visible examples: seed 6100.

**Measure.** Per function, gain = edge-call accuracy of NQ minus edge-call accuracy of N0 on the same function. Report the mean gain for each assigned allowance, with 95% intervals bootstrapped over functions. Also report by questions actually used.

| # | Prediction |
| --- | --- |
| K1 | Every team passes all visible examples |
| K2 | Questions cause the gain: functions allowed 3 questions gain at least 15 points more than functions allowed 0, and functions allowed 0 gain less than +8 |
| K3 | The first question is worth the most: gain at 1 ≥ half of gain at 3 (the observational table gave 58%) |
| K4 | Fourth replication: N30f − N0 between +15 and +43 points |
| K5 | Rules not guessable: N0 below 70% hidden |
| K6 | Treatment delivered: at least 25 of the 28 allowed questions are used |

Kills:
- If gain(3) − gain(0) < +5, the questions-per-function pattern was selection (builders asking where it pays), not cause.
- If K3 fails, concentrating questions beats spreading them.

Afterwards, by calculation and labelled as model: the best way to split 30 questions given the measured curve, and its predicted advantage over the free teams' allocations in Gates 4 and 5.
