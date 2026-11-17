# Hive

**Run your company from your phone.** Tell Hive what you want for the business, in plain words. It works out what to change, builds it with AI coding agents, shows you the result, and prepares a tested branch for review. It also helps with connected mail, calendars and data, remembers your decisions, and answers on Telegram in text or by voice.

Hive now supports tasks that **inspect a tool's result, change approach, and continue**. Connect MCP tools, enable an isolated browser, schedule recurring instructions, and pick up saved work after a restart.

[Get started](#quick-start) · [Adaptive tasks](#adaptive-tasks) · [Connect tools](#connect-tools) · [Recurring work](#recurring-work) · [Validation](#validation-and-current-limits) · [Research](#research-behind-hive)

**Current status:** adaptive execution is opt-in. The new runtime has passed local regression, MCP protocol and Chromium fixture tests. Live-model behavior, real accounts and authenticated browser workflows still need qualification. [Evidence and remaining checks](docs/reliability.md).

## What you can do

| You want to… | Say this on Telegram | What Hive does |
| --- | --- | --- |
| Improve the business | "I want more creators signing up this month" | Reads your product, proposes grounded changes, asks for your decisions and builds the approved plan |
| Build a feature | "build: add an invite page" | Builds in an isolated copy, runs checks and prepares the result for review |
| Work across tools | "agent: Find Asha's latest catering email, check Thursday's availability, and summarize both" | Chooses tools, reads their results and revises its approach when information is missing |
| Handle your office | "reply to Asha saying Thursday works" | Uses connected accounts and asks you to confirm the exact outward action |
| Understand your numbers | "how many orders came in this week?" | Answers from connected databases, spreadsheets or APIs through the existing data handlers |
| Keep useful context | "Asha orders 40 lunches every Monday" | Saves business facts and preferences; supports corrections and forgetting |
| Repeat a task | "every 2 hours: summarize new catering enquiries" | Creates a persistent interval routine using the adaptive runtime |
| Recover work | "tasks", then "resume task &lt;id&gt;" | Shows saved progress and continues eligible tasks without repeating completed steps |
| Get timely updates | "tell me about mail from Asha" | Pulse watches configured sources and uses your notification rules and quiet hours |
| Ship a change | "ship it" | Uses the existing approval flow to prepare a pull request; deployment remains a separate flow |

Voice notes and images work with the relevant optional dependencies. Software builders can use Claude Code, Codex or Gemini; the assistant and its connected tools remain separate from those builder processes.

## Quick start

### 1. Install Hive

The installers set up Git, Python, Node.js, Claude Code and Hive as needed.

**Linux / macOS**

```bash
curl -fsSL https://raw.githubusercontent.com/suryanshranjan/hive/main/install.sh | sh
```

**Windows PowerShell**

```powershell
irm https://raw.githubusercontent.com/suryanshranjan/hive/main/install.ps1 | iex
```

Already have Python 3.10+, Git and your model tooling? Install into your Python environment:

```bash
python -m pip install git+https://github.com/suryanshranjan/hive
```

### 2. Connect your phone

```text
claude          # Sign in, then /exit; or configure an API model with hive llm api
hive setup      # Guided setup, including Telegram
```

Run `hive doctor` to check the machine and project. Install and start Docker before using software builds or browser control.

### 3. Start talking

Send **"set me up"** to your Telegram bot. Connect the accounts you want Hive to use, then give it a task.

Run `hive listen` from your project directory to keep the listener active, or use `hive up` to start it in the background. Recurring work needs that host and listener to stay on.

<details>
<summary>Deploy the assistant from a phone with Render</summary>

The repository includes a Render blueprint for chat, memory and connected accounts. Builds and browser control additionally require a host that can run Hive's Docker containers.

1. Create a Telegram bot with **@BotFather** and keep its token.
2. Have an Anthropic API key ready for the configured model backend.
3. Open the deployment form and supply the bot token, model key and a secret pairing word.
4. Send that pairing word to your bot to bind your chat as the owner.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/suryanshranjan/hive)

See [render.yaml](render.yaml) for the configuration. Hosting and model usage are billed by your providers.

</details>

## Adaptive tasks

Prefix a request with `agent:`:

```text
agent: Find Asha's latest catering email. If the first search misses, try "tasting". Check my calendar for Thursday and summarize the options.
```

Hive chooses **one next action**, saves the decision, runs the tool, and feeds the observed result into its next decision. It can try a different search, use another available tool, ask for missing information, or finish with an answer.

The initial native tools cover email search/send, calendar read/create and memory search. Browser and MCP tools extend that catalog. Other existing Hive features, including software builds, retain their own handlers.

| Setting | Behavior |
| --- | --- |
| Default router | Existing intent routing; `agent:` starts an adaptive task explicitly |
| `HIVE_ROUTER=adaptive` | Routes ordinary assistant requests through the adaptive loop; explicit build, status, stop, connection and shipping flows stay available |
| `HIVE_ROUTER=plan` | Uses the older fixed router, with up to four planned steps |

Set `HIVE_ROUTER` in the listener's environment before starting it. Adaptive tasks default to **12 tool steps**, **$2 in reported model spend**, and a **10-minute limit checked between operations**. Spend reporting is an estimate, and an individual call can cross the limit.

External actions require confirmation of their exact arguments. A result with an uncertain side effect stops the task for inspection. [Runtime details and limits](docs/adaptive_tasks.md).

## Connect tools

### MCP integrations

Install the extra in the **same Python environment as Hive**:

```bash
python -m pip install "hive-swarm[mcp] @ git+https://github.com/suryanshranjan/hive"
```

Register your service's MCP endpoint; the URL below is a placeholder:

```text
hive mcp add reports https://your-service.example/mcp --token-env REPORTS_TOKEN --read-tool search
hive mcp list
hive mcp refresh reports
```

Set `REPORTS_TOKEN` in the listener's environment. Discovered tools appear under names such as `mcp.reports.search` and become available to adaptive tasks.

The adapter supports **MCP Streamable HTTP**, using HTTPS for remote services and HTTP for localhost. Tools require approval unless you explicitly mark them read-only with `--read-tool`; server hints cannot grant that permission. Only mark operations that are safe to repeat. Stdio, legacy SSE and interactive OAuth are not implemented.

### Browser control

With Docker running:

```text
hive browser setup
hive browser enable
hive browser status
```

Then ask, for example:

```text
agent: Open https://example.com and summarize the visible page.
```

Hive can open pages, inspect text and controls, click, fill fields and press keys. Navigation and interactions require approval; inspecting the current page is a read. Chromium runs as a non-root user in a dedicated container with its sandbox enabled. Cookies and site storage persist in a separate profile volume.

This is headless browser control. Interactive login takeover, CAPTCHA solving and screenshot reasoning are not included. Private network addresses are blocked by default; an exact development origin can be enabled with `hive browser allow-local`. [Browser isolation and profile details](docs/adaptive_tasks.md#browser-control).

## Recurring work

Schedule an instruction from Telegram:

```text
every 2 hours: Find new catering emails and summarize anything needing my attention.
routines
pause routine <id>
enable routine <id>
run routine <id>
```

Each occurrence creates an adaptive task using the tools available at that time. Intervals range from **5 minutes to 366 days**. Missed intervals coalesce into one run; an unfinished task prevents overlapping occurrences. External actions still need fresh approval.

Schedules persist across restarts, but execute only while `hive listen` is running. These are interval schedules; calendar cron, webhooks and workflow graphs are not included. Routine timing is separate from Pulse quiet hours.

## Recover saved work

| Telegram command | Purpose |
| --- | --- |
| `tasks` | List recent tasks for the current owner, chat and project |
| `task <id>` | Inspect steps, outcomes and current state |
| `resume task <id>` | Continue a queued or paused task |
| `answer task <id>: your answer` | Supply information requested by an adaptive task |
| `cancel task <id>` | Cancel a task that is not currently executing; earlier effects remain |

SQLite stores decisions, observations, owner answers and progress. Business-goal plans also save their approved steps and exact build state, so a restart between steps resumes the saved build instead of starting over.

Completed steps are skipped. Interrupted reads can resume explicitly. Interrupted writes stay blocked unless a confirmed receipt in the action ledger establishes success. A changed account or tool configuration invalidates the saved decision. Mid-build uncertain effects and moves to a different project path still need qualification.

## Controls and privacy

- **Review external actions.** Native mail/calendar writes and adaptive browser/MCP actions use persisted proposals with exact arguments and single-use approvals. Owner-marked MCP reads are exempt from approval.
- **Keep source authority separate.** Retrieved mail, documents, browser pages and tool output are treated as untrusted data. They cannot grant permission to act.
- **Isolate builders.** Software execution requires Docker. Builders receive their worktree, shared build state and required model access; the assistant's unrelated credentials are excluded.
- **Preserve uncertain outcomes.** Lost responses do not trigger blind retries of writes. The action ledger records proposals and outcomes; task checkpoints record progress.
- **Protect stored data.** Assistant credentials use Hive's encrypted vault. Memory, task arguments and results contain personal data and require private backups. Browser profiles live in Docker volumes and are **not encrypted by Hive's vault**.

Hive stores assistant state under `~/.hive/` on the machine running it. Relevant task context can be sent to your configured model and connected services. Browser profiles remain on their Docker host and are not included in cloud handoff. [More on boundaries and recovery](docs/reliability.md).

## Validation and current limits

Local results recorded **November 17, 2026**:

| Check | Result |
| --- | --- |
| Full Docker regression: 40 Python and 8 shell suites | **48/48 suites passed** |
| Final focused regression selection | **9/9 suites passed** |
| Expanded adaptive, scheduling and build-recovery tests | **22/22 passed on Windows and Docker** |
| Official MCP client against a local HTTP fixture | **5/5 passed** |
| Real Chromium against a local site, with external networking disabled | **3/3 passed** |
| Browser worker communication and mount boundaries | **1/1 passed** |

These checks use controlled fixtures, stand-in models and local services. They do not establish production reliability, live-model task quality or superiority over another assistant. Real Google/Telegram accounts, external MCP services, authenticated browser flows, cloud recovery and voice quality still need qualification. [Commands, evidence and remaining checks](docs/reliability.md).

Check connection readiness without sending messages or creating events:

```text
hive verify-services
hive verify-services --live-read-only
```

The live probe reads Gmail profile, Calendar list and Telegram bot identity. It checks connectivity; send/create/readback journeys need separate validation.

## For developers

```bash
git clone https://github.com/suryanshranjan/hive
cd hive
python -m pip install -e ".[mcp]"
```

| Command | Purpose |
| --- | --- |
| `hive` | Build through a terminal conversation |
| `hive start --overnight` | Build while questions wait for later review |
| `hive morning --phone` | Review overnight decisions on Telegram |
| `hive start --agent codex` | Select a builder; Claude, Codex and Gemini are supported |
| `hive google setup` | Configure Google account access |
| `hive access add --db <read-only-connection>` | Connect a database |
| `hive brain add docs/` | Add business documents |
| `hive memory search <words>` | Inspect saved business knowledge |
| `hive pulse status` | Inspect proactive notification settings |
| `hive audit` | Inspect recorded actions |
| `hive doctor` | Check local readiness |

Use `hive --help` and each command's `--help` for details. Optional Python extras include `voice`, `speech`, `memory`, `data`, `api` and `mcp`; see [pyproject.toml](pyproject.toml).

Run the full regression suite in the dedicated test container using the commands in [the verification guide](docs/reliability.md#repeatable-verification). Browser and worker isolation checks run separately on a Docker host. Do not enable the fixture-only `IS_SANDBOX=1` setting to run project code on the host.

Model, hosting and connected-service usage are billed by your providers. Hive reports build costs and supports budgets; estimates and reported spend are not guarantees of provider billing.

## Research behind Hive

Hive also publishes preregistered experiments on coding agents, coordination and how owners communicate intent. Predictions and failure conditions are recorded before a run; results include failures. Engineering changes based on code audits and regression fixtures are labelled separately.

| Finding | Evidence |
| --- | --- |
| Coding agents can coordinate through Git without a message board | [Gate 43](gates/gate43/RESULTS.md) |
| Owner review of a concrete description can expose rules an interview misses | [Gate 42](gates/gate42/RESULTS.md) |
| Mixed Claude and Codex teams can build together | [Gate 47](gates/gate47/RESULTS.md) |
| A full swarm is not always worth its cost on technical tasks | [Gate 89](gates/gate89/RESULTS.md) |
| Retrieval and explicit corrections improve business memory on mock cases | [Gate 118](gates/gate118/RESULTS.md), [Gate 119](gates/gate119/RESULTS.md) |

Many experiments use simulated owners, mock companies and small numbers of runs. Those results inform design; they do not guarantee the same outcome for a new business. Real-company experiments publish aggregate results without private code, rules or owner answers.

[BRAIN.md](BRAIN.md) records findings, confidence and open questions. [Research to product](docs/research_to_product.md) maps evidence to implementation. [The lab queue](lab/QUEUE.md) records completed work and what comes next.

## Repository map

| Path | Contents |
| --- | --- |
| [hive/](hive/) | Telegram assistant, builder orchestration, account integrations and memory |
| [hive/agent.py](hive/agent.py), [hive/tasks.py](hive/tasks.py) | Adaptive execution and durable task checkpoints |
| [hive/runtime_tools.py](hive/runtime_tools.py), [hive/connectors.py](hive/connectors.py) | Tool schemas, approvals and MCP adapters |
| [hive/browser.py](hive/browser.py), [hive/browser_worker.py](hive/browser_worker.py) | Browser container and Playwright worker |
| [hive/routines.py](hive/routines.py), [hive/buildplans.py](hive/buildplans.py) | Recurring instructions and saved business-goal plans |
| [tests/](tests/) | Regression fixtures, protocol tests and real container checks |
| [docs/](docs/), [gates/](gates/), [lab/](lab/) | Usage guides, research evidence and experiment tooling |

## License

MIT. See [LICENSE](LICENSE).
