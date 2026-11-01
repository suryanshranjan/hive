# The founder session (Gap 6): one real feature, in his repo, at his keyboard

Everything Hive knows about owners comes from synthetic ones whose answers never change. This session is the test nothing else can replace. It is set up so it can run the day the founder has an hour.

## What he does (about 45 minutes on day 1, 10 on day 2)

1. **Day 1.** Pick one small real feature for his product, one he would otherwise hand a developer: two or three parts and a few business rules.
2. In a terminal, in his repo, run `hive start` and describe the feature in his own words. He answers what Hive asks: the fast/cheap choice, the interview, any builder questions, and the short review.
3. He looks at the branch Hive delivers, and says in one line whether he would merge it.
4. **Day 2, at least 12 hours later.** He answers 10–12 concrete cases about the feature, written by the experimenter from the code's decisions, without seeing his day-1 answers.

No Telegram: the terminal flow only, so the bot stays untouched.

## What we measure

| Measure | From |
| --- | --- |
| His minutes and prompts, and the words he typed | `hive start`'s terminal log |
| Did he finish? Where did he stop or get confused? | the log, and one question to him afterwards |
| Would he merge the branch? | his one line |
| Do his day-1 answers hold on day 2? (Gate 38: 2 of 11 confirmed rules held) | day-1 rules against day-2 verdicts, judged blind |
| Is the delivered code right by his day-2 verdicts? | the day-2 cases, run against the branch |

## Predictions to register before he starts (in `gates/gate<k>/prompts/PREDICTIONS.md`)

- He finishes day 1 in under 30 minutes (Gate 85's synthetic median: 55 prompts, about 12 minutes of machine time).
- At least 7 of 10 day-2 verdicts match the delivered code.
- At least half of his day-1 rules hold on day 2 (Gate 38: 2 of 11).

## Privacy

- **His company stays out of the repo.** No name, rules, data or code is committed. Logs and results stay in `private/`, which git ignores.
- The public `RESULTS.md` reports numbers only, with mock names.
