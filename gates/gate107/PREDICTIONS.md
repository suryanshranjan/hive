# Gate 107: predictions (registered before launch, Nov 3 2026)

**Question.** Before a second founder tries it: does the whole product hold together for a fresh founder, end to end, on his phone? Today's pieces were each tested on their own (stand-ins). This is the first run of them together, with real Claude, real builds and real screenshots.

**Setup.**
- **The project:** a mock creator site (Gate 106's pages) with **no tests**, in its own git home, standing in for GitHub. It's fetched with `hive up --repo`'s fetch.
- **The founder:** simulated, on a fake Telegram. He taps the obvious yes and answers questions from a short policy, as a busy founder would.
- **Stand-ins:** his engineer's merge (a script merges the pull request's branch into main), and the hosting service (custom commands that copy the site to a preview folder or a live folder and print an address).

**The 14 steps:**
1. Hello
2. A policy document (company brain)
3. A business goal: plan, one yes, decisions, steps built, each shown. The first build writes the safety net, since the project has no tests
4. "Show me"
5. A picture: "make the header like this", before and after
6. A technical instruction
7. "Send me a link" (preview)
8. "Ship it"
9. The engineer merges
10. "Put it live"
11. "Undo that" (live goes back)
12. A customer complaint
13. "What's new?"
14. "Set my budget to $40 a month"

## Predictions

| # | Prediction | Fires if |
|---|---|---|
| E1 | It holds together | >= 12 of the 13 Hive steps (all but the engineer's merge) do the right thing the first time, judged against what each step should do (below) |
| E2 | Nothing raw reaches him | No traceback, raw error line or "something went wrong on my side" in anything Hive sends him |
| E3 | He never needs his computer | No step asks him to type a command, open a file or use his computer. The engineer's one-time host setup and his merge are not counted |
| E4 | The safety net works | The first build writes passing tests for the untested project, and every later delivery reports them passing |
| E5 | Affordable | <= $15 and <= 90 minutes in all |

**What "the right thing" means per step:**
- **1:** a greeting that says where things stand.
- **2:** facts kept, with a count.
- **3:** a plan in plain words, then each step shown, then "ship it" offered.
- **4:** screenshots.
- **5:** before and after screenshots.
- **6:** "Yes, let's do it", restated in his terms, then built.
- **7:** a preview address.
- **8:** sent to his engineer.
- **10:** live, with an address.
- **11:** live back to the version before.
- **12:** traced to a rule or a fault, in plain words.
- **13:** a brief naming what landed.
- **14:** the cap confirmed.

**What it changes.** Every step that fails is fixed before the second founder sees Hive. This gate is about readiness, not a claim.

**Confounds:**
- One run.
- A mock project with plain-to-see problems.
- A simulated founder.
- The host is a stand-in.
