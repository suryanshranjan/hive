# The Hive lab: run experiments from any Claude Code session

Everything needed to rerun a gate, or run the next one, lives here. Any Claude Code session, on a laptop, a VM, or the Claude app on your phone, can pick up the next experiment from `lab/QUEUE.md` and push the results.

## From your phone or any new session

Open a Claude Code session on this repository and say:

> Continue Hive: run the next ready experiment in lab/QUEUE.md.

The session reads `CLAUDE.md`, `BRAIN.md` and `lab/QUEUE.md`, runs the top ready card, writes the results, updates the brain and the queue, and pushes. The next day, say the same thing again.

## Setup on a laptop or VM (once)

- Python 3.11+ with `sqlite3`, git, Node, and Claude Code installed and logged in (`claude` on the PATH).
- Workers run shell commands, so use a container or a throwaway VM, not your main machine.
- More cores means more honest timings. On small machines pass `--max-parallel 3`.

## The pieces

| Script | What it does |
| --- | --- |
| `run_gate.py <config>` | The whole intent experiment in one command: checks the predictions are pushed, gets fresh rules from an independent rule-giver, checks them, builds tests, assigns allowances, starts product owners, builds and launches the swarms, scores everything, and writes `runs/<name>/summary.md` |
| `intent.py` | Builds visible and hidden tests from an oracle (it reproduces Gates 5 and 6 exactly), and scores an engine call by call |
| `new_intent_gate.py` | Builds a starting repo (the finished SQL engine plus the new spec and examples) and a hidden suite from an oracle |
| `ask_server.py` | The product owner: answers from the oracle, with a team budget or per-function allowances, and logs every question |
| `make_swarm.py` | One bare repo per team, one clone per worker, one rendered prompt per worker |
| `launch.py` | Runs each worker as a separate headless `claude -p` process, waits, and records minutes, tokens and cost |
| `templates/prompt_builder.md` | The builder prompt used since Gate 3 |
| `experiments/*.json` | One config per experiment. A `"stratified"` block (see `g11_spread_vs_blocks.json`) runs the baseline arm first, pairs functions by its edge errors, and sets each arm's questions per pair (`hi`/`lo`) |

## A scale run (no product owner)

```
python3 lab/make_swarm.py --run scale12 --seed gate3/seed_scale.bundle --prompt gate3/prompts/prompt_scale.md --arm F12:12
python3 lab/launch.py --run scale12
python3 gate2/referee/gen2.py hidden2 5000000 20        # regenerate the hidden suite (never commit it)
python3 gate2/referee/evaluate.py runs/scale12/upF12.git hidden2 runs/scale12/eval.json
```

## Writing a new intent experiment

1. Copy `experiments/g8_curve.json`. Give it a new `name` and seeds, its arms (`NAME:WORKERS:none`, `NAME:WORKERS:budget:PORT:N`, or `NAME:WORKERS:quota:PORT` with an `allowance` block), and an ask-text file with one `## NAME` section per arm.
2. Write `gate<k>/prompts/PREDICTIONS.md` with predictions and kill conditions, then commit and push it. `run_gate.py` refuses to launch until it is on origin/main.
3. Run `python3 lab/run_gate.py lab/experiments/<config>.json`.
4. Write `gate<k>/RESULTS.md` from `runs/<name>/summary.md`, failures included. Update `BRAIN.md` and `lab/QUEUE.md`, then push.

`runs/` and `private/` are git-ignored. Private rules are published only after their run is scored, and never for real companies.

## Limits seen so far

- A cloud session can restart, and background servers then die. `run_gate.py` starts them right before launch, so if a run dies, rerun it.
- Usage limits stopped a run once. A 3-team gate costs about 1M tokens.
- Each worker costs about 110k tokens to get started. Fewer, longer-lived workers are cheaper.

## Smoke test (no tokens)

```
HIVE_WORKER_CMD=true python3 lab/run_gate.py lab/experiments/test_plumbing.json --oracle gate6/referee/oracle.py --skip-prereg-check
```
Every stage runs with do-nothing workers, so every score is 0%. A real worker costs about 0.1M tokens just to start.
