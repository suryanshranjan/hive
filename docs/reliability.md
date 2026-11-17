# Reliability milestone

Implementation milestone, November 17, 2026. Telegram remains the only user interface.
This is a reliability milestone, not completion of the personal-assistant roadmap.

## Runtime boundaries

- `policy.RequestContext` carries transport authority, project, update ID and archived source ID.
  Retrieved documents cannot turn an outside request into an owner request.
- `actions` stores immutable proposals, a payload hash, account binding, expiry and the
  approving chat/message. Mail/calendar, shipping, preview/live deployment and cloud
  callbacks use these approvals. Older undo/test-page paths still need consolidation.
- An action moves from proposed to approved to executing and then a recorded outcome.
  An interrupted or ambiguous action becomes unknown and is never automatically replayed.
  Mail/calendar proposals can resume after listener restart; other proposals need reproposal.
- Gmail and Calendar writes require provider readback. SMTP cannot provide equivalent
  delivery verification. A successful SMTP submission does not prove recipient delivery.

## Memory and notifications

`store` is the SQLite authority. Migration 3 adds proposals/events, extraction jobs,
notification claims, received Telegram updates and deletion tombstones. It separates
deadline `due_at` from factual expiry. Legacy JSON imports once and becomes a derived
export. Corrections preserve the old fact's history; forgetting removes retrieval sources
and suppresses late extraction from the forgotten source.

`memory_jobs` processes extractions in order, retains failures across restarts and stops
retrying malformed extractions after three attempts. Explicit owner facts can be personal
or project-scoped. Document-derived facts remain outside evidence. Semantic retrieval
still needs the optional embedding dependency/model; keyword retrieval works without it.

Pulse commits findings and source checkpoints together. A dispatcher claims events before
sending, records delivery receipts and retains ambiguous deliveries for inspection.
Digest entries are consumed only after confirmed delivery. This conservatively avoids
duplicates; it does not promise exactly-once Telegram delivery. Account polling remains
bounded, so a very large backlog needs explicit catch-up qualification.

Telegram stores a fetched update batch before advancing its remote offset and consumes
one update at a time. Voice transcripts now have owner/source provenance, and temporary
downloaded audio is removed after transcription. Actual Hindi-English accuracy is unqualified.

## Isolation and secrets

Host execution fallback is disabled. Builder image `hive-builder:3` includes required
encryption dependencies. A worker sees Hive's package read-only, its own writable worktree,
shared Git/questions and its model login; unrelated assistant secrets are not passed in.
Containers drop capabilities, set resource limits, use an init process and prevent new
privileges. Project verification runs without network; timed-out containers are removed.
Builder network access remains enabled for models/packages and is not an exfiltration firewall.

Encryption is required for credential writes. Private paths use POSIX permissions or
Windows ACLs. Action arguments and the memory database contain personal data and need
private backups; the action/event records are not a tamper-proof audit service.

Cloud handoff snapshots SQLite with its backup API. Return verifies a consistent snapshot
and compares the local state with the recorded handoff baseline before restoring it.
Local divergence refuses automatic restore/deletion and preserves both copies. A destination
containing memory refuses another handoff. This is single-owner transfer, not concurrent
synchronization. SSH handoff, active-listener quiescence and credential changes across
machines still require real-machine qualification.

## Repeatable verification

Build test dependencies inside Docker, then run from a disposable source copy. The source
mount is read-only. `/tmp` is executable only inside this network-disabled fixture container
because packaging tests execute newly installed command scripts there.

```powershell
docker build -t hive-builder:3 deploy/builder
docker build -t hive-reliability-test:local -f deploy/test/Dockerfile deploy/test
docker run --rm --init --name hive-regression --network none --cap-drop ALL --security-opt no-new-privileges --pids-limit 256 --memory 2g --cpus 2 --tmpfs /tmp:rw,nosuid,exec,size=1g --mount "type=bind,source=$($PWD.Path),target=/source,readonly" --env PYTHONPATH=/source hive-reliability-test:local
```

This runs 37 Python scripts (including the failure-journey unittest suite) and eight shell
suites, without model calls or real service credentials. Optional speech/embedding model
checks are skipped unless their dependencies are installed. The fixture-only `IS_SANDBOX=1`
setting is suitable inside this container and must not be used to enable host execution.

Run `python -B tests/test_sandbox_docker.py` on the Docker host separately to check actual
worker mounts, secret filtering, sibling write protection and timeout cleanup. For selected
fixtures, use `python -B tests/run_reliability.py --fixture-execution --suite reliability`;
native Windows ACL checks require the normal user token.

### Results recorded November 17, 2026

- Full Docker fixture run: **45/45 suites passed** (37 Python scripts and eight shell suites).
  This includes **40 unittest failure journeys** in `tests/test_reliability.py`.
- Final targeted Docker rerun: reliability, installed command/doctor and cloud return,
  **3/3 suites passed**.
- Windows targeted run: reliability, Telegram and voice fixtures, **3/3 suites passed**.
- Real Docker host check: worker mount/secret boundaries and timed-out project-container
  removal both passed against `hive-builder:3`.
- All 66 application/runner Python files parsed; `git diff --check` passed. CI YAML parsed
  locally. Hosted GitHub Actions was not part of this local verification.

These results use stand-in services and controlled audio/model fixtures. They do not
measure live-account operation, Hindi-English recognition accuracy or TTS quality.

## Remaining release gates

1. Real Gmail/Calendar and Telegram journeys, including ambiguous provider outcomes and
   account changes; no mock test establishes account readiness.
2. Quiesced, authenticated cloud handoff/return with conflict recovery on real machines.
3. Persistent general multi-step execution and recovery. `HIVE_ROUTER=plan` stays opt-in.
4. Measured Hindi-English transcription, TTS quality and end-to-end voice latency.
5. Consolidation of remaining legacy action handlers and independent adversarial tests
   for retrieved content, filesystem reads and model-tool boundaries.
