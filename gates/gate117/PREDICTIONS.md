# Gate 117: predictions (registered before launch, Nov 15 2026)

**Question.** Can a founder with only a phone start Hive on his own Render account, with nobody hosting it for him? This flies the "only a phone" path built on Nov 15 (`render.yaml`, `deploy/render/Dockerfile`, `hive boot`, `telegram.bind_first`; unit-tested in `tests/test_render.py`, never deployed).

**The flight.** On the owner's own Render account, with a new Telegram bot made for this test and an Anthropic API key. All three are kept in `~/.hive/render_test.env` and never in the repo or the chat.
1. `python gates/gate117/render117.py up` makes the same worker the Deploy to Render button makes (Docker, 1 CPU and 2 GB, a 10 GB disk at `/data`, Singapore), and waits for it to go live. Using the API instead of the button lets it be timed and deleted cleanly. The button's form fills the same two settings.
2. The owner sends "hi" to the new bot from his phone, then "set me up", and answers the first steps.
3. `render117.py logs` reads what Hive did on Render.
4. `render117.py down` deletes the service and its disk.

The image was first built locally on Docker Desktop, where the build is checked: `docker build -f deploy/render/Dockerfile`.

| # | Prediction | Kill if |
|---|---|---|
| R1 | The image builds and the worker is live within 15 minutes of `up` | build fails, or not live in 40 min |
| R2 | His first "hi" is answered within 30 s, with the "I'm Hive, and I'm yours now" greeting. The chat is bound to him: a second account messaging the bot is told it belongs to someone else | no reply in 2 min, or a stranger gets in |
| R3 | "set me up" runs on the phone and its first steps work there (who he is, about the business) | setup errors out on Render |
| R4 | A restart (a manual redeploy) keeps his chat bound and his answers: the disk holds | after the restart, the bot asks a new person to bind, or setup starts over |
| R5 | `down` leaves no `hive-g117` service; cost under $0.50 (about 1 hour at Render's list price for 1 CPU, 2 GB, plus the disk) | anything left billing |
| R6 | No secret appears in the repo, in Render's logs as printed by Hive, or in this gate's results | any |

**Not tested here:**
- the phone-browser tap on the Deploy button itself: the API makes the same service;
- GitHub cloning of his product (`HIVE_REPO`): this flight starts an empty project;
- fast replies from another provider.
