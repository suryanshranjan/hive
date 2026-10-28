You are checking how much of a company's policy reached its engineers. Work only in this folder.

- `oracle.py` is the company's exact policy. Its `DECISIONS` dict lists, per function, the policy decisions an engineer could not guess from the one-line spec (`SPEC`). Read the code to understand each decision exactly.
- `sheets.json` holds four rule sheets: `D` (what a first build's code does, described as rules), `C` (sheet D after the owner marked and corrected rules and added missing ones), `H` (rules from an interview with the owner) and `R` (a complete rule sheet written by the owner).

For every decision in `DECISIONS` (function name and its index in that function's list, from 0), and for each sheet, label: `"right"` if the sheet states this decision so that an engineer following it would implement it as the policy does on the cases it covers; `"wrong"` if the sheet states it in a way that contradicts the policy; `"partial"` if it states it only for part of its cases or too vaguely to implement; `"absent"` if it does not address it. If a sheet states the decision twice in conflicting ways, label it `"wrong"`.

Write `{DIR}/labels.json`: `{"labels": [{"function": "...", "decision": 0, "label": "...", "D": "...", "C": "...", "H": "...", "R": "...", "note": "..."}]}` with one entry per decision. Then reply in one line: the counts.
