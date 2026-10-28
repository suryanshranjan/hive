You are checking how much of a company's policy reached its engineers. Work only in this folder.

- `oracle.py` is the company's exact policy. Its `DECISIONS` dict lists, per function, the policy decisions an engineer could not guess from the one-line spec (`SPEC`). Read the code to understand each decision exactly.
- `interview.json` holds the questions an assistant put to the owner and the owner's answers.
- `sheets.json` holds rule sheets given to engineers: key `H` (from the interview) and key `R` (written by the owner).

For every decision in `DECISIONS` (function name and its index in that function's list, from 0), label:
- `asked`: true if at least one interview question is about this decision (its answer would tell an engineer what the decision is), else false.
- `H`: `"right"` if sheet H states this decision so that an engineer following it would implement it as the policy does on the cases it covers; `"wrong"` if sheet H states it in a way that contradicts the policy; `"partial"` if it states the decision only for part of its cases or too vaguely to implement; `"absent"` if it does not address it.
- `R`: the same label for sheet R.
- `note`: a few words.

Write `{DIR}/labels.json`: `{"labels": [{"function": "...", "decision": 0, "label": "...", "asked": true, "H": "...", "R": "...", "note": "..."}]}` with one entry per decision. Then reply in one line: the counts.
