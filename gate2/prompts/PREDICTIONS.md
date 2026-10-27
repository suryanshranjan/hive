# Gate 2 predictions, registered before launch (Oct 27 2026)
Setup: 3 swarms (2, 6, 12 long-lived workers), same seed (Arm A engine + 113 new categories), 60-minute cap, run concurrently.
1. Tokens per landed task follow c_task + c_on * N / T with c_on ~ 101k, c_task ~ 5k (fitted in Gate 1).
   If all ~100 failing categories land: N=2 ~ 7k, N=6 ~ 11k, N=12 ~ 17k per task. Kill: off by more than 1.5x in either direction.
2. Throughput (tasks landed per minute) grows sublinearly: N=12 / N=2 ratio about 3 to 4, not 6 (critical paths: window, JSON, date cores).
3. Rebase conflicts per landing rise roughly as kappa * (N - 1) with kappa ~ 0.15: about 0.15, 0.75 and 1.6.
4. No gaming: visible and hidden (2,260 tests, disjoint seeds) pass rates stay within 2 points at every commit.
5. Long sessions grow per-task cost: per-worker tokens rise faster than linearly in tasks for workers with 15+ tasks (Gate 1 breaker-arm builders were 1.48x the linear model).
