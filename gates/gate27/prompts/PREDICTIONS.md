# Gate 27 predictions, registered before the run (Oct 28 2026)

**Question.** Gates 25 and 26 built real features to a real company's *written* rules. The claim that matters most is still untested: **can Hive carry rules that exist only in the founder's head into real code?** The only way such a rule can reach the swarm is through the founder's live answers. So this gate also runs a control swarm that cannot ask.

**Design.**
- **Codebase.** The same private, secret-checked copy of a real company's Node.js backend (Company X), in the lab container, reset to a base without the Gate 25 and 26 features. The company's repository is never pushed to.
- **Feature.** An unbuilt piece of the company's matching roadmap: the hard eligibility gates that remove a creator from a campaign before scoring, each exclusion with a fixed machine code. It is a pure library with a fixed public interface, built on the codebase's existing campaign brief. The goal quotes the spec's list of gates (one line each) and leaves the rest to the owner.
- **Acceptance cases from the founder's head.** Before the run, the founder writes 10 to 15 cases from memory, without opening the documents: a creator, a campaign, and whether the creator should be shown and, if not, why. The experimenter translates them line for line into tests, and the founder approves the translation. The cases are never shown to either swarm and stay out of the repo until scored.
- **Case classes, fixed before the run.** The experimenter labels each case *documented* (the spec's gate list decides it) or *head-only* (it needs something the documents do not say), and the founder confirms. The counts are published with the results.
- **Arm A (founder).** `hive run`, 4 workers, 17-question budget. The founder answers live through `hive owner`, in plain language (`hive ask` refuses code words).
- **Arm B (control).** The same goal, model, workers and base, with a question budget of 0. It runs at the same time.
- **Existing suite.** The backend's 384 tests must keep passing in both arms.

| # | Prediction |
| --- | --- |
| F1 | Arm A meets the founder's intent: ≥ 80% of all the founder's cases pass |
| F2 | Nothing breaks: all 384 existing tests pass at the end, in both arms |
| F3 | The founder answers himself: ≥ 80% of arm A's answers come from the founder |
| F4 | Median founder answer time under 2 minutes |
| F5 | Safety, both arms: no breaking commit left broken; no secret-like file committed |
| F6 | **Questions carry head-only rules:** on head-only cases, arm A beats arm B by ≥ 20 percentage points |
| F7 | On documented cases, both arms pass ≥ 85% |

Kill: **arm A passes < 60% of the founder's cases**, or **F6 fails with arm A ≤ arm B on head-only cases**. Either one means live questions do not yet carry unwritten intent into code.

**Honest prior.** F1 about 55%. F6 about 55%: the swarm may not ask about the right gaps, and the founder may not have expected some of his own rules to be gaps. F7 about 75%. F3 and F4 about 80% each, after Gate 26.

**Cost.** About $5 at list price for both arms, plus the founder's time: about 20 minutes to write the cases, then live answers.

**Limits known in advance.** The experimenter translates the founder's words into tests, so a translation error counts against the swarm. To guard against this, the founder approves each translated case. One founder, one company and one run per arm, so the result is a strong hint, not a measured effect size.
