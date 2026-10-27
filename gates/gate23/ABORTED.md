# Gate 23: first attempt aborted (Oct 27 2026)

23 of 24 workers stopped with HTTP 429 `usage_limit_reached`. The content-keyed team (K12) had already reached all 1,340 visible tests at 10.6 minutes; the baseline (F12) had not (best 1,210). By the lab's rule a run that dies midway is rerun from scratch, so **K2 (the finish ratio) is not scored** and the predictions stand for the rerun.

**Recorded, not scored:** before the stop, K12's content-keyed cache served **337 of 338** lookups from the cache (99.7%), against 61% and 58% for the commit-keyed caches of Gates 21 and 22. This is a property of the guard's mechanism, not of the race between teams, and it matches the diagnosis from Gate 22 (lock commits caused the misses). K12 had one commit on main that broke 10 passing tests, fixed by the end. Cost of the attempt: $28.97.

Usage note: the swarm workers and the driving session share one account. 24-worker gates (about $30 each) have now hit its limit twice. Rerun this gate on its own, spaced from other runs.
