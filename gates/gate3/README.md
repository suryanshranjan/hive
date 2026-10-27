# Gate 3

Three steps, each answering an open question from Gate 2. Results and scored predictions are in `RESULTS.md`.

1. **Protocol v2** (done). Claims name test categories, and landings are guarded. `tools/claim.py` and `tools/land.py` are tested against overlap, a simultaneous race, a regression and a duplicate definition.
2. **Scale** (done). The Gate 2 project with protocol v2 at 12 workers and at 8 (the 24-worker swarm was capped at 8). Both pass all 2,960 hidden tests. The finish time is set by the last large task claimed.
3. **Intent bandwidth** (done). Three swarms of 3 workers added 20 business functions whose rules were invented for this test. They differed only in how many questions they could put to a product owner: 0, 30, or unlimited. Hidden correctness was 58%, 87% and 98%.

The intent test was first started twice and stopped about 3 minutes in each time: once by a usage limit, once by the user. Those attempts don't count. Their data is in `aborted_intent_runs/`. The scored run started from clean repos and fresh question budgets.

## Files

| Path | Contents |
| --- | --- |
| `tools/` | `claim.py`, `land.py`, `ask_template.py` (the question client, rendered per swarm) |
| `referee/oracle.py` | The private intent: the 20 invented rules, registered as SQLite functions (sealed until the intent test had run) |
| `referee/gen3.py` | Generates the visible examples (2 per function) and the hidden suite (25 per function, seed 900000) |
| `referee/ask_server.py` | The product owner: one SELECT of up to 3 values per question, with a budget |
| `referee/probe.py` | Scores a final engine call by call against the oracle, marking each call as happy-path or edge case |
| `prompts/` | Exact worker prompts for steps 2 and 3, and the predictions registered before launch |
| `seed_scale.bundle`, `seed_intent.bundle` | Starting repos for steps 2 and 3 |
| `swarms/` | Full histories: F8, F12, Q0, Q30, Qinf |
| `logs/` | Every worker's CLAIM, LAND, CONFLICT and BLOCKED events |
| `results/` | Tokens per worker; per-commit replays; call-by-call probes; every question and answer (`asks_Q30.log`, `asks_Qinf.log`) |

Regenerate the hidden suite with `python3 referee/gen3.py hidden hidden3 900000`. It is never committed.
