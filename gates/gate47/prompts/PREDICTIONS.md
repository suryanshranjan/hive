# Gate 47 predictions: Claude and Codex in one swarm

Registered Oct 29 2026, before any team runs. Asked for by the user: "make the codex and claude swarms coordinate with each other", and test it. It also runs the Codex lead that Gate 46 could not (Codex was not installed there).

## Why this test

Hive's builders coordinate only through git: a claim file per task, and a guard that lets in nothing that breaks a passing test. Nothing in that protocol is specific to Claude, so in principle any agent that can run shell commands can join. Hive now takes a mix: `hive start --agent claude,codex` gives the builders each agent in turn.

What could go wrong with a mix:
- the two agents read the protocol differently, for example Codex skipping claims or leaving locks behind;
- they build the shared foundations in clashing styles, so one agent's landings break the other's work;
- one agent does most of the work while the other idles, so the mix is just a slower single-agent swarm.

Gate 46's deep project is the hardest test we have for this. It starts from a 221-line skeleton, so everyone depends on foundations nobody has built yet.

## Setup

- **Project:** Gate 46's deep project (`gates/gate46/seed_deep.bundle`): 1,340 visible tests in 127 categories, 9 pass at the start. Protocol v2 tools (claims, the guard). Gate 46's prompts, unchanged. Hidden suite: gen2.py, seed 5000000, generated privately, never committed; categories where this SQLite disagrees with the stored answers are left out (Gate 43's rule).
- **Machine:** the lab container (Docker on the user's laptop; 24 logical CPUs). Claude Code builders on the user's Claude login; Codex 0.160.1 builders on the user's Codex login. Each team runs alone, one after another.
- **Teams, in this order:**

| Team | Builders | Lead |
| --- | --- | --- |
| M1 | 4: w1, w3 Claude; w2, w4 Codex | none |
| C | 4 Claude | none |
| X | 4 Codex | none |
| LX | 6 Claude | Codex keeps `BRAIN.md` (Gate 46's lead prompt) |
| LC | 6 Claude | Claude keeps `BRAIN.md` (Gate 46's H, on this machine) |
| M2 | 4 mixed, as M1 | none |

- **Measured** (`referee/analyze.py`, committed now):
  - time to 95% of visible tests (t95) and the last landing;
  - landings per agent;
  - breaks of main per agent (a landing after which 20 or more visible tests fail that passed before);
  - leftover locks;
  - hidden pass;
  - Claude's cost in dollars, Codex's in tokens (it runs on a ChatGPT plan, so it has no per-run price).
- **Driver:** `referee/run47.py`.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| P1 | Both mixed teams reach 95% of the visible tests within 45 minutes | 80% |
| P2 | Both mixed teams break main at most once each | 70% |
| P3 | In both mixed teams, each agent lands at least 25% of the work | 65% |
| P4 | Mixing costs no speed: mean t95 of M ≤ 1.15 × the mean of C and X | 60% |
| P5 | Codex builders are slower: t95 of X ≥ 1.2 × C | 50% |
| P6 | All six teams' hidden pass within 3 points | 70% |
| P7 | The Codex lead's plan is on main within 6 minutes | 60% |
| P8 | The lead's agent does not matter: t95 of LX within 20% of LC | 65% |

## Decision rules

- **Ship:** mixed swarms become a supported, documented option (`--agent claude,codex`) if P1 and P2 hold.
- **Kill:** an M team does not reach 95%, or the M teams break main more than C and X together. Then Hive warns against mixing agents and says why.
- **The Codex lead** (P7, P8) only informs: Hive stays flat after Gate 46 whichever agent leads.

## Cost and limits

- About $15 to $25 of Claude: 4 + 2 + 2 + 6 + 6 Claude builders and one Claude lead. Codex uses the user's plan; if it hits its usage limit, that team is reported as cut short, not scored as a failure of mixing.
- One run per team except M (two). One project. A different machine from Gate 46 (24 CPUs, not 2), so its numbers are compared only with LC, never with Gate 46's directly.
