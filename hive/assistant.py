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

CLASSIFY = """You are Hive, a business owner's software assistant, reading his newest message in the context of your
conversation. The conversation so far (oldest first):
{history}

His newest message: "{text}"

What does he mean? Read it as a person would, using the conversation: "yes" or "go ahead" answers the last thing you
proposed; "I already told you" or "that one" points back to what he said before; a short correction ("no, Sunny Shop
Creators") changes what you just proposed. Reply with JSON only:
{{"intent": "build" | "change" | "rule" | "status" | "greeting" | "cloud_on" | "cloud_off" | "reply",
"rule": "for a build, exactly what to build (taken from the conversation if he points back to it); for a change or a
rule, the rule he now wants; otherwise empty",
"confirmed": true if he is agreeing to do what you just proposed (or clearly telling you to go ahead now), else false}}
- "build": he wants something built, added or made in the product (including agreeing to, or correcting, a build you
  proposed).
- "change": he has changed his mind about an earlier rule.
- "rule": he states, plainly and on purpose, a rule for how the product should behave from now on.
- "status": he asks how things are going.
- "greeting": a hello, with no request yet.
- "cloud_on" / "cloud_off": move Hive to the cloud / shut the cloud machine down.
- "reply": anything else: a question, a complaint, frustration, small talk. Never a rule."""

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
    if _building():
        lines.append(_building())
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

def read(ch, text):
    """What the owner means by his newest message, read in the context of the conversation (Gate 38 live test: "Yes",
    "I already told you" and a corrected request were each read alone, and went wrong)."""
    history = ch.recent() if hasattr(ch, 'recent') else ''
    return explain.ask_json(CLASSIFY.format(history=history, text=text)) or {}

BUILD = {}   # the build running in the background: {'proc', 'goal', 'started', 'log'}
CURRENT = {}   # the owner's chat, for news from a background build

def background_build(repo, goal, ch=None):
    """Run `hive start` for this goal in the background, so Hive keeps answering him; if it stops, tell him why at once
    (a cloud build stopped on "unsaved changes", and only the server's log knew)."""
    import subprocess, sys, tempfile, threading
    ch = ch or CURRENT.get('ch')
    gf = tempfile.NamedTemporaryFile('w', suffix='.md', delete=False); gf.write(goal); gf.close()
    log = os.path.join(os.path.expanduser('~'), '.hive', 'build.log')
    os.makedirs(os.path.dirname(log), exist_ok=True)
    import shlex
    cmd = (shlex.split(os.environ['HIVE_BUILD_CMD']) if os.environ.get('HIVE_BUILD_CMD') else   # tests: a stand-in
           [sys.executable, '-m', 'hive', 'start', '--overnight', '--goal', gf.name])
    proc = subprocess.Popen(cmd, cwd=repo,
                            stdout=open(log, 'w'), stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    BUILD.update(proc=proc, goal=goal, started=time.time(), log=log)

    def watch():
        rc = proc.wait()
        if rc != 0 and ch is not None:
            lines = [l.strip() for l in open(log, encoding='utf-8', errors='replace').read().splitlines() if l.strip()]
            why = lines[-1] if lines else 'no reason was given'
            try:
                ch.send(f"⚠️ <b>The build stopped before it finished.</b>\n\n{telegram.esc(why)}\n\n<i>Tell me how you'd "
                        "like to go on, or fix that and say \"build again\".</i>", html=True)
            except Exception:
                pass
    threading.Thread(target=watch, daemon=True).start()
    return proc

def _building():
    p = BUILD.get('proc')
    if p is None:
        return None
    mins = int((time.time() - BUILD['started']) / 60)
    if p.poll() is None:
        return f"A build is running ({mins} min so far): {BUILD['goal'][:200]}"
    return (f"The last build finished {'successfully' if p.returncode == 0 else 'with a problem'}: "
            f"{BUILD['goal'][:200]}")

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
        got = read(ch, text)
    intent, rule = got.get('intent', 'reply'), (got.get('rule') or text).strip()
    who = _who(ch)
    if intent == 'build' and start_build:
        go = bool(got.get('confirmed'))   # "yes, build it" / "I already told you": no need to ask again
        for _ in range(3):
            if go:
                break
            ch.send(f"🏗 <b>Shall I build this?</b>\n\n{telegram.esc(rule)}\n\n"
                    "<i>I'll work on copies, then bring you the decisions to check. Tap, or just tell me.</i>", html=True,
                    buttons=[[('🚀 Yes, build it', 'bld|yes')], [('Not now', 'bld|no')]])
            kind, ans = telegram._wait(ch, poll, {'bld|yes', 'bld|no'})
            if kind == 'tap':
                go = ans == 'bld|yes'
                if not go:
                    ch.send('Very good. Just say the word.'); return 'not_built'
                break
            again = read(ch, ans)   # a typed answer is read in context, not taken as "no" (it was)
            if again.get('confirmed'):
                rule = (again.get('rule') or rule).strip() if again.get('intent') == 'build' else rule
                go = True
            elif again.get('intent') == 'build' and again.get('rule'):
                rule = again['rule'].strip()   # he corrected what to build: ask once more, with his correction
            else:   # something else entirely: hold the build, and answer what he said
                ch.send("Very good, I'll hold that build for now.")
                return handle(ch, repo, ans, poll, apply_build, start_build, cloud)
        if not go:
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
                    "myself down. On your computer, run <code>hive cloud --stop</code>: it brings everything built here "
                    "back to your computer first, then deletes this machine.", html=True)
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
    if intent == 'status' and _building():   # a build in the background: say so first
        speak(ch, repo, f'He asked: "{text}". Tell him exactly where things stand, starting with the build.',
              telegram.esc('📊 ' + _building()))
        return 'status'
    if intent == 'status':
        st = latest_build(repo)
        speak(ch, repo, f'He asked: "{text}". Tell him exactly where things stand.',
              telegram.esc('📊 ' + ((f"The latest build is on branch hive/{st['name']}. {st.get('check', '')}".strip())
                                    if st else 'Nothing has been built on this project yet.')))
        return 'status'
    if intent not in ('change', 'rule'):   # a question, a complaint, small talk: answered, in context, never kept as a rule
        speak(ch, repo, 'The conversation so far:\n' + (ch.recent() if hasattr(ch, 'recent') else '') +
              f'\n\nHis newest message: "{text}". Reply as his assistant would: answer what he asked; if he is '
              'frustrated, own the mistake plainly and say what you are doing about it; if he refers back to something, '
              'pick it up from the conversation.',
              "🐝 I'm here. Tell me what to build, a change of mind, or ask for the status.")
        return 'chat'
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
    CURRENT['ch'] = ch   # a background build reports its problems here
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
