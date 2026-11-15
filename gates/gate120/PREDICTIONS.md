# Gate 120: predictions (registered before launch, Nov 16 2026)

**Question.** Can Hive read a message as a short plan of steps (`hive/router.py`) instead of one intent (`assistant.CLASSIFY`)? It must:
- read single requests no worse than today's reader;
- read chained requests ("find Asha's mail and put a call with her on Thursday"), which today's reader cannot express at all.

**Exam:** Gate 59's independent 130-message exam (13 intents; English, Hindi and mixed).
- Both readers run on the same model in the same run (`gates/gate120/run120.py exam`).
- For the plan reader, its first step must be the intent. A plan of more than one step on these single messages counts as reading them wrong only if the first step is wrong; how often it happens is reported.
- Today's reader is measured afresh: it has grown since Gate 59's 95.4%.

**Chains** (`chains.jsonl`, written before this run; `run120.py chains`):
- 14 requests that ask for 2-3 things in order.
- 4 controls that look like two things but are one ("add a share button and a download button").
- A chain counts as right only if its steps are exactly the ones written, in order. A few have an equally right alternative, listed in the file.
- 3 chains need a later step to use an earlier step's result (`$1`).

| # | Prediction | Kill |
|---|---|---|
| P1 | On the exam the plan reader is within 2 points of today's reader (non-inferior) | more than 4 points worse: it does not ship |
| P2 | Hindi and mixed messages: within 4 points of today's reader | more than 8 worse |
| P3 | The plan reader makes a multi-step plan for at most 3 of the 130 single messages | more than 8 |
| P4 | Chains: ≥ 11 of 14 exactly right | < 8 |
| P5 | Controls: ≥ 3 of 4 stay one step | ≤ 1 |
| P6 | Of the 3 chains whose later step needs an earlier result, ≥ 2 use `$1` for it | 0 |
| P7 | The plan reader takes at most 1.5 s longer per message (median) and costs at most 1.5× | more than 3 s, or 2.5× |

**What ships:**
- If P1 holds and the kill does not fire, the plan reader becomes the default, and the old reader stays as `HIVE_ROUTER=intent`.
- If P1 fails, the plan reader is used only for messages that contain more than one request, and only if P4 holds.

**Confounds:**
- The chains were written by the same author as the router.
- One run.
- The exam's messages are those of 13 intents only; the office steps (mail, calendar) are measured only by the chains.
