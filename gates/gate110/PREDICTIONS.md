# Gate 110: predictions (registered before launch, Nov 15 2026)

**Question.** Does a real host work from the phone, with nobody at the computer? Hive's Vercel path ("we're on Vercel", "send me a link", "put it live", "undo that") has only been unit-tested. The owner: "test on Vercel; Hive has the autonomy to do all this from the phone", then "test and then delete everything".

**Setup:**
- **The account:** the owner's personal Vercel (Hobby plan, free). It's signed in on the laptop. Its one project, `portfolio`, must not be touched.
- **The project:** a fresh copy of Dabba Days (the mock company) named `hive-test-dabba-days`, with Gate 109's build on its branch (the ₹500 trial-week line, linking to signup).
- **Before launch, Vercel's tool is uninstalled from the laptop,** so Hive has to install it itself.
- **His side:** a fake Telegram drives his words and taps; Hive's replies are logged.
- **His engineer:** a stand-in merges the build into main (`--no-ff`, as a pull request would) between the first and second "put it live".

**The steps:**
1. "We're on Vercel".
2. "Send me a link".
3. "Put it live" before the merge.
4. The engineer merges. "Put it live" again; he taps yes.
5. "Undo that"; he taps yes.
6. Delete everything: the Vercel project, the link files, Hive's records of this host. Then check.

## Predictions

| # | Prediction | Fires if |
|---|---|---|
| V1 | Set-up from the phone | Hive installs Vercel's tool itself (it was uninstalled), finds the sign-in valid, and says "Connected: Vercel"; no step asks for an engineer |
| V2 | A link to try | A preview address comes back on the phone within 5 minutes, on a new Vercel project named `hive-test-dabba-days` (not "code"). Its status is recorded: 200, or Vercel's login wall (401/403) |
| V3 | Never live before the merge | The first "put it live" is refused plainly (not merged), and nothing new appears in production |
| V4 | Live after the merge, on his yes | Asked first; after his yes, the tests on main pass, and the production address answers 200 with the trial line within 5 minutes |
| V5 | Undo goes back | After "undo that" and his yes, the production address answers 200 without the trial line |
| V6 | Everything deleted, nothing else touched | The project is deleted (gone from `vercel project ls`); `portfolio` keeps the same last-updated time; no Vercel link file or Hive host record for it is left on the laptop. $0 spent |

**Kill.** If anything is deployed to `portfolio` or any project other than the test one, or the test project is left behind, the gate fails whatever else held.

**Confounds:**
- One run.
- Only the install path is flown. The sign-in is already valid, so renewing it from the phone runs only in unit tests (`tests/test_logins.py` §8), An earlier sign-in by hand during set-up did not finish; the old login stayed.
- Plain static pages; no framework build.

## Amendment before attempt 3 (Nov 15 2026, registered before launch)

Attempt 2 found that Vercel puts a new project's first deployment live, so "send me a link" put the unmerged build at the live address. Fixed: previews are asked for as previews, and on a new project Hive asks him first; on his yes it puts his current version (not the build) live, then sends the build's link. In attempt 3 he taps yes to that question. V2 and V3 are read more strictly:
- **V2:** the link is not the live address, and Hive asked before anything went live.
- **V3:** after "send me a link" and after the refused "put it live", the live plans page does not show the trial line.

V1, V4-V6 and the kill are unchanged.
