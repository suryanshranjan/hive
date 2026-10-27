# Gate 25 results (Hive v1 M5): a real backlog feature in a real codebase, Oct 28 2026

Only aggregate numbers are published. The company (Company X), its product spec, code, owner answers and acceptance tests stay private.

**Question.** Does Hive v1, the tool, build a real backlog feature in a real company's codebase, without anyone reviewing the code?

**Answer.**
- **Yes, on this feature.** A 4-worker swarm built the settlement core of an unbuilt module from the company's roadmap: validating compensation terms across 5 models, and computing platform fee, creator payout, bonus caps and in-kind value. It passed **23 of 23** owner-approved hidden acceptance tests and **384 of 384** of the codebase's existing tests, in 10 minutes, for **$3.18**. Nobody reviewed the code.
- **But the owner role changed mid-run, and this must be read with that.** The founder answered 1 of the 12 questions, then handed the owner role to Claude, which answered the other 11 from the founder's approved decisions and the company's spec. The same Claude session had drafted the hidden acceptance tests from those same decisions. This run therefore tests **Hive v1 with an AI proxy owner holding the founder's written policy**, an optimistic setting, not the registered "founder answering live" test.

## Setup

- **Codebase.** The company's Node.js backend: a clean, shallow copy with no git history, no documentation folder and no remote, checked for secrets before copying (none found; one real-looking test-mode payment key ID in the company's archived documentation was reported to the founder and kept out). Run inside the lab container; the company's repository was never pushed to.
- **Feature.** A pure settlement library with a fixed public interface (`validateTerms`, `settle`), money in paise as BigInt, following the codebase's conventions. The goal quoted the company's product spec and left its open questions to the owner.
- **Hidden acceptance tests.** 23 tests: the spec's 3 worked fixtures, 8 rules the spec states, and 8 open choices the founder approved before the run (for example: a bonus above its cap is paid at the cap; the fee rounds half up to the paisa). Checked consistent against a private reference (23/23), then removed from the container before the run.
- **Swarm.** `hive run`, 4 workers, 4 areas (validation, fees, bonus, settlement), content-keyed guard, owner session with a 17-question budget. **No owner examples:** the examples the founder supplied were for different functions (Gate 20's), so none applied.
- Predictions pushed before the run (commits f610c4b, bf81e83).

| Measure | Result |
| --- | --- |
| Hidden acceptance tests | **23 / 23 (100%)** |
| Existing backend tests | **384 / 384** |
| All tests on the final branch | 430 / 430 (the swarm added 46) |
| Code | one new module (88 lines) plus tests; 10 files committed in all |
| Workers | 4, finished in 4.6–9.8 minutes, no API errors |
| Builder cost | $3.18 at list price |
| Questions | 12 of 17: 1 answered by the founder (110 s), 11 by the proxy owner (median 27 s) |
| Commits on the shared branch | 13; 0 that broke a test that passed before (2 swarm-written tests were renamed under an owner ruling, never failing) |
| Secret-like or artifact files committed | none |

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| M1 | ≥ 95% of the 23 hidden acceptance tests pass | **Held**: 23 / 23 |
| M2 | All 384 existing tests pass | **Held** |
| M3 | No commit that broke a passing test is still broken at the end; no secret-like file committed | **Held** |
| M4 | Under 45 minutes of the founder's time | **Held, but not meaningful**: the founder answered one question; the proxy answered the rest |
| M5 | ≥ 3 questions, each answered or timed out on record | **Held**: 12 asked, 12 answered |
| Kill | < 85% of hidden tests | **Did not fire** |

## What it means

1. **Hive v1 works end to end on real code.** The tool (guard, area claims, `hive run`, owner session) carried a real feature from a goal to a passing branch on a real company's backend, with the protocol behaving as in the lab: claims split four areas, one worker asked before changing tests written earlier in the run, and every ruling became a test.
2. **The owner is the hard part, and this run did not test the real one.** The founder said "I don't remember" to the first question and delegated the rest. A proxy that holds the founder's written decisions can answer fast (median 27 s) and consistently. Whether a founder answering from memory reaches the same result is untested, and it is the claim that matters.
3. **The 100% is optimistic.** The hidden tests and the proxy's answers both came from the same approved decisions, written by the same agent. A rule nobody wrote down could not have been answered, and no hidden test checked one. The feature is also small and pure: no database, no payment provider, no endpoints.

## What to do next

- **The registered test, properly:** the founder answers live, and someone other than the answerer writes the hidden tests (the founder alone, or a second person). Same feature design, a fresh module.
- **Make "I don't remember" a feature:** `hive owner` could show the owner's own past decisions and documents next to each question, so a founder who has forgotten can answer from their record instead of delegating.
- **A larger feature** with persistence and endpoints, scored by the owner's acceptance tests through the API.

## Limits

- One run, one feature, one company.
- The proxy owner and the hidden tests share an author.
- The feature result stays private in the container; the founder decides whether any of it enters the company's repository.
