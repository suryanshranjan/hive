# Gate 20 predictions, registered before the run (Oct 27 2026)

**Question.** On a real company's rules, examples drafted by an agent and confirmed by the owner fixed no more errors than the same number of builder questions (Gate 18: 0.93×). On agent-written rules, examples chosen by the owner fixed 2.7× more (Gate 13). The conjecture: **the examples' advantage needs the owner to choose the points.** Here the founder wrote the examples.

**Design (`python3 lab/run_gate.py lab/experiments/g20_owner.json --oracle <private wrapper>`; aggregates only).**
- **Rules.** Gate 7's 10 real functions as confirmed by the founder, kept privately; Gate 18's neutral one-line specs.
- **The founder's examples.** 58 example inputs (5 or 6 per function), written without looking at the old QA list, the check table or the rules. The founder wrote inputs only; outputs come from the confirmed rules.
- **Already measured before the run: 31 of the 58 (53%) equal an input on the agent-drafted QA list.** The founder and the agent pointed at the same inputs about half the time. By the fair copy rule (Gate 17), the founder's examples are all kept, and those 31 inputs are removed from the hidden and visible pools for every team. The hidden suite draws its edge inputs from the remaining 94 QA cases.
- **Teams** (3 builders each; names as in Gate 18 so `gate18/referee/analyze.py` applies unchanged): **N0** (nothing); **T** (the founder's 58 examples as visible tests); **Q** (19 questions for the team, up to 57 values); **TQ** (both).
- **Hidden suite.** 25 tests per function (seed 20200000), 70% edge calls.
- **Privacy.** Only aggregate numbers are committed.

| # | Prediction |
| --- | --- |
| O1 | Owner-chosen points beat builder-chosen points: fixed_T / fixed_Q ≥ 1.3 (Gate 18, agent-drafted: 0.93) |
| O2 | The founder's examples do better than Gate 18's agent-drafted ones: T − N0 ≥ +38.8 points (Gate 18's T − N0) |
| O3 | Examples plus questions reach 80%: TQ ≥ 80% hidden (Gate 18: 78.0%) |
| O4 | Treatment delivered: Q and TQ each use ≥ 17 of 19 questions; T and TQ pass every example test |
| O5 | Rules not guessable: N0 below 70% hidden |

Decision rules:
- **O1 holds:** the product asks owners to write examples themselves. Confirming a generated list is not enough.
- **O1 fails (ratio < 1.1):** with these rules, the founder points about where an agent points (53% overlap already). The product can generate the examples and ask the owner only to confirm and answer, which is cheaper for owners.

**Honest prior.** O1 about 35% (lowered after the 53% overlap was measured, before any builder ran); O2 about 45%; O3 about 55%.

**Cost.** About $7 at list price; about 5 minutes. Run after Gate 24, on its own.

## Amendment, registered before the run: the company's own documents (Oct 27 2026)

The founder asked to use the company's Notion documents to strengthen this gate. A search of the workspace found that **only 2 of the 10 functions' rules are written down anywhere** (a fee rule and a payout rule); the other 8 exist only in the founder's head. The policy sections of the two relevant pages (two sections of the company's strategy document and two of its product architecture document; 808 words, verbatim) become a private handbook.

- **New team HTQ** (3 builders): `HANDBOOK.md` + the founder's 58 examples + 19 questions. Same prompt; its ask text adds one sentence pointing to the handbook and noting it covers only some functions.
- **Analysis:** `gate20/referee/analyze_htq.py` (aggregates only), registered with this amendment.

| # | Prediction |
| --- | --- |
| O6 | Real documents add on top of examples and questions: HTQ − TQ ≥ +3 points hidden |
| O7 | Where the documents speak, they settle it: on the 2 documented functions HTQ fixes ≥ 0.9 of N0's edge errors, and at least 0.1 more than TQ |

**Honest prior.** O6 about 35% (the documents cover 2 of 10 functions); O7 about 50%.

**Cost of the amendment.** About $2 more (3 builders).
