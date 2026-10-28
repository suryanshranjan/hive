You are checking how much of a company's policy reached its engineers. Work only in this folder.

- `oracle.py` is the company's exact policy. Its `DECISIONS` dict lists, per function, the policy decisions an engineer could not guess from the one-line spec (`SPEC`). Read the code to understand each decision exactly.
- `interview.json` holds an interview an assistant held with the owner: `answered` (each question with the owner's reply, as typed) and `skipped` (questions the assistant wrote but never put to him, because it judged an earlier answer had settled them). `terminal` is the whole session as the owner saw it.
- `handovers.json` holds what engineers were given: `H` (a rule sheet), `K` (the same sheet plus the owner's answers to each situation, kept whole) and `R` (a complete rule sheet written by the owner).

For every decision in `DECISIONS` (function name and its index in that function's list, from 0), label:
- `asked`: true if at least one **answered** question is about this decision (its answer would tell an engineer what the decision is), else false.
- `skipped_only`: true if no answered question is about it but at least one skipped question is, else false.
- `answer`: if asked, `"right"` if the owner's replies (and the choices he picked) convey this decision as the policy does, `"partial"` if only for part of its cases or vaguely, `"wrong"` if they contradict it; `"-"` if not asked.
- `H`: `"right"` if hand-over H states this decision so that an engineer following it would implement it as the policy does on the cases it covers; `"wrong"` if it contradicts the policy; `"partial"` if it states it only for part of its cases or too vaguely to implement; `"absent"` if it does not address it.
- `K`, `R`: the same label for hand-overs K and R.
- `note`: a few words.

Write `{DIR}/labels.json`: `{"labels": [{"function": "...", "decision": 0, "label": "...", "asked": true, "skipped_only": false, "answer": "...", "H": "...", "K": "...", "R": "...", "note": "..."}]}` with one entry per decision. Then reply in one line: the counts.
