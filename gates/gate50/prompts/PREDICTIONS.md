# Gate 50 predictions: does the swarm beat one agent?

Registered Oct 30 2026, before any team runs. Overnight research, asked for by the user ("break Hive's research parameters"). Gate 45 (the founder's review, day 2 pending) and his Telegram are untouched.

## Why this test

Hive's whole premise is that several builders working in parallel beat one. The evidence for it is old:
- Gate 1: 2 → 6 builders bought 1.26×.
- Gate 2: 2 → 12 bought 2.3×, saturating near 6.

Those runs used an earlier, slower model, whose builders took 8 to 18 minutes on the scale project. Today's builders run on a much faster model and built the whole engine from a skeleton in 4 to 7 minutes with 7 of them (Gate 46). **One builder alone has never been measured.** If one fast agent gets nearly as far as seven, the swarm premise and the law's choice of team size are wrong for today's models.

The law (`hive/law.py`) predicts saturation from three terms:
- the guard's full-suite runs per landing (CPU: 2 cores here);
- onboarding cost per builder;
- coupling, which is small (Gate 46: almost no collisions even from a skeleton).

The critical path (Brent's limit) sets the floor: Gate 46's foundation took the first 1.6 to 4 minutes whatever the team.

## Setup

- **Project:** Gate 46's deep project, from a 221-line skeleton (9 of 1,340 visible) to 1,340 tests in 127 categories. Protocol v2 (claims and the guard). Hidden suite: gen2.py, seed 5000000, private, Gate 46's left-out categories.
- **Teams:** flat and silent, Gate 46's prompt with the time cap raised from 45 to 90 minutes so that one builder can finish. Teams of **1, 2, 4, 7 and 12**, each alone on the 2-CPU machine, run in a shuffled order: N4, N1, N12, N2, N7. One run each.
- **Measured:**
  - minutes to 95% of visible tests;
  - speedup S(N) = t95(1) / t95(N);
  - cost;
  - hidden pass;
  - breaks of main, from replaying every landing.
- **Fit:** a universal scalability law, S(N) = N / (1 + σ(N−1) + κN(N−1)), giving a serial share σ, a crosstalk κ, and a peak team size.
- **Driver and analysis:** `referee/run50.py`, `referee/analyze.py`, committed now. Gate 46's two flat teams of 7 (4.4 and 6.3 minutes) are reported beside N7 as earlier replicates, not scored.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| E1 | One builder reaches 95% within 90 minutes | 80% |
| E2 | Seven builders are at least 2× faster than one: S(7) ≥ 2.0 | 60% |
| E3 | Twelve builders are not more than 10% faster than seven (saturation on 2 CPUs) | 70% |
| E4 | Seven builders cost at most 1.5× one builder (one long session also pays to re-read its growing context) | 55% |
| E5 | Every team's hidden pass is within 1 point of the others | 75% |

## Decision rules

- **S(7) < 1.25:** with today's model the swarm barely beats one agent. The law should pick far fewer builders, and Hive's pitch changes from speed to other benefits (robustness, mixed agents), if any survive.
- **E3 holds and the fit puts the peak at or below 7:** the guard's CPU is the binding limit, as the law says. The next gate attacks it: a guard that checks the claimed categories plus a sample before landing, with full checks after.
- **E3 fails** (12 beats 7 by > 10%): the law's cap of 8 is too low for today's model. Raise it, and refit.

## Cost and limits

- About $20 to $30: 26 builders in all; one builder may run long.
- One run per team size. Gate 46 put the spread between two runs of 7 at 4.4 vs 6.3 minutes, so differences under about 30% in speed are within noise.
- 2 CPUs: absolute times are this machine's. Ratios are what transfer.
