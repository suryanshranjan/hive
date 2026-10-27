# Gate 8 pre-flight power check (written Oct 27 2026, 11:30 IST, after launch, before any result was seen)

The predictions were registered before launch. This note does not change them. It records, before the scores exist, what this design can and cannot tell apart, so the results cannot be read more strongly than the design allows.

**Method (model).** Per-function spread of the gain, taken from Gate 6's 95% intervals: SD ≈ 12 (0 questions), 6 (1), 17 (3), and about 12 assumed for 2. With 5 functions per level, 20,000 simulated runs per scenario. Script: a 30-line Monte Carlo, reproduced in this note's numbers.

| True curve, gain(0/1/2/3) | R1 holds | R2 holds | R3 holds | Kill fires |
| --- | --- | --- | --- | --- |
| Linear between 1 and 3: 8 / 12 / **28** / 44 | 0.99 | 0.96 | 0.99 | 0.00 |
| Step at the 3rd question: 8 / 12 / **12** / 44 | 0.99 | 0.51 | 0.98 | 0.00 |
| Saturating by the 2nd: 8 / 12 / **40** / 44 | 0.99 | 0.67 | 0.98 | 0.00 |
| No effect at all: 8 / 8 / 8 / 8 | 0.05 | 0.16 | 0.19 | 0.71 |

**What this means.**
- R1, R3 and the kill condition are well powered. If Gate 6's effect is real, they almost surely hold; if it is not, the kill fires about 70% of the time.
- **R2 cannot tell the curve's shape.** It holds 51% of the time even when the second question is worth nothing extra, and 67% when it is worth nearly as much as the third. A pass or a fail on R2 is weak evidence.
- The real information about the shape is the point estimate of gain(2), whose 95% interval will be about ±10 points. That separates "step" (12) from "saturating" (40), but not "linear" (28) from either.
- **Design change this forces for later gates:** to pin gain(2) to ±5, a gate needs about 20 functions at the 2-question level, or a repeat that pools with this one.
