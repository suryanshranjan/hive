# Gate 116: predictions (registered before launch, Nov 15 2026)

**Question.** Does a picture still beat words when it is messy, the way founders really send them? BRAIN §8 item 6. Gate 105 used clean screenshots of clean designs: picture 18/18 measured checks, words 13/18. Its confound note said a real site's screenshot would be noisier. Nobody has tested a phone photo of a screen.

**The targets.** Three pages from a made-up brand, Kite Market (t4 teal and red, square; t5 purple and orange, a pill button, a round card; t6 dark and yellow, full-width).
- **Made by:** a private generator (`private/g116/make_targets.py`).
- **Checks:** measured from the reference pages themselves, so the targets are exact. t4 and t6 have 6 checks each; t5 has 7 (19 in all):
  - the header colour;
  - the heading's size and colour;
  - the amount's colour;
  - the button's colour;
  - the button's shape;
  - for t5, the card's round corners.
- **The starting page** (Sunny Shop's invite page) matches 1/6, 0/7 and 0/6.

**Four arms**, each through Hive's own fix round (`start.apply_ruling`, one builder, every test re-checked), as in Gate 105:

| Arm | What he sends |
|---|---|
| C | The clean phone screenshot (Gate 105's picture arm, replicated) |
| F | A phone photo of that page on a laptop screen: tilted about 4°, a bezel, warm indoor light (t5's lavender page looks beige), glare, blur, screen moiré, noise, JPEG quality 45 |
| S | A phone screenshot of the page inside a real-looking site. It has a status bar over the header and a green promo strip. It also has three other buttons in other colours (a blue Subscribe, a red Download the app, a black cookie Accept), and a cookie banner across the bottom |
| W | His words: Gate 105's describer, writing what a founder would type after seeing the page |

**The measurer.** It is Gate 105's, with one fix found while making the targets, so the results here are not comparable cell-for-cell with Gate 105's button checks. The button's colour and shape are now read from the button itself. Before, a `<p>` around a `<button>` was read as the page's colour, and as full width. The fix is in `gates/gate116/measure116.py`.

| # | Prediction | Kill if |
|---|---|---|
| V1 | C replicates Gate 105: ≥ 17 of 19 | C ≤ 14: Gate 105 does not replicate on new targets |
| V2 | F (photo) ≥ 14 of 19, and F ≥ W in total | F < W: a photo of a screen is worse than words. Then Hive asks for a screenshot when a photo of a screen arrives |
| V3 | S (busy) ≥ 16 of 19, and its button is the right one on 3 of 3 (never Subscribe, Download or Accept) | the wrong button copied on ≥ 2 of 3. Then Hive asks which part he means before building |
| V4 | W 11-15 of 19 (Gate 105: 13 of 18) | — |
| V5 | All 12 deliveries pass all tests, keep Sunny Shop's words, and carry no Kite Market name or ₹250 | any delivery breaks a test or takes the other brand's words |
| V6 | Cost: F and S each ≤ 1.5× C's mean | > 2× |

**Product decision.** If V2 and V3 hold, the picture path stays as shipped, and Jarvis's "send a screenshot" hint also says a photo of a screen is fine. If either kill fires, the fix named in the table is built and tested before the gate is closed.

**n = 1 a cell** (12 cells). Builder, describer and model family are the same as Gate 105's. The real phone photos the owner takes are still untested: these photos are simulated from a clean render.

**Flight:** `python private/g116/make_targets.py`, then `python gates/gate116/flight116.py`. **Cost:** about $3-5.
