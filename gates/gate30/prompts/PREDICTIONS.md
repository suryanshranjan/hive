# Gate 30 design and predictions, registered before the cases exist (Oct 28 2026)

**Question.** Three gates found that questions (27), an assumption review (28) and kept rulings (29) add nothing measurable. Each time, the owner's rules matched what a capable builder does anyway. Hive's claim rests on the rules where the owner differs from that default. **On cases where the founder is surprising, does the founder's review of the builders' assumptions (with real alternatives, one tap each) carry his rules into the code, where a swarm without him does not?**

**How "surprising" is decided: objectively, before any build.**
1. The founder lists what new people at his company usually get wrong about deals, terms, payments or matching.
2. For each item, the experimenter writes 1 or 2 concrete situations, and the founder gives his verdict on each.
3. **Default probe:** a fresh model is asked each situation cold, with the feature's written spec and no other context. Its answers are recorded, and pushed in aggregate before the build.
4. A case is **surprising** if the founder's verdict differs from the probe's answer, and **ordinary** if they agree. The counts are published before the run; the cases stay private until scoring.
- At least 6 surprising cases are needed. With fewer, the gate is not run, and that fact is published as a finding.

**Arms** (same feature, base and model; 4 workers each):
- **N (no owner):** no questions; assumptions recorded; no review.
- **R (review):** the same build, then the founder reviews the business assumptions on his phone. Each comes with 2 or 3 alternatives and with **Hive's suggestions switched off** (`HIVE_ADVICE=0`), so his choices are his own. Then one fix round.

| # | Prediction |
| --- | --- |
| S1 | **On surprising cases, arm R beats arm N by ≥ 30 percentage points** |
| S2 | On ordinary cases, both arms pass ≥ 85% |
| S3 | All existing backend tests pass in both arms |
| S4 | The founder's review takes under 10 minutes, and he changes at least one assumption per 3 surprising cases |
| S5 | No secret-like file; no breaking commit left broken |

Kill: **arm R beats arm N by < 10 points on surprising cases.** If so, even a review built for disagreement does not carry an owner's surprising rules, and Hive's main claim fails on this evidence.

**Honest prior.** S1 about 45%. The builders may not record an assumption touching each surprising rule, and the founder can only correct what he is shown. That gap (the coverage of the assumption list) is measured as well.

**Cost.** About $6 at list price, plus about 20 minutes of the founder's time: the list, the verdicts, then the review.

The cases, the feature and the probe's answers are fixed by an amendment pushed before the build.
