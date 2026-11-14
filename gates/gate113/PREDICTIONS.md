# Gate 113: predictions (registered before launch, Nov 15 2026)

**Question.** Does Gate 108 replicate on a second company in another trade? Gate 108 was one company, Dabba Days, a lunchbox subscription. Its two open findings (BRAIN §8) need a second one:
- does the planner's price rule (how prices are shown is in scope) find a hidden-price problem elsewhere?
- do data answers hold away from the schema they were fixed on?

**The company.** FixKaro, a made-up doorstep appliance-repair service in Pune.
- **What it sells:** customers book a technician for an AC, washing machine, fridge, water purifier or microwave. A visit is ₹299, waived if repaired; labour and parts are billed; yearly maintenance plans are ₹1,999 and ₹3,499.
- **Who is paid:** 12 technicians, paid every Monday: ₹250 a completed job plus 30% of its labour.
- **The product:** 6 static pages and the billing rules, with 6 passing tests.
- **The data:** a SQLite database of 3.5 months (320 customers, 476 jobs, plans, payments, technician payouts).
- **Documents:** a policy, an FAQ and a pitch.
- **Determinism:** everything is made by a private generator (seed 20261115), kept outside this repo with its answer key.

**Planted, and kept private until scored:**
- the exact answers to the 10 data questions below;
- one rule about technicians' pay that exists only in the payouts table;
- 4 problems on the site, one of them about how prices are shown.

**The flight:** the same as Gate 108 (one run, real Claude, a fake Telegram, a simulated founder from a short brief), on today's Hive.
1. **"hi", then "set me up".** He chooses the business path:
   1. He describes the business.
   2. He says the site isn't live.
   3. He hands over the database.
   4. He sends the policy.
   5. He doesn't know the host.
   6. He keeps Hive on this computer (the new sixth step).
2. **"How are our technicians paid?"** The hidden rule is in the data only.
3. **Ten questions about his figures:**
   1. active maintenance plans;
   2. jobs completed in October;
   3. October bookings cancelled as outside the service area;
   4. the technician with the most jobs redone in October;
   5. October maintenance-plan revenue;
   6. October refunds;
   7. October's most-booked service;
   8. the area with the most October bookings;
   9. October's new customers;
   10. October technician pay after deductions.
4. **Screens:** "show me the services page on desktop", "and on tablet?", "show me the booking page on every screen".
5. **The goal:** "I want more people booking repairs". He answers from his brief and says yes to the plan.

## Predictions

| # | Prediction | Fires if |
|---|---|---|
| R1 | Onboarding works | All 6 steps complete, the database is confirmed by table count, the policy is read, the wrap-up arrives, nothing crashes |
| R2 | Data answers are right | **≥ 8 of 10** match the key (counts and rupees exact; names right) |
| R3 | The hidden rule surfaces | "How are our technicians paid?" states the hidden rule (what is taken off, how much, and when) as the key gives it |
| R4 | Screens | 1, 1 and 3 photos of the named page on the named screens |
| R5 | The planner's price rule replicates | The plan names the planted price problem: the services page shows no price at all |
| R6 | The plan finds the planted problems | ≥ 3 of the 4 planted problems named |
| R7 | Affordable | ≤ $10 and ≤ 60 minutes in all |

**Kill.** Fewer than 6 of 10 data answers right: data access does not carry to a second company.

**Confounds:**
- One run, a simulated founder.
- The same author made both companies, so they may share blind spots.
- The questions are phrased plainly.
