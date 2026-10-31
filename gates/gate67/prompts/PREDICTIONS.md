# Gate 67 predictions: does Hive get better the more one owner uses it?

Registered Nov 1 2026, before the run. Asked for by the user, travelling: "something that will genuinely impact hive … making it the best tool to exist". Synthetic owner only; Gate 45 and the founder's Telegram are untouched.

## Why this test

Every gate so far measured one feature. A real owner uses Hive week after week on one business, and a business has **house conventions**: how money is rounded, how a blank value is treated, how a boundary day counts. A good human team learns them once and stops getting them wrong. If Hive does that, each feature costs the owner less attention than the last, and the gap over any one-shot tool widens with use. That is a moat.

Hive today keeps the owner's corrections as standing rulings (`hive/memory.py`) and tells later builds about them. The wording says "Do not stretch one beyond the situation it describes" (from Gate 41, where stretched rulings broke calls). So a correction to one function may never reach a new function that follows the same convention.

## Setup

- **The policy:** an independent rule-giver writes one business's policy (`prompts/rulegiver_brief.md`): 15 functions in three features of 5, with 5 house conventions. Each convention applies to 4 or more functions spanning all three features, and none is a default an engineer would pick. Each function also has 1–2 decisions of its own (2–4 decisions in all).
- **One owner throughout:** a headless Claude holding the whole policy as prose rules (R, Gate 55's documenter), with the skimming brief of Gates 55–65.
- **Each feature, in each arm:**
  1. A first build: 3 builders.
  2. The code sheet D, from the build's code.
  3. Hive's hand-over as shipped: the list review, then spot checks of every function, untouched first, each correction applied alone and re-shown.
  4. A judge labels D and FINAL (what the second build is given) per decision.
  5. A second build: 3 builders, with its hidden pass scored. Its code is the next feature's starting point.
- **Feature 1** runs once, shared. From feature 2 on, three arms build on its code:

| Arm | What is carried from earlier features |
| --- | --- |
| **F** | Nothing (each feature as if it were a new project) |
| **M** | Hive as shipped: the owner's corrections as standing rulings to every later build, and the code sheet leaves out rules that only repeat them (`codesheet.split_known`) |
| **C** | M, plus **house rules**: after each hand-over, one model call distils all his corrections so far into general rules ("Across the business: …", `prompts/house_brief.md`), given to every later build |

Driver `referee/run67.py`, analysis `referee/analyze.py`, both committed now.

## Predictions (features 2 and 3 pooled)

| # | Prediction | Odds |
| --- | --- | --- |
| C1 | C's first builds get ≥ 4 more convention decisions right than F's | 45% |
| C2 | M's first builds get ≥ 2 more convention decisions right than F's | 30% |
| C3 | C's second builds pass ≥ 5 more hidden points than F's (mean) | 40% |
| C4 | C's owner changes ≤ 0.7× as many rules as F's (he is needed less) | 45% |

## Decision rules

- **Ship:** C1 and C3 hold. After every hand-over Hive distils the owner's corrections into house rules (shown to him, kept with the project) and gives them to every later build.
- **Kill:** C gets no more conventions right first time and no more hidden points than F. Nothing compounds this way.
- M against F is reported either way: does Hive's current memory carry anything to new functions?

## Limits

- One business, one run per arm, and a synthetic skimmer. The house conventions are built into this policy on purpose; how many a real business has is not known.
- Arms F, M and C run at the same time on a 2-CPU machine. Times are not compared.
- About $70.
