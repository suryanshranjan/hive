"""hive listen: Hive stays on the owner's Telegram between builds. The owner can wake it any time and say, in his own
words, that he has changed his mind. Hive finds the earlier ruling this overrides, confirms, updates the kept rulings,
and offers to update the latest build to match. Also: "status", and new rules to keep.

Gate 30: an answer contradicted the founder's own verdict from an hour earlier. People change their minds, so changing
one should be one message, not a new build.

Only one Hive process reads the bot at a time: while a build or review is talking to the owner, the listener steps
aside (see telegram.busy_elsewhere)."""
import glob, json, os, time

from . import explain, memory, telegram

RUNS = os.path.join(os.path.expanduser('~'), '.hive', 'runs')   # where `hive start` keeps its builds

CLASSIFY = """A business owner sent this message to his software assistant, Hive:
"{text}"

Classify it. Reply with JSON only: {{"intent": "build" | "change" | "rule" | "status" | "greeting" | "cloud_on" |
"cloud_off" | "other",
"rule": "the rule he now wants, or for a build, what to build, in plain sentences; otherwise empty"}}
- "build": he asks Hive to build, add or make something in the product.
- "change": he says he has changed his mind, or now wants something different from before.
- "rule": he states a new rule for how the product should behave.
- "status": he asks how things are going.
- "greeting": a hello, or waking Hive up with no request yet.
- "cloud_on": he wants Hive to move to the cloud, or keep working while his computer is off.
- "cloud_off": he wants the cloud machine shut down or deleted."""

RELATED = """A business owner's earlier rulings for his product:
{rulings}

He now says: "{rule}"

Which earlier rulings does this replace, because they are about the same situation and say something different?
Reply with JSON only: {{"replaces": [numbers]}} (an empty list if none)."""

def _who(ch):
    w = ch.name()
    return w[:1].upper() + w[1:] if w else ''

def latest_build(repo):
    """The most recent `hive start` build of this project, or None."""
    homes = sorted((h for h in glob.glob(os.path.join(RUNS, '*'))
                    if os.path.exists(os.path.join(h, 'state.json'))), key=os.path.getmtime)
    for h in reversed(homes):
        st = json.load(open(os.path.join(h, 'state.json')))
        if os.path.abspath(st.get('repo', '')) == os.path.abspath(repo):
            return st
    return None

VOICE = """You are Hive, a business owner's software assistant, in the manner of J.A.R.V.I.S. with Tony Stark: calm,
precise, courteous, quietly confident, with a light touch of dry wit, never servile and never verbose. Address him as
"{who}". Talk like a person, not a report: no labels, no lists, no folder, branch or file names unless he asks for
them; call it "your project". Lead with the one thing that matters to him right now. At most 3 short sentences,
ending with the most useful next step he could take. Use only the facts below; never invent a build, a number or an
event. No technical words.

What you know right now:
{facts}

{task}
Reply with JSON only: {{"reply": "..."}}"""

def facts(repo, ch=None):
    """What Hive knows about this owner's project right now, in plain lines, for its replies."""
    st = latest_build(repo)
    # (no folder name in the facts: given one, it said "your shop project")
    lines = [('Running in the cloud; his computer can be off.' if os.environ.get('HIVE_IN_CLOUD') or
              os.path.abspath(repo).startswith(os.path.join(os.path.expanduser('~'), 'hive-cloud')) else
              'Running on his computer.'),
             (f"Latest build: branch hive/{st['name']}. {st.get('check', '')}" if st else 'Nothing built on this project yet.'),
             f"Standing rules he has given for this project: {len(memory.load(repo))}."]
    note = ch.note() if ch is not None and callable(getattr(ch, 'note', None)) else None
    if note:
        lines.append(f'Happening now: {note}')
    return '\n'.join(lines)

def speak(ch, repo, task, fallback):
    """One message in Hive's own voice (the owner: "like Jarvis handles Tony"); the plain fallback if no model."""
    import threading
    box = {}
    t = threading.Thread(target=lambda: box.update(got=explain.ask_json(
        VOICE.format(who=_who(ch) or 'sir', facts=facts(repo, ch), task=task)) or {}), daemon=True)
    t.start(); t.join(float(os.environ.get('HIVE_VOICE_SECONDS', 8)))   # he is waiting: never long for a nice phrasing
    reply = ((box.get('got') or {}).get('reply') or '').strip()
    if reply:
        ch.send('🐝 ' + telegram.esc(reply), html=True)
    else:
        ch.send(fallback, html=True)

GREETINGS = {'hi', 'hii', 'hello', 'hey', 'hey hive', 'hi hive', 'hello hive', 'yo', 'hola', 'namaste', 'good morning',
             'good evening', 'good afternoon', 'jarvis', 'hive'}

def coalesce(texts):
    """Messages that arrived together are understood together: repeats once, and a bare greeting next to a real request
    needs no reply of its own. Returns (the messages to handle, whether he had to repeat himself)."""
    seen, out = set(), []
    for t in texts:
        k = ' '.join(t.lower().split()).strip(' ?!.')
        if k and k not in seen:
            seen.add(k); out.append(t)
    if len(out) > 1:
        out = [t for t in out if t.lower().strip(' ?!.') not in GREETINGS] or out[-1:]
    return out, len(out) < len(texts)

def handle(ch, repo, text, poll=20, apply_build=None, start_build=None, cloud=None):
    """Answer one message from the owner. apply_build(state, rule, ch) updates a build (hive.start.apply_ruling);
    start_build(repo, goal) runs a new build that reports to the phone (hive.start.start, overnight style);
    cloud(repo, on) makes a cloud machine and moves Hive there (on=True), or deletes it (hive.cloud_aws)."""
    low = text.lower().strip()
    typing = getattr(ch, 'typing', None)
    if callable(typing):
        typing()   # "typing..." at once, as a person would (the owner found it slow)
    if low.startswith('build:') or low.startswith('build '):   # an explicit request needs no model to recognise it
        got = {'intent': 'build', 'rule': text.split(':', 1)[1] if ':' in text else text[6:]}
    elif low.strip(' !.?') in GREETINGS:   # the obvious needs no model: one call less, seconds sooner
        got = {'intent': 'greeting'}
    elif telegram.is_status(text):
        got = {'intent': 'status'}
    else:
        got = explain.ask_json(CLASSIFY.format(text=text)) or {}
    intent, rule = got.get('intent', 'other'), (got.get('rule') or text).strip()
    who = _who(ch)
    if intent == 'build' and start_build:
        ch.send(f"🏗 <b>Shall I build this?</b>\n\n{telegram.esc(rule)}\n\n"
                "<i>I'll work on copies, then bring you the decisions to check.</i>", html=True,
                buttons=[[('🚀 Yes, build it', 'bld|yes')], [('Not now', 'bld|no')]])
        if telegram._wait(ch, poll, {'bld|yes', 'bld|no'})[1] != 'bld|yes':
            ch.send('Very good. Just say the word.'); return 'not_built'
        ch.send("🛠 Right away. I'll message you as it goes; text 'status' any time.")
        start_build(repo, rule)
        return 'built'
    if intent in ('cloud_on', 'cloud_off') and cloud:
        on = intent == 'cloud_on'
        ch.send("☁️ <b>Shall I move to the cloud?</b>\n\nI'll make a machine on your AWS account (about $0.09 an hour "
                "while it runs), move this project there, and keep working while your computer is off.\n\n<i>With your "
                "Claude login, builders can work there too; without it, I can only talk with you there.</i>"
                if on else "☁️ <b>Shall I delete the cloud machine?</b>\n\nBring results back first if you need them; "
                "after this nothing is left running or billing.", html=True,
                buttons=([[('⭐ Yes, with my Claude login', 'cld|yes')], [('Yes, without it (chat only)', 'cld|bare')],
                          [('Not now', 'cld|no')]] if on else [[('🗑 Yes, delete it', 'cld|yes')], [('Not now', 'cld|no')]]))
        choice = telegram._wait(ch, poll, {'cld|yes', 'cld|bare', 'cld|no'})[1]
        if choice not in ('cld|yes', 'cld|bare'):
            ch.send('Very good. Just say the word.'); return 'not_moved'
        if on:   # (for a delete, say nothing until it is known to be possible: it said "Deleting it now", then that it can't)
            ch.send("🛠 On it. This takes about 5 minutes; I'll tell you when I'm there.")
        try:
            rc = cloud(repo, on, choice == 'cld|yes')   # with the login: builders can work there
        except TypeError:
            rc = cloud(repo, on)
        if rc == 5:   # this copy runs in the cloud, without the owner's AWS keys (on purpose): it cannot delete itself
            ch.send("☁️ I'm the copy running in the cloud, and I don't hold your AWS keys, on purpose, so I can't shut "
                    "myself down. On your computer, run <code>hive cloud --stop</code>: it deletes this machine and "
                    "everything on it.", html=True)
            return 'cloud_elsewhere'
        if rc != 0:
            ch.send("⚠️ That didn't work. On your computer, run `hive cloud --new` (or `--stop`) to see why.")
            return 'cloud_failed'
        if not on:
            ch.send('✅ Deleted. Nothing is left running.')
        return 'moved' if on else 'cloud_off'
    if intent == 'greeting':
        speak(ch, repo, f'He just said: "{text}". Greet him and say, in a sentence, where things stand.',
              f"🐝 <b>At your service{', ' + telegram.esc(who) if who else ''}.</b>\n\nTell me if you've changed your "
              "mind about anything, give me a new rule, or ask for the status. 🎙 Voice notes work too.")
        return 'greeting'
    if intent == 'status':
        st = latest_build(repo)
        speak(ch, repo, f'He asked: "{text}". Tell him exactly where things stand.',
              telegram.esc('📊 ' + ((f"The latest build is on branch hive/{st['name']}. {st.get('check', '')}".strip())
                                    if st else 'Nothing has been built on this project yet.')))
        return 'status'
    if intent == 'other' and len(text.split()) < 5:   # small talk or a short question: answer it, in his assistant's voice
        speak(ch, repo, f'He said: "{text}". Answer him helpfully from what you know; if you cannot, say so and say what '
              'you can do.', "🐝 I'm here. Tell me what to build, a change of mind, or ask for the status.")
        return 'chat'
    if intent not in ('change', 'rule'):
        ch.send("📝 Noted. Shall I keep this as a standing rule for the builders?",
                buttons=[[('Yes, keep it as a rule', 'as|rule')], [('No, just a note', 'as|note')]])
        if telegram._wait(ch, poll, {'as|rule', 'as|note'})[1] != 'as|rule':
            ch.send('Very good.'); return 'note'
    rulings = memory.load(repo)
    listing = '\n'.join(f'{n}. {r["text"]}' for n, r in enumerate(rulings, 1))
    found = (explain.ask_json(RELATED.format(rulings=listing, rule=rule)) or {}).get('replaces', []) if rulings else []
    old = [n - 1 for n in found if isinstance(n, int) and 1 <= n <= len(rulings)]
    if old:
        before = '\n'.join(f'- {rulings[i]["text"]}' for i in old)
        ch.send(f"🔄 <b>Understood. Earlier you ruled:</b>\n{telegram.esc(before)}\n\n<b>Now:</b> {telegram.esc(rule)}\n\n"
                "Shall I replace the earlier ruling with this?", html=True,
                buttons=[[('🔄 Replace it', 'chg|replace')], [('Keep both', 'chg|both')], [('Cancel', 'chg|cancel')]])
        choice = telegram._wait(ch, poll, {'chg|replace', 'chg|both', 'chg|cancel'})[1]
        if choice == 'chg|cancel':
            ch.send('Of course. Nothing changed.'); return 'cancelled'
        if choice == 'chg|replace':
            memory.replace(repo, old, rule)
        else:
            memory.add(repo, rule, 'changed')
    else:
        memory.add(repo, rule, 'owner')
        ch.send(f"📌 Noted as a standing rule: {rule}")
    st = latest_build(repo)
    if st and apply_build:
        ch.send(f"Shall I update the latest build (branch hive/{st['name']}) to follow it?",
                buttons=[[('Yes, update it', 'upd|yes')], [('Not now', 'upd|no')]])
        if telegram._wait(ch, poll, {'upd|yes', 'upd|no'})[1] == 'upd|yes':
            ch.send("🛠 Right away. I'll let you know the moment it's done.")
            apply_build(st, rule, ch)
            return 'applied'
    ch.send('✅ Very good. The builders will follow it from the next build.')
    return 'kept'

def listen(repo='.', poll=10, apply_build=None, until=None, start_build=None, cloud=None, ch=None):
    """Stay on the owner's Telegram between builds and handle whatever he sends. Ctrl+C to stop."""
    if ch is None:
        cfg = telegram.load()
        if not cfg:
            print('Not connected yet: run hive telegram setup.'); return 1
        ch = telegram.Channel(cfg, listener=True)
    print("Listening on Telegram. Tell Hive anything, any time: a change of mind, a new rule, or 'status'. Ctrl+C to stop.",
          flush=True)
    try:
        while not (until and until()):
            if telegram.busy_elsewhere():
                time.sleep(poll); continue   # a build or review is talking to the owner: step aside
            try:
                batch = ch.updates(timeout=poll)
            except Exception as e:   # never go silent on the owner: report, wait, listen again
                print(f'Telegram error, retrying: {e}', flush=True); time.sleep(poll); continue
            texts, repeated = coalesce([t for t, _, _ in batch if t])
            if repeated and texts:   # he had to say it more than once: Hive was slow or away
                try:
                    ch.send(f"🐝 My apologies for the wait{', ' + ch.name() if ch.name() else ''}; I have all your messages "
                            "now. Here it is, once.")
                except Exception:
                    pass
            for text in texts:
                try:
                    if handle(ch, repo, text, apply_build=apply_build, start_build=start_build,
                              cloud=cloud) == 'moved':
                        print('Hive now runs in the cloud and reads Telegram there; this listener stops.', flush=True)
                        try:   # mark what this listener handled as read, so the cloud copy starts clean
                            ch.api('getUpdates', offset=ch.offset, timeout=0)
                        except Exception:
                            pass
                        return 0   # one reader of the owner's chat at a time
                except Exception as e:   # one message going wrong must not stop the listener
                    print(f'Could not handle "{text}": {e!r}', flush=True)
                    try:
                        ch.send("⚠️ Sorry, something went wrong with that one. I'm still here; try again, or say it "
                                "another way.")
                    except Exception:
                        pass
    except KeyboardInterrupt:
        pass
    return 0
