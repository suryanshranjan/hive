# Gate 37 predictions, registered before any case or verdict exists (Oct 28 2026)

**Question.** Gate 36's interview, written from the feature description, covered 44% of the owner's surprising rules and did not move the code. The pilot (`../PILOT_RESULTS.md`) found that an interview written from the decisions the code must take, one situation per decision, covers far more (7 of 9, then 9 of 9 post hoc). **With that coverage, do the owner's interview answers carry his surprising rules into the code?** And separately: **how often does he give the same rule when the same situation is framed differently?** (Gate 36: 0 of 2.)

**Design.**
- **Feature:** a fresh, unbuilt area, **content approval and revisions** (drafts, change requests, sign-off, and what happens after posting). It is a pure library with a fixed interface of 12 situations, given identically to both arms.
- **The hidden set (the referee).** The experimenter writes 12 situations, one per interface case, in his own framing. The founder gives verdicts on Telegram. A cold default probe (3 runs) and a blind judge label each one surprising, ordinary or unclear, and the founder confirms readings of free-text verdicts. At least 6 surprising are needed. Neither arm sees the cases.
- **Hive's interview (the treatment).** `hive/interview.py` as of `8c3414f`: it lists the decisions from the goal with its interface, then asks one situation per decision (up to 20), in its own framing. It does not see the hidden set. The founder answers through Hive's real code on his phone. His rules go to arm I through the product's own reading logic.
- **The consistency retest.** At the end of the same session, he is asked 6 situations he answered in Gate 36, reframed (new names, amounts and wording; same decision). A blind judge marks each pair same or different.
- **Arms,** built at the same time from the same base: 4 workers each, no questions, assumptions recorded, no review.
  - **N:** no owner input.
  - **I:** the same goal plus his interview rules.

| # | Prediction |
| --- | --- |
| S1 | **On surprising hidden cases, I beats N by ≥ 30 percentage points** |
| C2 | ≥ 80% of the surprising hidden cases have a matching interview situation (blind judge) |
| K1 | He gives the same rule on ≥ 4 of the 6 reframed situations |
| S2 | Ordinary cases ≥ 75% in both arms |
| S3 | Existing backend tests pass in both arms |
| S4 | His active time in the interview is under 8 minutes |

Kill: **I beats N by < 10 points on surprising cases, with C2 held.** If coverage is high and the code still does not move, the interview's answers do not carry his rules, and the gap is framing (K1) or transfer to code.

**Honest prior.** S1 about 45%, C2 about 70%, K1 about 50%. Gate 36's two contradictions out of two say framing could cap S1 even at full coverage.

**Cost.** About $7 at list price for both arms, plus about 10 to 12 minutes of the founder (12 hidden, about 14 interview, 6 retest).
