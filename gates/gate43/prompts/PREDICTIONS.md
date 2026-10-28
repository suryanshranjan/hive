# Gate 43 predictions: a talking swarm against a silent one

Registered Oct 29 2026, before any team runs. Asked for by the user: "can they become aware and talk to each other for high-level coordination and heightened efficiency?" Gate 38 is untouched.

## Why this test

Hive's builders never talk. They coordinate only through git: a claim file names what each one is building, and the guard refuses landings that would break main. The case for silence so far:
- Collisions were rare and cheap: about 5% of concurrent pairs edited the same lines, and a collision cost about a quarter of a restart (real compiler history; Gates 1–3).
- A broken shared tool was repaired within a minute through git alone (lab note).
- Speed stops improving at 6 to 12 workers because of onboarding cost and CPU for the guard (Gates 2, 10, 21), not because of missing coordination.

So the model predicts that talking can win at most the collision cost and some duplicated work, a few percent, and will pay for every message in reading time and tokens. But the model was fitted on silent swarms. A board might buy something it does not see, such as one worker announcing shared machinery (a window-function core) that others then build on instead of each building their own. Only a test can tell.

## Setup

- **Project:** the Gate 2/3 scale project. A SQL engine starts at 362 of 1,340 visible tests (28 of 127 categories). The judge is the hidden suite: gen2.py, seed 5000000, 20 per category. It is generated privately and never committed. Categories where this machine's SQLite disagrees with the stored visible answers are left out, as in Gate 10.
- **Teams:** 6 workers each, 45 minutes at most, protocol v2 (claims and the guard). The teams run one after another, each alone on the machine, in ABBA order: S1, T1, T2, S2.
  - **S (silent):** Gate 3's scale prompt, unchanged.
  - **T (talking):** the same prompt and repo plus `tools/board.py` (post to everyone; read new messages). Workers are asked to read the board at every sync and to use it for high-level coordination: shared machinery, splitting a big area, pitfalls, questions to a lock holder. Claims still decide who holds what.
- **Measured:**
  - finish (last landing on main, from the team's first start);
  - wall time and cost;
  - landings and messages;
  - conflicts and guard blocks, from workers' logs where they exported them;
  - visible and hidden pass.
- **Driver and analysis:** `referee/run43.py` and `referee/analyze.py`, committed now.

## Predictions (S and T are each the mean of their two teams)

| # | Prediction | Odds |
| --- | --- | --- |
| T1 | Talking neither speeds up nor slows down the finish by more than 15% (0.85 ≤ T/S ≤ 1.15) | 55% |
| T2 | Talking costs ≥ 10% more | 55% |
| T3 | Hidden pass within 2 points (both teams should finish nearly everything) | 80% |
| T4 | Each talking team posts ≥ 6 messages (they use the board) | 75% |
| T5 | Conflicts plus guard blocks per landing: T ≤ S | 50% |

## Decision rules

- **Ship a board** (as an option in Hive): T finishes ≥ 20% sooner than S in both pairings (T1 vs S1, T2 vs S2), at ≤ 1.10× the cost.
- **Silent stays:** T is not faster and costs more.
- Anything between: report it, and say what a longer project or more workers would need to show.

## Cost and limits

- About $10 to $20: 24 workers on a larger task than Gates 39–42.
- 2 CPUs: the guard's full-suite runs queue for the processor, so finish times carry machine noise. Earlier runs varied ±25% between repeats (Gate 21), which is why there are two teams per arm in ABBA order.
- One project, 6 workers. Talking may matter more with more workers or more tightly coupled work; this tests the case Hive meets most.
