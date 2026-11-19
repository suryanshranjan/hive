# Schedules and portable recovery

## Scheduling from Telegram

```text
every 2 hours: summarize the open invoices
daily at 17:30 Europe/London: draft the daily summary
weekly on Mon, Fri at 09:00 America/New_York: check upcoming renewals
weekdays at 09:00 Asia/Kolkata: prepare today's brief
on pulse.payments where {"priority":{"gte":2}}: review the payment alert
on webhook.invoice where {"status":"overdue"}: review the invoice
```

Hive shows the normalized calendar schedule and the next three local dates with UTC offsets before saving. A nonexistent local time is skipped. When a local time occurs twice, only the first occurrence runs. Downtime coalesces missed clock occurrences into one task. Each matching event ID is queued once per routine. A pending approval, pause, child build or unresolved outcome holds subsequent runs.

Use `routines`, `pause routine <id>`, `enable routine <id>` and `run routine <id>` to manage a routine. Each outward action still requires its own approval.

## Event sources

Pulse publishes `pulse.mail`, `pulse.calendar`, `pulse.payments` and `pulse.deadlines` with fields `title`, `body`, `priority` and `ref`. Filters require every field to match. They support scalar equality and numeric `gte` or `lte`. Event fields enter the model's untrusted observations. The saved owner instruction supplies authority.

Configure the HTTPS gateway, supply a shared signing key through the named environment variable on the sender and Hive host, then register the webhook. [Gateway setup](control_gateway.md).

```sh
hive gateway webhook invoice --project . --key-env INVOICE_SIGNING_KEY --field status --field invoice_id
```

Send a JSON object of declared scalar fields to `POST /events/invoice`. Set `X-Hive-Event-ID` to a stable source ID and `X-Hive-Timestamp` to Unix seconds. Set `X-Hive-Signature` to the lowercase hex HMAC-SHA256 of the exact timestamp bytes, a period, the event ID bytes, another period and the original body bytes. The gateway accepts timestamps within five minutes. Retrying the same ID returns acceptance without creating another occurrence.

## Moving a project

Use the existing approved cloud handoff or the owner's `hive cloud --to user@host` command from a clean, named Git branch. Use `--no-start` to stage a destination before starting its listener. The destination needs the same schema version. The source records a stable project ID and memory alias. The manifest identifies the destination path, repository roots, local branch tips, task checkpoints and portable build artifacts. The source installation stops execution while the shared database is away. Pause other executing tasks and return any browser takeover first. When startup is requested, Hive checks the receiving installation's handoff record and live reader before reporting that it is listening.

At startup the destination checks its path, repository identity, branch, checkpoints, account and artifact bindings. A matching task retains its ID and progress. A changed account or missing build artifact is visible as blocked. Browser sessions start with a fresh profile on the receiving installation. Re-establish login and review blocked requests there.

Use `hive cloud pull --from user@host` on the original checkout to return ownership. Hive quiesces the remote copy, fetches its branches under `refs/remotes/hive-cloud/`, and compares the local checkout and database with the saved baseline. It imports eligible result branches with compare-and-swap updates. Divergence stops automatic restoration. The local database and the returned database snapshot under `~/.hive/returns/` remain available for inspection. On a completed round trip the former host stays fenced.

Migration 9 records schedule definitions and event IDs. Migration 10 introduces install-local path mappings and handoff fences. The private `host-id` stays on its installation. Existing memory continues to use its previous namespace.
