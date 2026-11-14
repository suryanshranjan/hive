# Gate 109: results (Nov 15 2026)

Three tries:
- **Attempt 1:** interrupted by the laptop, not scored.
- **Attempt 2:** the whole flight. A3 and A4 failed on a bug.
- **Flight 109b:** the test page again after the fix. A3 and A4 held.

The kill held every time: nothing is left billing, checked against AWS.

## Scores

| # | Prediction | Attempt 2 | Flight 109b |
|---|---|---|---|
| A1 | The move works (≤ 12 min, he is told, the laptop's build stopped only after) | **Held:** 2.4 min; "✅ I'm in the cloud, Sir. You can shut your computer now"; the stand-in was alive during the move and stopped after | not part of it |
| A2 | The work restarts in the cloud, and its build finishes with every test passing | **Held, with a note:** the cloud copy messaged his real Telegram, built the goal, asked 2 questions, and built his answers in. 10 tests, all passing; the 7 from before still pass. Builders cost $0.87. The flight's own 25-minute watch ended while Hive was still building his answers, so the flight logged "not finished"; the branch that came home has the finished work | not part of it |
| A3 | The private link answers 200 with his home page; the secret part ≥ 16 characters | **Failed:** the page never went up (the bug below) | **Held:** 200, home page, 16-character secret, the plans page with the new line. On a t3.small made for the test, 2.4 min |
| A4 | Afterwards the link no longer answers; port 8080 closed | **Not run** (needs A3) | **Held:** the link no longer answers; the machine made for the test was deleted with its firewall rule ("nothing is left running or billing") |
| A5 | The cloud build's branch on the laptop after the delete; instance terminated; firewall rule and key gone | **Held:** `hive/on-plans-page-plans-1114-2144` home; terminated; firewall rule and key gone | **Held:** terminated (t3.small); firewall rule and key gone |
| A6 | ≤ $1 of AWS plus builders; ≤ 60 minutes | **Held:** 28.6 min; $0.011 machine + $0.87 builders | **Held:** 3.4 min; $0.001 |
| Kill | Nothing left billing | **Held** | **Held** |

## What attempt 2 found, fixed

**1. The test page killed its own command.**
- **The bug:** the first command on the machine stopped any old test server with `pkill -f "http.server 8080"`. That pattern also matches the shell running the command, so on Linux the shell was killed before the pages' folder was made. Unpacking then failed: "Cannot open: No such file or directory". "Take it down" had the same command.
- **The fix:** `[h]ttp.server`, which doesn't match itself. `hive/trydeploy.py` `STOP_SERVER`.
- **Why the tests missed it:** the stand-in machine only recorded commands. Now it runs them in a real shell, the web server aside.
- **Checked on Linux** (the lab container): the old command fails the new test, and the new one passes.
- **Flown:** flight 109b, above.

**2. Two questions arrived together**, right after "I'll send them one at a time" (the owner, on seeing it).
- **The fix:** the builders' questions go to the phone one at a time; the next goes out only once the last is answered (`hive/telegram.py` `bridge_questions`).
- **Tested:** `tests/test_telegram.py` §2.

**3. A machine made only for a test page** was the default t3.large. Now it's a t3.small (the owner's choice; plain pages need little).

## Confounds
- One run of each.
- The running build on the laptop was a stand-in; the real build was the one restarted in the cloud.
- Flight 109b made its own machine rather than reusing attempt 2's, which was already deleted. That is the path for a founder with no cloud machine. Attempt 2's path, a page on the machine the work moved to, uses the same code after the machine exists.
- In 109b, making the test machine also copied the project to it. That's harmless; the copy was deleted with the machine.

## Attempt 1 (Nov 14-15): interrupted, not scored

- **What happened:** the laptop ran low on memory while the t3.small set itself up: the lab container, two test databases and this session were all running. Claude Code stopped the flight.
- **AWS:** the machine was deleted with `hive cloud --stop` and checked in AWS (terminated, firewall rule and key gone; about 40 minutes, under $0.02).
- **Fixed:** deleting a machine nothing was ever moved to now says "Nothing was ever moved to it, so there is nothing to bring home" and deletes it, instead of asking for DELETE to "lose that work" (`tests/test_cloud.sh`).
