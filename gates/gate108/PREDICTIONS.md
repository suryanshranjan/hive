# Gate 108: predictions (registered before launch, Nov 14 2026)

**Question.** Can a founder run his company through Hive? This is the first flight of the Nov 14 features, all built but never flown before:
- onboarding ("set me up");
- read-only access to his data, and answers from it;
- screenshots on any screen.

**The company.** Dabba Days, a made-up lunchbox subscription in Bengaluru: home cooks make lunch for office workers.
- **Who pays and who is paid:** subscribers pay ₹2,400–3,400 a month for 20 lunches; cooks are paid ₹70 a lunch every Monday.
- **The product:** 10 static pages and the billing rules, with 7 passing tests.
- **The data:** a SQLite database of 3 months (200 subscribers, 12 cooks, 7,138 deliveries, payments, payouts, complaints).
- **Documents:** a policy, an FAQ and a pitch.
- **Determinism:** everything is made by a private generator from a fixed seed (20261114). It is kept outside this repo, with the answer key.

**Planted, and kept private until scored:**
- the exact answers to the 10 data questions below;
- one rule about how cooks are paid that exists only in the payouts table: never on the site, never in the policy. It is named in the private key and in RESULTS after scoring;
- 4 problems on the site that a growth goal should find.

**The flight (one run, real Claude, a fake Telegram, a simulated founder):**
1. **"hi"**, then **"set me up"**. He chooses the business path:
   1. He describes the business.
   2. He says the site isn't live yet.
   3. He hands over the database.
   4. He sends the policy as a document.
   5. He doesn't know the host.
2. **"How are our cooks paid?"** Only the data shows the hidden rule. It is asked first, so no later question can hint at it.
3. **Ten questions about his figures**, asked in his words: active subscribers; October sign-ups; October cancellations; the cook with the most October complaints; October skip credit; this month's refunds; October subscription revenue; the most popular plan; the area with most active subscribers; October cook pay, bonuses included.
4. **Screens:** "show me the plans page on desktop", then "and on tablet?", then "show me the sign up page on every screen".
5. **The goal:** "I want more office workers subscribing". He answers Hive's questions from a short brief and says yes to the plan.

## Predictions

| # | Prediction | Fires if |
|---|---|---|
| O1 | Onboarding works | All 5 business steps complete. The database is connected and confirmed by table count. The policy is read. The wrap-up arrives. No crash or raw error |
| O2 | Data answers are right | **≥ 8 of 10** answers match the key (counts and rupee amounts exact; names right) |
| O3 | The hidden rule surfaces | The answer to "how are our cooks paid?" states the hidden pay rule as the private key gives it (the amount and its condition) |
| O4 | Screens work from the phone | Each of the 3 requests returns photos of the named page on the named screen(s): 1, 1 and 3 photos |
| O5 | The goal finds the planted problems | The plan names **≥ 3 of the 4** planted problems |
| O6 | Affordable | ≤ $10 and ≤ 60 minutes in all |

**Kill.** **Fewer than 6 of 10** data answers right. That would mean Hive's data access is not ready for a founder: say so, and fix it before any founder session.

**What it changes:**
- every failed step is fixed and re-flown;
- if O2 and O3 hold, data access goes into the founder session;
- if O3 fails, plans and answers need a prompt to look for rules that live only in the data.

**Confounds:**
- One run, one company, a simulated founder.
- The questions are phrased plainly.
- SQLite, not his real database.
- The planted problems are easy to see.
