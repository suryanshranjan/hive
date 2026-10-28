# Gate 37 pilot: does a decisions-first interview cover more? Registered before running (Oct 28 2026)

**Question.** Gate 36's interview, written straight from the feature description, covered 4 of the founder's 9 surprising hidden situations. Hive now first lists the business decisions the code must take, each with the builders' default, and then writes one situation per decision, starting with the decisions where an owner is most likely to differ. Does that cover more of the same hidden set?

**Design.** No founder time, and no builds. This is retrospective: it reuses Gate 36's hidden set and blind coverage judge (3 votes, situations only, no answers). It is a pilot for Gate 37, not a test of the owner.
- **D:** decisions-first, from Gate 36's description only (the same input Gate 36's interview had).
- **G:** decisions-first, from the full goal with its interface (what `hive start` gives the interview in the product).
- 12 situations each. One generation per arm.

| # | Prediction |
| --- | --- |
| P1 | D covers ≥ 6 of 9 surprising hidden situations (Gate 36: 4) |
| P2 | G covers ≥ 7 of 9 |

Kill: **G covers ≤ 4 of 9.** If so, planning from the code's decisions does not find where this owner differs, and Gate 37 needs another design.

**Honest prior.** P1 about 40%, P2 about 60%. The interface lists all 12 hidden situations' cases (by design, it is the feature), so G should cover them if it asks about each case. Whether it picks the right 12 of more cases is the real question.
