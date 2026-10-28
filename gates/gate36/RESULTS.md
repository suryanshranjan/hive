# Gate 36 results: interview first, with Hive writing its own questions, Oct 28 2026

Only aggregate numbers are published. The situations, the founder's verdicts and answers, and the code stay private.

**Question.** Hive now interviews the owner before building: from the feature description alone, it writes the situations where his rules are likely to matter, asks him on his phone, and gives his answers to the builders as rules to encode as tests. Does that carry the owner's surprising rules into the code? The referee is a separate hidden set of situations, written by the experimenter, that neither arm saw.

**Answer: no, and the kill fired.** Both arms passed the same 2 of 7 surprising hidden cases. Two things stopped the interview, and the second is the more important:

1. **Coverage.** Written from the description alone, Hive's 12 questions asked about only 4 of the 9 surprising hidden situations (blind judge, unanimous on every case), and only 2 of the 7 scored ones. Most of its questions were about things the feature's interface does not decide (bonuses, team roles, deadlines moved by a pause).
2. **The owner's answer depended on how the situation was framed.** On both scored cases the interview did cover, the founder's interview answer pulled the opposite way from his hidden-set verdict on the same situation, given the same day. No build could satisfy both.

| Measure | Arm N (no owner) | Arm I (interview first) |
| --- | --- | --- |
| **Surprising cases** (7 scored) | **2 / 7** | **2 / 7** |
| Ordinary cases | 2 / 2 | 2 / 2 |
| Existing backend tests | 384 / 384 | 384 / 384 |
| Owner rules given to the builders | 0 | 9 (from 12 situations) |
| Builders, minutes, cost | 4, 37 min, $3.47 | 4, 31 min, $3.27 |

The two arms took the same decision on every scored case. They differed only on situations the hidden set does not score: what an added deliverable does to signed creators, and what a relaunch does to old collaborations. The interview did change the code, but not where the referee looked.

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| S1 | I beats N by ≥ 30 points on surprising cases | **Failed:** 0 points (2/7 each) |
| C2 | ≥ 50% of surprising hidden cases have a matching interview situation | **Failed:** 4 of 9 (44%); 2 of the 7 scored |
| S2 | Ordinary ≥ 75% in both arms | **Held:** 2 / 2 each |
| S3 | Existing tests pass in both arms | **Held:** 384 / 384 each |
| S4 | The interview takes under 6 minutes | **Failed:** 124 minutes, 102 of them stuck on a tool bug (below) |
| Kill | I − N < 10 points | **Fired** |

## What went wrong in the tool, and what was fixed

The interview ran through Hive's real code on the founder's phone, and it broke in ways no stand-in owner had shown:

- **The first run never sent its questions.** The process hung, then died on a dropped connection. Telegram's "two readers at once" error arrived as an exception the retry did not catch.
- **On the restart, a tap on an older message's button was dropped in silence.** He answered, nothing happened, and he waited 1 h 42 min on a question he thought he had answered. Once he was pointed at the right message, he finished the remaining checks in 5 minutes. Several of the later replies said, in effect, "you decide", a fair answer to a broken experience.
- **Two bugs in reading his own words.** A yes in his own words was stored as the rule itself, and a correction lost the situation it was about.
- **The first build launch died at once:** the container's Claude login had expired. That launch was void and rerun.

All of these are fixed and tested (commits `e1778da`, `89472c9`, `6607ca4`, `9711573`):
- Sends and polls survive dropped connections and a second reader.
- Every interview answer is saved as it comes, so a stop resumes at the first unanswered question.
- A tap on an old button is answered and pointed at the current question.
- A yes in any words keeps the reading, "you decide" gives no rule, and a correction keeps its situation.
- A builder stopped by a usage limit or an expired login is told so, and picks up again in its own clone once the limit resets or the login works. Before, the run was written off (Gate 35's first build).
- An interview answer that contradicts an earlier ruling is put to the owner before the builders get both.

Arm I's 9 rules came from the fixed reading logic, applied mechanically to the answers he actually gave and registered before the build: 3 taps, 3 rules in his own words, 3 corrections kept with their situation. Two replies left the decision to the builders, and one confirmed reading was lost to the bug.

## What it means

Gates 30 to 35 showed that this owner's rules come out when he is asked about concrete situations before a build, not when he audits a list after it. Gate 36 adds two limits to that:

- **Which situations to ask.** A model that knows only the feature description does not find where this owner's rules matter: it covered 44% of them, close to Gate 33's 35% for predicting his surprising answers. The questions should come from the decisions the build will actually make (the interface, or the builders' plan), not from the description alone. **Conjecture,** to be tested.
- **The owner is not one fixed rule set.** The same person, on the same day, gave opposite answers to two framings of the same situation, twice out of two covered cases. That is a ceiling for every intent channel measured so far, and the hidden tests inherit it: the referee itself is one framing of his rules. **Established for this owner, n = 2;** how often it happens is not measured. Hive's new contradiction check is the product side of this: when two of his answers clash, ask him which holds.

## Limits

- One founder, one feature, one run per arm. Two scored cases were dropped because their readings were not confirmed, so one case is 14 points.
- The interview was damaged by tool failures. A clean interview would have the same coverage (the questions were fixed before he answered), so S1 and C2 fail on coverage alone. But his answers on the uncovered rest may have been less careful after the stall.
- The coverage judge saw situations only (no answers), with 3 votes per case, all unanimous.
