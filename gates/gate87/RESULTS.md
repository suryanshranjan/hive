# Gate 87 results: Hive's own reading steps on a small model (Gap 3), Nov 2 2026

**Question.** Gate 85: Hive's own model spend was 4.8–8.6× the builders'. Does running its reading steps on Claude Haiku 5.5 cut that without losing quality?

**Answer.**
- **The spend fell to about a tenth:** mean $0.39 per flight against $3.70, 0.11×.
- **Reliability did not drop:** pass^1 0.80, the same as Gate 85.
- **But median hidden fell from 27 to 25** (H3 failed, so the claim did not fire), and the low scores have a cause that is not the model.
- **That cause is a product fault, found by reading the failures:**
  - In live3 and live4, the delivered `sales_summary` still had code marked `PLACEHOLDER (w3 / owner decision)`.
  - The same fault was in Gate 85's live5 (24 of 27), on the default model.
  - So the drop in median hidden cannot be pinned on Haiku. The fault comes first.

| Flights | Hidden | Prompts | Hive's own | Builders | pass^1 |
| --- | --- | --- | --- | --- | --- |
| Gate 85 (default model) | 27, 27, 27, 20, 24 | 59, 55, 67, 53, 33 | mean **$3.70** | $0.63 | 0.80 |
| Gate 87 (Haiku 5.5) | 27, 27, 21, 25, 25 | 93, 52, 24, 66, 24 | mean **$0.39** | $0.48 | 0.80 |

## The fault: the business-builder split meets derived areas

- **With 3 builders, Gate 74's split engages.** Its "build the rest" builders are told: "if something you build needs one of his decisions, leave a clear placeholder and let w3 fill it."
- **Since Gate 80, every part of the goal is a derived area.** On Tiny Shop all three parts turn on the owner's decisions, and each builder claims one (Gate 81: an even share).
  - So a "rest" builder claims the summary, builds its machinery with placeholders, and lands it.
  - The landed area is then protected (Gate 82: a landed area needs `--again`).
- **The business builder (w3) builds its own part, sees every area landed, and stops.** Nobody fills the placeholders.
- **Seen in Gate 85 live5 (loyalty and summary) and Gate 87 live3 and live4 (summary).** In live4 the owner even corrected the summary rule in the review. The change round got the right rule ("only card orders count toward revenue"), but the delivered `report.py` still carries the placeholder, and the hidden test reads 3,650 rupees of revenue where the policy gives 1,550.
- **MAST:** FM-1.2 (disobey role specification: the parts the business builder owns were claimed and landed by others), and FM-2.4 (information withholding: the placeholders were left for a builder that never learned of them).
- This is a fault of the rules Gates 74, 80, 81 and 82 each added, meeting for the first time. Each gate tested its rule alone.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| H1 | Hive's own spend ≤ 0.4× Gate 85's | **Held:** 0.11× |
| H2 | pass^1 ≥ 0.8 | **Held:** 0.80 |
| H3 | Median hidden ≥ 26 | **Failed:** 25 (placeholders left unfilled in 2 flights) |
| H4 | Median prompts ≤ 1.2× Gate 85's | **Held:** 52 vs 55 |
| Claim | H1, H2 and H3 | **Did not fire** |

## Observed (not predicted)

- **Haiku's re-shows looped more.** live1 had 21 "Right now?" re-shows (93 prompts) as the owner repeated a correction that the re-shown case did not reflect.
  - The interview and review prompts overall were not higher (median 52).
- **Flights took longer** (9–27 minutes, against 7–15).

## What changes

1. **Fix the placeholder fault first** (Gate 90, registered next):
   - the business builder may claim any landed area without `--again`, and beyond an even share;
   - it is told to fill every placeholder its teammates left;
   - five flights on the default model, compared with Gate 85.
2. **Then retest the small model on the fixed flow** (Gate 91), against Gate 90. Until then, Hive's own steps stay on the default model.

## Files

`prompts/`, `referee/` (`flight87.py`, `analyze.py`).

`results/live1` to `results/live5`:
- the terminal, prompts and replies;
- scores and spend by step;
- the run log.
