# Lab note: the guard crashed on the lab container's Python (found Oct 28 2026)

**What.** The guard (`tools/land.py`, from Gate 3 on) extracts a snapshot of main with `tarfile.extractall(..., filter='data')`. That keyword exists only from Python 3.11.4. The Docker lab container (Debian bookworm) has Python 3.11.2, so every call to the guard's main-snapshot step raised `TypeError`. It was found while building Hive v1 (`hive/guard.py`), not by any gate's analysis. It affects every gate run in Docker: 10, 11 to 18, 20 to 24.

**What the workers did.** They noticed and worked around it without being told:
- **Scale gates (10, 21, 22, 23):** in every team a worker committed a fix to main ("fall back when tarfile has no extraction filter") **0.8 to 1.3 minutes** after the start. At most 1 of 34 to 43 landings came before the fix. From then on the guard ran as designed.
- **Intent gates (13 to 24):** most teams never committed a fix. Workers landed through their own workarounds, mostly a wrapper in `/tmp` that dropped the argument and then ran the guard's checks (several reported the regression check's result). Whether every landing ran the regression check cannot be reconstructed from the saved summaries.

**What it changes.**
- **Intent results (hidden pass, gains, ratios): unaffected.** They are scored after the run by hidden suites the workers never saw.
- **"No breaking commit on main" (Gates 21 to 24): still valid as measured outcomes** (they come from replaying every commit), but in intent gates they cannot be credited to the guard alone.
- **Guard speed comparisons (Gates 21 to 23): roughly valid.** Both teams in each gate lost about the same minute to the fix; absolute finish times include it.
- **Guard cache statistics:** count only lookups that ran.

**Unplanned finding.** Silent swarms repaired a broken shared tool within about a minute in every scale team, through the same git workflow, with no supervisor. Observational, not tested.

**Fix.** `hive/guard.py` falls back to plain extraction on Pythons without the keyword; `tests/test_guard.sh` runs on Python 3.11.2. The lab's frozen gate tools are left as they were run.
