# Gate 38 results: does a confirmed general rule hold a day later? Oct 29 2026

Only aggregate numbers are published. The situations, the founder's answers, rules and verdicts, and the code stay private.

**Question.** In Gate 37 the founder's answers to two framings of one decision rarely agreed. Hive now ends its interview with the rule sheet: each answer becomes one general rule ("Whenever …, …"), and he confirms or fixes every rule. Does a rule he has confirmed hold a day later?

**Answer: no. His confirmed rules matched his next-day verdicts on 2 of the 11 decisions they covered, no better than his raw answers (2 of 11). The kill fired.** The builders followed his confirmed rules faithfully. Where his rule held, that won surprising cases no builder guessed (3 of 6, against 0 of 6). Where he changed his mind, it lost ordinary cases (2 of 6, against 5 of 6). The two arms tied overall at 5 of 12. Established for this owner: neither an answer nor a rule he confirmed predicts what he decides the next day. Conjecture: he decides at the moment he looks at a concrete outcome. So Hive should show him what was built and get a yes (the code sheet), not try to collect his policy beforehand.

| Measure | Arm N (no owner) | Arm I (goal + his confirmed rules) |
| --- | --- | --- |
| **Surprising cases** (6) | **0 / 6** | **3 / 6** |
| Ordinary cases (6) | 5 / 6 | **2 / 6** |
| All hidden cases | 5 / 12 | 5 / 12 |
| Existing backend tests | 384 / 384 | 384 / 384 |
| Owner rules given to the builders | 0 | 13 |
| Builders, minutes, cost | 4, 32 min, $3.27 | 4, 29 min, $3.38 |

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| A1 | Confirmed rules match day 2 on ≥ 70% of the decisions they cover | **Failed:** 2 of 11 (18%); 4 of 11 even if both "unclear" count as matches |
| A2 | Confirmed rules beat raw day-1 answers by ≥ 20 points | **Failed:** 0 points (2 of 11 each; unclear 2 vs 1) |
| S1 | On surprising cases, I beats N by ≥ 30 points | **Held:** +50 points (3/6 vs 0/6) |
| C2 | ≥ 80% of surprising day-2 situations covered by a confirmed rule | **Held:** 5 of 6 |
| S2 | Ordinary ≥ 75% in both arms | **Failed in I:** 2 / 6 (N: 5 / 6) |
| S3 | Existing tests pass in both arms | **Held:** 384 / 384 each |
| S4 | Day 1 under 10 minutes | **Held:** 7.9 minutes (13 questions, 13 rules, one corrected) |
| Kill | Confirmed rules match day 2 on < 50% | **Fired** (18%) |

The honest prior was A1 about 45%, A2 about 50%, S1 about 40%. A1 and A2 came out far below it. S1 held, for the reason below.

## What happened, case by case (by the experimenter's reading of the code against his rules)

- **The rules reached the code exactly.** On every hidden case where arm I differs from arm N, the code does what his confirmed rule says. That covers all three surprising cases won and all three ordinary cases lost. Transfer from rule to code is not the problem: it held in Gate 37 and holds again here.
- **The surprising cases won are the decisions where his rule and his day-2 verdict agree** (two of them), plus one decision no rule covered, where arm I's default happened to match.
- **The ordinary cases lost are decisions where his day-1 rule and his day-2 verdict point opposite ways.** Each time, day 2 is the answer a builder with no owner would also give. His day-1 rule was the unusual one, and he did not hold it.
- One ordinary case failed in both arms, for reasons outside his rules.

So a confirmed rule is worth exactly as much as its stability. Here stability was 2 of 11, and the gains and losses cancelled.

## What this means for Hive

- **Collecting an owner's policy in advance has hit a wall with this owner.** Three gates now agree:
  - Gate 37: one answer per framing, 1 of 8 same-session, 3 of 6 next day;
  - Gate 38: his own confirmed general rules, 2 of 11 next day.
  
  A better question, coverage or wording will not fix this. The owner's decision does not exist until he faces the case.
- **The hand-over is the main channel.** Gate 42's code sheet shows him what the built code does and lets him mark it, which is a decision at the moment of looking. That is the channel this result points to, and it already ships. Gate 45 tests it with him on his phone.
- **The interview stays, but light.** It still won 3 surprising cases here (S1 held). Its rules go into the build, and every one comes back to him on the code sheet before anything is final, so a rule he would no longer give is caught there.

## Limits

- One founder, one feature, one run per arm, 12 hidden cases (6 surprising). The stability numbers are blind-judged (3 votes per pair), but they come from 11 pairs.
- Day 2 used different framings from day 1, as in Gate 37. Some disagreement may be framing, not a changed mind. The design cannot separate the two, and for the product it does not matter: what he says when he faces the case is what has to be built.
- A guard leak, seen in arm N: one builder committed the shared `node_modules` link (same target, so scoring was unaffected). Logged for the guard.
