# Gate 116: results (flown Nov 15 2026, the owner's Windows laptop, no container)

**Question.** Does a picture still beat words when it is messy, the way founders really send them? (Predictions: `PREDICTIONS.md`, pushed before launch in `7a2ce54`.)

**Answer (established for these three targets, n = 1 a cell).** Yes. A phone photo of a screen and a busy real-site screenshot each landed almost as close as a clean screenshot, and well ahead of words:

| Arm | What he sent | Checks matched | Mean cost | Mean minutes |
|---|---|---|---|---|
| C | Clean phone screenshot | **19 of 19** | $0.42 | 1.0 |
| F | Phone photo of the page on a laptop screen | **17 of 19** | $0.43 | 1.0 |
| S | Busy real-site screenshot | **18 of 19** | $0.47 | 1.1 |
| W | His words | **11 of 19** | $0.46 | 1.2 |

## By target

| Target | Start | C | F | S | W | Misses |
|---|---|---|---|---|---|---|
| t4: teal and red, square, full-width | 1/6 | 6/6 | 5/6 | 6/6 | 4/6 | F: heading size. W: header colour, heading size |
| t5: purple and orange, pill, round card | 0/7 | 7/7 | 7/7 | 7/7 | 4/7 | W: heading colour, amount colour, pill shape |
| t6: dark and yellow, full-width | 0/6 | 6/6 | 5/6 | 5/6 | 3/6 | F, S: heading size. W: header colour, heading size, amount colour |

**What the mess cost.** All 3 misses on pictures were the heading's size, which the photo's tilt and the busy page's bigger, wider screenshot make harder to read in pixels. Every colour held, even under the photo's warm cast, which made t5's lavender page look beige. On S, the builder copied the right button every time: never the blue Subscribe, the red Download the app or the black cookie Accept.

**Where the words slipped (as in Gate 105).** The words were faithful, but they are too coarse to land:
- **t4:** "a solid dark green bar" gave a forest green (distance 74 from the teal), and "a big bold heading" gave 34 px for 24.
- **t5:** "a big purple heading" gave a violet (distance 50), the amount "in blue" gave a royal blue (67 from the sky blue), and "one rounded bright orange button" gave 10 px corners, not a pill.
- **t6:** "a blue strip at the top" gave a bright blue (81 from the navy), and the amount "in bright green" was off by 58.

## Predictions scored

| # | Prediction | Result |
|---|---|---|
| V1 | C ≥ 17 of 19 (Gate 105 replicates) | **Held:** 19 of 19 |
| V2 | F ≥ 14 of 19, and F ≥ W | **Held:** 17 vs 11 |
| V3 | S ≥ 16 of 19, the right button on 3 of 3 | **Held:** 18; the button's colour matched on 3 of 3 |
| V4 | W 11-15 of 19 | **Held:** 11, at the bottom of the range |
| V5 | All 12 pass all tests, keep Sunny Shop's words, none of Kite Market's | **Held:** 6-13 tests each, all passing (builders added look tests); words kept in 12/12; no Kite Market name or ₹250 |
| V6 | F and S cost ≤ 1.5× C | **Held:** 1.03× and 1.13× |

**Faults found while flying:**
- **Lab:** Gate 105's measurer read the button's colour and width from the box around it. A `<p>` around a `<button>` read as the page's colour and as full width, so a starting page would have passed "full-width button". This was fixed before launch in `measure116.py`, so Gate 105's button checks are not comparable cell-for-cell with these. Gate 105's code is unchanged.
- **Lab:** the first launch failed because the shell wrote the log before the results folder existed. Relaunched; no cell had run.

## What it changes in Hive

- **The picture path stays as shipped.** Nothing in the mess needs a new step: no asking for a screenshot instead of a photo (V2 held), and no asking which part he means (V3 held).
- **Jarvis's hint now says a photo of the screen works too.** It appears when he describes a look in words. `hive/assistant.py`; `tests/test_visual.py`.

**Confounds.**
- n = 1 a cell.
- The photos are simulated from a clean render, not taken with a phone camera: real glare, focus and screen moiré vary more. The owner's own phone photos are still untested.
- The busy page's clutter is mine. A real site has more layers: overlays, ads, sticky video.
- The builder, the describer and the measurer's targets are from the same model family as in Gate 105.

**Files:**
- `results/<t><arm>.json` (score, measured values, cost, minutes, tests);
- `results/<t><arm>.png` (the delivered page);
- `results/run.log`.

The private inputs (`private/g116/`: the generator, the targets and their pictures) are made by `make_targets.py`. They hold no real company, and can be published on request.
