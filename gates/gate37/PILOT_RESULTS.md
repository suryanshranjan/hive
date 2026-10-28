# Gate 37 pilot results: where to ask, Oct 28 2026

Registered in `prompts/PILOT.md` before running. Retrospective: it reuses Gate 36's hidden set and the same blind coverage judge (3 votes per case, situations only, no answers), and it took no founder time. Only aggregates are published.

| Arm | Interview written from | Situations | Surprising hidden situations covered (of 9) | Of the 7 scored |
| --- | --- | --- | --- | --- |
| Gate 36 (for reference) | the description, directly | 12 | 4 | 2 |
| **D** | the description, decisions first | 12 | **3** | 2 |
| **G** | the goal with its interface, decisions first | 12 | **7** | 5 |
| G2 (post hoc, after the fix below) | the goal with its interface, one situation per decision | 14 | 9 | 7 |

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| P1 | D covers ≥ 6 of 9 | **Failed:** 3 |
| P2 | G covers ≥ 7 of 9 | **Held:** 7 |
| Kill | G ≤ 4 of 9 | Not fired |

## What it means

- **Listing the decisions first does not help when the description alone is the input** (D: 3, against Gate 36's 4). It produced 40 loose "decisions", most of them about things the code never decides.
- **What helps is asking from the cases the code must actually decide.** With the interface in hand, the planner found 14 decisions, and 12 questions covered 7 of 9. One run each, so this is a **model** to be tested in Gate 37, not established.
- **Ranking cut exactly the owner's surprises.** G's two misses were the decisions that look minor (extending a deadline, changing a title). Both were cut by "ask where an owner most likely differs first", and the founder had surprised on both. Gate 33 had already shown that a model cannot predict where this owner differs (35%). So Hive now asks about **every** decision the code takes, up to 20, in the planner's order. Run once after the change (G2): 14 situations covered 9 of 9. That run is **post hoc** (the change was made after seeing the misses), so it is a check of the fix, not evidence.

## Limits

- One generation per arm, and one owner's hidden set. The judge has already scored Gate 36's interview on this hidden set, and the interface in G names the same 12 cases the hidden set was built from, so G's coverage is an upper bound for a feature whose interface is known in advance.
