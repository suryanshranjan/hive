# Gate 55 results: the skimming owner, Oct 30 2026

**Question.** The code sheet took builders to 99.6–100% when the owner read every rule carefully (Gates 42, 44). The founder does not read that way: on day 1 of Gate 45 he marked none of 46 rules. How much is lost when the owner skims, and does Hive's conversational review, where Jarvis says how each part works, recover it?

**Answer.**
- **The owner's attention is the limit, and the conversational format did not rescue a skimmer.**

| Review of the same 83-rule code sheet | Wrong decisions repaired | Missing ones added | Hidden pass | Owner replies | Time |
| --- | --- | --- | --- | --- | --- |
| Careful owner, rule list (CC) | **19 of 19** | 5 of 5 | **100%** | 48 | 5.0 min |
| Skimming owner, rule list (CS) | 5 of 19 | 4 of 5 | 65.2% | 13 | 1.1 min |
| Skimming owner, Jarvis's conversation (CT) | 6 of 19 | 2 of 5 | 66.4% | 27 | 3.9 min |
| No owner (N0) | – | – | 36.0% | – | – |

- **Skimming still roughly doubled what the build got right**, from 36% to 65–66%. The careful owner made it perfect. The gap between the two (+33.6 points against the conversation, CI +19.6 to +48.8) is what attention is worth.
- **The conversation drew the skimmer out** (27 replies against 13), and his replies were real corrections: "Late fees need a 5-day grace period, a 500-cent minimum, and a cap of 20% of the invoice." But it repaired only one more decision. Each section's summary covers several rules in a few sentences. A skimmer accepts a summary that sounds right, and the wrong detail sits inside it.
- **Nothing was spoiled** in any review: no right rule became wrong.

## Setup

- **Rules:** a fresh independent rule-giver (Gate 39's brief): 10 functions, 25 declared decisions. Hidden: 250 tests (seed 55200000), never committed. Predictions pushed before the rules existed (`5ed5ccb`).
- **The owner's knowledge:** his policy as prose rules (written from the oracle by a documenter). He cannot run anything.
- **Stage 1:** N0 built. The describer wrote D from N0's code: 83 rules. Of the 25 declared decisions, D had 1 right, 19 wrong and 5 absent.
- **Three separate reviews of D:**
  - CC and CS used the terminal rule list (`interview.confirm_sheet`).
  - CT was Hive's phone review (`confirm_sheet` with a chat channel: sections, "why it matters", Jarvis's summary covering every rule, replies read in his own words), driven through a fake Telegram whose other end was the synthetic owner.
- **Owner briefs:** `prompts/owner_careful.md` and `prompts/owner_skim.md` ("You skim… you correct something only when it jumps out at you as clearly wrong").
- **Stage 2:** fresh builders from each reviewed sheet, 3 each.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| S1 | Careful list review repairs ≥ 80% | **Held:** 100% (19/19) |
| S2 | Skimming list review repairs ≤ 50% | **Held:** 26% (5/19) |
| S3 | The conversation repairs ≥ 15 points more for the skimmer | **Failed:** +5 points (6/19 vs 5/19) |
| S4 | CT ≥ CS + 5 hidden points | **Failed:** +1.2 (CI −24.0 to +22.8) |
| S5 | CC ≥ 95% hidden | **Held:** 100% |
| Model check | The skimming brief changed nothing (CS ≥ 80%) | **Did not fire:** the brief changed behaviour (13 replies against 48) |

## What it means

1. **The code sheet's value scales with the owner's attention.** A careful owner gets 100%; a skimmer gets about half the gain. That is the ceiling of every verification channel.
2. **The registered rule for S3's failure applies:** the next lever is fewer, sharper things to read. Of the 83 rules, 25 carried the owner's decisions; the rest described NULLs, text-as-number and other mechanics. Hypothesis for the next gate: a short sheet with only the business choices the code made lets a skimmer catch more.
3. **For Gate 45 (the founder, day 2):** expect his review to behave more like CS/CT than CC. Hive's best help is to show him less, not to say it more nicely.

## Limits

- A synthetic owner told to skim is a model of a busy person, not one.
- The describer here was the lab's (rules named by function), so Hive's paging grouped them as "Other rules (1–12)" rather than by business area. In the product the describer names the part of the product each rule is about, so the pages are by area. CT tested the conversation, not the area paging.
- One run per review; the hidden difference between CS and CT is noise-sized.

## Files

`prompts/` (owner briefs, judge, describer, predictions), `referee/` (`review55.py` with the chat-channel driver, analysis, unsealed oracle), `results/`:
- sheet D;
- each review's full transcript and resulting sheet;
- judge labels;
- probes, costs and run log.

Also `swarms/`, `logs/`.
