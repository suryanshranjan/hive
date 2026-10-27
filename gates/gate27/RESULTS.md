# Gate 27 results: rules from the founder's head, live founder vs a swarm that cannot ask, Oct 28 2026

Only aggregate numbers are published. The company (Company X), its spec, code, cases, verdicts and answers stay private.

**Question.** Can Hive carry rules that exist only in the founder's head into real code? The only way such a rule can reach the swarm is through the founder's live answers. So arm A could ask the founder and arm B, otherwise identical, could not.

**Answer: not yet. The questions changed nothing measurable.**
- **Both arms passed the same 19 of 24 cases and missed the same 5.** On the 10 head-only cases, both arms passed 6. On the 14 documented cases, both passed 13.
- **The founder did his part.** He answered all 9 questions himself, median 61 s. On every head-only case a question touched, the swarm then did what he said.
- **But on each of those, his answer matched what the swarm that could not ask had guessed anyway.** The 5 misses were never asked about. They are places where his rule departs from the obvious default, and the builders applied the default without asking.
- The registered kill condition fired: on head-only cases, arm A did not beat arm B (6 vs 6).

## Setup

- **Codebase.** The same private, secret-checked copy of the company's Node.js backend, reset to a base without the Gate 25 and 26 features. The company's repository was never pushed to.
- **Feature.** The hard eligibility gates that remove a creator from a campaign before scoring: a pure library with a fixed public interface and 11 machine codes, built on the codebase's campaign brief. The goal quoted the spec's one-line gate list and left the rest to the owner.
- **Cases (amended before the run).** 24 in all:
  - 15 written by the founder, of which the experimenter judged 14 decided by the spec;
  - 9 situations proposed by the experimenter, with the founder's own verdicts.
  - Labelled before the run: **14 documented, 10 head-only.** Scored on the shown / not shown verdict only.
  - A private reference passes all 24. They were kept out of the container until scoring.
- **Arm A:** 4 workers and a 17-question budget, with the founder answering live through `hive owner`. **Arm B:** the same, with a question budget of 0. Both ran at the same time.
- Predictions were pushed before the run (commits 805f202, be47bdc).

| Measure | Arm A (asks the founder) | Arm B (cannot ask) |
| --- | --- | --- |
| All 24 cases | **19 / 24** (79%) | **19 / 24** (79%) |
| Documented cases | 13 / 14 | 13 / 14 |
| Head-only cases | **6 / 10** | **6 / 10** |
| Cases missed | the same 5 | the same 5 |
| Existing backend tests | 384 / 384 | 384 / 384 |
| All tests on the final branch | 423 / 423 | 407 / 407 |
| Questions | 9 asked, **9 answered by the founder**, median 61 s (14 to 125 s) | none |
| Commits on the shared branch | 12 (8 code); no test ever went from passing to failing | 12 (8 code); same |
| Files committed | 5; no secret-like files, no artifacts | 6; same |
| Worker time | 3.8 to 5.8 minutes | 1.6 to 9.4 minutes |
| Cost | $3.18 | $2.79 |

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| F1 | Arm A ≥ 80% of all cases | **Failed, narrowly:** 79.2% (19 / 24) |
| F2 | 384 existing tests pass, both arms | **Held** |
| F3 | ≥ 80% of answers from the founder | **Held:** 9 / 9 |
| F4 | Median founder answer under 2 minutes | **Held:** 61 s |
| F5 | No breaking commit left broken, no secret-like file, both arms | **Held** |
| F6 | Head-only: arm A beats arm B by ≥ 20 points | **Failed:** 60% vs 60%, a gap of 0 |
| F7 | Documented: both arms ≥ 85% | **Held:** 93% each |
| Kill 1 | Arm A < 60% | Did not fire |
| Kill 2 | F6 fails with arm A ≤ arm B on head-only cases | **Fired** |

The honest prior for F6 was about 55%. It failed.

## What it means

1. **Where the 9 questions went.** 4 of them touched head-only cases. On all 4, the founder's answer agreed with the default that arm B chose without asking. Of the other 5, one touched a documented case, and four settled points no case tested. **Questions confirmed defaults; they did not correct them.**
2. **Where the misses came from.** All 5 misses are places where the founder's rule departs from the obvious default. Their topics:
   - missing data when a requirement is set;
   - near-matching names (cities and languages);
   - a mixed cash-and-goods deal;
   - a campaign with no per-creator budget.

   No builder asked about any of them. Each builder was confident in a default, and a confident builder does not ask.
3. **The law this suggests (conjecture).** A question is worth something only when the owner's rule differs from the builder's default. Builders ask where they feel *uncertain*, not where they are *wrong*, so the rules that differ most from common sense are the ones never asked. This fits two earlier findings:
   - Gate 8 conjectured that a question confirming the builders' guess buys nothing.
   - Gate 12 found a floor at decisions builders cannot imagine.

   Gate 27 is the first direct test with a real founder.
4. **What would have caught the misses (post hoc, not yet tested).** Arm A's builders wrote every one of these defaults into their commit messages in plain terms, for example:
   - missing data never excludes;
   - names are matched exactly;
   - a creator open to goods is not ruled out on cash.

   All 5 misses trace to one of four such stated assumptions. **If the founder had read back the builders' assumptions in plain words, he could have corrected all 5.** That is the next experiment: an *assumption review* step, where builders list the defaults they applied and the owner marks the wrong ones.

## Limits

- One run per arm, one feature, one founder, one company. Arms A and B landing on exactly the same 19 cases is striking, but it is still one pair of runs.
- 9 of the 10 head-only situations were proposed by the experimenter, who chose places the documents leave open. Those are not the same as places where the founder's rule is surprising. 6 of the 10 matched the default, which left little room for questions to help.
- The experimenter translated the cases into tests. All 5 misses are straight readings of the founder's verdicts, not translation choices.
- The feature is small and pure (no database, no network).

## Files

| Path | Contents |
| --- | --- |
| `prompts/PREDICTIONS.md` | Predictions and the pre-run amendment |
| `RESULTS.md` | This file (aggregates only) |
