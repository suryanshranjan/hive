# Gate 31 predictions, registered before the cases exist (Oct 28 2026)

**Question.** Gate 30 found that the owner's review raised his surprising rules from 2/6 to 3/6 (+17 points). The review itself was the limit:
- impact ranking showed only 3 of the 6 rules;
- a menu of options led him away from his own free-text rule.

Since then the review:
- lists **every** decision in one line, so the owner marks the ones he would change;
- asks marked decisions **openly first** (options only on request);
- ranks by where the owner is likely to differ;
- checks new answers against his earlier rulings.

**With that review, does the owner's input now carry his surprising rules into the code?**

**Design.** The same as Gate 30 (its amendment applies), on a fresh feature. Only the review differs.
- **Feature:** a part of the company's roadmap that is unbuilt and barely specified: the policy for AI credits (what is charged, when credits expire, failed or partial runs, team sharing, refunds).
- **Cases:**
  1. The experimenter writes 12 situations; the founder gives verdicts on Telegram.
  2. A cold default probe answers the same situations (3 runs).
  3. A blind judge labels each case surprising, ordinary or unclear.
  4. The founder confirms the readings of the surprising ones.
  5. At least 6 surprising cases are needed, or the gate is not run.
- **Arms from one shared build:** N (no owner) and R (after his phone review and one fix round), 4 workers, suggestions off.

| # | Prediction |
| --- | --- |
| S1 | **On surprising cases, R beats N by ≥ 30 percentage points** |
| C1 | **Coverage:** of the surprising rules with a matching recorded assumption, the founder marks one for ≥ 80% |
| S2 | On ordinary cases, both arms pass ≥ 75% |
| S3 | All existing backend tests pass in both arms |
| S4 | The review takes under 10 minutes |
| S5 | No secret-like file; no breaking commit left broken |

Kill: **R beats N by < 10 points on surprising cases.**

**Honest prior.** S1 about 50%. C1 about 60%: the owner has to recognise his rule in a one-line title. Gate 30's +17 was one case, so even a working fix could show as +17 again.

**Cost.** About $7 at list price, plus about 15 minutes of the founder's time on Telegram.

## Amendment, registered before the build (Oct 28 2026)

- **Cases.** The experimenter wrote 12 situations on AI credits, and the founder gave verdicts on Telegram. The cold probe (3 runs) was unanimous on 10 of 12. The blind judge labelled **9 surprising, 3 ordinary, 0 unclear.** The founder confirmed the experimenter's readings of the 6 surprising verdicts he gave in his own words (6 of 6 "Yes, exactly"); the other 3 surprising ones were taps on an option.
- **Hidden cases:** 12 (9 surprising, 3 ordinary). A private reference passes 12/12. The cases are kept out of the container until scoring.
- **Interface:** a fixed `decide(situation, facts)` with enumerated decisions, as in Gate 30.
- **The review** uses the full list (every decision in one line, the founder marks the ones to change), open-first questions, ranking by likely disagreement with his kept rulings, and the contradiction check against earlier rulings. Hive's suggestions are off.
- With 9 surprising cases, one case is 11 points. S1 (≥ 30) needs at least 3 more surprising cases in arm R than in arm N; the kill (< 10) fires on a gain of 0 cases.
- Predictions are unchanged.
