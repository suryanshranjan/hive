You are writing test inputs for business functions that engineers have just built from the one-line spec below. You do not know what the right outputs are, and you must not try to work them out: your inputs will be run on two independent builds, and wherever their results differ, the business owner will be asked which is right. So aim your inputs at the places where two careful engineers could make **different choices**. Work only in this folder; do not read any other folder on this machine.

For **every** function, write **30 calls**, spread over:
- typical business cases;
- values just below, at and just above any cut-off a business might set (tiers, grace periods, minimums, caps, discounts, quarter or year boundaries, time limits);
- rounding (amounts that end in odd cents or fractions, halves);
- zero, negative and very large numbers;
- missing values (null), empty or blank text, text where a number is expected, numbers given as text;
- unusual formats a real customer might type (spaces, capitals, separators, extra characters, times on dates).

Write `{OUT}/calls.json`: a JSON list. For a scalar function: `{"function": "late_fee", "args": [10000, 31]}` (JSON values; `null` for a missing value). For the aggregate function (marked below): `{"function": "<name>", "values": [4, 5, null, 3]}`, the column's values over one group of rows (an empty list is allowed).

The functions (as the product team specified them):
{SPEC}

Reply in one line: how many calls you wrote.
