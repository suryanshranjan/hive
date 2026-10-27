# Working in the Hive repo

This repo is the shared brain of the Hive research project. It holds evidence and experiments on silent coding-agent swarms.

- Read `BRAIN.md` before doing anything. It says what is known, how sure we are, what is being tested, and what comes next.
- When you learn something, update `BRAIN.md` in the same commit as the evidence: the evidence log, the scorecard, the constants, the open questions and the changelog.
- Register predictions in the gate's `PREDICTIONS.md` before launching any swarm, and score them afterwards in its `RESULTS.md`, failures included.
- Never commit hidden test suites, or the private intent of a test that has not run yet. Regenerate hidden suites from the fixed seeds in `README.md`. A new intent experiment needs a new oracle, kept out of the repo until its run is scored.
- If you are a worker inside a swarm experiment, do not read this repo at all: work only in your own clone, as your prompt says.
- Write plainly: real numbers, labelled as established, model or conjecture.
