You are checking how much of a company's policy reached its engineers. Work only in this folder.

- `oracle.py` is the company's exact policy. Its `DECISIONS` dict lists, per function, the policy decisions an engineer could not guess from the one-line spec (`SPEC`). Read the code to understand each decision exactly.
- `sheets.json` holds rule sheets: `D` (what a first build's code does, described in full), `DS` (the same code described briefly, business choices only), `SF` (D after the owner's review), `SS` (DS after the owner's review) and `R` (a complete rule sheet written from the policy).

For every decision in `DECISIONS` (function name and its index in that function's list, from 0), and for each sheet, label: `"right"` if the sheet states this decision so that an engineer following it would implement it as the policy does on the cases it covers; `"wrong"` if it states it in a way that contradicts the policy; `"partial"` if it states it only for part of its cases or too vaguely to implement; `"absent"` if it does not address it. If a sheet states the decision twice in conflicting ways, label it `"wrong"`.

Write `{DIR}/labels.json`: `{"labels": [{"function": "...", "decision": 0, "label": "...", "D": "...", "DS": "...", "SF": "...", "SS": "...", "R": "...", "note": "..."}]}` with one entry per decision. Then reply in one line: the counts.
