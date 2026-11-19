# Adaptive tasks, browser tools and recurring work

Hive can now choose one tool, inspect its result, revise its approach, and continue.
This is an opt-in implementation with deterministic regression evidence. It has not
been benchmarked against Grok or qualified with a live model and real accounts.

## Use it from Telegram

Keep `hive listen` running and send:

```text
agent: Find Asha's latest email. If the first search misses, try the subject "catering". Draft and send a reply confirming Thursday.
chat: Explain what you're waiting for.
tasks
task <id>
resume task <id>
answer task <id>: North region
pause task <id>
cancel task <id>
verify task <id>
resolve task <id> complete
resolve task <id> incomplete
```

The exact recipient and message still require your approval. A task can ask for missing
information and save the answer across restarts. The initial conversation context and
request time are preserved so follow-ups and relative dates remain grounded after resume.
The listener acknowledges requests with a task ID. Use Telegram's Reply gesture on the
specific question to answer a legacy prompt. Ordinary messages enter the queue as new
requests. Two workers can execute across projects, with one active worker per project.
Adaptive questions and approvals release the worker. The listener must remain running
while a separate build or review uses Telegram.

`agent:` works with the default router. To route ordinary assistant requests through the
loop, set `HIVE_ROUTER=adaptive` before starting the listener. Explicit builds, business
goals, status, stop, account connection and shipping retain their existing flows.
`HIVE_ROUTER=plan` still selects the older, fixed, four-step router.

The native catalog includes email search/send, calendar read/create, project memory
search/add/update/forget, business database queries, document retrieval, payment totals,
and build submission/status/result. Business queries use the existing read-only database
adapter. Documents must be registered by name. Memory edits show the exact text for
approval. Configured command sources are excluded from this catalog.
The loop can also use the browser and configured MCP tools. It does not invent missing
capabilities or execute arbitrary host shell commands. An approved build becomes a child
task. The parent releases its worker until the child has a checked result.

### Completion and controls

Pause and cancellation take effect at the next safe boundary. Inspect an in-flight
action with `task <id>`. A lost response leaves the outcome open. Read-only verification
and owner resolution never submit the original action. Owner assessments are recorded
as `owner_confirmed` or `owner_reported_incomplete`. Old successful tasks retain their
historical status.

Use `agent: output: Draft a two-sentence invitation` for a text artifact. This criterion
disables mutations and requires the model to produce the artifact. For an exact Gmail
submission use `agent: send email: {"to":"owner@example.invalid","subject":"Pilot","body":"Hello"}`.
For an exact Calendar change use `agent: create event:` followed by a JSON object with
`title`, offset-aware `start` and `end`, `where`, and `guests`. Each change still needs a
fresh owner approval. A provider readback must match the saved fields. SMTP supplies
evidence of submission only. Delivery to a person's inbox requires separate evidence.

For free-form instructions Hive retains the entire request. A partial receipt, a browser
click, a connector response, or a model's completion proposal leaves the full outcome in
`waiting_verification` when Hive cannot check all of it. The task detail reports the
waiting reason, step outcomes, evidence type and reported model spend.

Tasks default to 12 tool steps, a $2 reported model-cost budget and a 10-minute limit
checked between operations. The Python API accepts up to 40 steps. Cost accounting uses
the model adapter's reported spend; it is not a billing guarantee and one model call can
cross the limit. Repeated operations and oversized context pause the task.

## Connect MCP tools

```text
python -m pip install -e ".[mcp]"
hive mcp add reports https://your-service.example/mcp --token-env REPORTS_TOKEN --read-tool search
hive mcp list
hive mcp refresh reports
hive mcp remove reports
```

Set the named token environment variable on the listener's host. Do not put a token in
the command or URL. HTTP is accepted only for localhost; remote connections require HTTPS.
Discovery uses the official MCP Python v1 SDK and Streamable HTTP, including pagination.
Tools appear as `mcp.reports.search`. Each call opens a bounded session and checks the
discovered input schema. Containerized stdio and gateway OAuth setup are documented in
[Owner control gateway](control_gateway.md). Legacy SSE is outside this release.

Every tool requires an exact-argument approval unless you explicitly list it with
`--read-tool`. Server-supplied read-only hints cannot grant permission. Only mark a tool
read-only if it has no side effects and can safely be repeated after interruption.
Changed connection settings, token or schema invalidate saved decisions. MCP writes are
never automatically retried. A successful response is a connector receipt; Hive cannot
independently verify every third-party tool's effect.

## Browser control

```text
hive browser setup
hive browser enable
hive browser status
hive browser disable
```

Docker must be running. Setup builds the pinned Playwright image. The browser supports
opening a page, reading visible text and controls, clicking, filling a field and pressing
a key. All operations except inspection require approval, including navigation. Click,
fill and press must name the current URL and exactly one matching element.

Chromium runs headless as a non-root user with its own sandbox, resource limits, dropped
outer capabilities and a seccomp profile. Only the Hive package is mounted read-only;
the project, host home, Docker socket and assistant credentials are not mounted. Cookies
and site storage persist in a Docker volume named `hive-browser-profile-<scope hash>`.
These profiles are sensitive and are **not encrypted by Hive's credential vault**. They
remain on this Docker host and are not included in cloud handoff. Disabling browser tools
does not delete profiles.

Public HTTP(S) pages are allowed. Private IPs, file URLs, downloads, service workers,
popups and WebSockets are blocked. For a local development site, explicitly allow its
exact origin, for example `hive browser allow-local http://host.docker.internal:8000`.
This host must resolve from the container. Request-time DNS checks are not an egress
firewall against hostile DNS rebinding. DOM inspection omits input values; page text
and URLs can still contain personal information. Page text is untrusted model input.

The optional headed browser supports mobile takeover through the control gateway.
Cookies persist;
the exact open page is not a recovery checkpoint. Inspect again after a browser restart.

The container follows [Playwright's Docker guidance](https://playwright.dev/python/docs/docker).
`browser-seccomp.json` is derived from the [Playwright profile](https://github.com/microsoft/playwright/blob/v1.58.0/utils/docker/seccomp_profile.json)
with `chroot` allowed so Chromium can initialize its inner sandbox while all outer
container capabilities remain dropped.

## Recurring instructions

```text
every 2 hours: Find new messages about catering and summarize anything needing my attention.
routines
pause routine <id>
enable routine <id>
run routine <id>
```

Intervals range from 5 minutes to 366 days. Each occurrence creates an adaptive task;
the instructions can use any available tool. These are interval schedules, not calendar
cron, webhooks or a general workflow graph. They run in `hive listen`, so the host and
listener must stay on. Missed intervals coalesce into one run. A paused, blocked or
running task prevents another occurrence from overlapping it. Resolve or cancel that
task before the routine continues. `run routine` can run a paused routine once without
reenabling its recurring schedule. Pausing clears a queued manual-run request.

Routine writes still require fresh approval. Schedule state and the next task are saved
in one SQLite transaction; a queued task is reused if the process stops before execution.
Routines use their own interval settings, not Pulse quiet hours.

## Recovery and connection checks

Migration 5 adds task modes, metadata, action links and routines. Completed steps and
observations survive a restart. Safe reads require explicit task resume after interruption.
Unknown writes stay blocked. If the separate action ledger confirms that the write already
succeeded, resume reconciles the receipt and skips the write. Pending MCP/browser approvals
can also complete after restart, provided their configuration and expiry still match.

Business-goal build plans save the approved steps, owner answers, current step and
the exact build state. A first build is tagged with its task ID to reject stale build
results. A restart between completed steps resumes the saved branch without rebuilding
earlier steps. An interrupted build step remains blocked for inspection; Hive does not
assume its edits failed or replay it. Migration 7 records parent/child links and build
manifests. Each managed build records its source commit, result branch and commit,
state file, artifact repository and validation results. A matching result with missing
validation evidence is checked again in the sandbox. A missing artifact or changed
branch keeps the build blocked. Use `resume task <child-id>` after restoring the
recorded branch and artifacts. Shipping and deployment retain their own approval flows.

```text
hive verify-services
hive verify-services --live-read-only
```

The optional live probe reads Gmail profile, Calendar list and Telegram bot identity.
It never sends mail/messages or creates events. Missing configuration, missing scope or
failed reads return a nonzero exit status. This verifies connectivity only; successful
send/create/readback and account-switch journeys remain separate release gates.

On this development machine, Google and Telegram configuration were absent. No live
account writes, deployment or model experiment was performed. See [reliability evidence](reliability.md).
