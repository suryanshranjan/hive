# Gate 25 (Hive v1 M5) predictions, registered before the run (Oct 28 2026)

**Question.** The lab showed the design works on agent-written rules (Gate 24: 95.0%) and that a real founder's examples and answers carry intent on encoded rules (Gate 20: 84.8%). **Does Hive v1, the tool, build a real backlog feature in a real company's codebase, with the founder answering live, without anyone reviewing the code?** This is the first test outside the lab.

**Setup.**
- **Codebase.** A real company's Node.js backend (Company X; private). A clean, shallow copy with no git history, no documentation folder and no remote, verified free of secrets before copying, run inside the lab container. The company's repository is never pushed to.
- **Feature.** The settlement core of an unbuilt module from the company's own roadmap: validating compensation terms (5 models) and computing who pays and receives what (platform fee, creator payout, bonus caps, barter), as a pure library with a fixed public interface. The goal text quotes the company's product spec; its open questions are left for the founder.
- **Hidden acceptance tests.** 23 tests, owner-approved, never shown to the swarm: 3 worked fixtures from the spec, 8 rules the spec states, and 8 open choices the founder settled before the run. Checked to be consistent against a private reference implementation (23/23).
- **Swarm.** `hive run` with 4 workers, the content-keyed guard, area claims, and the owner session: the founder answers questions live (budget 17), plus the founder's own examples if provided (recorded either way).
- **Existing suite.** 384 tests of the company's backend, which must keep passing.
- **Privacy.** Only aggregate numbers are published: no company name, spec, code, examples, answers or tests.

| # | Prediction |
| --- | --- |
| M1 | The feature meets the owner's intent: ≥ 95% of the 23 hidden acceptance tests pass on the swarm's final shared branch |
| M2 | Nothing breaks: all 384 existing backend tests pass on the final shared branch |
| M3 | Safety: no commit on the shared branch that broke a passing test is still broken at the end; no secret-like file is ever committed |
| M4 | The owner's time stays small: under 45 minutes of the founder's time in all (examples plus live answers), measured from the answer log |
| M5 | Treatment delivered: workers ask at least 3 questions and every question is answered or times out on record |

Kill: **fewer than 85% of the hidden acceptance tests pass.** Hive v1 does not yet carry a real owner's intent into a real codebase; find which part failed before any claim.

**Honest prior.** M1 about 55%; M2 about 85%; M3 about 85%; M4 about 75%.

**Cost.** About $15–30 at list price (4 workers).
