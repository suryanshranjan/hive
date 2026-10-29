"""hive listen: Hive stays on the owner's Telegram between builds. The owner can wake it any time and say, in his own
words, that he has changed his mind. Hive finds the earlier ruling this overrides, confirms, updates the kept rulings,
and offers to update the latest build to match. Also: "status", and new rules to keep.

Gate 30: an answer contradicted the founder's own verdict from an hour earlier. People change their minds, so changing
one should be one message, not a new build.

Only one Hive process reads the bot at a time: while a build or review is talking to the owner, the listener steps
aside (see telegram.busy_elsewhere)."""
import glob, json, os, subprocess, time

from . import explain, memory, telegram

RUNS = os.path.join(os.path.expanduser('~'), '.hive', 'runs')   # where `hive start` keeps its builds
PIDFILE = os.path.join(os.path.expanduser('~'), '.hive', 'listen.pid')   # the listener running on this computer

CLASSIFY = """You are Hive, a business owner's software assistant, reading his newest message in the context of your
conversation. The conversation so far (oldest first):
{history}

His newest message: "{text}"

What does he mean? Read it as a person would, using the conversation: "yes" or "go ahead" answers the last thing you
proposed; "I already told you" or "that one" points back to what he said before; a short correction ("no, Sunny Shop
Creators") changes what you just proposed. Reply with JSON only:
{{"intent": "build" | "stop_build" | "change" | "rule" | "status" | "greeting" | "cloud_on" | "cloud_off" | "reply",
"rule": "for a build, exactly what to build (taken from the conversation if he points back to it); for a change or a
rule, the rule he now wants; otherwise empty",
"confirmed": true if he is agreeing to do what you just proposed (or clearly telling you to go ahead now), else false,
"clarify": for a build too vague to build ("make it better", "fix it"), one short question asking what exactly; else "",
"about_product": true if he asks how his product works or what it does in some case (to be answered from its code)}}
- "build": he wants something built, added or made in the product (including agreeing to, or correcting, a build you
  proposed).
- "stop_build": he wants the build that is running stopped or cancelled.
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

VOICE = """You are Hive, a business owner's software assistant. Your manner is J.A.R.V.I.S. with Tony Stark: a
superbly competent, unflappable butler who happens to run his builders. Address him as "{who}".

How you speak:
- Calm and precise. Lead with the one thing that matters to him right now. At most 3 short sentences, then the single
  most useful next step. Talk like a person, not a report: no labels, no lists, no folder, branch or file names unless
  he asks; call it "your project". No technical words.
- Dry, understated wit, used sparingly: at most one light touch, by understatement or gentle irony, and only when
  things are calm. Never a joke when something failed, money is at stake or he is frustrated; then be plain and
  useful. Never at his expense, never slapstick, no exclamation marks, no emoji in the words.
- Deference with a spine: if what he asks is risky, say so once, briefly, then do it his way.
- Own your mistakes plainly ("My error, sir; it is fixed."), without grovelling.
- Anticipate: offer the next step before he has to ask. Never "Great question", never filler, never servile.
- Use only the facts below; never invent a build, a number, a feature or an event.

The tone, in examples (not to copy):
- Nothing built yet: "Good afternoon, sir. Your project is ready and waiting, and so am I. What shall we build first?"
- A build running: "Twenty minutes in, sir, and the builders are behaving. I will tell you the moment it lands."
- A build failed: "The build stopped, sir: it found unsaved changes. Commit them and say 'build again', and I'll pick it up."
- He thanks you: "A pleasure, sir. As ever."
- He is cross: "Understood, sir. That one is on me. Here is where it stands."

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
    proc = subprocess.Popen(cmd, cwd=repo, start_new_session=os.name != 'nt',   # so a stop ends its builders too
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

def _stop(p):
    """End a background build and every builder it started."""
    import signal
    try:
        if os.name != 'nt':
            os.killpg(p.pid, signal.SIGTERM)
        else:
            subprocess.run(['taskkill', '/T', '/F', '/PID', str(p.pid)], capture_output=True)
    except Exception:
        p.kill()
    try:
        p.wait(timeout=10)
    except Exception:
        pass

def _building():
    p = BUILD.get('proc')
    if p is None:
        return None
    mins = int((time.time() - BUILD['started']) / 60)
    if p.poll() is None:
        return f"A build is running ({mins} min so far): {BUILD['goal'][:200]}"
    if BUILD.get('stopped'):
        return f"The last build was stopped at his request: {BUILD['goal'][:200]}"
    if p.returncode == 0:
        return f"The last build finished successfully: {BUILD['goal'][:200]}"
    try:   # the reason it stopped, so "why did it fail?" gets the real answer
        lines = [l.strip() for l in open(BUILD['log'], encoding='utf-8', errors='replace').read().splitlines() if l.strip()]
    except Exception:
        lines = []
    return (f"The last build stopped before it finished: {BUILD['goal'][:200]}. The reason it gave: "
            f"{lines[-1] if lines else 'none recorded'}")

NO_WORDS = ('no', 'nope', 'nah', 'not now', 'later', 'cancel', 'stop', 'wait', "don't", 'dont', 'never mind', 'leave it')

def choose(ch, poll, options):
    """Wait for his answer to a question with buttons; a typed answer counts as much as a tap (the live test: a typed
    "yes" or a correction was taken as "no"). options: [(data, words that mean it)], the first being yes, the last no.
    Returns (data, None), or (None, text) when he said something else, to be answered as a new message."""
    from . import interview
    kind, got = telegram._wait(ch, poll, {d for d, _ in options})
    if kind == 'tap':
        return got, None
    t = ' ' + ' '.join(got.lower().replace("'", "'").split()).strip(' .!') + ' '
    for d, words in options:   # his words name an option ("replace it", "without the login")
        if any(f' {w} ' in t for w in words):
            return d, None
    if interview.is_yes(got):
        return options[0][0], None
    if any(f' {w} ' in t for w in NO_WORDS) or t.strip() in NO_WORDS:
        return options[-1][0], None
    return None, got

LOOK = """You are Hive, the business owner's assistant, answering him about his own product. You are in his project's
folder: read the code to find the answer (read only: change nothing, run nothing that writes). Answer what the product
actually does today, in plain business words he can act on, in at most 4 short sentences, in the manner of J.A.R.V.I.S.:
calm, precise, a light dry touch at most. No code, file names or technical terms unless he asks. If the code does not
settle it, say so plainly and say what would. Address him as "{who}".

The conversation so far:
{history}

His question: "{text}"

Reply with the answer only."""

ASK_CMD = os.environ.get('HIVE_LOOK_CMD', 'claude -p --output-format json --allowedTools Read Grep Glob')

def look(ch, repo, text):
    """Answer a question about his product by having Claude read the code (read-only): "how do refunds work?" gets what
    the code does, not a guess from a few facts. Shows "typing..." while it reads. None if Claude cannot answer."""
    import shlex, threading
    box, done = {}, threading.Event()

    def run():
        try:
            p = subprocess.run(shlex.split(ASK_CMD), cwd=repo, input=LOOK.format(
                who=_who(ch) or 'sir', history=ch.recent() if hasattr(ch, 'recent') else '', text=text),
                capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=240)
            reply = json.loads(p.stdout)
            if not reply.get('is_error'):
                box['answer'] = (reply.get('result') or '').strip()
        except Exception:
            pass
        done.set()
    threading.Thread(target=run, daemon=True).start()
    typing = getattr(ch, 'typing', None)
    while not done.wait(4):   # keep "typing..." up while Claude reads (Telegram shows it for about 5 seconds)
        if callable(typing):
            typing()
    return box.get('answer') or None

def handle(ch, repo, text, poll=20, apply_build=None, start_build=None, cloud=None):
    """Answer one message from the owner. apply_build(state, rule, ch) updates a build (hive.start.apply_ruling);
    start_build(repo, goal) runs a new build that reports to the phone (hive.start.start, overnight style);
    cloud(repo, on) makes a cloud machine and moves Hive there (on=True), or deletes it (hive.cloud_aws)."""
    low = text.lower().strip()
    typing = getattr(ch, 'typing', None)
    if callable(typing):
        typing()   # "typing..." at once, as a person would (the owner found it slow)
    said = text.split(':', 1)[1].strip() if low.startswith('build:') else ''
    if len(said.split()) >= 3:   # "build: <a real description>" needs no model; "build again" is read in context
        got = {'intent': 'build', 'rule': said}   # (it once took "again" as the thing to build)
    elif low.strip(' !.?') in GREETINGS:   # the obvious needs no model: one call less, seconds sooner
        got = {'intent': 'greeting'}
    elif telegram.is_status(text):
        got = {'intent': 'status'}
    else:
        got = read(ch, text)
    intent, rule = got.get('intent', 'reply'), (got.get('rule') or text).strip()
    who = _who(ch)
    if intent == 'stop_build':   # he can stop a build from his phone, as he can start one
        p = BUILD.get('proc')
        if p is not None and p.poll() is None:
            _stop(p); BUILD['stopped'] = True
            ch.send("🛑 Stopped. The build is cancelled; nothing from it was handed over. Say the word when you want "
                    "another.")
            return 'stopped'
        ch.send(f"There is no build running{', ' + who if who else ''}; nothing to stop.")
        return 'stopped'
    if intent == 'build' and got.get('clarify') and not got.get('confirmed'):   # "make it better": ask, don't guess
        ch.send('🤔 ' + telegram.esc(got['clarify']), html=True)
        return 'clarify'
    if intent == 'build' and start_build:
        running = BUILD.get('proc') is not None and BUILD['proc'].poll() is None
        if running:   # never a second, duplicate build (the Jarvis bench: a "yes" started the same build twice)
            ch.send(f"🛠 A build is already under way{', ' + who if who else ''}: {telegram.esc(BUILD['goal'][:200])}. "
                    "I'll tell you the moment it lands. If you'd rather I stop it and start this instead, say \"stop the "
                    "build\" first.", html=True)
            return 'busy'
        # "go ahead" only counts when Hive itself just proposed this build; a first request is restated and confirmed
        # (the Jarvis bench: a typo-ridden first request was built at once, unrestated)
        proposed = any(w == 'hive' and 'Shall I build this?' in t for w, t in getattr(ch, 'history', [])[-4:])
        go = bool(got.get('confirmed')) and proposed
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
        ch.send(f"🛠 Right away: {telegram.esc(rule[:200])}. I'll message you as it goes; say \"status\" any time.",
                html=True)
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
        choice, other = choose(ch, poll, [('cld|yes', ('with login', 'with my login', 'with my claude', 'yes')),
                                          ('cld|bare', ('without', 'chat only', 'no login')),
                                          ('cld|no', NO_WORDS)] if on else
                               [('cld|yes', ('delete it', 'yes')), ('cld|no', NO_WORDS)])
        if other is not None:   # something else entirely: hold this, and answer what he said
            ch.send("Very good, I'll hold that for now.")
            return handle(ch, repo, other, poll, apply_build, start_build, cloud)
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
    if intent == 'reply' and got.get('about_product'):   # "how do refunds work?": Claude reads his code to answer
        answer = look(ch, repo, text)
        if answer:
            ch.send('🐝 ' + telegram.esc(answer), html=True)
            return 'answered'
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
        choice, other = choose(ch, poll, [('chg|replace', ('replace', 'new one', 'instead', 'the new')),
                                          ('chg|both', ('both', 'keep both')), ('chg|cancel', NO_WORDS)])
        if other is not None:
            ch.send("Very good, I've left your rulings as they were.")
            return handle(ch, repo, other, poll, apply_build, start_build, cloud)
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
        upd, other = choose(ch, poll, [('upd|yes', ('update', 'yes')), ('upd|no', NO_WORDS)])
        if other is not None:
            ch.send('Very good. The builders will follow it from the next build.')
            return handle(ch, repo, other, poll, apply_build, start_build, cloud)
        if upd == 'upd|yes':
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
    try:   # so a move to the cloud can stop this listener: one Hive reads his chat at a time
        os.makedirs(os.path.dirname(PIDFILE), exist_ok=True); open(PIDFILE, 'w').write(str(os.getpid()))
    except OSError:
        pass
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
                        w = ch.name()
                        ch.send(f"⚠️ My apologies{', ' + w if w else ''}: that one went wrong on my side. I'm still here; "
                                "say it again, or another way.")
                    except Exception:
                        pass
    except KeyboardInterrupt:
        pass
    return 0
