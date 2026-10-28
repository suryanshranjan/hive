# Gate 35 predictions, registered before the founder's verdicts (Oct 28 2026)

**Question.** Gate 34b showed that Hive's review carries an owner's unusual rules into code (0/8 to 7/8) when the owner answers every marked decision; that owner was synthetic. Gate 31 showed that the real founder finds his rules on the one-line list (8/9) but, with the old answering step, kept every one. **With the fixed answering step ("You marked this one. What would you do instead?"), does the real founder's review carry his surprising rules into the code?**

**Design.** The Gate 34 design, with the founder himself as the owner, on the same 12 situations on plans and payments (he has not answered them; Gate 34 used a stand-in).
- His verdicts are given on Telegram, then the cold default probe (already run, unanimous 12/12) and the blind judge label each case. At least 6 surprising are needed.
- He confirms the readings of free-text verdicts.
- One shared build (4 workers, no questions, assumptions recorded): arm N is the build with no owner; arm R is the build after his phone review (scan and mark, "what would you do instead?", suggestions off) and one fix round.

| # | Prediction |
| --- | --- |
| S1 | **On surprising cases, R beats N by ≥ 30 percentage points** |
| C1 | He marks a matching decision for ≥ 80% of the surprising rules recorded |
| A1 | Of those marked, he changes ≥ 60% (Gate 31: 0% with the old flow; Gate 34b's synthetic owner: 100%) |
| S2 | Ordinary cases ≥ 75% in both arms |
| S3 | Existing backend tests pass in both arms |
| S4 | Review under 15 minutes |

Kill: **R beats N by < 10 points on surprising cases.**

**Honest prior.** S1 about 55%, A1 about 65%. The mechanism works with a careful owner (Gate 34b); the open question is a busy person on a phone.
