# Gate 3 results, Oct 27 2026

Gate 3 had three steps:

1. Build protocol v2.
2. Run it at larger swarm sizes.
3. Measure intent bandwidth: how much a product owner's answers raise correctness on rules a model cannot guess.

Predictions were registered before launch in `prompts/PREDICTIONS.md`.

## Step 2: scale with category claims and guarded landing

**Setup.** The Gate 2 project (1,340 visible tests in 127 categories, 362 passing at the start) with protocol v2:

- `tools/claim.py` claims named test categories. It refuses any overlap and withdraws the later claim when two collide.
- `tools/land.py` refuses a landing that adds a duplicate definition, or that fails any test which passes on main.

Two swarms launched at the same time on one 2-CPU machine, as in Gate 2. The 24-worker swarm got only 8 workers: this session caps concurrent agents at 20, so its workers 9 to 24 never started. It is reported here as **F8**; its files keep the original `F24-wN` names.

| Swarm | Workers | Tokens | Per worker | Minutes to all 1,340 | Landings | Conflicts per landing | Landings blocked by guard | Hidden (2,260 + 700) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F8 | 8 | 1.23M | 154k | 10.4 | 36 | 0.36 | 1 (would have broken 10 tests) | 2,260/2,260 and 700/700 |
| F12 | 12 | 1.61M | 134k | 8.7 | 36 | 0.44 | 1 (would have broken 20 tests) | 2,260/2,260 and 700/700 |
| Gate 2, 6 workers | 6 | 963k | 161k | 8.2 | | 0.33 | no guard | 2,260/2,260 |
| Gate 2, 12 workers | 12 | 1.62M | 135k | 7.8 | | 0.48 | no guard; 1 regression reached main | 2,260/2,260 |

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| S1 | Tokens = 111k per worker + 3.0k per category: 12 workers ≈ 1.63M | **Held.** 1.61M (1% off). The same law gives 1.19M for 8 workers; observed 1.23M (4% off). This is the third project size it has predicted. |
| S2 | Finer claims lower the floor: 12 workers under Gate 2's 7.8 min | **Failed.** 8.7 min. |
| S3 | 24 workers buy little over 12 | **Not tested**: only 8 of 24 started. Partial: 12 workers were 1.20× faster than 8 for 1.5× the workers. |
| S4 | The guard keeps regressions off main | **Held at every push.** Both would-be regressions were blocked and fixed. But see the bisect note below. |
| S5 | No category held by two locks | **Held** by construction. Duplicated machinery still happened: workers rebuilt small parsers that sat under another worker's lock. |
| S6 | No gaming: visible and hidden within 1 point | **Held.** At most 0.40 points apart at any commit, on matching categories, in both swarms. |

**Bisect note.** Replaying every commit finds 2 broken commits in each history: one would have broken 20 visible and 40 hidden tests, the other 10 visible and 20 hidden. Each is the commit the guard blocked. It was immediately followed by the same worker's fix, and `land.py --continue` pushed both together, so the tip of main was never broken. The history, though, is not bisect-clean. Fix: `--continue` should fold the fix into the blocked commit before pushing.

## Why S2 failed: the tail

Twelve workers reached 1,290 of 1,340 at 5.8 minutes. The last 50 tests took another 2.9 minutes, done by one worker while the other eleven had stopped. Those 50 tests were the JSON extensions, which F12-w10 had claimed as its third task. F8 shows the same pattern: 1,320 at 8.8 minutes, then one worker finished RETURNING and INTEGER PRIMARY KEY alone at 10.4.

Finish time is set by the last big task that starts late, not by the number of workers:

- **Established (scheduling theory):** makespan ≥ max(total work / N, longest task). Greedy claiming in arbitrary order can be up to (2 − 1/N) × optimal. Claiming the largest task first (LPT) is within 4/3 of optimal.
- **Protocol change for the next run:** a worker claims the largest unclaimed failing category first. The guard's cost also matters: it runs the full suite twice per landing on a shared 2-CPU machine.

## Where conflicts come from

Nearly every rebase conflict (16 in F12, 13 in F8) was two workers adding a line at the same registration point: the function table in `engine.py` or the imports in `parser.py`. Each took about a minute. Category claims did not reduce them, because the shared registration lines, not the categories, are what collide. Letting each module register itself would remove most of them. That is a shaper's job (lower κ).

## Files

- `swarms/F12.bundle`, `swarms/F8.bundle`: full histories (`git clone swarms/F12.bundle`).
- `logs/`: CLAIM, LAND, CONFLICT and BLOCKED events for every worker.
- `results/tokens.csv`: tokens, tool calls and duration per worker.
- `results/eval_F12.json.gz`, `results/eval_F8.json.gz`: every first-parent commit replayed against the visible suite, the 2,260 Gate 2 hidden tests and the 700 Gate 1 hidden tests, with per-test results.

## Step 3: intent bandwidth

**Setup.**

- The finished engine gets 20 business functions with rules invented for this test, so no model can know them. Each rule is in `referee/oracle.py`, which stayed sealed until this run ended.
- Workers saw a one-line spec and 2 happy-path examples per function: 40 visible tests. The 1,340 SQL tests already passing had to keep passing.
- Three swarms of 3 workers launched together. They differed only in how many questions they could put to a product owner, one SELECT returning up to 3 values per question: **none**, **30** shared by the team, or **unlimited**.
- The judge was 500 hidden tests, 25 per function, each holding 3 calls, so 1,450 calls. 72% of the calls are edge cases: NULL, empty, zero, negatives and boundaries.

| Swarm | Questions used | Tokens | Minutes to all 40 visible | Visible | Hidden tests | Hidden calls | Edge calls | Happy-path calls |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Q0 | 0 | 343k | 4.4 | 40/40 | **290/500 (58.0%)** | 80.3% | 72.8% | 99.0% |
| Q30 | 30 (all spent by minute 3.4) | 333k | 5.0 | 40/40 | **433/500 (86.6%)** | 94.6% | 92.4% | 100% |
| Qinf | 320 | 384k | 6.9 | 40/40 | **488/500 (97.6%)** | 98.8% | 98.3% | 100% |

No swarm broke any of the 1,340 existing tests at any commit. The two scoring methods agree exactly: the replay of every commit (`results/eval_Q*.json.gz`) and the call-by-call probe of the final engine (`referee/probe.py`, `results/probe_Q*.json.gz`).

### Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| I1 | Every swarm passes all 40 visible tests | **Held** |
| I2 | Hidden correctness rises with questions: none < 30 < unlimited | **Held**: 58.0% < 86.6% < 97.6% |
| I3 | None ≤ 70% hidden; unlimited ≥ 90% | **Held**: 58.0% and 97.6% |
| I4 | Visible minus hidden gap ≥ 25 points with no questions | **Held**: 42 points |
| I5 | Kill limit 7 if the no-questions swarm reaches 90% | **Not killed**: intent is binding |
| Cheating signature | The no-questions swarm must miss rules no one can guess | **Clean.** It missed every one: UK tax exemption under 10, A+ at 100, 'I' for a NULL grade, 'n-a' for an empty slug, small words in titles, the log tier of SCORE, 'N weeks ago'. One item was badly chosen: CHECKSUM's +97 can be read off the visible example CHECKSUM('abc') = 105, and all three swarms derived it in the open. |

### What it shows

1. **Intent is binding (limit 7, first measurement).** The no-questions swarm passed 100% of what it could see and 58% of what was intended. Its happy-path calls were 99% right; its edge calls only 73%. Visible examples cannot tell a right guess from a wrong one. Unlike Gates 1 and 2, this gap is not overfitting: it is intent that never entered the swarm.
2. **A rule enters only where someone asks.** Pooled over all 60 (swarm, function) pairs, edge calls were right **75.7%** of the time on functions nobody asked about and **96.1%** on functions someone did. Q30 spent its whole budget in 3.4 minutes on the functions claimed first. Four functions claimed later never got a question; FISCAL_Q came out right anyway because it was guessable.
3. **Unlimited access still leaves the rules no question touches.** Qinf asked 320 questions, 26 of them about TAX, but none about a UK amount under 10, so it missed the exemption. It also never asked how WAVG rounds. All 12 of its failing tests come from those two rules. The leftover error is set by *which* questions get asked, not by how many are allowed.
4. **Guesses are noisy across swarms.** On ROUND_HALF_EVEN, neither swarm asked. Q0 guessed decimal rounding (88% right) and Q30 guessed binary-float rounding (72%).
5. **Questions are cheap in tokens, dear in attention.** 320 questions cost 12% more tokens and about 2.5 more minutes. The real price is the product owner's 320 answers.
6. **Diminishing returns.** Edge-call error went 27.2% → 7.6% → 1.7% at 0, 30 and 320 questions. The first 30 questions removed 72% of the errors; the next 290 removed 78% of what was left.

**Model (not yet tested).** For each function, edge error ≈ e_g × (1 − coverage). Here e_g ≈ 24% is the guessing error on edge behaviour, and coverage is the share of input classes some question touched: NULL, empty, zero, negative, boundaries, each category value, and their pairs. The model predicts that a planner choosing questions by coverage, including pairs such as region × small amount, can match Qinf with about 30 questions instead of 320.

**Design consequences for Hive's intent interface:**

- Budget questions per function, not first come, first served.
- Generate questions by input-class coverage, including pairs.
- Turn every answer into a shared test at once, so the knowledge leaves the asking worker's head.
