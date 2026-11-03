# Gate 105: results (flown Nov 3 2026, lab container on the user's laptop)

**Question.** Does a builder given the owner's picture ("make it like this") match the look better than one given his
words? (Predictions: `PREDICTIONS.md`, pushed before launch in `fcb7c89`.)

**Answer (established for these three targets, n = 1 a cell).** Yes.
- **Measured checks matched:** with the picture, **18 of 18**; with his words, **13 of 18**.
- **Blind judge:** preferred the picture on all three targets (10 vs 5, 9 vs 6, 9 vs 8).
- **The cost is the same:** $0.26 vs $0.25 a fix round, each under a minute.
- **Nothing broke:** every delivery passed all its tests and kept Sunny Shop's own words.

## The numbers

| Target | Starting page | P (picture) | W (words) | Judge: start / P / W | P cost, min | W cost, min |
|---|---|---|---|---|---|---|
| t1 flat teal, red full-width button | 0/6 | **6/6** | 3/6 | 3 / **10** / 5 | $0.26, 0.7 | $0.23, 0.6 |
| t2 soft purple, pill button, round card | 0/6 | **6/6** | 4/6 | 4 / **9** / 6 | $0.25, 0.6 | $0.27, 0.8 |
| t3 dark, yellow full-width button | 0/6 | **6/6** | 6/6 | 3 / **9** / 8 | $0.25, 0.6 | $0.25, 0.7 |
| **Total** | 0/18 | **18/18** | 13/18 | | mean $0.256 | mean $0.251 |

The describer wrote the owner's words at $0.14-0.15 a target. Those words cost nothing in a real conversation.

**Where the words slipped.** These are the slips founders make:
- **t1:** "a solid dark green bar" gave a forest-green header (distance 74 from the teal). "A box with a thin green border" gave rounded corners (12 px against square). The amount stayed the old green (distance 58).
- **t2:** "a big bold dark purple heading" gave 36 px. The reference's heading is small, 20 px. The judge also saw content centred where the reference is left-aligned.
- **t3:** the words caught all six checks. The judge still saw neutral grey-black where the reference is navy-tinted.

**With the picture, the builder read exact values:** #0f766e, #e11d48, 34 px, Georgia, #64748b. The builder's transcript shows it opened only the copied picture (`.hive/refs/ref_1.png`), the page and the test. It never opened the target's source.
- **Confound:** the targets use the Tailwind palette, which models recognise on sight. A screenshot of a real site will be noisier.

## Predictions scored

| # | Prediction | Result |
|---|---|---|
| V1 | P matches more checks in total, and P >= W on each target | **Held:** 18 vs 13; 6>3, 6>4, 6=6 |
| V2 | P >= 5/6 on at least 2 of 3 targets | **Held:** 6/6 on 3 of 3 |
| V3 | Judge P > W on at least 2 of 3, every result above the starting page | **Held:** 3 of 3; every result above the start (3-4) |
| V4 | All 6 pass 5/5 tests and keep his words, never the other brand's | **Held:** all passing (10-12 tests: builders added look tests); Sunny Shop, Invite a creator and ₹500 kept; no other brand's name |
| V5 | P's mean cost <= 1.5x W's | **Held:** 1.02x |

**Failures and faults found while flying:**
- **Product (fixed):** with Playwright installed but its browser missing, the camera raised a raw Playwright error instead of a plain reason. A clean home has no browser. `hive/screens.py` now says "the browser isn't installed (run: playwright install chromium)".
- **Lab:** cell t1P's screenshot failed for that reason. Its finished fix round was measured afterwards rather than flown again. The flight now resumes a finished round.

## What it changes in Hive

- **The picture path stays as shipped** (`d2c0dfc`). V1 held, so Jarvis does not also put the picture into words.
- **New:** when he asks for a change to a look in words only ("make the header a darker colour"), Jarvis adds: "If you have a screenshot of a page you like, send it next time: a picture lands closer than words." (`hive/assistant.py`, `LOOK_WORDS`; tested in `tests/test_visual.py`)

**Confounds.**
- n = 1 a cell.
- The describer, the builders and the judge are the same model family.
- The targets are simple one-page designs in a well-known palette.
- The judge saw the reference and one page at a time. It was never told the arm, but it could see that the results share the starting page's wording.

**Files:**
- `results/<t><arm>.json` (measured values, cost, minutes, the instruction given);
- `results/<t><arm>.png` (the delivered page, shot by `hive/screens.py`);
- `results/summary.json`.

The targets and their checks stay in `private/g105` on the lab.
