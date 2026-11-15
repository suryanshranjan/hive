# Gate 115b: predictions (registered before launch, Nov 15 2026)

**Question.** Does Gate 115's gain hold once its flaws are removed? Gate 115 had three: (`gates/gate115/RESULTS.md`)
- **A founder who over-shares:** asked about capacity, he volunteered most of his secrets.
- **One company,** whose facts I wrote alongside the prompt's list of places to look.
- **It always asked 3 questions,** even when nothing was hidden.

**What changes:**
- **A strict founder.** His brief no longer says "say it plainly when a question touches a fact". He is told to answer only exactly what each question asks, never to bring up another fact, and to answer a general question with "Nothing comes to mind."
- **A second company, CrumbHouse** (cakes delivered in Pune, `private/g115b/`), written after Gate 115's prompt. Its four hidden facts are of kinds the prompt does not name. Each changes the right plan for one goal:

  | Goal | His words |
  |---|---|
  | B1 | "Get more people ordering our classic cakes for birthdays." |
  | B2 | "Our chocolate truffle is the bestseller. Make more people buy it." |
  | B3 | "I want more office orders. Make the offices page convert better." |
  | B4 | "More midnight surprise orders, please. People love them." |
  | BC (control) | "Make the FAQ page answer what customers actually ask." |

  The kinds of fact are a licence limit, a supplier problem, a brand rule and a safety rule. They are kept private until scored.
- **TutorNest again:** G1-G4 and the control C1 (G5 is left out: it did not separate the arms).
- **A third arm, `fit`** (`HIVE_PLAN_ASK=fit`). Same places to look as `three`, but it asks only where his answer would change a step, often 0 or 1, at most 3.
  - I first wrote two phrases into it that matched CrumbHouse's facts ("rules", and "anything the site still offers that may no longer be true"), then removed both before registering. `fit` differs from `three` only in when it asks.
  - Its example question mentions a kitchen, as `three`'s does; no CrumbHouse fact is about capacity.

**Arms:** `one` (Gate 106's way), `three` (today's default since Gate 115), `fit`. Each is run once per goal: 10 goals × 3 arms = 30 runs. Same flow, judge and surfacing check as Gate 115. Flight: `python gates/gate115b/flight115b.py --only T:G1,T:G2,T:G3,T:G4,T:C1,C:B1,C:B2,C:B3,C:B4,C:BC`.

| # | Prediction | Kill if |
|---|---|---|
| Q1 | TutorNest, strict founder: `three` accounts for the fact in ≥ 3 of 4; `one` ≤ 2 of 4 | `three` ≤ `one`: Gate 115's gain was the over-sharing |
| Q2 | CrumbHouse (unnamed kinds): `three` ≥ 2 of 4; `one` ≤ 1 of 4 | `three` ≤ `one`: the gain does not reach kinds the prompt does not name |
| Q3 | `fit` is within 1 of `three` on the 8 goals together | — |
| Q4 | Controls: `fit` asks ≤ 1 question on each of C1 and BC; `three` asks 3 | `fit` asks ≥ 2 on both controls |
| Q5 | Over the 8 goals, `fit` asks a mean of ≤ 2.0 questions | — |
| Q6 | No final plan in any arm states a business fact that is neither on the site nor in his answer (checked by hand) | ≥ 2 runs with an invented fact |

**Decision rule:**
- If Q1 or Q2 kills, `three` stops being the default and goes back to `one`, and RESULTS says so.
- If neither kills, `fit` becomes the default when it is within 1 of `three` (Q3) and Q4 holds; otherwise `three` stays.

**Said up front:**
- n = 1 per cell.
- I wrote both companies.
- The strict founder may be stricter than a real one, who often adds context; that would understate every arm.

**Cost:** about $26 (30 runs at Gate 115's $0.88).
