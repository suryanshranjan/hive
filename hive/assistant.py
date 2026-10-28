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

def handle(ch, repo, text, poll=20, apply_build=None, start_build=None, cloud=None):
    """Answer one message from the owner. apply_build(state, rule, ch) updates a build (hive.start.apply_ruling);
    start_build(repo, goal) runs a new build that reports to the phone (hive.start.start, overnight style);
    cloud(repo, on) makes a cloud machine and moves Hive there (on=True), or deletes it (hive.cloud_aws)."""
    low = text.lower().strip()
    if low.startswith('build:') or low.startswith('build '):   # an explicit request needs no model to recognise it
        got = {'intent': 'build', 'rule': text.split(':', 1)[1] if ':' in text else text[6:]}
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
                "while it runs), move this project there, and keep working while your computer is off."
                if on else "☁️ <b>Shall I delete the cloud machine?</b>\n\nBring results back first if you need them; "
                "after this nothing is left running or billing.", html=True,
                buttons=[[('✅ Yes' if on else '🗑 Yes, delete it', 'cld|yes')], [('Not now', 'cld|no')]])
        if telegram._wait(ch, poll, {'cld|yes', 'cld|no'})[1] != 'cld|yes':
            ch.send('Very good. Just say the word.'); return 'not_moved'
        ch.send("🛠 On it. This takes about 5 minutes; I'll tell you when I'm there." if on else '🛠 Deleting it now.')
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
        ch.send(f"🐝 <b>At your service{', ' + telegram.esc(who) if who else ''}.</b>\n\nTell me if you've changed your mind "
                "about anything, give me a new rule, or ask for the status. 🎙 Voice notes work too.", html=True)
        return 'greeting'
    if intent == 'status':
        st = latest_build(repo)
        ch.send('📊 ' + (f"The latest build is on branch hive/{st['name']}. {st.get('check', '')}".strip()) if st else
                'Nothing has been built on this project yet.')
        return 'status'
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
            for text, data, _ in batch:
                try:
                    if text and handle(ch, repo, text, apply_build=apply_build, start_build=start_build,
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
