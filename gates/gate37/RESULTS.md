# Gate 37 results: an interview from the code's decisions, and how stable the owner's rules are, Oct 28 2026

Only aggregate numbers are published. The situations, the founder's verdicts and answers, and the code stay private.

**Question.** Gate 36's interview, written from the feature description, covered too little. Here Hive wrote its interview from the decisions the code must take (one situation per decision). With that coverage, do the owner's answers carry his surprising rules into the code? And does he give the same rule when the same situation is framed differently?

**Answer: coverage is solved, and the code followed his interview answers. But those answers disagreed with his answers to the referee's framing of the same decisions, so the score did not move (0/4 both arms), and arm I lost 2 ordinary cases.** The limit is no longer where Hive asks, or how answers reach the code. It is that this owner's rule for a decision depends on how the situation is put to him.

| Measure | Arm N (no owner) | Arm I (interview first) |
| --- | --- | --- |
| **Surprising cases** (4 scored) | **0 / 4** | **0 / 4** |
| Ordinary cases | 4 / 4 | **2 / 4** |
| Existing backend tests | 384 / 384 | 384 / 384 |
| Owner rules given to the builders | 0 | 20 |
| Builders, minutes, cost | 4, 39 min, $3.44 | 4, 31 min, $3.74 |

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| S1 | I beats N by ≥ 30 points on surprising cases | **Failed:** 0 points (0/4 each) |
| C2 | ≥ 80% of surprising hidden cases have a matching interview situation | **Held:** 6 of 6 (Gate 36: 4 of 9) |
| K1 | Same rule on ≥ 4 of 6 reframed situations | **Failed:** 3 of 6 |
| S2 | Ordinary ≥ 75% in both arms | **Failed in I:** 2 / 4 (N: 4 / 4) |
| S3 | Existing tests pass | **Held** |
| S4 | Interview active time under 8 minutes | **Failed:** 15.6 minutes, and redundant (below) |
| Kill | I − N < 10 points with C2 held | **Fired** |

## Why the score did not move

**The interview's answers did reach the code.** On the scored decisions where arm I differs from arm N, it follows his interview answer every time (4 of 4, by the experimenter's reading). Transfer from answer to code worked.

**But the same owner, the same evening, answered the two framings differently.** A blind judge compared each hidden situation with the interview situation about the same decision (3 votes each; post hoc, run after scoring):

| Same decision, two framings | Same rule | Different rule | Too vague to say |
| --- | --- | --- | --- |
| Hidden set vs Hive's interview, same session, about 20 minutes apart (8 pairs) | 1 | 5 | 2 |
| Gate 36 situations reframed in Gate 37, one day apart (6 pairs, K1) | 3 | 3 | 0 |

The two ordinary cases arm I lost are both "different" pairs. The builders followed his interview answer, which disagreed with his hidden-set answer. The one "same" pair still failed in both arms. His rule depended on a fact the fixed interface does not carry, so the builders could not apply it.

## The interview itself

- **Coverage held, with room to spare:** 20 situations, one per decision, covered every surprising hidden situation.
- **It was redundant, and he said so.** The planner asked about some decisions twice, at different numbers of days. From the 12th question on he answered in 2 to 5 seconds each. Fixed after the session (`f5fccc1`): one question per decision, the cut-off named in the options, a final pass that drops same-decision pairs, and skipping questions his own words already settle.
- **A stale-tap reply fired twice,** pointing him back to the current question (Gate 36's 1 h 42 min stall did not recur).

## What it means, across Gates 30 to 37

| Gate | Channel | What limited it |
| --- | --- | --- |
| 27–29 | Questions, memory | The owner matched the default; nothing to add |
| 30–31, 35 | Review after the build | He does not audit lists: half found, all kept, none marked |
| 36 | Interview from the description | Coverage (4 of 9) and framing (2 of 2 covered cases differed) |
| **37** | **Interview from the code's decisions** | **Framing:** coverage 6 of 6, transfer worked, but his answers to two framings agreed on only 1 of 8 (same session) and 3 of 6 (a day apart) |

- **Established for this owner** (two gates, 14 pairs, blind-judged): on decisions where he differs from the default, his answer to a concrete situation is not a stable rule. It changes with the wording, the example and the options offered. Any hidden set is one framing of his rules, so no intent channel scored against one framing can show more than his agreement with himself.
- **Conjecture:** for many such decisions the owner has no settled policy until he is asked. The question creates the rule. Then Hive's job is not to extract a rule that already exists, but to make him **decide once, knowingly**: show the decision as a general rule, with the cases it covers, and get it confirmed. When two of his answers on the same decision disagree, show both and ask which is the policy. Gate 34b's consistent synthetic owner went 0/8 → 7/8 through the same machinery.
- **Method change:** future referees should be built from rules he has **confirmed as general statements**, not from single answers to one framing. Consistency should be measured in every gate, as here.

## Limits

- One founder, one feature, one run per arm; 4 scored surprising cases (one is 25 points).
- The same-session agreement table is post hoc, and its pairs come from the coverage judge's matches.
- His answers late in the interview were fast, after redundant questions, which may have lowered agreement. The day-apart retest (K1, 3 of 6) had no such strain and still split in half.
