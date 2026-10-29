# Gate 54, first launch: stopped on a product fault (and a harness gap), Oct 30 2026

The law put 3 builders on the three-part job, as predicted. During the build, builder w1 asked the owner a live
question ("Priya ... asks for a refund because it was the wrong size, which is none of your usual reasons"). Hive's
question loop (`owner.serve`) reads the keyboard directly, and in this flight the keyboard input was closed (the
synthetic owner answered only the prompts that go through `start._ask`). On a closed input `readline()` returns an
empty string, which the loop took for "press Enter to come back later": it showed the same question again every 2
seconds, **173 times**, while the builder waited up to 30 minutes for an answer. The flight was stopped after about
9 minutes; nothing from it is scored.

- **Product fix** (`hive/owner.py`): a closed input is told apart from an empty line. Hive then says once that no one
  can answer, and every waiting or later question is answered "decide as the goal most likely intends, and record your
  choice with `hive assume`", so builders never wait on a keyboard no one is at. Test: `tests/test_owner.sh`.
- **Harness fix** (`gates/gate52/referee/flight.py`): the synthetic owner now also answers anything that reads the
  keyboard directly (live questions, the assumption review).
The flight then reran from scratch with the same predictions.
