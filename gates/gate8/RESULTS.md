# Gate 8 results: the question curve, replicated, with the 2-question point, Oct 27 2026

**Question.** Gate 6 found, by random assignment, that one question per function bought little (+12 points of edge accuracy) and three bought a lot (+44). It never measured two. Is the curve real, and where does the second question sit?

**Answer.**
- **Questions cause the gain, again.** Functions randomly allowed 3 questions gained +39.1 points of edge accuracy over the no-question team (CI +25.8 to +52.3); unasked functions gained exactly 0.
- **The first question is not cheap. Gate 6's "one question buys little" was mostly bad luck in the randomization.** Here one question bought +21.0, more than half of three (R3 failed, and its kill condition fired). Going back to Gate 6's data: its 1-question functions happened to start with half the fixable errors of its 3-question functions (23% of edge calls wrong with no questions, against 46%).
- **One law fits both gates once headroom is counted (model).** Each answered question fixes about half of the edge errors still left on its function: p = 0.53 in Gate 6, 0.56 in Gate 8. Returns diminish: about 0.55, then 0.25, then 0.11 of the original errors.
- **Design change:** the advice "ask in blocks of about 3 per function" is withdrawn. Under this law, one question on every function, then second questions, fixes about 1.5× as many errors as blocks of 3 (model, not yet run head to head).

## Setup

- **Rules.** A fresh independent rule-giver (same neutral brief as Gates 5 and 6, headless Claude Code, $0.82) wrote 20 rules, checked mechanically (248 calls, deterministic) and not edited. Predictions were pushed before the rules existed (commit a43088d).
- **Teams.** Two teams of 3 builders, one run each, in a Docker container on a 24-core laptop:
  - **N0:** no questions.
  - **NQ:** each function allowed 0, 1, 2 or 3 questions, five functions at each level, by the registered shuffle `random.Random(8000)`. The server enforced it. A question is one SELECT returning up to 3 values, as in Gate 6.
- **Hidden suite.** 500 tests (seed 8200000), 70% edge calls. Not committed; it regenerates from the seed and `referee/oracle.py`.

| Team | Questions | Builder cost | Minutes | Visible | Hidden tests | 95% CI by function |
| --- | --- | --- | --- | --- | --- | --- |
| N0 | 0 | $2.34 | 2.1–2.7 | 1,380/1,380 | **212/500 (42.4%)** | 30.4–54.8% |
| NQ | 30 (as assigned) | $2.83 | 2.5–3.4 | 1,380/1,380 | **359/500 (71.8%)** | 60.6–82.0% |

Paired difference NQ − N0: **+29.4 points** (CI +16.0 to +42.6), the fifth replication of the gain from 30 questions (Gates 3 to 6: +28.6, +29.0, +32.4, +25.0).

Token note: `launch.py` reports 0.9 to 1.8M tokens per worker. That count includes cache reads, which cost a tenth of fresh input. The dollar cost at list price, $6.0 in all, is the comparable number; the "0.8M tokens" budget in the queue card was in fresh-token terms.

## The measurement

Gain per function = NQ's edge-call accuracy minus N0's on that function. The pre-flight note (`PREFLIGHT.md`, written before any score was seen) said R2 was too weak to tell the curve's shape, and gain(2) would carry about ±10 points.

| Allowance (random) | Functions | Mean gain | 95% CI | Gate 6 |
| --- | --- | --- | --- | --- |
| 0 questions | 5 | **+0.0** | 0 to 0 | +7.9 |
| 1 question | 5 | **+21.0** | −1.5 to +43.6 | +11.9 |
| 2 questions | 5 | **+26.1** | +5.0 to +47.8 | not measured |
| 3 questions | 5 | **+39.1** | +25.8 to +52.3 | +44.0 |

Gain(1) / gain(3) = 0.54 (Gate 6: 0.27).

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| R1 | Replication: gain(3) − gain(0) ≥ +15 | **Held**: +39.1 (CI +25.8 to +52.3) |
| R2 | The curve rises: gain(1) ≤ gain(2) ≤ gain(3) | **Held**: 21.0 ≤ 26.1 ≤ 39.1. Weak evidence: the pre-flight check showed it passes about half the time even when the 2nd question adds nothing |
| R3 | The first question is worth less than half of three: gain(1) < 0.5 × gain(3) | **Failed**: 21.0 against 19.6 (ratio 0.54) |
| R4 | Rules not guessable: N0 below 70% hidden | **Held**: 42.4% |
| R5 | At least 27 of 30 allowed questions used | **Held**: 30 of 30, exactly as allotted |
| Kill (R1) | gain(3) − gain(0) < +5 means Gate 6 did not replicate | **Did not fire** |
| Kill (R3) | If R3 fails, "one question buys little" was a fluke and "ask in blocks of about 3" must be withdrawn | **Fired.** The advice is withdrawn |

## What it means

### 1. Gate 6's curve was shaped by headroom, not by the first question being weak

A function can only gain what its no-question version gets wrong. Random assignment over 6 or 7 functions does not balance that. Counting the share of N0's edge errors that NQ fixed (`referee/share_fixed.py`):

| Gate | Questions | Functions | N0 edge error rate | Share of errors fixed | Law 1 − (1−p)^q |
| --- | --- | --- | --- | --- | --- |
| 6 | 0 | 6 | 54% | +0.15 (spillover) | 0 |
| 6 | 1 | 7 | **23%** | 0.51 | 0.53 |
| 6 | 3 | 7 | **46%** | 0.92 | 0.89 |
| 8 | 0 | 5 | 34% | 0.00 | 0 |
| 8 | 1 | 5 | 50% | 0.56 | 0.56 |
| 8 | 2 | 5 | 43% | 0.65 | 0.80 |
| 8 | 3 | 5 | 45% | 0.87 | 0.91 |

p, fitted per gate on errors fixed: **0.53** (Gate 6, 95% CI 0.43–0.65) and **0.56** (Gate 8, CI 0.38–0.75). The two rule-givers were independent.

**The law (model).** For a function f with E_f edge errors when nobody asks, after q answered questions:

```
errors fixed ≈ E_f · (1 − (1 − p)^q),    p ≈ 0.55
```

Each answer resolves about half of what is still wrong. Status: fitted on Gate 6, then checked once on held-out Gate 8. The 2-question point (0.65 against 0.80) sits below the law, driven by two functions where nothing was fixed (below).

**Held-out check of the level means** (`referee/curve_fit.py`, parameters fitted on Gate 6 only, then used to predict Gate 8):

| Model (one parameter) | Predicted G8 gain at 1 / 2 / 3 | Error on level means | Error per function (SSE) |
| --- | --- | --- | --- |
| Linear: s·q points | 14.4 / 28.8 / 43.2 | 4.1 pts | 0.80 |
| Headroom: (1 − a0)(1 − (1−p)^q) | 26.5 / 32.7 / 39.7 | 4.3 pts | **0.43** |
| Headroom, linear in q | 22.9 / 38.4 / 44.3 | 6.7 pts | 0.47 |
| Observed | 21.0 / 26.1 / 39.1 | | |

On level means the linear and headroom laws are tied. Per function, the headroom law has half the error, because it knows that a function already right cannot gain.

### 2. What it means for spending a budget (model)

The marginal value of the q-th question on a function is E·p(1−p)^(q−1): about 0.55E, then 0.25E, then 0.11E. With equal headroom, a 30-question budget over 20 functions fixes:

| Allocation | Errors fixed (units of E) |
| --- | --- |
| Blocks of 3 on 10 functions (Gate 6's advice) | 9.1 |
| One on every function, then 10 second questions | **13.5** (about 1.5×) |

Gate 6's allocation table, which favoured blocks of 3, came from the headroom imbalance above. This is a model until it is run head to head.

### 3. Questions that confirm a guess buy nothing (conjecture)

Every asked question was replayed against N0's final engine (`referee/surprise.py`). A "surprise" is an answered value that differs from what the builders would have guessed anyway.
- The two asked functions with **zero** surprises, `normalize_phone` (0/3) and `sku_normalize` (0/6), fixed nothing, though they had 24 and 15 edge errors. The questions landed on points the builders already had right, and their errors lay elsewhere.
- So a confirming answer does **not** mean the guess is right: `normalize_phone` was still wrong on 46% of its edge calls.
- **A "surprise law" did not survive its held-out test.** Fitting errors fixed on the surprise count instead of the question count worked well on Gate 8, where it was found (weighted MSE 0.030 against 0.102), but did worse on Gate 6 (0.056 against 0.033). The question-count law is the one that held out.

### 4. Spillover is not universal

Gate 6's unasked functions gained +7.9 (0.15 of their errors), plausibly through shared conventions. Here they gained exactly 0. The two independent teams scored the same on each of the 5 unasked functions, so without answers the guess behaves like a fixed property of the spec and the model, not like noise.

### 5. One question can teach the wrong rule

`review_score` got worse with its one question (−2 calls). The question varied three things at once (a 0 rating, a 7 rating, NULLs), the same failure Gate 5 saw with `nps_score`.

## Design consequences for Hive's intent interface

- **Withdrawn:** "spend questions in blocks of about 3 per function." It came from a randomization imbalance.
- **New default (model):** give every function a first question before any function gets a second. Then spend the seconds where the first answer surprised and the function's spec is widest.
- **New rule for experiments:** randomize allowances *within strata of headroom*. Run N0 first (it needs no product owner), measure each function's edge errors, then assign allowances in balanced blocks. Report gains as the share of errors fixed, not raw points.
- **Unchanged:** vary one thing per question; write answers as tests; put the allowed input values in the spec.

## Honest odds and what would kill this

- p ≈ 0.55 holds within ±0.15 on a third independent rule-giver: about 65%.
- One-then-second beats blocks of 3 head to head, in errors fixed: about 60%. **Kill:** if blocks of 3 fix as many errors or more in a headroom-stratified test, the diminishing-returns law is wrong and Gate 6's original reading comes back.

**Cheapest next experiment.** Run N0 first (about $2.3), then two arms on the same rules: "one on every function plus 10 seconds" against "3 on 10 functions", with the 10 functions per arm matched on headroom. Prediction to register: the spread arm fixes at least 1.3× as many edge errors.

## Limits

- One run per team, 5 functions per allowance level; the intervals are wide (pre-flight: ±10 points on each level).
- The headroom law was proposed after seeing Gate 8's raw curve. Its parameter came from Gate 6 and predicted Gate 8, so it has one held-out check, in one direction.
- The rule-giver is the same kind of model as the builders.

## Files

| Path | Contents |
| --- | --- |
| `prompts/PREDICTIONS.md` | Predictions and kill conditions, pushed before the rules existed |
| `PREFLIGHT.md` | Power check written after launch and before any score was seen |
| `referee/oracle.py` | The rule-giver's 20 rules, unsealed after scoring (synthetic) |
| `referee/curve_fit.py`, `referee/share_fixed.py`, `referee/surprise.py` | Held-out curve fits, the headroom table, and the surprise replay |
| `results/summary.md`, `results/summary.json` | `run_gate.py` output |
| `results/allowance.json`, `results/asks_NQ.log` | The random assignment; every question and answer |
| `results/probe_*.json.gz`, `results/tokens.csv`, `results/run.log` | Call-by-call probes, cost and minutes per worker, the run log |
| `results/*.txt` | Outputs of the three analysis scripts |
| `swarms/*.bundle`, `logs/` | Both teams' git histories; worker logs |
