# Gate 26 results: a real feature with the founder answering live, Oct 28 2026

Only aggregate numbers are published. The company (Company X), its spec, code, cases and answers stay private.

**Question.** Gate 25 built a real feature in a real codebase, but the founder answered only 1 of 12 questions (all written in code terms) and delegated the rest to an AI proxy. With questions now required to be plain language, **does the founder answer the swarm himself, and does the result still meet the company's rules?**

**Answer: yes on both.**
- **The founder answered every question himself:** 4 of 4, in 61 to 129 seconds (median about 100 s). The questions were plain situations with named people and lettered choices, as `hive ask` now requires.
- **The feature met every acceptance case:** 18 of 18, and all 384 of the backend's existing tests still pass. 4 workers, 4 to 7 minutes, $2.26, no code review.
- **The founder's answers carried rules the documents do not state:** all 4 questions were about situations the written spec leaves open, and the founder settled each one in a sentence. The workers encoded every ruling as a test. (The rulings themselves are the company's policy and stay private.)

## Setup

- **Codebase.** The same private, secret-checked copy of the company's Node.js backend, reset to a base without Gate 25's code. The company's repository was never pushed to.
- **Feature.** A deterministic creator reliability score from the company's roadmap (unbuilt), a pure library with a fixed public interface. The goal quoted one section of the company's architecture document and left the rest to the owner.
- **Acceptance cases (amended before the run).** The founder chose to take them from the company's documents rather than write them. 18 cases, from the written spec only, translated by the experimenter, approved by the founder, checked consistent against a private reference (18/18) and removed from the container before the run. Within each case the collaborations are identical, so open choices do not affect the result. **So F1 measures the documented rules plus the founder's live rulings, not undocumented intent.**
- **Swarm.** `hive run`, 4 workers, 4 areas, the content-keyed guard, 17-question budget, plain-language questions enforced, no owner examples.
- Predictions pushed before the run (commits 05889ae, 036ecbc).

| Measure | Result |
| --- | --- |
| Acceptance cases | **18 / 18** |
| Existing backend tests | **384 / 384** (412 / 412 with the 28 the swarm added) |
| Questions | 4 asked, **4 answered by the founder**, 0 by a proxy; median about 100 s |
| Commits on the shared branch | 9; no test ever went from passing to failing |
| Files committed | 8; no secret-like files, no artifacts |
| Workers | 4, finished in 4.0–6.8 minutes, no API errors |
| Cost | $2.26 at list price |

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| F1 | ≥ 85% of acceptance cases pass | **Held**: 18 / 18 |
| F2 | All 384 existing tests pass | **Held** |
| F3 | ≥ 80% of answers from the founder | **Held**: 4 / 4 |
| F4 | Median founder answer time under 2 minutes | **Held**: about 100 s |
| F5 | No breaking commit left broken; no secret-like file committed | **Held** |
| Kill | < 70% of acceptance cases | **Did not fire** |

## What it means

| | Gate 25 | Gate 26 |
| --- | --- | --- |
| Questions in plain language | 0 of 12 (code terms throughout) | 4 of 4 (enforced) |
| Answered by the founder | 1 of 12 | **4 of 4** |
| Acceptance | 23 / 23 (cases and answers from the same proxy) | **18 / 18** (cases from the documents; answers from the founder) |
| Existing tests | 384 / 384 | 384 / 384 |
| Cost | $3.18 | $2.26 |

1. **Plain questions brought the owner back.** The same founder who delegated after one code-worded question answered every plain one, in under about two minutes each. Asking in the owner's language is not polish; it decides whether the owner stays in the loop. (One founder, two runs: a strong hint, not a measured effect.)
2. **The swarm asked about the rules the documents leave out.** All 4 questions were about cases the spec does not settle (disputes, empty history, missing data), and the founder's answers became tests. This is the intent channel working on real rules.
3. **What this does not show yet:** acceptance cases written from the founder's own head (he chose the documents), a larger feature with persistence and endpoints, and other founders and companies.

## Limits

- One run, one feature, one founder, one company.
- The acceptance cases come from the written spec, so they test the documented rules; the founder's live rulings are checked only through the tests the workers wrote from them.
- The feature is small and pure (no database, no network).

## Files

| Path | Contents |
| --- | --- |
| `prompts/PREDICTIONS.md` | Predictions and the pre-run amendment |
| `RESULTS.md` | This file (aggregates only) |
