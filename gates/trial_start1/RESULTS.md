# Trial results: the first real `hive start` run, overnight mode, Oct 28 2026

Only aggregate numbers are published. The company (Company X), its spec, code and the builders' assumptions stay private.

**Question.** Does Hive's one-command flow work for real, unattended, on a real company's codebase?

**Answer: yes, with one prediction missed.**
- The run went from the goal file to a tested branch with nobody at the keyboard.
- All 384 existing tests were kept, and 35 new ones were added.
- 5 minutes, $2.49.
- The owner's list for the morning held **15 business assumptions** (5 technical ones were filtered out). That is above the 12 predicted, so the list still needs ranking.

| Measure | Result |
| --- | --- |
| Tests on the result | **419 / 419**; all 384 that passed before still pass |
| Builders | 4, finished in 1.1 to 4.4 minutes, all exited cleanly, no API errors |
| Files committed | Hive's settings file, 1 new module and 3 test files; no secret-like files, no artifacts |
| Assumptions | 20 recorded: **15 business** for the owner, 5 technical for engineers |
| Time and cost | 5 minutes, $2.49 at list price |

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| T1 | Completes unattended, with the result as a `hive/...` branch | **Held** |
| T2 | 384 existing tests pass; Hive's own check reports none broken | **Held:** 419/419 |
| T3 | Every builder exits cleanly, with no API errors | **Held** |
| T4 | 3 to 12 business assumptions reach the owner | **Failed:** 15 (5 technical filtered out) |
| T5 | Under $6 and under 30 minutes | **Held:** $2.49, 5 minutes |
| T6 | No secret-like file or artifact committed | **Held** |

## What it means

1. **The one-command flow works on a real codebase.** It found the test command, kept every existing test, and handed over a branch, with nobody at the keyboard. This is the first real run, not one with stand-in builders.
2. **The business assumptions are real decisions,** not noise. They cover:
   - what a combined total shows when two data sources disagree;
   - whether one creator's reach on two platforms is added together;
   - whether a social account imported twice is counted twice.

   The last one looks like a default the owner would want changed. These are the questions Gates 27 and 28 showed builders do not ask on their own.
3. **The list is still too long for a busy owner.** The technical filter removed 5 of 20, but 15 remain from a 5-minute build. The next step is to rank them by how many outcomes each one changes, and show the top few first.

## Small fixes from this trial

- The test source read "Your tests: your hive settings." It now reads "the command in your hive settings".
- Branch names dropped the word "goal" from a goal file's title.

## The owner's review on his phone, and the fix round (same day)

The founder reviewed the 15 assumptions on Telegram with `hive morning --phone`. Before he saw them, three changes went in after his first look:
- The first version showed the builders' raw wording, and he found it "too technical". Each assumption is now rewritten with context and an example, the list is ranked, and at most 8 are shown first.
- Each decision now carries Hive's recommendation, so one tap is enough.
- An undo button was added.

| Measure | Result |
| --- | --- |
| Decisions answered by the founder | **15 of 15**: the 8 most important, then the minor ones, which he chose to see |
| Changed / kept | 4 changed, 11 kept |
| Changes that took Hive's suggestion | **4 of 4** |
| Time per decision | median about 4 seconds (the first, in the earlier flow, took 25 minutes to be noticed) |
| Fix round | 4 changes landed by 3 builders in under 2 minutes; a 4th builder found nothing left and idled 26 minutes ($0.54) |
| Final result | **437 / 437 tests**, all 384 original tests still pass |
| Whole run | 32 minutes from start to the fixed branch, $4.81 at list price |

**What it means:**
- **The phone review works on a real build:** every decision was answered, mostly in seconds.
- **Suggestions steer:** each change the founder made was the one Hive suggested. That is the product working as intended, and the reason experiments switch suggestions off (`HIVE_ADVICE=0`).
- **Two answers could not both hold,** and the builders received both. The bot now checks for such contradictions before sending and asks which should win.
- **The idle builder** led to two fixes: a fix round now uses one builder per two corrections, and a builder with nothing left stops at once.
