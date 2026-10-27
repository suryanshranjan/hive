# Gate 28 predictions, registered before the run (Oct 28 2026)

**Question.** In Gate 27, live questions did not carry the founder's unwritten rules: a swarm that asked him and a swarm that could not ask both passed 6 of 10 head-only cases. The misses were defaults the builders felt sure of, so they never asked. All 5 were stated in the builders' own commit messages. **If builders write down every default they apply, in plain words, and the founder corrects the wrong ones after the build, are the head-only rules recovered?**

**New tool (`hive`).**
- `hive run --assumptions` tells workers to record every default the goal does not state, especially the ones that seem obvious. They record each with `hive assume "<one plain sentence>"`; the same plain-language check as `hive ask` applies.
- After the build, the owner runs `hive review`. Each assumption is shown in turn: press Enter if it is right, or type the rule. The wrong ones go to `corrections.md`.
- A fix phase then gives the workers the original goal plus the corrections.

**Design.**
- **Codebase.** The same private, secret-checked copy of a real company's Node.js backend (Company X), on the Gate 27 base. The company's repository is never pushed to.
- **A new feature, so the founder cannot know the answers in advance.** In Gate 27 the founder was told which of his rules were missed, so the same feature cannot test a blind review. The new feature is a pure library from the company's spec that decides whether an edit to signed collaboration terms forces both sides to accept again. The spec says only that "any material edit" does; what counts as material is left to the owner.
- **Cases.** The experimenter proposes about 16 edits to one signed deal, and the founder gives his verdict on each (both must accept again, or not). Each case is labelled *documented* or *head-only* before the run. The cases are kept out of the repo and the container until scoring.
- **Arm Q (questions).** 4 workers, 17-question budget, the founder answering live. This is Gate 27's arm A.
- **Arm R (assumption review).**
  1. Build with 4 workers, `--assumptions`, and a question budget of 0. The result is scored as **R-before**.
  2. The founder reviews the assumptions with `hive review`.
  3. 4 workers fix the code from the corrections, with no questions. The result is scored as **R-after**.
- Both builds run at the same time. Scoring is on the verdict only.

| # | Prediction |
| --- | --- |
| P1 | **The review recovers unwritten rules:** R-after beats R-before on head-only cases by ≥ 20 percentage points |
| P2 | R-after beats arm Q on head-only cases by ≥ 15 points |
| P3 | Documented cases do not drop: R-after ≥ R-before |
| P4 | All 384 existing tests pass at the end of every phase |
| P5 | The assumption list names the situation behind ≥ 70% of R-before's head-only misses (the experimenter judges this before seeing R-after) |
| P6 | The founder's review takes under 15 minutes |
| P7 | Replication of Gate 27: arm Q is within 10 points of R-before on head-only cases |

Kill: **R-after beats R-before by < 10 points on head-only cases.** If so, writing down assumptions does not carry unwritten rules either.

**Honest prior.** P1 about 60%: the builders may not record the defaults that matter, or may record too many for a careful review. P2 about 50%. P5 about 55%. P7 about 65%.

**Cost.** About $8 at list price, plus the founder's time: verdicts on the cases, live answers for arm Q, and the review for arm R.

**Limits known in advance.**
- Arm R gets a second build phase and arm Q does not. Extra build time alone could change results, but it cannot supply rules no one stated. P5 records which misses the list covered, so a gain can be traced to specific corrections.
- One founder, one feature, one run per arm.

## Amendment, registered before the run (Oct 28 2026)

- **Cases.** The founder gave his verdicts on all 17 proposed edits: **15 need both sides to accept again and 2 do not.** Before the run, 2 cases are labelled documented and 15 head-only. A private reference passes all 17. The cases are kept out of the container until scoring.
- **Ceiling rule.** The founder's rule turned out close to "every real change counts". A careful builder's default may already match it, which would leave a review nothing to recover (as in Gate 27, where 6 of 10 head-only cases matched the default). So: **if R-before already passes ≥ 80% of head-only cases (12 or more of 15), P1, P2 and the kill are scored "no room" rather than held or failed,** and the gate is reported as uninformative on them. P3 to P7 are scored as written.
