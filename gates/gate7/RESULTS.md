# Gate 7 results: a real company's rules as the product owner, Oct 27 2026

**Question.** Every product owner before this gate was code or an agent. Does the intent of a real business reach a silent swarm through answered questions?

**Answer: yes, at about the same strength as with agent owners.**
- The team that got answers passed **49.6%** of the hidden tests, against **32.8%** for the team that got none: +16.8 points (95% CI +6.0 to +31.2).
- The same team scored 28.4% before its answers arrived and 49.6% after: +21.2 points (CI +6.8 to +39.6).

## Setup

- **The rules.** The user, a founder of a real early-stage company, wrote 10 of the company's business functions. The company is called **Company X** here; its name and details are withheld, and the specifics below are mocked. Each function had a public one-line spec, two examples and private rules. When asked to check them against the company's internal documents, the user ruled that **the documents always win**. Two rules changed before launch:
  - A fee rule was replaced by the documented fee policy.
  - A payout rule was replaced by the documented payout policy.

  The resulting rules were encoded as an oracle. All 20 of the owner's examples come out exactly right.
- **Privacy.** This repository is public, so the oracle, the edge cases, the questions and answers, and the per-test results are kept out of it. They hold Company X's internal policy and are available from the user.
- **Teams.** Two teams of 3 builders, one run each:
  - **N:** no questions.
  - **H:** in round 1, builds first drafts and writes up to 15 questions (at most 5 per worker, 3 per function, 3 calls each). The answers become tests. In round 2, the same builders continue.
- **Hidden suite.** 250 tests (25 per function, seed 7200000), 70% edge calls.
- **How the questions were answered.** The user chose to have the answers taken from the confirmed rules, rather than answering live. So the answers were perfectly consistent with the scoring oracle, and they came back in 50 seconds.

| Team | Questions | Tokens (approx.) | Visible | Hidden tests | 95% CI by function | Edge calls right |
| --- | --- | --- | --- | --- | --- | --- |
| N | 0 | 260k | 1,350/1,350 | **82/250 (32.8%)** | 18.8–50.8% | 56.3% |
| H, round 1 (before answers) | 15 asked | 263k | all landed | **71/250 (28.4%)** | 17.2–41.2% | 50.3% |
| H, final | 15 answered | + round 2 | 1,365/1,365 | **124/250 (49.6%)** | 35.2–67.6% | 70.3% |

The replays of every commit and the call-by-call probes agree exactly. No team broke an existing test.

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| Q1 | The answers help: H − N ≥ +15 points | **Held**: +16.8 (CI +6.0 to +31.2) |
| Q2 | A person's live answers disagree with their own rules on at least 5% of values | **Not tested**: the answers came from the documented rules |
| Q3 | Median answer time under 60 s per question | **Not tested** for a person. Answering from documented policy took 50 s for all 15 |
| Q4 | The rules are not guessable: N below 70% | **Held**: 32.8% |
| Kill | H − N < +5 | **Did not fire** |

## What it shows

1. **A real company's intent transfers like a synthetic one.** At about 1.5 questions per function, the gain was +17 to +21 points. Agent owners at the same density gave +25 to +32 (Gates 3 to 6). These rules were harder to guess, which is why the starting point was lower.
2. **The biggest losses are vocabulary, not logic.** Nobody told the builders the allowed input values: the types, categories and statuses each function accepts. So:
   - builders rejected valid values they had never seen (a third value of a type field, one of the category values);
   - they accepted invalid ones;
   - when a ruling said a few unknown labels give empty, they stretched it to "every status except one gives empty". That wiped out five correct actions.

   Listing the allowed values in the one-line spec is the cheapest intent there is.
3. **Rulings are still read as rules (Gates 4 to 6).** A ruling on three specific inputs was generalized to whole classes of inputs. Where a function got no question, round 2 still changed some of its behaviour. One worker applied the rulings to every failing function, including those it did not own.
4. **Company documents settle intent too.** Checking the rules against the company's internal documents overturned two of them before any code was written. That is intent arriving from a source other than questions. It is cheap, and a Hive intent interface should read it first.

## Limits

- One run per team.
- The answers came from documented policy, not a person in real time, so human consistency and speed remain unmeasured.
- Team H had an extra round of work. The H − H1 comparison holds the team fixed but not the extra round.
- The builders and the encoder are the same kind of model.
