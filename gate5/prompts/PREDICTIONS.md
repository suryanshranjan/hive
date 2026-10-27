# Gate 5 predictions, registered before the rules exist (Oct 27 2026, 14:45 IST)

**Question.** Gate 4 found that both teams with questions missed the same kind of rule: places where the owner departs from a convention the builders took for granted (NULL handling, caps on extremes). Does a team told to ask about its defaults first beat free asking? And is that true for a rule-giver other than the experimenter, who formed this idea after seeing his own rules?

**Rule-giver.** An independent agent that has never seen this project's hypotheses, earlier rules or conversation. It gets only `rulegiver_brief.md`. I only check its rules mechanically (they run, and repeated runs agree) and don't edit them.

**Teams.** Three teams of 3 builders on the same engine as Gates 3 and 4, one run each. They differ only in one paragraph of the prompt (`ask_texts.md`):
- **D0:** no questions.
- **D30f:** 30 questions, asked freely; the control, with the same text as Gate 4's R30.
- **D30d:** 30 questions, defaults first.

**Hidden suite.** 25 tests per function, 70% edge calls, drawn from the rule-giver's own TYPICAL and EDGE lists, never seen by any builder. Built with the same generator scheme as Gates 3 and 4 (visible: 2 tests of 3 typical calls per function).

| # | Prediction |
| --- | --- |
| H1 | Every team passes all visible examples |
| H2 | Defaults-first beats free: D30d ≥ D30f + 5 points hidden. Odds: about 40% |
| H3 | Replication of the gain from 30 questions: D30f − D0 between +15 and +43 points (Gates 3 and 4: +28.6, +29.0) |
| H4 | The treatment is followed: at least a third of D30d's questions contain NULL; fewer than a fifth of D30f's do |
| H5 | The rules are not guessable: D0 below 70% hidden |

Analysis fixed in advance:
- Hidden pass rates with 95% intervals bootstrapped over functions.
- The paired difference D30d − D30f with its interval.
- The share of questions containing NULL in each team.
- The share of failing calls containing NULL in each team.

Kills:
- If D30d ≤ D30f while H4 holds, "ask about your defaults" does not carry over to another rule-giver.
- If H4 fails, the treatment was not delivered and the test is inconclusive.
- If D0 ≥ 85% (H5 badly off), the rules were guessable and the test says little.
