# Gate 66 results: Hive against a Claude Code agent with the same owner, Nov 1 2026

**Question** (from the user, travelling: "test something … that will genuinely impact hive"). Every earlier gate compared Hive with itself or with no owner. Does Hive beat what an owner can already do: open Claude Code, describe the feature, and answer the agent's questions?

**Answer.**
- **No, and by a wide margin.** With the same owner, one Claude Code agent that asks him questions beat Hive's hand-over by 21 to 30 hidden points, and needed 13× less of his reading. Neither headline prediction held.

| Pooled over 2 fresh rule sets | Hidden pass | Owner's load per run |
| --- | --- | --- |
| No owner, 3 builders (N0) | 34.8% | – |
| **One agent, may ask (CC)** | **84.6%** | 10.5 questions, 2,030 characters |
| **One agent, told to ask first (CQ)** | **93.0%** | 16 questions, 2,417 characters |
| Hive's hand-over of N0's build (HV): code sheet, list review, spot checks of every function | 63.4% | 82.5 replies, 30,839 characters |

- **Paired differences:**
  - HV − CC: −21.2 (95% CI −32.8 to −10.2);
  - HV − CQ: −29.6 (CI −40.0 to −19.0);
  - CQ − CC: +8.4 (CI +1.0 to +16.8).
- **Today's model asks on its own.** Told only that the owner was available, the agent asked 10–11 questions per run, in plain business words: "If the end date is before the start date, should the working-day count be negative, zero, or blank?" Gate 4 (an older model) saw builders leave whole functions unasked.
- **Why questions win:** the answer goes straight into code, written by the one who asked. The hand-over has two lossy steps:
  - the owner must *notice* an error in a long sheet or a case (he skims);
  - the correction must survive the trip from his words to a rule to a new build.

  The skimmer's sheet still had only 5 and 18 of 25 decisions right after 78–87 replies.
- **Cost:** one agent cost $0.27–0.39 a run. Hive's hand-over cost $1.96 (two builds of 3 builders, describer and spotter), excluding the synthetic owner.

## Setup

- **Rules:** two fresh rule sets from an independent rule-giver (g66a, g66b; 10 functions and 25 declared decisions each; now published in `referee/oracle_g66a.py` and `oracle_g66b.py`). Predictions pushed before the run (`ecaa286`).
- **The owner:** one person model, a headless Claude holding the policy as prose rules (R).
  - Asked a question, he answers in a sentence or two from his policy (`prompts/owner_qa.md`, served by `referee/owner_server.py`).
  - Reviewing, he skims (Gates 55–65's brief).
- **Arms:**
  - CC and CQ: one builder each (Sonnet, the default), asking via `referee/ask_owner.py`.
  - N0: 3 builders, no owner.
  - HV: Hive's hand-over of N0 as shipped after Gate 63, then 3 fresh builders from the corrected sheet.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| B1 | HV ≥ CC + 10 | **Failed:** −21.2 |
| B2 | HV ≥ CQ + 5 | **Failed:** −29.6 |
| B3 | CQ asks ≥ 15 per run | **Held:** 16 |
| B4 | CC asks ≤ 5 per run | **Failed:** 10.5 (today's model asks unprompted) |
| B5 | HV's owner reads ≥ 2× CQ's | **Held:** 12.8× |
| Headline | B1 and B2 | **Did not fire** |
| Registered next step | CQ ≥ HV, so test them combined | **Gate 68**, registered before this was scored |

## Disclosed

- **HV is Hive's hand-over alone, not Hive as shipped.** When the owner is present, `hive start` also lets builders ask him (`hive ask`) and opens with an interview. The predictions called HV "Hive's hand-over as shipped", which is accurate for the hand-over but not for the whole product. Gate 68 tests Hive's swarm asking, with and without the hand-over after.
- **The synthetic owner answers consistently and generously.** His answers come from one fixed policy, and often add a related rule the question did not ask about ("…capped at 25%. There's a 3-day grace period…"). A real founder's answers drifted from his own later verdicts (Gates 36–38), and in Gate 27 live questions to him did not beat no questions. So this gate shows what questions are worth when the owner knows his rules, not that they will work as well with a real founder.

## What it means

1. **The binding limit moved.** With today's models, a builder that may ask an owner who knows his rules gets 85–93% of them, alone, in minutes, for cents. Hive's design centred on the hand-over (Gates 42–63) because, with earlier models and a real founder, questions under-delivered. In the wind tunnel, that premise is now false.
2. **Whatever Hive is for, it must at least ask as well as one agent does.** Gate 68 measures whether Hive's swarm with questions matches it, and whether the hand-over adds anything after.
3. **Where the hand-over may still earn its place:**
   - builds the owner cannot answer during (overnight);
   - owners whose answers drift. A concrete outcome is what the real founder decided on (Gate 38).
   - Both need the founder to test.

## Files

`prompts/` (owner answering brief, skimming brief, builder prompt, predictions).

`referee/`:
- `review66.py`, `owner_server.py`, `ask_owner.py`, `analyze.py`;
- both rule sets, published after scoring.

`results/g66a/`, `results/g66b/`:
- every question and answer (`owner_CC.jsonl`, `owner_CQ.jsonl`);
- Hive's sheets, cases, corrections and judge labels (`sheet.json`);
- probes, summaries, agents and run logs.
