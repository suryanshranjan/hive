# Gate 26 predictions, registered before the run (Oct 28 2026)

**Question.** Gate 25 built a real feature in a real codebase (23/23 hidden tests), but the founder answered 1 of 12 questions and delegated the rest to an AI proxy that had also drafted the hidden tests, so the result was optimistic. Since then, `hive ask` requires plain-language, multiple-choice questions. **With the founder writing the acceptance cases and answering live, does Hive v1 still build a real feature to the founder's intent?**

**Design.**
- **Codebase.** The same private, secret-checked copy of a real company's Node.js backend (Company X), in the lab container. The company's repository is never pushed to.
- **Feature.** A different unbuilt feature from the company's roadmap: a deterministic score computed from a creator's past collaborations, with weights, a minimum history, display bands and an achievement ratio stated in the company's spec. A pure library with a fixed public interface; the goal quotes the spec and leaves the rest to the owner.
- **Acceptance cases.** Written by the founder, before the run, in plain words (a situation and the expected result). The experimenter only translates them line for line into tests, which the founder approves. They are never shown to the swarm. Their count and the share the swarm passes are reported.
- **Owner.** The founder answers live through `hive owner`. Every answer records who gave it (founder or proxy) and how long it took. Questions must be plain language (`hive ask` refuses code words).
- **Swarm.** `hive run`, 4 workers, 17-question budget, no owner examples.
- **Existing suite.** The backend's 384 tests must keep passing.

| # | Prediction |
| --- | --- |
| F1 | The feature meets the founder's intent: ≥ 85% of the founder's acceptance cases pass |
| F2 | Nothing breaks: all 384 existing tests pass at the end |
| F3 | The founder answers the questions himself: ≥ 80% of answers come from the founder, not a proxy |
| F4 | Plain questions are answerable: median founder answer time under 2 minutes |
| F5 | Safety: no breaking commit left broken; no secret-like file committed |

Kill: **< 70% of the founder's acceptance cases pass.** Hive v1 does not yet carry a founder's live intent into real code.

Note: F1's bar is lower than Gate 25's (95%) on purpose. The cases come from the founder's own head, not from a spec-derived list, so they can include rules nobody wrote down.

**Honest prior.** F1 about 55%; F2 about 85%; F3 about 70%; F4 about 70%.

**Cost.** About $4 at list price, plus the founder's time (cases, then live answers).

## Amendment, registered before the run (Oct 28 2026)

The founder chose to have the acceptance cases taken from the company's documents rather than writing them himself. So:
- **The 18 acceptance cases come only from the company's written spec** (one section of its architecture document, plus the matching table that refers to it), translated by the experimenter, approved by the founder, and checked consistent against a private reference (18/18). Within each case the collaborations are identical, so choices the spec leaves open (for example how to combine different collaborations) do not affect the result.
- **The founder still answers live** (F3, F4). This is the main change from Gate 25, where an AI proxy answered 11 of 12 questions.
- **What F1 now measures:** whether the swarm implements the company's *documented* rules plus the founder's live rulings without breaking them. It no longer measures undocumented intent from the founder's head; that remains open.
