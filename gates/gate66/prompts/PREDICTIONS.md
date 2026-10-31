# Gate 66 predictions: Hive against a Claude Code agent, with the same owner

Registered Oct 31 2026, before the run. Asked for by the user, travelling for two days: "test something … that will genuinely impact hive … making it the best tool to exist". Synthetic owner only; Gate 45 and the founder's Telegram are untouched.

## Why this test

Every gate so far compared one version of Hive against another, or against no owner at all. None compared Hive with what an owner can already do today: open Claude Code, describe the feature, and answer the agent's questions as it builds. If Hive does not beat that with the same owner, nothing else about it matters. If it does, by how much, and at what cost in his attention?

## Setup

- **Rules:** two fresh rule sets, each from an independent rule-giver (Gate 58's brief): g66a (seeds 66100, 66200000) and g66b (seeds 66300, 66400000). Each has 10 functions and 25 declared decisions; the hidden suite is never committed.
- **The owner:** one person model for every arm. A headless Claude holds the owner's policy as prose rules (R, from Gate 55's documenter).
  - Answering a question (`prompts/owner_qa.md`): he types one or two short sentences from his policy, as on a phone between meetings.
  - Reviewing (Gates 55–65's skimming brief): he reads quickly and corrects only what jumps out.
- **Arms:**

| Arm | What it is |
| --- | --- |
| **CC** | One Claude Code builder (Sonnet, the default). It may ask the owner in plain words at any time (`referee/ask_owner.py` → `referee/owner_server.py`): Claude Code as an owner uses it today |
| **CQ** | The same, told to ask the owner about every business decision the spec leaves open before building each function: the best-practice prompt |
| **N0** | Hive's first build: 3 builders, no owner |
| **HV** | Hive's hand-over as shipped after Gate 63: the code sheet of N0's build as a rule list, then spot checks of every function (untouched ones first), each correction applied alone and re-shown; then 3 fresh builders from the corrected sheet |

- **Builds:** CC, CQ and N0 build in stage 1, together; HV in stage 2. The judge labels D, SL, HV and R.
- **Measures:**
  - hidden pass;
  - the owner's load: questions or replies, and characters read;
  - builder and Hive-side cost (describer, spotter). Synthetic-owner model calls are left out.
- Driver `referee/review66.py`, analysis `referee/analyze.py`, both committed now. `lab/experiments/g66a_bakeoff.json` and `g66b_bakeoff.json`.

## Predictions (means over the two runs)

| # | Prediction | Odds |
| --- | --- | --- |
| B1 | HV hidden ≥ CC + 10 points | 60% |
| B2 | HV hidden ≥ CQ + 5 points | 45% |
| B3 | CQ asks ≥ 15 questions per run | 60% |
| B4 | CC asks ≤ 5 questions per run (builders rarely ask unprompted) | 55% |
| B5 | HV's owner reads ≥ 2× the characters CQ's owner reads | 60% |

## Decision rules

- **Headline:** B1 and B2 hold, so Hive beats a Claude Code agent with the same owner (wind tunnel, two rule sets).
- **If CQ ≥ HV:** asking first matches Hive's hand-over. The next gate tests the two combined (questions first, then the hand-over), and Hive's interview is re-examined.
- Either way the owner's load is reported beside the score. A win that costs him 10× the reading is not a win for a skimmer.

## Limits

- A synthetic owner, so answers are as consistent as his policy. A real founder's answers drift (Gates 36–38), which may favour the hand-over (he decides when he sees outcomes).
- One run per arm per rule set; about $50.
