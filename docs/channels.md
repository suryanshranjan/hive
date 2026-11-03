# Channels: where the founder talks to Hive

**Today: Telegram.** It's set up in two minutes with `hive setup`. It handles text, voice notes, pictures, documents, buttons and screenshots.

**Next: the same assistant on more channels.** All of Hive's conversation goes through one small interface, `telegram.Channel`:
- `send(text, buttons)`, `send_photo(path, caption)`;
- `updates()`, which yields text, a picture as `[photo: path]` and a document as `[document: path | name]`;
- `typing()`, `name()`, `recent()`.

A new channel is one class with these methods. Each needs an account that only the owner can create:

| Channel | What the owner creates once | What Hive needs | Note |
|---|---|---|---|
| **WhatsApp** (most founders in India) | A Meta Business account, a WhatsApp Business phone number, and an app in Meta for Developers | The number's ID and a permanent access token. Receiving messages needs a public webhook address, so this runs where Hive runs in the cloud | Messages to him outside a 24-hour window must use approved templates, which suits the morning brief |
| **Slack** (teams) | A Slack app in his workspace with Socket Mode on (no public address needed) | A bot token and an app-level token | Buttons are Slack's interactive blocks. Each founder can get his own channel, e.g. #hive |
| **A web page** | Nothing | A sign-in, so only he sees it | Needs Hive hosted (below) |

**Hosted Hive (no laptop at all).** Today Hive runs on his computer, or on his own AWS machine through `hive cloud --new`. A hosted service would mean "sign in with GitHub, connect Telegram, done". That needs a server we run and a way to hold each founder's Claude or Codex login safely. That's the spin-off's first engineering project, not a switch to flip.
