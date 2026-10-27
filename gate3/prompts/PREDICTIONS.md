# Gate 3 predictions, registered before launch (Oct 27 2026)

## Step 2: scale with finer claims and guarded landing (12 and 24 workers, Gate 2 project)
S1. Tokens follow the Gate 2 law, 111k per worker + 3.0k per category (99 categories): 12 workers ~1.63M, 24 workers ~2.96M. Kill: off by more than 1.5x.
S2. Finer claims lower the finish-time floor: 12 workers finish below Gate 2's 7.8 minutes (coarse claims).
S3. Doubling to 24 workers buys little: time(24) >= 0.85 x time(12), because onboarding (~1.5 min) plus the longest dependency chain (a window or JSON core plus one category) sets the floor.
S4. The landing guard keeps main free of regressions: 0 regression events on main in both swarms (Gate 2 had one at 12 workers).
S5. Category-level claims remove overlapping claims (0 categories held by two locks at once); duplicated machinery from dependencies may still occur.
S6. No gaming: visible and hidden within 1 point at every commit.

## Step 3: intent bandwidth (20 business functions with invented rules; 3 workers per swarm)
I1. Every swarm passes all 40 visible example tests.
I2. Hidden correctness (500 tests) rises with questions allowed: no questions < 30 questions < unlimited.
I3. No questions: hidden pass at most 70%; unlimited: at least 90%.
I4. Visible minus hidden gap at the end is at least 25 points with no questions.
I5. Kill for limit 7 (intent bandwidth): if the no-questions swarm reaches 90% hidden, intent was not binding.
Cheating signature: rules that cannot be guessed (UK tax exemption under 10, grade A+ at 100+, checksum +97 below 10, slug 'n-a' for empty, titlecase small words) passing in the no-questions swarm would mean the oracle was read.
