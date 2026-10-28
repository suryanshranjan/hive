You are checking how much of a company's policy reached its engineers. Work only in this folder.

- `oracle.py` is the company's exact policy. Its `DECISIONS` dict lists, per function, the policy decisions an engineer could not guess from the one-line spec (`SPEC`). Read the code to understand each decision exactly.
- `interview_H.json` and `interview_H2.json` hold two separate interviews: the questions an assistant put to the owner and the owner's answers.
- `sheets.json` holds rule sheets given to engineers: `H` (from interview H), `H2` (from interview H2) and `R` (written by the owner).

For every decision in `DECISIONS` (function name and its index in that function's list, from 0), label:
- `asked_H`, `asked_H2`: true if at least one question in that interview is about this decision (its answer would tell an engineer what the decision is), else false.
- `H`: `"right"` if sheet H states this decision so that an engineer following it would implement it as the policy does on the cases it covers; `"wrong"` if sheet H states it in a way that contradicts the policy; `"partial"` if it states the decision only for part of its cases or too vaguely to implement; `"absent"` if it does not address it.
- `H2`, `R`: the same label for sheets H2 and R.
- `note`: a few words.

Write `{DIR}/labels.json`: `{"labels": [{"function": "...", "decision": 0, "label": "...", "asked_H": true, "asked_H2": true, "H": "...", "H2": "...", "R": "...", "note": "..."}]}` with one entry per decision. Then reply in one line: the counts.
