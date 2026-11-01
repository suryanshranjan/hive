# Gate 73 results: the mixed job again, with Hive's two fixes, Nov 1 2026

**Question** (the user: "make hive surpass all levels of agents"). Gate 72's swarm built the engine faster but got the business rules less right. With Hive's two fixes, is the swarm sooner *and* as right as one agent?
- the repeated-question rule (S7D);
- that rule plus Hive asking every question first (S7Q).

**Answer.**
- **No. Neither fix closed the business gap, and asking first made the swarm slower.** The claim did not fire.

| Means over 2 runs | Finish (wall) | 95% visible | Business hidden | Engine hidden | Questions to the owner | Cost |
| --- | --- | --- | --- | --- | --- | --- |
| One agent (A1) | 37.6 min | 35.1 min | **97.0%** | 99.8% | 21.5 | $2.98 |
| 7 builders, repeated-question rule (S7D) | **25.7 min** | 13.0 min | 89.8% | 99.8% | 22.5 | $5.00 |
| S7D plus Hive asks first (S7Q) | 64.0 min | **6.5 min** | 91.0% | 99.8% | 65.0 | $6.70 |

- **The repeated-question rule worked as designed.** It answered 6 questions from an earlier answer (1 and 5 per run), so S7D put no more questions to the owner than one agent did (22.5 vs 21.5).
- **Asking first flooded the owner.** Hive's question writer asked 49 and 71 questions. At 60 s an answer, the swarm waited for him: 64 minutes against 37.6, though its engine reached 95% in 6.5 minutes. Its business rules were still less right (91.0%).
- **The business gap is not the questions' fault.**
  - S7Q's builders waited for the answers and landed the business functions "per owner answers", one as late as minute 57.
  - Yet both swarms missed rules the single agent got right.
  - The single agent asks about each function systematically: the rule, then rounding, then missing or invalid input. The swarms' questions were scattered, and their business functions were built several at a time by one or two builders.

  Gate 74 (registered before this was scored) gives all business functions to one dedicated builder who asks systematically.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| Y1 | S7Q finishes in ≤ 0.8× A1's time | **Scored "held" by the registered formula, but failed in substance.** In g73a one agent ended at 1,359 of 1,360 visible tests (one date test, `timediff_001`), so its time to all visible was infinite and the ratio 0. By wall time S7Q took 1.70× as long (64.0 vs 37.6 min) |
| Y2 | S7Q business ≥ A1 − 2 | **Failed:** −6.0 |
| Y3 | S7D business ≥ A1 − 2 | **Failed:** −7.2 |
| Y4 | S7D asks ≤ 1.1× A1 | **Held:** 1.05× |
| Claim | Y1 and Y2 | **Did not fire** |

## What it means

1. **No change for "Hive asks first."** Writing questions for every decision up front, on a live build, is too many for an owner at a person's pace. It is the right shape overnight (Gate 70), where nobody waits on his answers.
2. **The repeated-question rule stays** (already shipped). It removes duplicates without loss.
3. **The swarm's business gap is about how the business work is done, not about the questions.** Gate 74 tests a dedicated business builder.

## Disclosed

- Registered Y1's formula treats "never passed every visible test" as infinite time, so one failing test made the mean infinite. Gate 74's analysis (registered before this was scored) uses wall minutes in that case.

## Files

`prompts/` (question writer, repeated-question brief, owner, builder prompt, predictions).

`referee/`:
- `run73.py`, `owner_server.py` (queued, paced, `--dedupe`), `ask_owner.py`, `analyze.py`;
- the published rule sets.

`results/g73a/`, `results/g73b/`:
- every question, answer and repeated question (`owner_*.jsonl`, `*.dupes`);
- Hive's first questions (`ask_first.json`);
- probes, team progress, agents and run logs.
