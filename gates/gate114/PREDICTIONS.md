# Gate 114: predictions (registered before launch, Nov 15 2026)

**Question.** The owner said "let's fix it all" about four gaps (BRAIN §8 item 3, and `lab/QUEUE.md`'s list of what needs his word):
1. replies take 7-8 s;
2. Hive runs on his AWS root login;
3. renewing an expired login from the phone has never flown on a real expired login;
4. his real mail, calendar and payments are not connected.

Items 1-3 were built and unit-tested today (`tests/test_fast.py`, `tests/test_aws_limit.py`, `tests/test_logins.py`; no tokens). This gate flies them for real. Item 4 is his to start ("connect my email" on the phone) and is scored as Part E.

**What changed in Hive before this gate (built, not flown):**
- **Fast replies, any provider** (`hive llm api`). Supported keys:
  - Anthropic, through its SDK (default model `claude-opus-5-5` at low effort);
  - any provider that speaks the OpenAI chat API (OpenAI, NVIDIA NIM, Groq, OpenRouter, or another).

  Hive's own reading calls go straight to that model. Chat replies stream into his Telegram message as they are written, then are finished in place. With no key, nothing changes.
- **A limited AWS login** (`hive cloud --limit`):
  - It makes the IAM user `hive-builder` and points Hive at the AWS profile `hive`.
  - The user can only start, stop and delete things tagged `hive`, and can only make machines that carry that tag, in the sizes Hive offers.
  - It has no IAM, S3 or other rights.
  - Signed in as root, Hive now says so plainly.
- **The AWS login check** now looks at Hive's own profile once it exists. Its keys do not expire, so AWS sign-ins stop expiring for Hive.

## Part A: an expired AWS login renewed from his phone (real, now)

The laptop's AWS sign-in expired on its own ("Your session has expired", seen Nov 15). Flight: `python gates/gate114/flight114.py aws-renew` runs `logins.ensure` on his real Telegram. He taps the link, signs in and sends the code back.

| # | Prediction | Kill if |
|---|---|---|
| A1 | The link reaches his phone within 60 s of the start | no link, or later than 120 s |
| A2 | After he sends the code, `aws sts get-caller-identity` works, with no typing at the computer | it needs the computer |
| A3 | He does exactly 2 things: tap and sign in, then send the code | more than 3 |
| A4 | Hive's message has no technical words beyond the link (no "CLI", "token", "profile", "STS") | any |

## Part B: the limited login on real AWS

Flight: `flight114.py limit`. It runs `hive cloud --limit` with the renewed login, then checks the rights with AWS's own `--dry-run`, which makes nothing.

| # | Prediction | Kill if |
|---|---|---|
| B1 | `hive-builder` is made; profile `hive` answers as `.../user/hive-builder` within 30 s | it never answers |
| B2 | Allowed, dry run: a t3.small tagged `hive`, a key pair tagged `hive`, a firewall tagged `hive`, Ubuntu's address | any is refused (Hive could not work) |
| B3 | Refused: deleting or stopping his own `barternow-staging` (untagged), listing IAM users, a machine with no `hive` tag, a c5.4xlarge tagged `hive` | any is allowed (the limit does not hold) |
| B4 | Every later AWS call by Hive goes out with `--profile hive` (seen in the flight's log) | any root call after `--limit` |

## Part C: the whole cloud cycle on the limited login (real, a few cents)

Flight: `flight114.py cycle`. As `hive-builder`, it runs:
1. `hive cloud --new --size t3.small --no-login --no-start`;
2. a check that the machine answers over SSH;
3. `hive cloud --stop`.

| # | Prediction | Kill if |
|---|---|---|
| C1 | The machine is made and answers SSH within 6 minutes | refused for want of a right (then the policy is fixed and C is flown again) |
| C2 | `--stop` deletes it, its key and its firewall; nothing tagged `hive` is left (checked as root) | anything left |
| C3 | His `barternow-staging` is untouched (same state and launch time before and after) | any change |
| C4 | Cost under $0.05 | over $0.20 |

## Part D: fast replies (flown only once he gives a key; otherwise recorded as not flown)

Flight: `flight114.py fast`. It sends 10 ordinary messages to Hive's reply path on his real Telegram ("hi", "status", "what can you do", and 7 others). Each is timed from the send to the first words and to the whole reply. The baseline is Claude Code on the same messages, measured the same way in the same flight.

| # | Prediction | Kill if |
|---|---|---|
| D1 | Median time to first words ≤ 2.0 s with the key (baseline ~7-8 s) | median > 4 s |
| D2 | Median time to the whole reply ≤ 6 s | median > baseline |
| D3 | 10/10 replies finish in place: one message each, ending without "…" | any left unfinished, or two messages for one reply |
| D4 | Cost ≤ 2 cents a reply on `claude-opus-5-5` (or the provider he picks, priced from its list) | > 5 cents |

## Part E: his real office (his word; scored only after he connects)

He says "connect my email", "connect my calendar" and "connect Stripe"/"connect Razorpay" on the phone. Then Gate 112's questions run on his real accounts:
- "what's in my inbox";
- "anything urgent";
- "what's on today";
- "how much came in this week";
- "draft a reply to …" (never sent without his yes).

| # | Prediction | Kill if |
|---|---|---|
| E1 | Each connection takes him ≤ 3 messages, and the secret is deleted from the chat | a secret stays visible |
| E2 | He judges ≥ 4 of 5 answers right against his own accounts | ≤ 2 |
| E3 | Nothing is marked read, sent, or changed in his accounts without his yes | anything |

**Privacy.** Nothing from his real mail, calendar or payments is committed. Only his right/wrong judgements and timings are recorded. His AWS account number is masked in anything committed.
