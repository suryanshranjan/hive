# From the research to the product

The point of the gates is to make Hive better. This is the audit: every finding that should change what Hive does, the evidence, and where in the code it does so. When a gate ends, add its row here in the same commit as its results, or say why it changes nothing.

Status: **in the tool** means it is code with a test; **not used** means the evidence says don't.

## How the builders work together

| Finding | Evidence | What Hive does | Where |
| --- | --- | --- | --- |
| Silent builders coordinating only through git finish real projects without gaming the tests | Gates 1–3, 24–26 | Builders never talk; each claims an area with a lock and lands through the guard | `hive/claims.py`, `hive/guard.py` |
| A guard keeps regressions off main | Gate 3 | Landing is refused if a passing test fails, a definition is duplicated, or a secret is committed | `hive/guard.py` |
| Onboarding costs about 110k tokens per builder, against 3–5k per task after | Gates 1–3 | Builders loop: land, then claim the next area, until the work is done | `hive/templates/worker.md` (the loop) |
| Caching main's test results saves about a fifth of the finish; lock commits change no code | Gates 21–23 | The guard caches main's results by code content | `hive/guard.py` (cache) |
| **The swarm law**: useful work is the minimum of coupling, the guard's test time and intent; about a core per builder | Gates 2, 10, 21–22; BRAIN §3 | **The number of builders is chosen from this project's measured test time, the computer's cores and the job's size**, and Hive says which limit set it | `hive/law.py`, `hive/start.py` |
| Largest-first claiming did not help | Gate 10 | Not used | |

## How the owner's intent gets in

| Finding | Evidence | What Hive does | Where |
| --- | --- | --- | --- |
| Without the owner, builders miss rules nobody wrote down (24–58% hidden) | Gates 3–24 | Hive always asks before building | `hive/interview.py` |
| Questions in code words lose the owner (1 of 12 answered); plain situations keep him (4 of 4) | Gates 25–26 | `hive ask` refuses code words; every question is a real-life situation with choices | `hive/owner.py` |
| A fixed question budget fixes more when spread, about 2 per area before any gets a third | Gate 11 | Builders are told to spread their questions | `hive/owner.py` (asking text) |
| Builders stretch an answer into rules it does not state | Gates 4, 28 | Each answer is labelled a ruling on that input only; stretching it must be recorded as an assumption | `hive/owner.py` |
| Never being told the allowed values (statuses, types) caused the largest losses | Gate 7 | Builders must record the values they accept when the goal does not list them | `hive/owner.py` (assumptions text) |
| Builders ask where they are unsure, never where they are confidently wrong | Gate 27 | Builders record every default, especially the obvious ones, for the owner | `hive/owner.py` |
| The company's documents settle what they cover, and overturned the owner's memory twice; a document that says "the standard" misleads | Gates 7, 15–17, 20 | **`hive start --docs <folder>`**: the interview skips what documents settle; builders follow them and treat silence or "the standard" as unknown | `hive/docs.py`, `hive/interview.py` |
| The owner answers concrete situations reliably (48 of 48) but does not audit long lists (half found, all kept, none marked) | Gates 30–35 | **Interview first**; the review after the build is a short safety net | `hive/start.py` |
| Questions written from the description miss where the owner differs (4 of 9); from the decisions the code takes, they find them (6 of 6) | Gates 36, 37 and pilot | The interview lists the code's decisions with the builders' defaults, and asks one situation per decision, every decision, up to 20 | `hive/interview.py` |
| Ranking "where he most likely differs" cut exactly his surprises; a model predicts only 35% of them | Gate 33, Gate 37 pilot | No ranking: every decision is asked | `hive/interview.py` |
| Repeated and near-duplicate questions tire him (2–5 s per answer after the 12th) | Gate 37 | One question per decision; same-decision pairs dropped; any answer that settles a later question skips it | `hive/interview.py` |
| "What does it mean?" was taken as his rule | Gate 38 | Each reply is reasoned about: a question about the question gets a plain explanation; a choice said in words counts as that choice | `hive/telegram.py` (`understand`) |
| His answers to two framings of one decision agree 1 of 8 (same session), 3 of 6 (next day) | Gates 36–37 | **The rule sheet**: answers become one general rule per decision, disagreeing answers are put to him, he confirms the whole sheet; **the hand-over**: "here is what it does now; looks right?" | `hive/interview.py` (`rule_sheet`), `hive/start.py` (`handover`) |
| A new answer can contradict an earlier ruling | Gate 30 | Contradictions with earlier rulings are put to him before the builders get both | `hive/interview.py` (`_settle`), `hive/telegram.py` |
| A menu of alternatives led him away from his own rule | Gate 30 | High-stakes decisions in the review ask open first ("what would you do instead?") | `hive/telegram.py` |
| Rulings kept between builds stop repeat questions (25 → 13 decisions to review) | Gate 29 | Rulings are remembered per project and reminded to every build | `hive/memory.py` |
| Contrast examples moved boundaries and broke more | Gate 14 | Not used | |
| Coverage-planned or defaults-first questions did not beat free asking | Gates 4, 5 | Not used | |
| A model of the founder cannot answer for him | Gates 33, 34 | Hive never answers for the owner | |

## Keeping the owner in it

| Finding | Evidence | What Hive does | Where |
| --- | --- | --- | --- |
| A tap on an old button was dropped and he waited 1 h 42 min; a lost connection ended an interview | Gate 36 | Stale taps are answered; sends and polls retry; every answer is saved and a rerun picks up | `hive/telegram.py` |
| A usage limit voided a build; an expired login killed another | Gates 35, 36 | Builders stopped by a limit or a login wait, tell the owner when they will continue, and resume in their own clone | `hive/swarm.py`, `hive/start.py` |

## Still to turn into the product

- **Gate 38** (running): does a confirmed rule hold a day later? If not, the hand-over ("looks right?") becomes the main channel, and the interview shrinks.
- Self-registering modules would cut collisions further (BRAIN §7); not yet needed at 8 builders.
