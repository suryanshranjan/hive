# Gate 34 predictions, registered before the cases exist (Oct 28 2026)

**Question.** Gate 31 showed that scanning every decision lets the owner find his surprising rules (8 of 9), but the answering step lost them: he kept all 22 he had marked. The answering step is now fixed:
- a marked decision asks "What would you do instead?", with keeping as the last, separate button;
- three quick keeps of marked decisions prompt a check.

**With both halves of the review working, does the owner's input carry his surprising rules into the code?**

**Design.** The same as Gates 30 and 31 (their amendments apply), on a fresh feature: **plans and payments** (plan upgrades and downgrades, failed payments, creator payouts, refunds, tips, chargebacks). Gate 32 was not run because selection and invitations gave only 5 surprising cases; Gates 31 and 33 suggest the founder differs most where the business is its own, as with plans and money.
- 12 situations from the experimenter, with the founder's verdicts on Telegram.
- A cold default probe (3 runs) and a blind judge label the cases; at least 6 surprising are needed.
- The founder confirms the readings of his free-text verdicts.
- One shared build: arm N is the build with no owner; arm R is the same build after his phone review (scan, mark, his way first, suggestions off) and one fix round.

| # | Prediction |
| --- | --- |
| S1 | **On surprising cases, R beats N by ≥ 30 percentage points** |
| C1 | He marks a matching decision for ≥ 80% of the surprising rules recorded |
| A1 | **Of the decisions he marks that match a surprising rule, he changes ≥ 60%** (Gate 31: 0%) |
| S2 | Ordinary cases ≥ 75% in both arms |
| S3 | Existing backend tests pass in both arms |
| S4 | Review under 15 minutes |
| S5 | No secret-like file; no breaking commit left broken |

Kill: **R beats N by < 10 points on surprising cases.**

**Honest prior.** S1 about 50%. A1 about 65%. A change must also be built right: the fix round has to turn his words into the tested behaviour.

**Cost.** About $7 at list price, plus about 15 minutes of the founder's time on Telegram.

## Amendment before any verdict (Oct 28 2026): a stand-in owner

At the founder's request, **the founder model from Gate 33 plays the owner throughout**: it gives the verdicts, confirms the readings and does the phone review, through a simulated chat that drives the same review code. The founder gave no verdict for this gate.

- **What this measures:** the mechanism. Does the fixed review (scan and mark, then "what would you do instead?") carry an owner's divergent rules into the code? Here "surprising" means the stand-in's verdict differs from the cold default.
- **What it cannot measure:** real owners. Gate 33 found the model matches only 35% of the founder's surprising rules, and it does not tire or skim like a person on a phone (Gate 31). Results here count for the tool, not as evidence about founders.
- Predictions and the kill condition are unchanged, now about the stand-in owner. The 6-surprising minimum still applies.
