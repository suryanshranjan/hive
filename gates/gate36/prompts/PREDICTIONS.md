# Gate 36 predictions, registered before any case or verdict exists (Oct 28 2026)

**Question.** Across Gates 30 to 35 the founder answered concrete situations reliably (48 of 48), but reviewed lists of the builders' decisions poorly (Gate 35: marked 0 of 27). Hive now **interviews first**: from the feature description alone, it writes the situations where the owner's rules are likely to matter, asks him on his phone, and gives his answers to the builders as rules to encode as tests. **Does an interview Hive writes itself, before the build, carry the owner's surprising rules into the code?**

**Design: two independent question sets, so the test is fair.**
- **The hidden set (the referee).** The experimenter writes 12 situations on the feature, and the founder gives verdicts on Telegram. As before, a cold default probe (3 runs) and a blind judge label each case surprising, ordinary or unclear; the founder confirms the readings of free-text verdicts. At least 6 surprising are needed. These become the hidden tests. **Neither arm sees them.**
- **Hive's interview (the treatment).** `hive/interview.py` writes 12 situations from **the feature description and the company's spec only**, not from the hidden set and not from the interface. The founder answers them on his phone through Hive's real interview code, and his confirmed answers become the arm's rules.
- **Feature:** a fresh, unbuilt part of the roadmap: **launching, pausing, editing and cancelling a campaign**. It is a pure library with a fixed interface, given identically to both arms.
- **Arms, built at the same time from the same base:** 4 workers each, no questions during the build, assumptions recorded.
  - **N:** no owner input.
  - **I:** the same goal plus the founder's interview rules.
  - No review after the build in either arm, to isolate the interview.

| # | Prediction |
| --- | --- |
| S1 | **On surprising hidden cases, arm I beats arm N by ≥ 30 percentage points** |
| C2 | **Coverage:** ≥ 50% of the surprising hidden cases have a matching situation in Hive's interview (blind judge) |
| S2 | Ordinary cases ≥ 75% in both arms |
| S3 | Existing backend tests pass in both arms |
| S4 | The founder's interview takes under 6 minutes |

Kill: **arm I beats arm N by < 10 points on surprising cases.** If so, an interview Hive writes itself does not reach the owner's surprising rules, and interview-first fails on this evidence.

**Honest prior.** S1 about 55%; C2 about 55%. Hive's interview must guess where this owner differs without seeing the referee. Gate 33 showed a model predicts his answers poorly, but this only needs it to predict **which questions to ask**, not the answers.

**Cost.** About $6 at list price for both arms, plus about 6 minutes of the founder's time.

## Amendment, registered before the build (Oct 28 2026)

- **Hidden set (the referee).** The founder answered all 12 hidden situations on Telegram. The cold default probe was unanimous 12/12. The blind judge labelled **9 surprising, 2 ordinary, 1 unclear** (the unclear one is not scored).
- **Readings.** He was asked to confirm the experimenter's reading of 4 free-text surprising verdicts: **2 "Yes, exactly", 2 "Not quite".** The two not confirmed are not scored. That leaves **7 surprising and 2 ordinary hidden cases.** A private reference passes 9/9 (11/11 with the two dropped cases). The cases stay out of the container until scoring. One surprising case is 14 points, so S1 (≥ 30) needs at least 3 more surprising cases passing in I than in N.
- **Hive's interview was damaged by a tool failure, so S4 is already scored as failed.**
  - A tap on a stale button was dropped in silence, so the founder waited 1 h 42 min on a question he thought he had answered. The whole interview took 124 minutes against S4's limit of 6.
  - Two more bugs showed up in reading his free-text replies: a yes in his own words was stored as the rule itself, and a correction lost the situation it was about.
  - All three are fixed in the tool (`89472c9`), with tests.
- **Arm I's rules.** These come from the fixed reading logic, applied mechanically to the answers he actually gave, with no experimenter judgment:
  - 3 tapped answers;
  - 3 rules in his own words;
  - 3 corrections kept with their situation;
  - 2 replies that left the choice to the builders give no rule;
  - 1 confirmed reading was lost to the bug and is not used.
  That is **9 rules from 12 situations.** His wording stays private.
- **Arms.** Both arms are built at the same time from `hs1-base`, 4 workers each, assumptions recorded, no questions, no review. The tool now resumes a builder stopped by a usage limit. A builder that still ends on an API error voids that arm, which is then rerun.
