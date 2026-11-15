# Hive as a Telegram-first personal agent: the plan (approved Nov 15 2026)

This follows the capability audit of Nov 15 2026. That audit found:
- **Strong:** the swarm, the guard, the intent work and the Telegram assistant.
- **Missing:** spoken replies, event monitoring, structured memory, encrypted secrets, a sandbox for builders, and any defence against instructions hidden in mail.

## Scope

Telegram is the only interface in this phase, and Hive stays one Python application. A separate `hive pulse` process is allowed.

**Out of scope:** a web dashboard, phone apps, desktop apps, a browser extension, phone calls and telephony, and identity across devices.

## Decisions taken (the owner, Nov 15)

| Question | Choice |
|---|---|
| Memory store | SQLite with FTS5 full-text search, in a file only the owner can read. Secrets are encrypted separately (`hive/vault.py`). |
| Spoken replies | Local Piper by default; an API provider is optional. |
| Google | Plain REST calls with OAuth from Telegram. No Google client libraries. |
| Builders | A Docker sandbox by default where Docker exists. Elsewhere, today's behaviour with a warning. |
| Optional extras | `keyring`, `cryptography` and `ffmpeg`. The base install keeps zero required dependencies. |

## Order

- **P0, security and reliability.**
  - The test-page link leak.
  - Render pairing word.
  - Shell quoting.
  - Encrypted secrets.
  - Timeouts.
  - Main's tests must be readable before anything lands.
  - Builders run without Hive's secrets in their environment.
  - Outside text is marked as data in prompts.
  - An audit log of outward actions.
  - Then the Docker sandbox.
- **P1, structured memory and retrieval.**
  - `hive/store.py` (SQLite, with versioned migrations).
  - Owner profile, preferences, people, projects, facts with source and trust, the full message archive.
  - `recall()` search feeding the replies.
  - "Forget that", correcting a fact, export.
  - The existing `memory.py` API kept as wrappers.
- **P2, Pulse.**
  - A `hive pulse` process, which never reads Telegram.
  - Watchers for mail, calendar (time zones fixed first), payments, builds and deadlines.
  - Triage, notification rules, duplicate suppression.
  - An outbox the listener shares.
- **P3, voice.**
  - `voice.synthesize`, `Channel.send_voice`.
  - Voice in gets voice out, unless the reply carries links, numbers or buttons.
- **P4, tools.**
  - A registry with a risk level on each tool, and `policy.authorize`.
  - Native tool calls on the API path.
  - Model tiers by task.
  - `assistant.py` split into modules.
- **P5, integrations.**
  - Gmail, Calendar and Drive (`drive.file`) over REST with the smallest scopes.
  - Idempotent sends through an outbox.
  - Real-account gates.

Each phase keeps the lab's rules: predictions before any live run, results scored, and BRAIN, QUEUE and research_to_product updated in the same commit.
