# Gate 22: first attempt aborted (Oct 27 2026)

All 24 workers stopped at 6.4 to 7.4 minutes with HTTP 429 `usage_limit_reached` ("session limit, resets 6:20pm UTC"). Neither team finished: F12 reached 900 and S12 1,035 of 1,340 visible tests. By the lab's rule, a run that dies midway is rerun from scratch, so nothing here is scored. The predictions in `prompts/PREDICTIONS.md` stand unchanged for the rerun.

Cost of the attempt: $19.15 at list price. Worker costs and the run log are in `aborted_run/`.

For the record only (not evidence): before the stop, S12's cache had 116 hits and 81 misses (59%), so storing before pushing did not obviously raise the hit rate. Misses may come from the rebase-then-lookup window rather than from late storing.

**To rerun after the limit resets:** host `docker update --cpus 4 <container>`; container `sh gates/gate22/run.sh swarm`; host `docker update --cpus <host cores> <container>`; container `sh gates/gate22/run.sh score`. Space gates out: Gates 10, 21 and 22 together used about $78 of usage within roughly an hour.
