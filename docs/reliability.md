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
  Mail/calendar and adaptive MCP/browser proposals can resume after listener restart;
  other proposals need reproposal.
- Gmail and Calendar writes require provider readback. SMTP cannot provide equivalent
  delivery verification. A successful SMTP submission does not prove recipient delivery.

## Saved assistant tasks

Migration 4 stores the general router's plans, intermediate results and step checkpoints.
`tasks` lists the five latest tasks for this owner, chat and project; `task <id>` shows the
steps; `resume task <id>` explicitly continues a queued or paused task. These commands work
with every router setting. `HIVE_ROUTER=plan` remains opt-in and retains its four-step limit.

Completed steps are skipped on resume, and their saved results feed dependent steps.
Redelivery of the same request/update reuses its task even if the model proposes different
steps. An atomic claim prevents two executors from running one task. Connected mail/calendar
configuration is hashed at creation and checked again before execution; a changed account
blocks the task. Existing per-action approvals still apply to every external write.

On listener restart, an interrupted `mail_find` or `calendar_check` can be retried on explicit
resume. An interrupted mutation has an unknown outcome and blocks the chain without replay.
On explicit resume, a confirmed success in the linked action ledger reconciles the task
without repeating the write. Unconfirmed effects remain blocked.
Other failed steps also stop the chain. Invalid references to a later step refuse the entire
plan before any step starts. Task records contain private request and result data in SQLite.

Migration 5 extends checkpoints to adaptive tasks, linked action receipts, recurring
instructions and business-goal build plans. `agent:` selects an observe/act/replan loop;
`HIVE_ROUTER=adaptive` makes it the ordinary assistant route. Build plans retain their
approved steps, owner answers and exact build state. Safe read failures can trigger a new
approach; uncertain writes cannot. Cross-machine project-path remapping remains unsupported.
Setup, controls and limits are in [Adaptive tasks](adaptive_tasks.md).

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

Recent conversation storage preserves the complete last 32 entries. Model context uses a
24,000-character budget, retaining the newest contiguous entries and marking omissions.
An oversized latest entry keeps its beginning and ending with an explicit middle-omission
marker; the stored entry stays complete. Existing entries previously cut at 600 characters
cannot be restored from the legacy conversation file by this change.

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

This runs 40 Python scripts (including adaptive tasks and MCP protocol fixtures) and eight shell
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

### Task and context follow-up, November 17, 2026

- Added 19 tests in `tests/test_tasks.py`: restart checkpoints and result dependencies,
  interrupted writes, explicit read retries, duplicate deliveries, concurrent claims,
  owner/chat/project boundaries, account changes, invalid plan references, schema upgrade,
  resumed-send approval, and long/bounded/reloaded conversation context.
- Native Windows run: all 19 tests passed.
- Docker regression selection: tasks, reliability (40 existing failure journeys), router,
  Telegram, store, assistant, tools, memory2 and shell/cloud: **9/9 suites passed**.
- Final Docker selection after account-binding and approval tests: tasks (19 tests), router,
  office, Google, calendar, plan and voice: **7/7 suites passed**.
- Both Docker selections ran with network disabled and a read-only source mount. CI includes
  the new suite; hosted CI and live-account journeys were not run for this follow-up.

### Adaptive runtime follow-up, November 17, 2026

- Full network-disabled Docker regression: **48/48 suites passed** (40 Python, eight shell).
  This run included 17 adaptive recovery tests and five real MCP protocol fixture tests.
- Expanded adaptive suite: **22/22 tests passed on Windows and Docker**, adding interrupted build,
  stale build result, cancellation/approval, paused manual schedules and conversation/date
  context retained across restart.
- Final focused Docker rerun: **9/9 suites passed**, including the expanded 21-test adaptive
  suite before the final conversation/date-context case was added.
- All 124 application/test Python files parsed, CI YAML parsed, and `git diff --check`
  passed. The final adaptive context change also passed its focused Docker rerun.
- Real Chromium in the dedicated browser image, with network disabled and a loopback
  fixture: **3/3 tests passed** for form submission, page/selector checks, private URL
  refusal, omitted input values and persistent cookies.
- Host browser IPC and mount boundary check: **1/1 passed**. Only the package and a fresh
  private profile volume were mounted. The fixture profile was removed afterwards.
- Initial browser execution failed because the seccomp profile conditioned `chroot` on
  an outer capability that Hive drops. Allowing that syscall lets Chromium create its
  inner namespace sandbox without granting the container outer capabilities. The
  browser rerun passed with `chromium_sandbox=True` and all capabilities dropped.
- `hive verify-services --live-read-only`: Google and Telegram both `not_configured`.
  No model calls, live-account writes or deployment. Hosted CI remains unrun.

## Remaining release gates

1. Real Gmail/Calendar and Telegram journeys, including ambiguous provider outcomes and
   account changes; no mock test establishes account readiness.
2. Quiesced, authenticated cloud handoff/return with conflict recovery on real machines.
3. Live-model qualification of adaptive routing, real MCP services, authenticated browser
   sessions and build-plan recovery. Mid-build uncertain effects and cross-machine task
   mapping need qualification. Plan/adaptive routing stay opt-in.
4. Measured Hindi-English transcription, TTS quality and end-to-end voice latency.
5. Consolidation of remaining legacy action handlers and independent adversarial tests
   for retrieved content, filesystem reads and model-tool boundaries.
