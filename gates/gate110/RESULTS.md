# Gate 110: results (Nov 15 2026)

**Question.** Does a real host work from the phone, with nobody at the computer? It was flown on the owner's personal Vercel (free Hobby plan), with a copy of Dabba Days named `hive-test-dabba-days` and Gate 109's build.

**Three attempts:**
- **Attempt 1:** the flight's own checks were wrong; nothing could be scored on them.
- **Attempt 2:** found that Vercel puts a new project's first deployment live.
- **Attempt 3:** after the fix, every prediction held.

The kill held in all three: the owner's `portfolio` kept the same last-updated time (2026-11-13), and every test project was deleted. $0 spent.

## Scores

| # | Prediction | Attempt 2 | Attempt 3 (after the fix) |
|---|---|---|---|
| V1 | Set-up from the phone | **Held:** Hive installed Vercel's tool itself (uninstalled before the flight), found the sign-in valid, "Connected: Vercel", 0.4 min | **Held:** the same |
| V2 | A link to try, on a project named after his | **Failed:** the "preview" link was the live address. The project was named `hive-test-dabba-days`, not "code" | **Held:** Hive asked first ("Your product isn't on Vercel yet, and Vercel always puts a product's first version live. Shall I put your current version there first…?"). After yes, the build got its own preview address in 0.3 min. That address leads to Vercel's sign-in page for anyone not signed in to Vercel (confirmed with a throwaway project, deleted) |
| V3 | Never live before the merge | **Failed:** the first preview had put the unmerged build live. "Put it live" was refused correctly ("Not yet, sir: your engineer hasn't merged it…") | **Held:** after "send me a link" and after the refused "put it live", the live plans page did not show the trial line |
| V4 | Live after the merge, on his yes | Held (the line was already live from the preview) | **Held:** asked first; after yes, the tests on main passed and the live plans page showed the trial line (0.3 min) |
| V5 | Undo goes back | Held | **Held:** after "undo that" and yes, the live plans page no longer showed the line (0.1 min) |
| V6 | Everything deleted, nothing else touched | Held | **Held:** the test project deleted; `portfolio` untouched; no link file, host record or copy left by the flight |
| Kill | `portfolio` touched, or a test project left | Held | Held |

## What it found, fixed

**1. Vercel puts a new project's first deployment live** (attempt 2).
- **What happened:** "send me a link" on a product new to Vercel put the unmerged build at its live address. That broke Hive's rule that nothing goes live before his engineer merges it and he says yes.
- **The fix:**
  - Hive asks Vercel for a preview as a preview (`--environment preview`). On a new project, Vercel then refuses instead of going live.
  - Hive then asks him. On his yes, it puts his current version live (not the build), then sends the build's link.
  - A setup made before this fix gets the safe command too.
- **Tested** in `tests/test_deploy.py` §8; **flown** in attempt 3.

**2. Hive shared the wrong address.** It took the last link Vercel printed. Now it reads the address Vercel labels (Aliased, Preview or Production).

**3. Vercel previews are private** to his Vercel team: anyone else lands on Vercel's sign-in page. Hive now says so when it sends the link, so the sign-in page doesn't look broken.

**4. Every deploy left a whole copy of his project in the temp folder on Windows.** Git's read-only files made the delete fail silently, and 172 copies had piled up. Now a delete that handles read-only files (`deploy.remove`) is used for previews, going live and AWS test pages. Tested; all 172 were removed.

**Found while setting up, fixed before the flight:**
- **Vercel's tool wouldn't start from Hive on Windows** (npm tools are `.cmd` files). Hive now finds the tool's full path.
- **Every project would have been named "code"**, after the temporary folder Hive deploys from. The folder now carries his project's name, and Vercel's link is kept beside his code, out of his git.
- **Signing in to Vercel and installing its tool** now happen from the phone. `hive/logins.py` covers Vercel, as it does AWS and GitHub.

## Attempt 1 (measurement, not Hive)

The flight looked for the trial line on the home page; it's on the plans page. It also took its before-list of projects before Vercel's tool was installed, so the list was empty. Both were fixed for attempt 2 (`flight110.py`). Hive's steps ran, but V2-V5 could not be read from it.

## Confounds
- One clean run (attempt 3) on one account.
- Plain static pages; no framework build.
- The sign-in was already valid, so Vercel sign-in from the phone runs only in unit tests (`tests/test_logins.py` §8). An earlier sign-in by hand, during set-up, did not finish.
- The owner's side was a fake Telegram. The preview behind Vercel's sign-in was not opened on his phone.
