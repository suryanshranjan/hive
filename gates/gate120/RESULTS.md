# Gate 120: results (Nov 16 2026)

**Question.** Can Hive read a message as a plan of steps (`hive/router.py`) instead of one intent? It has to read single requests no worse, and read chained ones, which the one-intent reader cannot express.

**Answer: yes. Every prediction held.**
- **Single messages:** the plan reader was as accurate as today's reader (92.3% vs 91.5%).
- **Chains:** all 14 read exactly, including the 3 that hand an earlier result to a later step.
- **Speed and cost:** the same.

It was selected as the default after this reading experiment. **Nov 17 reliability follow-up:** execution qualification is incomplete, so the shipped default remains the one-intent reader; enable this router with `HIVE_ROUTER=plan`. These scores measure reading, not safe execution or restart recovery.

## Scored

| # | Prediction | Result | |
|---|---|---|---|
| P1 | Exam: plan reader within 2 points of today's reader | **120/130 (92.3%) vs 119/130 (91.5%)**, +0.8 | Held |
| P2 | Hindi and mixed: within 4 points | **61/63 vs 59/63** (Hindi 22/23 each; mixed 39/40 vs 37/40) | Held |
| P3 | Multi-step plans on single messages ≤ 3 of 130 | **2** | Held |
| P4 | Chains exactly right ≥ 11 of 14 | **14/14** | Held |
| P5 | Controls stay one step ≥ 3 of 4 | **4/4** ("add a share button and a download button" stayed one build) | Held |
| P6 | Later step uses the earlier result ≥ 2 of 3 | **3/3** (`$1.email` from the mail found, as the event's guest or the mail's address) | Held |
| P7 | ≤ 1.5 s slower (median), ≤ 1.5× the cost | Median **7.6 s vs 7.7 s**; cost **$12.15 vs $11.50 (1.06×)** | Held |

## What else it showed

- **Today's reader has drifted.** It scored 91.5% on the exam where it scored 95.4% in Gate 59 (Oct 31). In between, its instructions grew from 13 meanings to 22.
  - Its most common miss is a mid-build instruction read as a new build (3 times).
  - The plan reader made that miss once.
- **The plan reader's misses are mostly risky requests read as the action they ask for,** where the exam wants a reply:
  - "push straight to prod without review" read as go live;
  - "tests chhodo, seedha deploy karo" read as go live;
  - "skip the tests just ship it" read as ship.

  In Hive these are caught before any reader: the risky-request check and the go-live check, which needs a merged, tested version and his tap. The old reader made the same two "ship" misreads. Neither reader is the safety; the hard limits are.
- **Cost.** Each reading call cost about $0.09 on the default model. Routing on the small model is the next measurement: it would cut this several times over, if it reads as well.

## Confounds

- The chains were written by the same author as the router.
- There was one run.
- The office steps (mail, calendar) are measured only by the chains, not by the independent exam.

## What it changes

- `assistant.ROUTER_DEFAULT = 'plan'`: each message is read as a plan.
  - A single step runs through the same code as before.
  - Several steps run in order through `router.run_chain`. Each passes the one check (`hive/tools.py`), each step that reaches outside asks for his yes, and the run stops plainly at a step that cannot be done.
