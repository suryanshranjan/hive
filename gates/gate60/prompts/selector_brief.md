Two engineering teams built the same business function independently, from the same one-line spec. On the calls below, their results differ. A busy business owner will check a few of these, one at a time, to settle what his business wants.

The function: {SPEC_LINE}

Differences (the call; our build's result; the second build's result):
{LIST}

Pick **at most 4** differences that come from **different choices** (a cut-off, a rounding, a minimum or a cap, how a missing or odd value is treated...), the ones that matter most to the business first. Skip a difference that comes from the same choice as one you already picked.

For each, write `say`: one sentence in plain business words, with names and amounts, giving the case, our build's outcome, and in brackets the second build's outcome, for example: "Ravi's 100-rupee invoice is paid 31 days late: our build charges a 2-rupee late fee (a second build charged nothing)." Amounts in cents become money. No code words (no "null", "error", "function", "returns"): say what it means for the customer.

Reply with JSON only: {"cases": [{"call": "<the call, copied>", "say": "..."}]}
