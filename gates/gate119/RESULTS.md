# Gate 119: results (Nov 15 2026)

**Question.** Do the fixes for Gate 118's gaps hold on cases they were not tuned on? The fixes are meaning-based recall, and one REMEMBER call that names what a new fact replaces. One run of each part:
- `results_heldout.json`;
- `results_live2.json`, on the small model.

## Scored

| # | Prediction | Result | |
|---|---|---|---|
| H1 | `meaning` ≥ 9/12; `words` ≤ 4/12 | **`meaning` 12/12**; `words` **6/12** | Half held: the gap is closed, but words alone did better than predicted (kill not fired) |
| H2 | R1 stays ≥ 29/30 with `meaning` | **30/30** | Held |
| H3 | ≤ 300 ms per recall | **69 ms** | Held |
| L1 | All 10 first messages and all 6 changes kept | Changes **6/6**, including all 4 about how the business works (Gate 118 lost one such change each run); first messages **9/10** | **Failed** on first messages (kill < 8 not fired) |
| L2 | Old fact replaced ≥ 5/6 (store-based) | **5/6**; the 6th had no old fact to replace (its first message was the one not kept) | Held |
| L3 | Controls ≥ 4/4 untouched | **4/4**; the 4 same-topic messages replaced nothing | Held |
| L4 | Current answer in the reply's context ≥ 9/10 | **10/10** | Held |
| L5 | Under $1 | **$0.36** (Gate 118: $6.80, then $1.77) | Held |

## The one miss, and why it is left as it is

"A customer can cancel until 9 am for the same day" was not kept when first said. REMEMBER is told not to keep rules for how the product behaves, and a cancellation cutoff reads as one.
- **In a real chat, the message does not stop at REMEMBER.** Hive's reader classes a statement like this as a standing rule and keeps it among his rules (`memory.add`, the path Gates 30 and 101 measured). This bench sends messages to REMEMBER only, so that path is not exercised here.
- **The later change was kept** ("cancellations now close at 7 am"), and is the one recalled.

The open question for a later gate is whether the rule path and the notes path agree on the same statement in a real chat.

## What it changes in the product

- **Recall by meaning:** `pip install "hive-swarm[memory]"` (fastembed, local, about 70 MB once). It is in the Render image.
  - A reply never waits for the model: it loads in the background when Hive starts, and until then recall uses words alone.
  - The model is downloaded once per machine (`HIVE_MODELS`; on Render, the disk).
- **One call per message for memory:** the fact, its kind and person, and which kept facts it replaces. The separate REPLACES call is gone.
