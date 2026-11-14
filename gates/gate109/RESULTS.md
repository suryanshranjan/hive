# Gate 109: results (attempt 1, Nov 14-15 2026: interrupted, not scored)

**What happened.** Attempt 1 started on the owner's laptop, signed in to AWS (account …1696). It made the t3.small machine (`i-034654a7868a77193`, Mumbai), and the machine began setting itself up. Then Claude Code stopped the flight because **the laptop was low on memory**, not because of anything in the flight. The laptop was running the lab container, two test databases (Postgres and MySQL from Gate 108's checks) and this session. The flight stopped before the move, so nothing was moved to the machine.

**Predictions A1-A6: not scored.** The move, the restart in the cloud, the test deploy and its take-down never ran.

**The kill condition (nothing left billing): held.**
- The machine was deleted by Hive's own `hive cloud --stop`, run by hand.
- AWS was then checked directly: the instance `terminated`, its firewall rule and its key `NotFound`.
- It ran about 40 minutes, under $0.02.

**One finding, fixed.** Deleting a machine that was made but never moved to:
- **Before:** Hive said "Tell me where from: hive cloud pull --from user@host" and asked him to type DELETE to "lose that work". There was no work, and a founder would be stuck there.
- **Now:** if no move ever completed (no `~/.hive/cloud.json`), it says "Nothing was ever moved to it, so there is nothing to bring home" and deletes it.
- **Tested:** `tests/test_cloud.sh`, last check.

**Side effect, undone.** After the delete, Hive started a Telegram listener on the laptop, as it does for a founder coming home from the cloud. It was stopped, and the Telegram link copied over for the flight was removed. The laptop is as it was.

**Next attempt.** The same predictions and flight, with more memory free: the test databases stopped (done; 5.3 of 23.7 GB free), nothing else heavy running. Only on the owner's word.
