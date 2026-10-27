# Gate 8 predictions, registered before the rules exist (Oct 27 2026, 16:30 IST)

**Question.** Gate 6 found, with questions randomly assigned per function, that one question bought little (+12 points of edge accuracy) and three bought a lot (+44), but it never measured two. Is the curve real, and where does the second question sit?

**Design (one command: `python3 lab/run_gate.py lab/experiments/g8_curve.json`).**
- **Rules.** A fresh independent rule-giver (`gate5/prompts/rulegiver_brief.md`, headless Claude Code) writes 20 rules into `private/g8/`. They are checked mechanically and not edited.
- **Teams.** Two teams of 3 builders:
  - **N0:** no questions.
  - **NQ:** each function gets an allowance of 0, 1, 2 or 3 questions, five functions at each level (30 questions), assigned by the fixed shuffle `random.Random(8000)` over the sorted function names. The server enforces it.
- **Hidden suite.** 25 tests per function (seed 8200000), 70% edge calls.
- **Measure.** Per function, the gain in edge-call accuracy of NQ over N0. Report the mean per allowance level, with 95% intervals bootstrapped over functions.

| # | Prediction |
| --- | --- |
| R1 | Replication: gain(3) − gain(0) ≥ +15 points (Gate 6: +36) |
| R2 | The curve rises: gain(1) ≤ gain(2) ≤ gain(3) |
| R3 | The first question is worth less than half of three: gain(1) < 0.5 × gain(3) (Gate 6: 0.27) |
| R4 | Rules not guessable: N0 below 70% hidden |
| R5 | Treatment delivered: at least 27 of the 30 allowed questions used |

Kills:
- If gain(3) − gain(0) < +5, Gate 6's causal result did not replicate.
- If R3 fails, Gate 6's "one question buys little" was a fluke, and the advice to ask in blocks of about 3 must be withdrawn.
