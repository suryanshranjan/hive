# Gate 33 predictions, registered before the run (Oct 28 2026)

**Question.** Each owner-intent gate needs about 15 minutes of the founder's time, so iterating Hive's review is slow. **Can a model of this founder predict his decisions, including the surprising ones a cold builder misses, well enough to stand in for him while Hive's review is tuned?** It would never stand in for evidence about real owners. Final checks stay with him.

**The founder model.**
- A model is told the company's business, as written in its documents.
- It is given the founder's own past verdicts on other situations, with his reasons where he gave them. Those come from Gates 27, 28, 30, 31 and 32: about 80 decisions, all private.
- It answers new situations as he would.

**The test: leave one gate out, three times.**
- For each of Gates 30, 31 and 32, the model sees every verdict except that gate's, then answers that gate's 12 situations.
- 36 answers in all: 20 on cases already labelled surprising, 16 ordinary or unclear.
- A blind judge (3 votes, not told which answer is whose) compares each with the founder's real verdict: same, different, or unclear.

**Baseline.** The cold default probe from those gates. By construction it matches 0 of the 20 surprising verdicts (that is what "surprising" means), and nearly all the ordinary ones.

| # | Prediction |
| --- | --- |
| P1 | **The founder model matches ≥ 50% of his surprising verdicts** (cold default: 0%) |
| P2 | It matches ≥ 70% of his ordinary verdicts (cold default: about 100%) |
| P3 | Overall it matches ≥ 60% of the 32 clearly labelled cases |

Kill: **it matches < 25% of the surprising verdicts.** Then a stand-in cannot replace the founder, even for tuning.

**If P1 holds:** the founder model becomes a labelled stand-in owner for fast tuning of Hive's review, as Gates 34 and on. Any improvement it finds is confirmed with the real founder before it counts.

**Honest prior.** P1 about 40%. Surprising rules are, by definition, ones the obvious reasoning misses. His past verdicts may reveal a style (for example plan-tied credits, or reminders before penalties) but not every rule.

**Cost.** About $3 at list price. No founder time.
