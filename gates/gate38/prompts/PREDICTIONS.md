# Gate 38 predictions, registered before any case or verdict exists (Oct 28 2026)

**Question.** In Gate 37 the owner's answers to two framings of the same decision agreed only 1 of 8 times in a session and 3 of 6 a day apart. So an interview's answers could not carry his rules: there was no single rule to carry. Hive now ends the interview with **the rule sheet**:
- his answers become one general rule per decision ("Whenever …, …");
- two answers that disagree are put to him;
- he sees every rule at once and fixes the wrong ones.

**Does deciding once, as a general rule, make his policy stable enough to build from?**

**Design.**
- **Feature:** a fresh, unbuilt area, **ratings and reviews after a collaboration** (brands rate creators, creators rate brands, disputes over a review). It is a pure library with a fixed interface of about 12 situations, given identically to both arms.
- **Day 1, Hive's interview with the rule sheet.** This is `hive/interview.py` as of this commit, writing from the goal with its interface: one question per decision, no repeats, and the rule sheet at the end. The founder answers on his phone. Kept separately: his raw answers, and his confirmed rules.
- **Day 2, the referee, at least 12 hours later.** The experimenter writes 12 situations, one per interface case, in his own framing, and the founder gives verdicts. As before, a cold probe and a blind judge label each one surprising, ordinary or unclear, and the founder confirms readings of free-text verdicts. These become the hidden tests. Neither arm sees them.
- **Stability, judged blind.** For each day-2 situation, a blind judge (3 votes) decides whether day 2's verdict matches:
  - (a) his confirmed rule on that decision;
  - (b) his raw day-1 answer on that decision.
- **Arms,** built at the same time from the same base: 4 workers each, no questions, assumptions recorded, no review.
  - **N:** no owner input.
  - **I:** the goal plus his confirmed rules.

| # | Prediction |
| --- | --- |
| A1 | **His confirmed rules match his day-2 verdicts on ≥ 70% of the decisions they cover** (Gate 37 raw answers: 1 of 8 same-session, 3 of 6 next day) |
| A2 | Confirmed rules match day 2 at least 20 points more often than his raw day-1 answers do |
| S1 | On surprising hidden cases, I beats N by ≥ 30 points |
| C2 | ≥ 80% of the surprising day-2 situations are covered by a confirmed rule (blind judge) |
| S2 | Ordinary cases ≥ 75% in both arms |
| S3 | Existing backend tests pass in both arms |
| S4 | Day 1 (interview plus sheet) takes under 10 minutes |

Kill: **confirmed rules match day 2 on < 50% of the decisions they cover.** If so, stating his policy as rules does not make it stable either. An owner's intent on these decisions would then be made at the moment of asking, and Hive's job becomes showing him what was built and getting a yes, not predicting his rules.

**Honest prior.** A1 about 45%, A2 about 50%, S1 about 40%. A general rule is easier to remember than an answer to one example, but nothing yet shows he will hold it a day later.

**Cost.** About $7 at list price for both arms, plus about 10 minutes of the founder on day 1 and 5 on day 2.

## Amendment, Oct 29 2026, after day 2 and before any build (counts only)

- **Day 2:** the founder gave verdicts on all 12 situations. A blind judge (3 votes) labelled 6 surprising and 6 ordinary; all were taps on the offered options, so no free-text readings needed confirming. The cold probe had agreed 12/12. These are the hidden tests (12) with a private reference that passes 12/12.
- **Stability, judged blind (3 votes), 11 situations covered by a day-1 decision (one was covered by none):**
  - confirmed rules vs day 2: 2 same, 7 different, 2 unclear;
  - raw day-1 answers vs day 2: 2 same, 8 different, 1 unclear.
- So A1 (≥ 70%) fails and **the kill fires** (2 of 11 = 18% < 50%, and 36% even if both unclear cases count as matches). A2 fails (0 points apart).
- The arms are still built and scored as registered (N and I, 4 workers each, the frozen Hive of the day-1 commit), so S1 to S3 are measured. Expected after the stability result: I does not beat N on the surprising cases, and may lose ordinary ones where his day-1 rule disagrees with day 2.
