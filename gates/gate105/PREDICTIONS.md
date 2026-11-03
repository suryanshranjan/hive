# Gate 105: predictions (registered before launch, Nov 3 2026)

**Question.** The visual loop (commit `d2c0dfc`) lets the owner send a picture from his phone: "make it like this".
Does a builder given his picture match the look better than a builder given his words?

**Setup.**
- The starting build is Sunny Shop's invite page (one `index.html`, 5 tests).
- **Targets:** 3 pages from other mock brands, each rendered at phone size as the picture he would send:
  - t1: flat teal with a full-width red button;
  - t2: soft purple with a pill button and round card;
  - t3: dark with a yellow full-width button.
- **Arms:** one fix round each, through Hive's own `start.apply_ruling`. Every arm has one builder (Claude) and every test is re-checked.
  - **P:** "Make the invite page look like this." plus the picture, carried into the code by `hive/refs.py`.
  - **W:** "Make the invite page look like this: <words>". The words come from a separate model that looked at the picture and wrote what a founder would type: plain words, no colour codes or pixel numbers.
- **Scoring:**
  - **Measured:** the delivered page in a browser, against 6 private checks per target. Colours must be within 45 RGB, sizes within 3 px, plus corners and button shape and width.
  - **Calibration:** each target scores 6/6 against itself. The starting page scores 0/6 on all three.
  - **Judged:** a blind model sees the reference and one page and scores the look 0-10. It is never told the arm.
- **Sample:** n = 1 flight per cell (6 flights). This is a first look, not a precise estimate.

## Predictions

| # | Prediction | Fires if |
|---|---|---|
| V1 | The picture beats words, measured | P matches more checks than W in total over the 3 targets, and P >= W on each target |
| V2 | The picture gets there | P matches >= 5 of 6 checks on at least 2 of 3 targets |
| V3 | The blind judge agrees | P's judge score > W's on at least 2 of 3 targets, and every result scores above the starting page |
| V4 | Nothing breaks | all 6 deliveries pass 5/5 tests and keep his own words (Sunny Shop, Invite a creator, ₹500), never the other brand's name |
| V5 | A picture costs no more | P's mean builder cost <= 1.5x W's |

**What ships either way.** The picture path is already in Hive.
- **If V1 fails** (words match as well or better), Jarvis will also put the picture into words for the builders. The builders then get both the picture and a description.
- **If V4 fails** on P (the builder copied the other brand's text), the instruction carried with a picture will say: "match its look, keep your own words".

**Confounds stated now:**
- one flight per cell;
- the describer and the builders are the same model family;
- the targets are simple one-page designs.
