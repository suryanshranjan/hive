# Gate 109: predictions (registered before launch, Nov 14 2026)

**Question.** Do the cloud paths work on real AWS? Each was unit-tested, never flown:
- "I'm sleepy" with a build running: the work is handed over, Hive moves to a new cloud machine, and the cloud copy restarts the build;
- a test deploy of static pages at a private link, then "take it down";
- deleting the machine, which brings the work home.

**Setup:**
- **The machine:** one **t3.small** (2 GB, about $0.022 an hour) on the owner's AWS account, Mumbai, made by `hive cloud`'s own code. The owner asked for t3.small, smaller than the default t3.large.
- **The project:** Dabba Days (Gate 108's company), from the laptop.
- **The running build:** a stand-in process with a real, small goal: "On the plans page, add one line under the heading: 'Not sure? Try a week of lunches for ₹500.' Add a test for it."
- **His side on the laptop:** a fake Telegram drives "I'm sleepy" and taps the cloud.
- **His side in the cloud:** the cloud copy talks to the owner's real Telegram, so he gets its messages on his phone.

**The steps:**
1. The owner says "I'm sleepy, shutting my laptop" while the build runs.
2. He taps "Move to the cloud". Hive renews nothing (AWS is signed in), makes the machine, moves, and stops the build on the laptop.
3. The cloud copy starts listening, picks up the handed-over work, and builds it there.
4. The flight waits for the cloud build to finish (up to 25 minutes).
5. A test deploy of the project's pages on the same machine, at a private link. The laptop fetches it.
6. "Take it down".
7. Deleting the machine (`hive cloud --stop`): every branch comes home, then the machine, its firewall rule and its key are deleted.

## Predictions

| # | Prediction | Fires if |
|---|---|---|
| A1 | The move works | Machine made and Hive moved in ≤ 12 minutes; the owner is told he can shut his computer; the laptop's stand-in build is stopped only after the move |
| A2 | The work restarts in the cloud | The cloud copy announces it is picking up the work (its message reaches his Telegram), and a build with the handed-over goal finishes there with every test passing |
| A3 | The test page works | The private link answers 200 from the laptop with the project's home page, and the address has a secret part of ≥ 16 characters |
| A4 | "Take it down" works | Afterwards the link no longer answers, and port 8080 is closed on the machine's firewall |
| A5 | Nothing is lost, nothing is left | The cloud build's branch is on the laptop after the delete; the instance is terminated, and its firewall rule and key are gone (checked against AWS) |
| A6 | Affordable | ≤ $1 of AWS (machine hours) plus builders, ≤ 60 minutes in all |

**Kill.** If the machine is not deleted at the end, or anything is still billing, the gate fails whatever else held. The flight checks AWS itself and deletes by hand if needed.

**Confounds:**
- One run.
- The running build is a stand-in on the laptop; the real build is the one restarted in the cloud.
- A 2 GB machine may be too small for a builder. That is a finding, not a fault of the flight.
