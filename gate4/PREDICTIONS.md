# Gate 4 predictions, registered before launch (Oct 27 2026, 14:35 IST)

The question: does choosing questions by coverage, and turning every answer into a shared test, beat letting builders ask freely with the same budget?

Setup:

- A fresh set of 20 invented business rules (`referee/oracle.py`, kept out of the repo until scored), on the same engine as Gate 3.
- Three teams of 3 builders:
  - **R0:** no questions.
  - **R30:** 30 shared questions, asked freely by the builders, as Gate 3's Q30.
  - **P30:** 30 questions spent first by one planner agent. The planner writes a coverage plan, covers every function, and turns each answer into a test. The builders then start and cannot ask.
- Scored on 500 hidden tests, 70% edge cases, seed 4200000.

| # | Prediction | Basis |
| --- | --- | --- |
| G1 | Every team passes all 40 visible examples; P30 also passes all of the planner's tests | Gate 3 I1 |
| G2 | Planned beats free: P30 hidden ≥ R30 hidden + 5 points | Coverage model: edge error ≈ e_g·(1 − coverage) |
| G3 | P30 reaches ≥ 95% hidden | Same model; Gate 3 Qinf reached 97.6% with 320 questions. Our odds: about 55% |
| G4 | Replication on new rules: R0 in 45–70%, R30 in 78–92% | Gate 3: 58.0% and 86.6% |
| G5 | Allocation: P30 asks about all 20 functions; R30 leaves at least 3 functions unasked | Gate 3: Q30 left 4 unasked |

Kills:

- If P30 ≤ R30, coverage planning does not help, and the claim that *which* questions matters more than *how many* is wrong (or the planner is poor).
- If R0 ≥ 85%, the new rules were too guessable and the comparison says little.

Caveat registered in advance: P30 changes three things at once (allocation per function, coverage-driven choice, answers as shared tests). One run cannot separate them.
