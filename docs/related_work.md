# Related work and what Hive can claim (checked Oct 28 2026)

A web search of published work (arXiv, practitioner sources) against Hive's main claims. This is a first pass, not a systematic review: about ten searches and three abstracts read. Anything marked "not found" means "not found in this search", not "does not exist".

## Not new: the building blocks exist

| Hive idea | Prior work | What it means for Hive |
| --- | --- | --- |
| Many coding agents working in parallel through git | Anthropic's 16 parallel Claude agents built a ~100k-line C compiler over ~2 weeks ([coverage](https://www.analyticsvidhya.com/blog/2026/02/claude-agents-built-c-compiler/)); Cursor's FastRender browser, built by thousands of agents with planners splitting work into non-overlapping chunks ([Willison](https://simonwillison.net/2026/Jan/23/fastrender/)); git-worktree isolation is the standard 2026 pattern ([arXiv 2609.00252](https://arxiv.org/pdf/2609.00252), [OpenHands](https://www.openhands.dev/blog/agentic-swarm)) | Hive's protocol (claims, guarded landing) is in this line. Hive analysed both projects' histories in its first gates. Its contribution here is measurement, not invention |
| Merges that pass alone and fail together | STALE benchmark: 1 of 834 mined Django pairs interfered, 97% of constructed cases did; a message about the concurrent change fixed 82% ([arXiv 2609.25396](https://arxiv.org/abs/2609.25396)) | Matches Hive's measurements (collisions rare and cheap; one semantic conflict in Gate 2). Hive's guard (no test passing on main may fail) is one answer to the same problem |
| Agents asking clarifying questions about code | ClarifyGPT ([FSE 2024](https://dl.acm.org/doi/full/10.1145/3660810)); AMBIG-SWE ([ICLR 2026](https://arxiv.org/pdf/2502.13069)); ClarEval ([arXiv 2603.00187](https://arxiv.org/html/2603.00187v1)); Ask or Assume? ([arXiv 2603.26233](https://arxiv.org/html/2603.26233v1)); FDE-Bench ([arXiv 2610.14539](https://arxiv.org/html/2610.14539)); ClarifyCodeBench ([arXiv 2607.00711](https://arxiv.org/html/2607.00711v2)) | The "builder questions" arm of every Hive intent gate is this. The common finding there (agents guess or over-ask) matches Hive's |
| Tests as the way to pin intent, with the user confirming | TiCoder: the LLM proposes tests and the user approves them; +46 points pass@1 on average within 5 interactions ([TSE 2024](https://www.microsoft.com/en-us/research/publication/llm-based-test-driven-interactive-code-generation-user-study-and-empirical-evaluation/), [arXiv 2208.05950](https://arxiv.org/abs/2208.05950)) | Close to Hive's Gate 18 arm (agent-drafted cases, owner confirms) and its "answers become tests" rule |
| The owner gives one worked example per business rule | **Specification by Example** (Adzic) and BDD: key examples per rule serve as specification, acceptance tests and documentation ([summary](https://fourweekmba.com/specification-by-example/)) | Hive's "decision tour" is Specification by Example, applied to agent swarms. It must be called that |
| Examples plus language beat either alone | Fu et al., ISSTA 2025: LLMs drop >60% from language to examples only, and recover with rough language added ([arXiv 2411.06774](https://arxiv.org/abs/2411.06774)); Wen et al. 2024 ([arXiv 2402.08073](https://arxiv.org/abs/2402.08073)) | Consistent with Hive: the tour works alongside the one-line spec, and questions add on top |
| Elicitation does not always help | "Eliciting Specifications: When Does Interactive Clarification Help?": an agent asking a simulated developer up to 3 or 10 questions *lowered* strict accuracy within one model, and raised it by up to +6.3 points across models ([arXiv 2610.22382](https://arxiv.org/abs/2610.22382)) | Consistent with Hive's Gates 4, 5 and 12: questions have a ceiling |
| LLMs and unknown unknowns in requirements | LLMs flag gaps in documentation but miss tacit, expert knowledge; one study captured a little over 70% of intended requirements ([arXiv 2310.13976](https://arxiv.org/pdf/2310.13976), [arXiv 2507.02564](https://arxiv.org/pdf/2507.02564), [arXiv 2609.05667](https://arxiv.org/pdf/2609.05667)) | The same phenomenon Hive measured in Gate 12, described qualitatively |

## Possibly new: what this search did not find

| Hive result | Evidence in this repo | Search result |
| --- | --- | --- |
| **A randomized head-to-head of owner-chosen examples against the same budget of builder-chosen questions**, scored on hidden tests: owner examples fixed 2.7× the errors on agent-written rules and 1.17× on a real founder's rules | Gates 13, 18, 20 | Not found. The closest search reported "none of these sources directly measures whether a user supplying I/O examples outperforms the agent asking questions" |
| **A measured floor on questions:** about a fifth of errors survive any number of builder questions, and 87% of the errors left after 4 questions per function were also left after 1 and 2. Every stuck error was a decision no question probed | Gate 12 | Unknown unknowns are discussed qualitatively; no measurement of a question floor found |
| **Who points matters more than who confirms:** agent-drafted, owner-confirmed examples did no better than questions (0.93×); founder-written ones did better (1.17×, and far fewer calls broken); the founder and the agent picked the same inputs 53% of the time | Gates 18, 20 | TiCoder studies confirmation; no comparison of owner-chosen against agent-chosen points found |
| **A limit decomposition for silent swarms** (coordination, serial gate, intent), with constants measured on real agents, including CPU per guard check as the speed limit on small machines | Gates 0–3, 10, 21, 22 | Swarm projects report outcomes; no comparable quantitative model found |
| **Pre-registered, falsifiable experiments** with kill conditions, every failure reported | All gates | Methodology, not a result, but uncommon in this literature |

## What Hive can honestly say today

1. Hive applies **Specification by Example** to silent agent swarms and measures it. Not invented here: worked examples, clarifying questions, test-based intent and parallel agents all exist.
2. The measured, possibly new findings: **who chooses the points sets how much intent gets through**, and builder questions hit a **floor at the decisions nobody imagines**.
3. Real-world evidence: one founder, one company, 10 rules, one run per team (84.8% hidden at best).

## Before claiming novelty in public

- A systematic search (Google Scholar, ACM, IEEE) on: example-based vs question-based elicitation; Specification by Example with LLMs; multi-agent coding with acceptance tests.
- Read in full: arXiv 2610.22382, 2610.13022 ([Don't Guess, Just Ask](https://arxiv.org/html/2610.13022)), 2609.25396, 2502.13069, TiCoder.
- Replicate the founder result on a second company before generalizing from it.
