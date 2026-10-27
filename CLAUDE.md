# Working in the Hive repo

This repo is the shared brain of the Hive research project. It holds evidence and experiments on silent coding-agent swarms.

- Read `BRAIN.md` before doing anything. It says what is known, how sure we are, what is being tested, and what comes next.
- When you learn something, update `BRAIN.md` in the same commit as the evidence: the evidence log, the scorecard, the constants, the open questions and the changelog.
- Register predictions in the gate's `PREDICTIONS.md` before launching any swarm, and score them afterwards in its `RESULTS.md`, failures included.
- Never commit hidden test suites, or the private intent of a test that has not run yet. Regenerate hidden suites from the fixed seeds in `README.md`. A new intent experiment needs a new oracle, kept out of the repo until its run is scored.
- If you are a worker inside a swarm experiment, do not read this repo at all: work only in your own clone, as your prompt says.
- Write plainly: real numbers, labelled as established, model or conjecture.

## Session protocol (laptop, VM or phone)

- **Start:** read `BRAIN.md`, then `lab/QUEUE.md` ("Where we left off" and the ready cards).
- **"Continue" or "run the next experiment":** take the top ready card in `lab/QUEUE.md` and run its command. Lab scripts are documented in `lab/README.md`. If the card needs design first, write its config and `PREDICTIONS.md`, push them, then run.
- **Never launch** before the predictions are pushed. `lab/run_gate.py` checks this.
- **After a run:**
  - Write `gate<k>/RESULTS.md` (predictions scored, failures included).
  - Update `BRAIN.md` (evidence log, scorecard, constants, open questions, changelog) and `lab/QUEUE.md` ("Where we left off").
  - Commit and push in one go.
- **Before stopping for the day:** make sure "Where we left off" says exactly what is done and what is next, and push.
- **Real companies:** never commit a real company's name, rules or data. Use mock names in anything public.
