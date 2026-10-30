# Gate 64 results: dynamic effort, Oct 30 2026

**Question** (from the user: "orchestrator better agent then worker lesser capable agent … dynamically increase effort as required"). Is a smarter planner over cheap builders, with stronger builders called in only when work is left, better than today's all-Sonnet team? Tested on the hardest project we have: a SQL engine from a 221-line skeleton to 1,340 tests.

**Answer.**
- **No. The kill rule fired; Sonnet builders stay.**
- **Haiku can do the hard work, but it is not cheaper.** Four Haiku builders built the whole engine (1,340/1,340, 99.4–99.9% hidden) and never needed escalation. But they used about 4.5 times the tokens (66–82M against 17.5M per team) and took about twice as long. A cheap model is cheap per token, not per job.
- **The Opus planner made the Haiku team slower and dearer.** Its plans were good: on main in 75–80 s, with interfaces the builders used. But the Haiku builders already found the work without one. With a planner, 95% took 11.2–11.6 minutes against 9.4–11.2 without, and the lead added $0.97–1.30. This is Gate 46's result again, now with weaker builders under a stronger lead.

| Team (4 builders) | 95% visible | All 1,340 | Hidden | Cost | Tokens |
| --- | --- | --- | --- | --- | --- |
| **S: Sonnet (today's Hive)** | **5.3 min** | **5.3 min** | 99.8% | **$5.01** | 17.5M |
| H: Haiku | 9.4 | 10.8 | 99.4% | $4.89 | 78.6M |
| HE: Haiku, escalation ready (never needed) | 11.2 | 11.5 | 99.9% | $5.13 | 81.5M |
| OH: Opus lead + Haiku | 11.6 | 12.4 | 99.8% | $5.20 ($0.97 lead) | 65.5M |
| OHE: Opus lead + Haiku, escalation ready (never needed) | 11.2 | 13.7 | 99.7% | $5.56 ($1.30 lead) | 66.3M |

- **H and HE ran the same way**, since escalation never started. Their gap (9.4 vs 11.2 minutes to 95%) is the noise: about 20%.
- **No team broke main**, and all were correct. The differences are time and money only.
- **The escalation mechanism was never exercised**, because nothing was left for it. Whether it rescues a stuck cheap team is untested.

## Why the cheap model was not cheap

Gate 62 found Haiku builders cost about a sixth of Sonnet's on small intent-bound jobs: ten business functions, each a few lines. On a large engineering job, a weaker model reads more, tries more and reruns tests more. Its tokens grew about 4.5-fold, which ate its lower price. Sonnet is the cheapest builder per finished job here, and the fastest.

## Setup

- Gate 46's deep project; Gate 50's hidden suite (2,260 tests; the three categories where local SQLite disagrees are left out of the score).
- 4 builders per team; each team alone on the 2-CPU machine, in the order H, OHE, S, HE, OH.
- 30-minute cap per wave.
- **The lead:** Gate 46's lead prompt on Opus (`--model opus`). It plans the levels and interfaces and keeps BRAIN.md current. The Haiku builders followed it (Gate 46's worker prompt).
- **Escalation:** when the first wave stops with any visible test failing, 2 Sonnet builders, then 1 Opus builder.
- Predictions pushed before any team ran (`2e65cb5`).
- Total cost about $26.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| D1 | Haiku alone reaches 1,340 visible | **Held** |
| D2 | The Opus planner gets Haiku to 95% in ≤ 0.8× the time | **Failed:** 11.6 vs 9.4 min (slower) |
| D3 | Haiku plus escalation finishes at ≤ 0.6× Sonnet's cost, as correct | **Failed:** 1.02× the cost (as correct) |
| D4 | Planner plus Haiku plus escalation, the same | **Failed:** 1.11× |
| D5 | The planner's team costs at least as much as without it | **Held:** $5.56 vs $5.13 |
| Cheap pace / planner | | **Did not fire** |
| Kill | Neither cheap team reaches ≤ 0.6× Sonnet's cost | **Fired** |

## What it means

1. **No change to Hive's builders.** Sonnet is both the fastest and the cheapest per finished job on hard work. On small jobs Haiku is cheaper, but those jobs cost cents anyway. `hive pace cheap` stays one Sonnet builder (Gate 50: $2.94 for this engine).
2. **An orchestrator does not pay at any strength tried.** Same-strength lead (Gate 46): 1.2× slower. Stronger lead over weaker builders (here): 1.0–1.2× slower and 1.06–1.08× the cost. The builders find the work from the tests and the claims. A plan adds a dependency on the planner, which is the serial share that limits a swarm.
3. **Escalation remains a sound safety net, but an untested one.** It needs a job where cheap builders get stuck, and none did here.

## Limits

- One run per team, on one project. A harder project, where Haiku actually gets stuck, would test escalation.
- Opus led for 13–17 minutes in each lead team; its cost is fully counted.

## Files

`prompts/` (flat, lead and lead-following worker prompts with a 30-minute cap; predictions), `referee/` (`run64.py`, `analyze.py`).

`results/`:
- agents and their costs;
- each team's progress replay and scores (`teams_summary.json`), meta and the run log;
- the analysis.
