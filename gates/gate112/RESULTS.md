# Gate 112: results (Nov 15 2026)

**Question.** Does the office work on real protocols, with the real model answering? It ran on:
- a real IMAP and SMTP server (GreenMail);
- Stripe's official mock;
- a Razorpay stand-in;
- an iCal calendar.

Claude answered. There were three runs, each under a minute. Run 3, after two prompt fixes, held on every prediction. The kill held in all three: no mail sent without his tap, nothing marked read, only GET sent to any payment API.

| # | Prediction | Run 1 | Run 2 | Run 3 |
|---|---|---|---|---|
| O1 | The mail that matters | Held: Asha's order, the cold-lunch complaint, the cook's bonus and the invoice; noise last | Held | **Held:** the same four, 50 words |
| O2 | Read-only (6 of 6 still unread) | Held | Held | **Held** |
| O3 | A reply he approves, in the thread | **Failed (strict):** the first draft added "₹4,800 in total" itself. The second draft, the one sent, didn't, and arrived in Asha's real mailbox from his address, In-Reply-To set to her message | Held | **Held** |
| O4 | Nothing sent without his yes | Held | Held | **Held** |
| O5 | Payments | Held: ₹4,500 from 2, the failed ₹999 named, Stripe requests all 200, GET only | **Failed:** the failed payment was left out ("not asked") | **Held:** "You made ₹4,500 this week from 2 payments… 1 payment failed: ₹999 from late@x.in… you may want to follow up." |
| O6 | The calendar | Held: "No. You have a tasting with Asha… 3:00 to 4:00 pm tomorrow" | Held | **Held** |
| O7 | Plain (< 80 words, answer first) | **Failed:** the mail summary was 89 words | Held (68) | **Held** (50, 34, 18) |

## Fixed from it
- **Drafts never add a figure he didn't say:** no totals, taxes or discounts, even worked out from his own numbers (`hive/mail.py` DRAFT).
- **The mail summary stays under 70 words,** one short line per item.
- **A failed payment is always mentioned,** in one line, so he can follow up (`hive/payments.py`).
- **Payments keep only what falls in the dates asked.** Stripe's mock returned a 2009 charge for "this week"; a real API's paging could too. The filter was added before run 1.

## Confounds
- Stand-in servers, not his real Gmail, Stripe or Razorpay accounts. The protocols are real; the accounts are not. Stripe's mock checks request shape, not real totals.
- One model, three runs.
- Mail was connected the engineer's way (`mail.setup`). Connecting it in the chat, with the password deleted from the chat, is unit-tested only (`tests/test_office.py`).
