# Closing the gaps: from lab result to a founder's tool

Written Nov 2 2026, after Gate 84. The honest state, from the founder's side:
- Hive matches one strong asking agent on a toy project, with a simulated owner.
- It asks the owner 22–71 prompts per feature.
- Its results swing from 14 to 27 of 27 between runs.
- Its own model calls cost 6–9× the builders'.
- It has never met a real founder or a real product codebase.

Each gap below gets a test, Wright-brothers style: measure first, change one thing, register the prediction, and keep the failures. Wherever someone has already built the measuring stick, we use theirs.

## What others already learned (use it, don't relearn it)

| Source | What it found | What we take |
| --- | --- | --- |
| **Ambig-SWE** (Vijayvargiya et al., ICLR 2026; arXiv 2502.13069) | 500 SWE-bench Verified issues, rewritten underspecified, with a simulated user who answers from the full issue. Asking recovers about 80% of full-information performance. Models rarely ask unless prompted. Many detailed questions overwhelm users. | **The real-codebase benchmark for Gap 4**, and a published single-agent baseline to compare Hive with. Fewer, better questions (Gap 2). |
| **Ask or Assume?** (Edwards & Schuster, 2026; arXiv 2603.26233) | A separate intent agent that watches and forces a question when context is missing: Claude Sonnet 4.5 resolves 69.4% underspecified vs 70.8% fully specified, at 1.7× the cost. When the agent did not ask, it did as well as without help. | Hive's business-builder split is the same idea. Compare against its numbers, and ask only where needed. |
| **MAST** (Cemri et al., NeurIPS 2025; arXiv 2503.13657) | 1,642 multi-agent traces: 41–87% fail. The failures are system design (44%), inter-agent misalignment (32%) and verification (24%), not model limits. A task-objective verification step gave +15.6%. | **Label every Hive failure with MAST's 14 modes** instead of our own words. Gate 83's result-shape change is FM-1.1 (disobey task spec), and its fix, Gate 84, is the objective check MAST recommends. Duplicated work (Gates 78–82) is FM-1.3 and FM-1.5. |
| **τ-bench** (Yao et al., ICLR 2025; arXiv 2406.12045) | Agents that pass a task once often fail it on a retry. It measures pass^k, whether k independent tries all succeed. | **pass^k as Hive's reliability measure (Gap 1).** A founder judges by the bad run, not the average. |

## The gaps, in order

| # | Gap (founder's words) | Measure | Test | Needs |
| --- | --- | --- | --- | --- |
| 1 | "Same quality every time" | pass^1 and pass^5: a run succeeds at ≥ 24 of 27 hidden | Gate 85 baseline 0.80; after Gates 90, 93-95: **10 of 10 flights (Gates 95-96)** | done on Tiny Shop |
| 2 | "Under 10 minutes of my time" (now: median 33 prompts, 8-16 min, from 55) | prompts and words typed per feature, at no loss in pass^k | Batch every question into one sitting; replace the 19-rule sheet and 20 checks with ≤ 5 highest-stakes checks; compare with Gate 85 | Gate 85 |
| 3 | "My bill is the building" (Gate 97: 6.5x -> 1.0x; ~$0.97 a feature) | Hive's own spend ÷ builders' spend | Gate 85 shows which step spends it. Cheaper model for internal steps (untested; Gates 62–65 only tested builders), fewer calls | Gate 85 |
| 4 | "Works on my real codebase" | resolve rate on Ambig-SWE's underspecified issues, Hive vs one agent, against the published numbers | **Gate 86:** 10 Django issues via Ambig-SWE's GitHub release and a Docker-free harness: one builder 8 full / 7 summary, hive start 8 at 15x cost; the interview misfires on technical goals. Next: issues whose summaries lose what a builder cannot infer | Gates 94, 100: Hive matches one builder (8/10; 9/10 on a harder sample), 0 prompts; public summaries no longer hurt modern builders, so intent on real code needs the founder |
| 5 | "When I change my mind, the fix is cheap" | cost and correctness of a change after a rule flips | **Gate 92:** announced drift: memory safe (29/29). **Gate 101:** silent drift: memory 27-29 vs none 17-29; the contradiction check notices the change | done on Tiny Shop; open: an existing product with no memory |
| 6 | Real founder | his minutes, his corrections, whether his answers hold a day later | Gate 45 day 2: one real feature in his repo, terminal flow (Telegram stays untouched) | the founder |
| 7 | Know why it fails | MAST labels for every failed flight | Label Gates 76–85's failures with MAST's modes; fix the most common first | the flights |

## Rules for this phase

- Measure the shipped flow first (Gate 85). Every later change is compared with it, with at least 3–5 runs per arm. A single flight is never a result.
- A change ships only if pass^k does not drop.
- Real companies' names, rules and data never enter the repo. Use mock names.
