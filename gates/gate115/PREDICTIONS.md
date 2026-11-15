# Gate 115: predictions (registered before launch, Nov 15 2026)

**Question.** Does Hive find what lives only in the founder's head before it plans? BRAIN §8 item 5: Gate 106's one miss was in the data, and Gate 108 found it there. What neither the product nor the data shows has never been measured.

Since Gate 106, the planner can ask one question ("missing") when it suspects something the product can't show. Nobody has measured how often that question finds the thing that matters.

**The company.** TutorNest, a made-up home-tutoring service in Hyderabad.
- **Site:** 5 pages and one test.
- **Data:** none, so nothing is in the data either.
- **Determinism:** made by a private generator, `private/g115/make_company.py`.

**What lives only in his head.** These are written into the simulated founder's private brief (`private/g115/key.json`), and nowhere else. Each one changes the right plan for one goal. The facts are kept private until scored.

| Goal | His words |
|---|---|
| G1 | "I want more board-exam students. Get me more Class 10 sign-ups." |
| G2 | "I want more families coming through schools." |
| G3 | "Make the subjects and fees page bring in more bookings." |
| G4 | "Too many families drop after the free demo. Fix that." |
| G5 (held out) | "I want more families from Gachibowli and Kondapur." |
| C1 (control: nothing hidden) | "Make the FAQ page answer what parents actually ask." |

**Two arms**, each the real planner (Claude Code, reading the site in a copy):
- **`one`** (Hive today, since Gate 106): at most one question, when the planner suspects something is missing.
- **`three`** (new, `HIVE_PLAN_ASK=three`): the planner lists what its plan silently assumes about his business that nothing it saw can confirm, and asks the up to 3 that would change the plan most. The prompt suggests five places to look:
  - capacity;
  - deals outside the site;
  - things about to start or stop;
  - the real reason customers leave;
  - who on his team does what.

The flow is the same as on the phone (`hive/assistant.py` pursue):
1. plan;
2. the questions;
3. his one answer (simulated founder, `claude -p`, from the brief; he answers what he is asked and never volunteers);
4. plan again with it.

**Scoring.** A blind judge (`claude -p`, no tools) is given only the goal, one rubric line and the final plan. It never sees the arm, the questions or his answer. It answers whether the plan accounts for the hidden fact. A second judge says whether his answer stated the fact ("surfaced"). Each goal is run 2 times per arm, and the control once per arm: 22 runs. Flight: `python gates/gate115/flight115.py`.

**Known bias, said up front.** I wrote the `three` prompt's list of places to look knowing G1-G4's facts, so it may be fitted to them. G5 was written after the prompt, and its fact is not one of the planted kinds by name (it is about where tutors will travel). G5 is scored separately as the held-out check. A second company in another trade, written by someone else, would be the real test.

| # | Prediction | Kill if |
|---|---|---|
| P1 | `one` accounts for the fact in ≤ 4 of 8 runs (G1-G4) | — (baseline) |
| P2 | `three` accounts for it in ≥ 7 of 8 runs (G1-G4) | `three` − `one` < 3 runs: then the default stays `one` |
| P3 | `three` surfaces the fact (he states it) in ≥ 7 of 8; `one` in ≤ 4 of 8 | — |
| P4 | Held out (G5): `three` accounts for it in 2 of 2; `one` in ≤ 1 of 2 | `three` 0 of 2: the gain is fitted to the planted kinds, said so in RESULTS |
| P5 | Burden: `three` asks ≤ 3 questions every time, mean ≤ 3.0; on the control (C1) it asks ≤ 2 and still gives ≥ 2 steps | a control plan with < 2 steps, or derailed by its questions |
| P6 | No invented facts: in `three`, no final plan states a business fact that is neither on the site nor in his answer (judged by hand on all 10 G1-G5 `three` runs) | ≥ 2 runs with an invented fact |

**Decision rule.** If P2 holds and P4 is not killed, `three` becomes the default (`hive/plan.py` `ASK_DEFAULT`). Otherwise Hive stays on `one`, and RESULTS says why.

**Cost.** About 22-44 planner calls on the Claude Code login, plus about 66 small judge and founder calls. Estimated at $8-15 at list price.
