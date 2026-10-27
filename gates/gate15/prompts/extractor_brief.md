You are the QA lead for an engineering team that is adding 20 business functions to the company's SQL engine. The product owner will answer your example inputs with the intended outputs, and those answers will become tests the engineers must pass.

Work only in `{DIR}`: do not read any other directory or file on this machine. Read `{DIR}/handbook.md` (the company's policy handbook) and `{DIR}/spec.md` (the one-line spec of each function).

For each function, find every policy decision the handbook states or hints at, and suspect the ones the spec leaves open (rounding, caps, thresholds, invalid or unusual inputs, alternative formats, calendar rules and so on). Then choose **at most 50 inputs in total** across all functions, each placed to show one decision at work, so that the owner's answers pin down as many decisions as possible.

Write `{DIR}/tour_inputs.json`: a JSON object mapping each function name to a list of argument lists, for example `{"late_fee": [[30, 1000], [2, 20]]}`. Arguments are JSON numbers, strings or null. For the aggregate function, each entry is the list of column values to aggregate.

Reply in one line: how many inputs you chose.
