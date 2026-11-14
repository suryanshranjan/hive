# Gate 111: results (Nov 15 2026)

**Question.** Does the founder's own choice of always-on machine work on real AWS? Two attempts. Attempt 2, after two fixes, held on every prediction. The kill held in both: nothing is left billing, checked against AWS.

| # | Prediction | Attempt 1 | Attempt 2 |
|---|---|---|---|
| W1 | The choice, at real prices | **Held:** "Small, about $23 a month… Bigger, about $72 a month… Or keep me on this computer, free" | **Held** |
| W2 | His size is what gets made (≤ 12 min) | **Held, just:** AWS reports t3.small; remembered as t3.small. The move took 11.2 min, 8 of them one stuck ssh call (below) | **Held:** t3.small, 2.3 min |
| W3 | Always on | **Held:** `hive listen` running on the machine | **Held** |
| W4 | Off on his word | **Failed:** "A build is still running there, so I've kept the machine". The flight's safety net then deleted it by hand, and its firewall rule and key were deleted afterwards | **Held:** "✅ Deleted. Nothing is left running."; AWS shows it terminated, firewall rule and key gone |
| W5 | Cheap (≤ $0.05) | **Held:** $0.005 | **Held:** $0.002 |
| Kill | Anything left billing | Held, after the hand clean-up | Held |

## What attempt 1 found, fixed

**1. One ssh call hung for 8 minutes on a machine that was ready.**
- **The bug:** ssh had no connection timeout. A call made while the machine was still booting waited until it was killed by hand.
- **The fix:** every ssh and scp call now gives up after 20 seconds, and the wait tries again (`hive/cloud.py`).
- **Attempt 2:** the move took 2.3 minutes.

**2. Old work was replayed in the cloud and blocked the delete.**
- **The bug:** Gate 109's "I'm sleepy" hand-over (`~/.hive/resume.json`) stayed on the laptop after the move. The next machine picked that work up and started building it again. So "delete the cloud machine" correctly refused to stop a running build, but the build should never have been there.
- **The fix:** the laptop's copy is cleared once the move succeeds, and the cloud copy ignores a hand-over older than 12 hours.
- **Tested** in `tests/test_away.py`.

## Confounds
- One run of each attempt.
- The bigger size is only unit-tested.
- His side on the laptop was a fake Telegram. The cloud copy used his real Telegram.
