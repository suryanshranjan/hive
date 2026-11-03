# Gate 104 predictions: confirm the owner's rules once, at the end

Registered Nov 3 2026, before any flight. From the plan in `lab/QUEUE.md` ("Owner time, Gap 2"), run because the user asked for everything that needs only the computer.

## Why this test

Gates 95–98 and 102 average about 11 interview questions plus about 9 per-answer rule confirmations per feature. After the interview, Hive reads each answer given in the owner's own words back to him, one at a time ("Your rule, as I'll build it: ... Right?"). It then shows all the rules together on one sheet. The read-backs double-check what the sheet checks again. Can the sheet alone, one confirmation at the end, do the job with about 9 fewer prompts and nothing lost?

## Setup

- **Flight:** Gate 103b's live flight, unchanged. `hive start` as shipped on Tiny Shop with Gate 54's three-part goal. A synthetic owner answers every prompt from Gate 54's published policy. The delivered branch is scored on Gate 54's 27 hidden tests.
- **Arms**, alternated P1 B1 P2 B2 P3 B3, each starting with an empty `~/.hive`:
  - **P:** Hive as shipped. Each own-words answer is read back and confirmed, then the sheet.
  - **B:** `HIVE_CONFIRM_EACH=0`. No read-backs; the rule sheet that follows is the one confirmation. It applies only when the sheet will be shown (two or more rules).
- **Measured:** owner prompts, read-back confirmations, hidden tests passed, minutes, cost.
- **Driver and analysis:** `referee/flight104.py`, `referee/analyze104.py`, committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| Q1 | B saves at least 5 owner prompts per flight (median) | 65% |
| Q2 | Every B flight passes at least 24 of 27 hidden tests (the bar of Gates 98 and 103b) | 70% |
| Q3 | B's median hidden is at least P's minus 1 | 65% |

## Decision rules

- **Ship:** Q1, Q2 and Q3 all hold. Confirming once at the end becomes the default.
- **Kill:** a B flight falls below 24 while every P flight reaches it, or B's median is more than 1 below P's. Each answer stays confirmed.

## Cost and limits

- About $10–15: 6 flights.
- One synthetic owner and one goal; 3 flights per arm.
