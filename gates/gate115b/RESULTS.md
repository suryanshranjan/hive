# Gate 115b: results (flown Nov 15 2026, the owner's Windows laptop, real Claude, strict simulated founder)

**Question.** Does Gate 115's gain hold once its flaws are removed: a strict founder, a second company with kinds of fact the prompt does not name, and a `fit` arm that asks only where the answer changes a step? (Predictions: `PREDICTIONS.md`, pushed before launch in `1cc3430`.)

**Answer (model; simulated founder, n = 1 a cell).** The gain holds, but it is smaller.
- **Even a strict founder stated the hidden fact** in **7 of 8** goals with `three`, against **3 of 8** with `one`.
- **The final plan used it** in 6 of 8 against 3 of 8. Across Gates 115 and 115b together, that is **14 of 16** against **7 of 16**.
- **The gain reached the kinds of fact the prompt never names** (a licence limit, a supplier problem, a brand rule, a safety rule): CrumbHouse 4 of 4 against 2 of 4.
- **`fit` did not work.** It asked fewer questions on real goals (1.6), still asked 3 on both controls, and found fewer facts.
- **`three` stays the default.**

## The numbers (30 runs, no errors; $24.04)

| Arm | TutorNest G1-G4 accounts | CrumbHouse B1-B4 accounts | Fact stated by him (8 goals) | Questions a goal | Questions on the 2 controls | Mean cost a run, min |
|---|---|---|---|---|---|---|
| one | 1/4 | 2/4 | 3/8 | 1.0 | 1, 1 | $0.78, 1.57 |
| three | 2/4 | **4/4** | **7/8** | 3.0 | 3, 3 | $0.77, 1.69 |
| fit | 2/4 | 2/4 | 3/8 | 1.6 | **3, 3** | $0.85, 1.73 |

- **B3 is passed by default.** "Never discount" passes any plan that offers no discount, and all three arms passed it. Leaving B3 out: `one` 2/7, `three` 5/7, `fit` 3/7.
- **"Stated" was counted by hand.** It means the fact itself is in his answer, checked against each answer. The model judge for "surfaced" missed plain statements ("Class 10 is full… no new Class 10 before April" was marked not surfaced), so its numbers are not used here.

**Where `three` still missed:**
- **G2 (schools):** he named the three partner schools but, being strict, never said the 20%. He also invented a constraint that isn't in his brief: "none has agreed to be named on the site". The plan then avoided naming schools and showed no discount.
- **G4 (the demo):** he said the cause (a junior tutor demos, then a senior one teaches) but not that he would change it. The plan only told parents the senior tutor's name in advance.

In both cases the fact or half of it came out, and the plan stopped at what he said.

## Predictions scored

| # | Prediction | Result |
|---|---|---|
| Q1 | TutorNest: `three` ≥ 3 of 4, `one` ≤ 2 of 4 | **Failed:** `three` 2 of 4 (`one` 1 of 4). Kill (`three` ≤ `one`) not fired |
| Q2 | CrumbHouse: `three` ≥ 2 of 4, `one` ≤ 1 of 4 | **Half held:** `three` 4 of 4; `one` 2 of 4 (1 of 3 without B3). Kill not fired |
| Q3 | `fit` within 1 of `three` on the 8 goals | **Failed:** 4 vs 6 |
| Q4 | `fit` ≤ 1 question on each control | **Kill fired:** 3 and 3 |
| Q5 | `fit` mean ≤ 2.0 questions | **Held:** 1.6 |
| Q6 | No invented business facts in any final plan | **Held:** checked by keyword and by hand on all 30. The one inference ("April", from his "full until March") is written as a conditional example |

**Decision rule:**
- Neither Q1 nor Q2 killed, so `three` stays the default.
- `fit` failed Q3 and Q4, so it is not adopted. It stays available as `HIVE_PLAN_ASK=fit`.

## What we learned

1. **The question count matters even when he volunteers nothing.** The strict founder stated the fact 7/8 times when asked 3 specific questions, against 3/8 with one. Gate 115's gain was not only over-sharing.
2. **The bottleneck has moved to what he says next.** When the fact came out only in part, the plan used only that part. A real founder answering narrowly would leave the same gaps. A follow-up on a narrow answer ("you mentioned the schools: do their families get anything?") is the next thing to try.
3. **Asking fewer did not work by telling the model to ask fewer.** `fit` still asked 3 on both controls, where nothing was hidden. Ask only when needed is still unsolved here.
4. **A simulated founder can invent constraints.** G2's "none has agreed to be named" is not in his brief. A judge for "did he say it" needs a hand check.

## What it changes in Hive

- **Nothing new ships:** `three` stays the default, as since Gate 115. `fit` is kept as an option, not the default.
- **Open, next on this thread:**
  - a follow-up question when his answer only touches the fact;
  - asking fewer when nothing is hidden, measured on the controls;
  - a real founder.

**Files:**
- `results/runs.json` (every run: questions, his answer, first and final plan, verdicts, cost);
- `results/run.log`.

The private inputs are in `private/g115/` and `private/g115b/`. They hold no real company and can be published.
