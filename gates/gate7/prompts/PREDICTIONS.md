# Gate 7 predictions: a real human product owner, registered before the rules exist (Oct 27 2026, 15:40 IST)

**Question.** Every product owner so far was code or an agent. Does a real person's intent reach a swarm as well? How fast and how consistently does a person answer?

**Design.**
1. The user writes 10 business functions privately in chat, which builders never see. Each has a public one-line spec, 2 typical examples, and at least 2 private rules an engineer could not guess.
2. I encode the rules as an oracle. I write a QA-style list of edge cases for each function, and the user confirms the expected outputs in a check table before any builder starts.
3. **Team N:** 3 builders, no questions.
4. **Team H:** 3 builders. In round 1 they build first drafts and write up to 15 questions to the product owner. Each question is about one function, has at most 3 calls, and there are at most 3 questions per function. They land their best guesses.
5. The user answers all of H's questions in one batch in chat, and the answer times are recorded. The answers become tests in H's repo, labelled as rulings on those inputs only.
6. In round 2, the same H builders continue and finish.
7. Both teams are scored on 25 hidden tests per function (250 in all), with 70% edge calls.

| # | Prediction |
| --- | --- |
| Q1 | The person's answers help: H − N ≥ +15 points hidden. Agent owners gave +25 to +32 at a similar 1.5 questions per function |
| Q2 | People are less consistent than code: the user's live answers disagree with their own confirmed rules on at least 5% of answered values |
| Q3 | Median answer time under 60 seconds per question; under 20 minutes for the whole batch |
| Q4 | The rules are not guessable: N below 70% hidden |

**Kill.** If H − N < +5, a real person's intent does not reach the swarm through this channel the way an agent owner's did.

**Known confounds, stated in advance.**
- I encode the user's English rules into code. That is itself a transfer of intent, which the check table is there to catch.
- Answers arrive in one batch rather than live.
- One run per team.
