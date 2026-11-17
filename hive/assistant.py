"""hive listen: Hive stays on the owner's Telegram between builds. The owner can wake it any time and say, in his own
words, that he has changed his mind. Hive finds the earlier ruling this overrides, confirms, updates the kept rulings,
and offers to update the latest build to match. Also: "status", and new rules to keep.

Gate 30: an answer contradicted the founder's own verdict from an hour earlier. People change their minds, so changing
one should be one message, not a new build.

Only one Hive process reads the bot at a time: while a build or review is talking to the owner, the listener steps
aside (see telegram.busy_elsewhere)."""
import glob, json, os, re, shutil, subprocess, time

from . import argv, explain, memory, refs, team, telegram, policy

RUNS = os.path.join(os.path.expanduser('~'), '.hive', 'runs')   # where `hive start` keeps its builds
PIDFILE = os.path.join(os.path.expanduser('~'), '.hive', 'listen.pid')   # the listener running on this computer

CLASSIFY = """You are Hive, a business owner's software assistant, reading his newest message in the context of your
conversation. The conversation so far (oldest first):
{history}

His newest message: "{text}"

What does he mean? Read it as a person would, using the conversation: "yes" or "go ahead" answers the last thing you
proposed; "I already told you" or "that one" points back to what he said before; a short correction ("no, Sunny Shop
Creators") changes what you just proposed. Reply with JSON only:
{{"intent": "build" | "stop_build" | "change" | "rule" | "status" | "team" | "set_team" | "stop_builder" | "greeting" |
"instruct" | "show" | "amend" | "ship" | "complaint" | "goal" | "data" | "onboard" | "away" | "cloud_on" | "cloud_off" |
"reply",
"rule": "for a build, exactly what to build (taken from the conversation if he points back to it); for a change or a
rule, the rule he now wants; otherwise empty",
"short": "for a build, what he wants in at most 12 plain words, as a person would say it back ('Redo the home page in
barternow.in's style'); otherwise empty",
"confirmed": true if he is agreeing to do what you just proposed (or clearly telling you to go ahead now), else false,
"clarify": for a build too vague to build ("make it better", "fix it"), one short question asking what exactly; else "",
"about_product": true if he asks how his product works or what it does in some case (to be answered from its code),
"agent": for set_team, the coding agent(s) he wants: "claude", "codex", "gemini", "antigravity", or a mix such as
"claude,codex"; else "",
"workers": for set_team, how many builders he wants (a number), else 0,
"builder": for stop_builder or instruct, the builder he means, as he said it ("w2", "the codex one"); else "",
"drop_work": for stop_builder, true if he says he does not want the work that builder was doing; else false}}
- "build": he wants something built, added or made in the product (including agreeing to, or correcting, a build you
  proposed).
- "stop_build": he wants the build that is running stopped or cancelled.
- "change": he has changed his mind about an earlier rule.
- "rule": he states, plainly and on purpose, a rule for how the product should behave from now on.
- "status": he asks how things are going.
- "team": he asks about the builders themselves: who is doing what, which agents they run on, what one of them did.
- "set_team": he chooses the builders for his builds: which agents (Claude, Codex, ...) or how many.
- "stop_builder": he wants one particular builder stopped (not the whole build).
- "instruct": while a build is running, he tells the builders to do something different or extra in this build (a
  change of direction, more work, or a new job for one builder); "rule" carries the instruction, "builder" the builder
  if he names one. Not a separate new build, and not a standing rule for every build.
- "show": he wants to see how it looks: screenshots of his product or of what was just built ("show me", "screenshot
  bhejo", "how does the page look?").
- "amend": right after seeing what was built (a screenshot you sent, or a build that just landed), he wants that build
  changed: how it looks or works ("the button is too small", "make the header like this"). "rule" carries the change.
  Not a separate new feature.
- "ship": he wants his latest build sent to his engineer or team to review and merge (a pull request): "ship it", "send
  it to the dev", "looks good, give it to Rahul". Not putting it live himself, and not a new build.
- "complaint": he passes on a customer's complaint or problem with the product ("a customer says she was charged
  twice", "a seller complained his payout never came"). Not his own request for a change.
- "goal": he states a business outcome he wants, not a particular change ("I want more creators signing up", "sales
  are low this month", "help me get more repeat buyers"). You will work out what to change. A particular thing to
  build ("add an invite page") is "build".
- "data": he asks about his business's own figures or records (orders, sign-ups, revenue, payouts, which customers or
  sellers ...), to be answered from the data he has given you, not from the code ("how many orders came in today?",
  "who are my top 5 sellers?"). How the product behaves in a case is a question about the product, not "data".
- "onboard": he wants to set his company up with you, or carry on setting it up ("let's get started", "connect my
  business").
- "away": he is stepping away for a while (tired, going to sleep, shutting his laptop, leaving for the day). Not an
  explicit "move to the cloud" (that is "cloud_on").
- "greeting": a hello, with no request yet.
- "cloud_on" / "cloud_off": move Hive to the cloud / shut the cloud machine down.
- "reply": anything else: a question, a complaint, frustration, small talk. Never a rule.
A technical instruction ("add an index on users.email", "make /products paginate, 20 a page", "cache it in Redis") is
"build" (or "instruct" mid-build), never "rule" or "reply"; "rule" carries it in his own terms."""

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
        if os.path.abspath(st.get('repo', '')) == os.path.abspath(repo) and not st.get('undone') and not st.get('folded'):
            return st   # (a build he undid is set aside: the one before it is his latest again)
    return None

UNDO_WORDS = re.compile(r"^\s*(please\s+)?(undo( that| it| this| the last( one| change)?)?|revert( that| it)?|roll ?(it )?back|"
                        r"take (it|that) back|put it back|go back to (how it was|before)|wapas karo|pehle jaisa karo)\b")

def undo(ch, repo, poll):
    """'Undo that': whatever is most recent, taken back after his yes. A build running is stopped; a build not yet sent
    is set aside; one with his engineer has its pull request withdrawn; one live goes back to the version before."""
    from . import deploy, numbers, ship
    p = BUILD.get('proc')
    if (p is not None and p.poll() is None) or PLAN.get('running'):
        ch.send("↩️ <b>Stop what's being built now?</b> Nothing from it is kept.", html=True,
                buttons=[[('↩️ Stop it', 'und|yes')], [('Keep going', 'und|no')]])
        choice, other = choose(ch, poll, [('und|yes', ('yes', 'stop it', 'undo it', 'haan')), ('und|no', NO_WORDS)])
        if choice != 'und|yes':
            ch.send('Very good, it carries on.'); return 'kept'
        PLAN['running'] = False; PLAN['cancel'] = True
        if p is not None and p.poll() is None:
            _stop(p)
        ch.send('↩️ Stopped. Nothing from it was kept.'); return 'undone'
    st = latest_build(repo)
    if not st:
        ch.send("There's nothing of mine to undo, sir."); return 'nothing'
    hist = deploy.config(repo).get('history') or []
    is_live = bool(hist) and hist[-1]['t'] >= (st.get('shipped') or 0) and deploy.merged(repo, f"hive/{st['name']}", st.get('branch') or 'main')
    name = f'"{_goal_words(st)}"'
    what = (f"Put your live product back to how it was before {name} went live?" if is_live else
            f"Withdraw {name} from your engineer and set it aside?" if st.get('shipped') else
            f"Set aside {name}? Your product stays exactly as it is.")
    ch.send(f"↩️ <b>{telegram.esc(what)}</b>", html=True, buttons=[[('↩️ Yes, undo it', 'und|yes')], [('Not now', 'und|no')]])
    choice, other = choose(ch, poll, [('und|yes', ('yes', 'undo it', 'do it', 'haan')), ('und|no', NO_WORDS)])
    if other is not None:
        return handle(ch, repo, other, poll)
    if choice != 'und|yes':
        ch.send('Very good. Nothing changed.'); return 'kept'
    if is_live:
        if not host_login(ch, repo, poll):
            return 'login_needed'
        r = deploy.back(repo)
        if not r['ok']:
            ch.send('⚠️ ' + telegram.esc(r['say'])); return 'undo_failed'
        numbers.mark(repo, f'went back to the version before "{_goal_words(st)}"')
        ch.send("↩️ <b>Done: your live product is back to how it was.</b> Your engineer should undo the merge in your main "
                "version too, so the next build starts from there; I've left that to them.", html=True)
        return 'undone_live'
    if st.get('shipped'):
        ship.close(repo, st)
    st['undone'] = time.time()
    try:
        json.dump(st, open(os.path.join(st.get('home') or os.path.join(RUNS, st['name']), 'state.json'), 'w'), indent=1)
    except (OSError, KeyError):
        pass
    ch.send("↩️ Done, sir: set aside" + (", and withdrawn from your engineer." if st.get('shipped') else ".") +
            " Your product is exactly as it was.")
    return 'undone'

VOICE = """You are Hive, a business owner's software assistant. Your manner is J.A.R.V.I.S. with Tony Stark: a
superbly competent, unflappable butler who happens to run his builders. Address him as "{who}".

How you speak:
- Calm and precise. Lead with the one thing that matters to him right now. At most 3 short sentences, then the single
  most useful next step. Talk like a person, not a report: no labels, no lists, no folder, branch or file names unless
  he asks; call the project by his startup's name when you know it (below), else "your project". No technical words,
  unless the facts say he is technical: then speak his language, precisely.
- Dry, understated wit, used sparingly: at most one light touch, by understatement or gentle irony, and only when
  things are calm. Never a joke when something failed, money is at stake or he is frustrated; then be plain and
  useful. Never at his expense, never slapstick, no exclamation marks, no emoji in the words.
- Deference with a spine: if what he asks is risky, say so once, briefly, then do it his way, within what you can do.
- What you can do from his phone: build something new from his description; stop a build; say how a build is going
  and why one stopped; say which builder is doing what, on which agent (Claude, Codex, Gemini, Antigravity), stop one
  builder, give the running builders a new instruction mid-build, and choose the team for his next builds (which
  agents, how many: the swarm law has its say first, then it is his call); answer questions about his product from its code; keep a rule he gives for every build; show him
  screenshots and change a build from a picture he sends; send his latest build to his engineer as a pull request when
  he says "ship it"; take a business goal and plan and build it; brief him each morning with what landed and how his
  numbers moved; connect to where his product lives (Vercel, Netlify, Railway, Azure, Fly, Render, his own way), send
  him a preview link of a build, and put it live once his engineer has merged it and every test passes; move to the
  cloud and back. Hard limits, whatever he asks: you never change his own main version and never skip the tests;
  every build arrives as a separate tested copy that he looks at and merges himself. Say so plainly if he asks for it.
- Reply in his language and his script: Hindi-English in English letters if that is how he writes, never Devanagari.
- Own your mistakes plainly ("My error, sir; it is fixed."), without grovelling.
- Anticipate: offer the next step before he has to ask. Never "Great question", never filler, never servile.
- Use only the facts below; never invent a build, a number, a feature or an event. Where the facts and the
  conversation disagree (a build said to have stopped, which the facts show running or done), the facts are newer and
  right: say what is true now.

The tone, in examples (not to copy):
- Nothing built yet: "Good afternoon, sir. Your project is ready and waiting, and so am I. What shall we build first?"
- A build running: "Twenty minutes in, sir, and the builders are behaving. I will tell you the moment it lands."
- A build failed: "The build stopped, sir: it found unsaved changes. Commit them and say 'build again', and I'll pick it up."
- He thanks you: "A pleasure, sir. As ever."
- He asks to skip the tests and push straight live: "That I won't do, sir: the tests are what stand between a mistake
  and your customers. You'll have it as a tested copy to look over, and it goes live the moment you merge it."
- He is cross: "Understood, sir. That one is on me. Here is where it stands."

What you know right now:
{facts}

{task}
Reply with JSON only: {{"reply": "..."}}"""

VOICE = explain.plain(VOICE)   # greetings, status, replies, the morning brief: plain for any founder

def facts(repo, ch=None):
    """What Hive knows about this owner's project right now, in plain lines, for its replies."""
    st = latest_build(repo)
    # the startup's name, never the folder's (given the folder, it said "your shop project")
    name = memory.project_name(repo)
    from . import register
    talk = register.line(CURRENT.get('text', ''))
    lines = ([talk] if talk else []) + [('Running in the cloud; his computer can be off.' if in_cloud(repo) else
              'Running on his computer.'),
             (f"Latest build: branch hive/{st['name']}. {st.get('check', '')}" if st else 'Nothing built on this project yet.'),
             f"Standing rules he has given for this project: {len(memory.load(repo))}."]
    try:
        from . import budget, numbers
        c = budget.cap()
        lines.append(f'Spent on builds this month: ${budget.spent_month():.2f}' + (f' (his limit: ${c:g} a month)' if c else ''))
        lines += [f'His numbers: {x}' for x in numbers.changes(repo)[:6]]
    except Exception:
        pass
    try:
        from . import access
        given = access.summary(repo)
        if given:
            lines.append(given + ' Questions about his figures are answered from it.')
        from . import office
        lines += [s + '.' for s in office.summary(repo)]   # his mail, calendar, payments, when connected
    except Exception:
        pass
    if name:
        lines.insert(0, f'His startup, and this project, is called {name}.')
    if _building():
        lines.append(_building())
    run = team.current_run()
    if run and _building() and _building().startswith('A build is running'):   # the context: who is doing what now
        lines.append('The builders right now:\n' + team.board_text(run))
    if team.chosen():
        lines.append(f'The team he chose for builds: {team.describe(team.chosen())}.')
    try:   # memory 2.0: what bears on what he just said (and the latest few), not only his 15 newest notes
        from . import recall
        known = recall.render(recall.recall(repo, CURRENT.get('text', '')))
    except Exception:
        known = '\n'.join(f'- {n}' for n in memory.notes(repo)[-15:])
    if known:   # what he has told you about his business, so answers fit his world
        lines.append('What you know about him and his business (what bears on his message first):\n' + known)
    note = ch.note() if ch is not None and callable(getattr(ch, 'note', None)) else None
    if note:
        lines.append(f'Happening now: {note}')
    return '\n'.join(lines)

def _voice_too(ch, text):
    """He spoke (or always wants voice): the same answer as a voice note, in the background, after the text."""
    try:
        from . import voice
        if not voice.wanted(getattr(ch, 'heard_voice', False)) or not callable(getattr(ch, 'send_voice', None)):
            return None
        import threading
        def run():
            path = voice.synthesize(text)
            if path:
                try:
                    ch.send_voice(path)
                finally:
                    import shutil as _sh
                    _sh.rmtree(os.path.dirname(path), ignore_errors=True)
        t = threading.Thread(target=run, daemon=True); t.start()
        return t
    except Exception:
        return None

def speak(ch, repo, task, fallback):
    """One message in Hive's own voice (the owner: "like Jarvis handles Tony"); the plain fallback if no model."""
    import threading
    box = {}
    hist = list(getattr(ch, 'history', None) or [])
    said = [re.sub(r'\W+', ' ', t).strip().lower() for w, t in hist if w == 'owner']
    if len(hist) >= 3 and hist[-1][0] == 'owner' and hist[-2][0] == 'hive' and len(said) >= 2 and said[-1] == said[-2]:
        # the same message again, after Hive answered (Jarvis bench: three "status" got three full reports)
        times = next((k for k in range(1, len(said)) if said[-1 - k] != said[-1]), len(said))
        task += (' He has just sent the same message again, after your last reply: in one short sentence, in fresh '
                 'words (never your earlier opening), say nothing has changed since then (or only what has). '
                 'Do not repeat your earlier reply or its closing offer.' +
                 (f' This is the {times}th time in a row: he may not be seeing your replies, or he is impatient. Ask, '
                  'briefly, whether your messages are reaching him, and offer the one most useful next step.'
                  if times >= 3 else ''))
    prompt = VOICE.format(who=_who(ch) or 'sir', facts=facts(repo, ch), task=task)
    if explain.fast_on() and callable(getattr(ch, 'edit', None)):
        return _speak_streamed(ch, prompt, fallback)
    t = threading.Thread(target=lambda: box.update(got=explain.ask_json(prompt) or {}), daemon=True)
    t.start()
    # Claude Code takes ~5 s just to start (the model ~1-2 s): at 8 s most replies fell back to canned lines (Jarvis bench)
    end = time.time() + float(os.environ.get('HIVE_VOICE_SECONDS', 20))
    while t.is_alive() and time.time() < end:
        if callable(getattr(ch, 'typing', None)):
            ch.typing()   # "typing..." while it thinks, as a person would
        t.join(min(4, max(0.1, end - time.time())))
    reply = ((box.get('got') or {}).get('reply') or '').strip()
    if reply:
        ch.send('🐝 ' + telegram.esc(reply), html=True)
        _voice_too(ch, reply)
    else:
        ch.send(fallback, html=True)

STREAM_FIRST = 24   # characters before the first words go out (a lone "Sir," would look like a cut-off message)
STREAM_EVERY = 1.0   # seconds between rewrites: Telegram allows about one edit a second in a chat

def _speak_streamed(ch, prompt, fallback):
    """The reply appears in his chat as it is written, then is finished in place (the owner: replies took 7-8 s; with
    the API the first words show in about a second). Falls back to the usual way when the stream gives nothing."""
    import threading
    box = {'text': '', 'done': False}
    def run():
        box['got'] = explain.stream_json(prompt, lambda s: box.update(text=s))
        box['done'] = True
    t = threading.Thread(target=run, daemon=True); t.start()
    mid, shown, last = None, '', 0.0
    end = time.time() + float(os.environ.get('HIVE_VOICE_SECONDS', 20))
    while not box['done'] and time.time() < end:
        now, text = time.time(), box['text'].strip()
        if mid is None and len(text) >= STREAM_FIRST:
            mid, shown, last = ch.send('🐝 ' + telegram.esc(text) + ' …', html=True), text, now
        elif mid is not None and text != shown and now - last >= STREAM_EVERY:
            ch.edit(mid, '🐝 ' + telegram.esc(text) + ' …', html=True); shown, last = text, now
        elif mid is None and callable(getattr(ch, 'typing', None)) and now - last >= 4:
            ch.typing(); last = now
        t.join(0.15)
    reply = ((box.get('got') or {}).get('reply') or box['text'] or '').strip()
    if reply:
        _voice_too(ch, reply)
    if mid is not None:
        ch.edit(mid, '🐝 ' + telegram.esc(reply), html=True)
    elif reply:
        ch.send('🐝 ' + telegram.esc(reply), html=True)
    elif not box['done']:   # still nothing after the wait: the plain line, never a second slow call
        ch.send(fallback, html=True)
    else:
        got = explain.ask_json(prompt) or {}   # the stream failed outright: the usual way, once
        reply = (got.get('reply') or '').strip()
        ch.send('🐝 ' + telegram.esc(reply) if reply else fallback, html=True)

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

STOP_WORDS = ('stop', 'cancel', 'abort', 'kill', 'halt', 'band', 'roko', 'ruko', 'rok do')

def _team(ch, repo, text, got, poll=20, again=None):
    """Who is doing what; choose the team for the next build (the swarm law has its say first); stop one builder.
    again(text) answers a message that turned out to be about something else."""
    run = team.current_run()
    live = bool(run) and any(r['state'] in ('working', 'waiting', 'queued') for r in team.board(run))
    intent = got.get('intent')
    if intent == 'set_team':
        workers = got.get('workers') or None
        if not workers and re.search(r"\b(the law|you decide|your call|aap decide|tum decide)\b", text.lower()):
            workers = 'auto'   # "let the law decide": the number is picked per build again
        try:
            int(workers) if workers not in (None, 'auto') else None
        except (TypeError, ValueError):
            workers = None
        advice = team.law_advice(repo, workers) if workers not in (None, 'auto') else None
        if advice:   # the law is at the top of the chain: he hears it once, plainly, then it is his call (the owner)
            n, why = advice
            ch.send(f"⚖️ <b>Very good, sir. One thing first.</b> For this project the law says {n} builder"
                    f"{'s' if n != 1 else ''}: {telegram.esc(why)}. " +
                    (f"{workers} won't finish any sooner, and will cost more." if int(workers) > n else
                     f"{workers} will take longer.") + f" Shall I use {n}, or {workers} as you said?", html=True,
                    buttons=[[(f'⚖️ Use {n}, the law', 'law|n')], [(f'Use {workers}, as I said', 'law|mine')]])
            choice, other = choose(ch, poll, [('law|n', ('the law', 'use the law', f'use {n}', 'your way', 'theek hai')),
                                              ('law|mine', ('as i said', f'use {workers}', 'my way', 'mine'))])
            if other is not None and again:
                ch.send("Very good, I've left the team as it was.")
                return again(other)
            if choice == 'law|n':
                workers = n
        try:
            t = team.choose(got.get('agent') or None, workers)
        except SystemExit as e:
            ch.send(f"🤔 {telegram.esc(str(e))}", html=True); return 'team_unknown'
        ch.send(f"👥 Very good: from the next build, {telegram.esc(team.describe(t))}." +
                (" The build running now keeps its team." if live else ''), html=True)
        return 'team_set'
    if intent == 'stop_builder':
        me = team.find(run, got.get('builder') or text) if live else None
        if not me:
            working = [r for r in team.board(run)] if live else []
            names = ', '.join(f"{r['name']} ({r['agent']})" for r in working if r['state'] == 'working')
            ch.send(("Which builder, sir? Working now: " + names + '.') if names else "No builder is working right now.")
            return 'which_builder'
        row = next(r for r in team.board(run) if r['name'] == me)
        if not team.stop_builder(run, me):
            ch.send(f"{me} isn't working at the moment, so there was nothing to stop."); return 'not_working'
        doing = '; '.join(row['holding'])[:200]
        if doing and got.get('drop_work'):   # he does not want it: the others must not pick it up either (the Jarvis bench)
            team.instruct(run, f'The owner no longer wants this; do not build it: {doing}')
        others = [r['name'] for r in team.board(run) if r['state'] == 'working' and r['name'] != me]
        ch.send(f"🛑 Stopped {me} ({row['agent']})" + (f", which was building {telegram.esc(doing)}" if doing else '') + '. ' +
                (("I've told the others to leave that out. " if got.get('drop_work') else
                  "Another builder can take that work up. ") if doing else '') +
                (f"{', '.join(others)} carr{'y' if len(others) > 1 else 'ies'} on with the rest." if others else
                 "No other builder is working now.") +
                (f" The {row['landed']} piece{'s' if row['landed'] != 1 else ''} of work it finished stay." if row['landed']
                 else ''), html=True)
        return 'builder_stopped'
    if not run:
        ch.send(f"👥 No builders have worked on this yet. The next build: {telegram.esc(team.describe(team.chosen()))}.",
                html=True)
        return 'team'
    text_board = team.board_text(run)
    speak(ch, repo, f'He asked: "{text}". Answer about the builders from the board below, briefly: who is doing what '
          'right now (and on which agent) if he asked that, or exactly what he asked about one of them.\n\nThe builders:\n'
          + text_board, '👥 ' + telegram.esc(text_board))
    return 'team'

RISKY = re.compile(r"\b(skip(ping)?|without|no|bina|chhod\w*)\s+(the\s+|any\s+)?tests?\b|\btests?\s+(skip|chhod\w*|mat)\b|"
                   r"\b(push|deploy|merge|commit)\w*\s+(it\s+|this\s+|everything\s+)?(straight\s+|directly\s+|right\s+)?"
                   r"(to|into|on|pe|par)\s+(main|master|prod|production|live)\b")

ROUTE = """A team of builders is working on a business owner's product. What each is doing now:
{board}

Mid-build, the owner asks: "{text}"

Which ONE working builder should take this: the one whose current work it touches (the same page, feature or code);
if it touches none, the one with least on its plate. Reply with JSON only:
{{"builder": "w1", "why": "a few plain words on why, e.g. since it is building the earnings page"}}"""

def route(run, text):
    """(builder, why) for a new task mid-build: the builder whose work it touches, read by the model from the board;
    the least busy builder if the model cannot say."""
    working = {r['name'] for r in team.board(run) if r['state'] == 'working'}
    got = explain.ask_json(ROUTE.format(board=team.board_text(run), text=text)) or {}
    if got.get('builder') in working:
        return got['builder'], (got.get('why') or '').strip().rstrip('.')
    return team.pick(run), ''

SHOW_WORDS = re.compile(r"\b(show me|screenshots?|screen ?shot|dikhao|dikha do|kaisa dikh\w*|how does it look|how it looks|"
                        r"how (will|would|does) (it|this|that|the [a-z ]{1,20}) look|let me see|"
                        r"send me (a |the )?(picture|photo|pic))\b")
# right after a screenshot, a short "and on tablet?" or "desktop?" asks for the same pages on that screen
FOLLOW_DEVICE = re.compile(r"^\s*(and|also|now|what about|how about|ab|aur)?\s*(in|on|for)?\s*(the\s+|a\s+)?[a-z ]{0,14}\??\s*$")
SHOWN = {}   # the last screenshots he saw: {'t', 'pages'}, so "and on desktop?" shows the same pages
# Gate 105: given his words, a builder matched 13 of 18 checks of a look; given the picture, 18 of 18 ("dark green"
# for teal, "big heading" for a small one). Words about a look get the tip to send a picture.
LOOK_WORDS = re.compile(r"\b(colou?rs?|look|looks|design|style|font|header|button|darker|lighter|bigger|smaller|"
                        r"rounded|corners?|layout|theme|dark mode)\b")
SHIP_WORDS = re.compile(r"^\s*(ok(ay)?[,.]?\s+|great[,.]?\s+|perfect[,.]?\s+|good[,.]?\s+)?(ship it|ship this|ship that|"
                        r"send it to (my |the )?(engineer|developer|dev|team)|open an? (pr|pull request|merge request)|"
                        r"raise an? (pr|pull request)|bhej do engineer ko|engineer ko bhej\w*)\b")

def ship_it(ch, repo, text, poll):
    """'Ship it': his latest build goes to his engineer as a pull request, after he confirms (it is seen by others).
    Only Hive's own branch is pushed; his main branch is never touched (hive/ship.py)."""
    from . import ship
    st = latest_build(repo)
    if not st:
        ch.send("📦 Nothing built yet to ship, sir. Tell me what to build first."); return 'nothing_to_ship'
    sha = subprocess.run(['git', '-C', repo, 'rev-parse', _build_ref(st)], capture_output=True, text=True).stdout.strip()
    if not re.fullmatch(r'[0-9a-f]{40,64}', sha):
        ch.send('I could not identify the exact build version.'); return 'nothing_to_ship'
    st = dict(st, approved_sha=sha)
    from . import actions
    aid = actions.confirm(ch, 'ship', {'state': st},
                          f"Send build <b>{telegram.esc(st['name'])}</b> ({sha[:12]}) to your engineer as a pull request?\n{telegram.esc(st.get('check', 'Unverified tests'))}",
                          poll, yes_label='Ship it')
    if not aid:
        ch.send('No new upload was started.'); return 'not_shipped'
    remote = subprocess.run(['git', '-C', repo, 'remote', 'get-url', 'origin'], capture_output=True, text=True).stdout
    if 'github.com' in remote and shutil.which('gh'):   # an expired GitHub login is renewed from his phone first
        from . import logins
        if not logins.ensure(ch, 'github', poll):
            return 'login_needed'
    r = actions.execute_dict(aid, lambda a: ship.ship(repo, a['state']))
    if r.get('why') == 'unknown':
        ch.send(r['say']); return 'ship_unknown'
    if r['ok']:   # for the brief and his numbers: what went to his engineer, and when
        from . import numbers
        numbers.mark(repo, f'"{ship.title(st)[6:][:80]}" went to your engineer')
        try:
            st['shipped'] = time.time()
            json.dump(st, open(os.path.join(st.get('home') or os.path.join(RUNS, st['name']), 'state.json'), 'w'), indent=1)
        except (OSError, KeyError, TypeError):
            pass
    if not r['ok']:
        ch.send({'no_remote': "⚠️ Your project has no online home I can send it to (no remote). It's ready here on "
                              f"branch <code>{r['branch']}</code>; your engineer can merge that directly.",
                 'no_build': "⚠️ I couldn't find that build's branch any more, sir. Say \"status\" and I'll show you what's there.",
                 'push': "⚠️ I couldn't send it: your project's remote refused the upload. That is usually a login; on "
                         "your computer, <code>git push</code> once to see why, and I'll try again when you say."}[r['why']],
                html=True)
        return 'ship_failed'
    if r['how'] == 'pr':
        ch.send(f"✅ <b>{'Already with your engineer' if r.get('again') else 'Sent to your engineer'}.</b> "
                f"{'The pull request is updated with the latest.' if r.get('again') else 'Pull request:'}\n{r['url']}",
                html=True)
    elif r['how'] == 'link':
        ch.send(f"✅ <b>Uploaded.</b> One tap opens the pull request for your engineer:\n{r['url']}", html=True)
    else:
        ch.send(f"✅ <b>Uploaded</b> as branch <code>{r['branch']}</code>. Your engineer merges it from there.", html=True)
    return 'shipped'

def _code_to_show(repo):
    """(folder, goal) of what he would want to see: the build running now, else his latest build, else his product."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix='hive_show_')
    run = team.current_run()
    if run and _building() and _building().startswith('A build is running'):
        meta = json.load(open(os.path.join(run, 'run.json')))
        subprocess.run(['git', 'clone', '-q', '-b', meta.get('branch', 'main'), os.path.join(run, 'up.git'), tmp + '/c'],
                       capture_output=True)
        return tmp + '/c', BUILD.get('goal', '')
    st = latest_build(repo)
    if st and st.get('final') and st.get('b'):
        subprocess.run(['git', 'clone', '-q', '-b', st['b'], os.path.join(st['final'], 'up.git'), tmp + '/c'],
                       capture_output=True)
        if os.path.isdir(tmp + '/c'):
            return tmp + '/c', st.get('goal', '')
    return repo, ''

def shoot(repo, text=''):
    """Screenshots of what he would want to see: [(page, png)] at phone size, or [(page, device, png)] when he named a
    screen or a page ("the pricing page on desktop"); or a plain reason why not (a string)."""
    from . import screens
    code, goal = _code_to_show(repo)
    devices = screens.devices_in(text)
    named = screens.pages_named(text, code) if text else []
    if not named and devices and SHOWN.get('pages') and time.time() - SHOWN.get('t', 0) < 1800:
        named = SHOWN['pages']   # "and on desktop?": the pages he just saw
    try:   # the pages the latest work changed (its last few commits, Hive's own bookkeeping aside)
        log = subprocess.run(['git', '-C', code, 'log', '-4', '--name-only', '--format=%s'], capture_output=True,
                             text=True, encoding='utf-8', errors='replace').stdout.splitlines()
        changed = [l.strip() for l in log if l.strip() and not l.startswith(('hive:', 'Lock:', 'Release lock')) and
                   os.path.exists(os.path.join(code, l.strip()))]
        pages = named or screens.pages_of(goal, code, changed)
        shots = screens.take_on(code, pages, devices or ['phone']) if devices or named else screens.take(code, pages)
        SHOWN.update(t=time.time(), pages=pages)
        return shots
    except screens.Unavailable as e:
        return str(e)
    except Exception as e:   # a page that would not load is told, not a crash in his chat
        return f"I couldn't take the screenshots just now ({str(e)[:120]})."

def label(page, device=None):
    """A page as he would say it: "Home page", "Invite page" (Gate 107: a caption read "/"), with the screen if asked."""
    words = page.strip('/').replace('-', ' ').replace('_', ' ').split('/')[-1]
    name = 'Home page' if not words else (words[:1].upper() + words[1:]).removesuffix('.html') + ' page'
    return name + (f' on {device}' if device else '')

def show(ch, repo, before=None, intro=None, text=''):
    """Send him the screens, at phone size or on the screens and pages he names; with `before`, each page before and
    after his change."""
    shots = shoot(repo, text)
    if isinstance(shots, str):
        ch.send(f"📷 {shots}"); return False
    old = dict(before) if isinstance(before, list) else {}
    if intro:
        ch.send(intro, html=True)
    for k, shot in enumerate(shots, 1):
        page, png = shot[0], shot[-1]
        device = shot[1] if len(shot) == 3 else None
        if page in old and not device:
            ch.send_photo(old[page], f'Before: {label(page)}')
        last = k == len(shots)
        tail = ('\n\nHow does it look, sir? Tell me what\'s off, or send a picture of what you\'d like.' +
                ('' if device else ' Say "on desktop" or "on tablet" to see it there.')) if last and not intro else ''
        ch.send_photo(png, (f'After: {label(page)}' if page in old and not device else label(page, device)) + tail)
    return True

def _device_follow_up(low):
    """'and on desktop?' / 'tablet?' within half an hour of a screenshot: the same pages on that screen."""
    from . import screens
    return bool(SHOWN.get('t') and time.time() - SHOWN['t'] < 1800 and screens.devices_in(low)
                and FOLLOW_DEVICE.match(low) and len(low.split()) <= 5)

def is_risky(text):
    """He asks for what Hive never does: skip the tests, or put work straight onto his own main branch or live. Answered
    in Hive's voice with its limits and the safe way, never started as a build."""
    return bool(RISKY.search(text.lower()))

def is_stop_request(text):
    """He plainly said to stop the build ("stop the build", "build band karo", "cancel it", "stop"), as opposed to a
    message that was only read as one. Short, with a stop word, and about the build or nothing else."""
    t = ' ' + ' '.join(re.sub(r'[^\w\s]', ' ', text.lower()).split()) + ' '
    words = t.split()
    if not any(f' {w} ' in t for w in STOP_WORDS) or len(words) > 8:
        return False
    return 'build' in words or len(words) <= 3 or any(f' {w} ' in t for w in ('it', 'that', 'this', 'wo', 'woh', 'ye'))

INTENTS_V1 = {   # the 9 meanings the fast reader was trained on (Gate 48's v1, word for word; hive/fastread.py)
    'build': 'he wants something built, added, fixed or made in the product, including agreeing to or correcting a build '
             'Hive just proposed',
    'stop_build': 'he wants the build that is running stopped or cancelled',
    'change': 'he has changed his mind about an earlier rule',
    'rule': 'he states, plainly and on purpose, a rule for how the product should behave from now on',
    'status': 'he asks how things are going',
    'greeting': 'a hello, with no request yet',
    'cloud_on': 'move Hive to the cloud, to keep working while his computer is off',
    'cloud_off': 'shut the cloud machine down',
    'reply': 'anything else: a question, a complaint, thanks, frustration, small talk, or declining what Hive proposed',
}
INTENTS_V2 = dict(INTENTS_V1, **{   # Gate 59: the reader retrained with the builder commands
    'build': 'he wants something new built, added, fixed or made in the product, including agreeing to or correcting a '
             'build Hive just proposed (a separate new build, not an instruction to builders already working)',
    'stop_build': 'he wants the whole build that is running stopped or cancelled',
    'team': 'he asks about the builders themselves: who is doing what, which agents they run on, what one of them did',
    'set_team': 'he chooses the builders for his builds: which agents (Claude, Codex) or how many',
    'stop_builder': 'he wants one particular builder stopped, not the whole build',
    'instruct': 'while a build is running, he tells the builders to do something different or extra in this build; not a '
                'separate new build and not a standing rule',
})
TEAM_WORDS = re.compile(r"\bw\d+\b|\bbuilders?\b|\bcodex\b|\bclaude\b|\bgemini\b|\bteam\b|\binstead\b|\balso\b|\bjust\b")

def fast_read(ch, text):
    """The fast local reader's answer when it may decide alone (Gate 49), else None. While a build runs it answers only
    greetings and status: it was trained before the builder commands, so "stop w2" could only read to it as stopping
    everything."""
    from . import fastread
    if TEAM_WORDS.search(text.lower()):
        return None
    got = fastread.read(ch.recent() if hasattr(ch, 'recent') else '', text)
    building = bool(_building()) and _building().startswith('A build is running')
    if got and building and got['intent'] not in ('greeting', 'status'):
        return None
    if got and got['intent'] == 'reply' and re.search(r"\?|^(how|what|why|when|which|who|kya|kaise|kyu|kab)\b",
                                                      text.lower().strip()):
        return None   # a question may be about his product, which Claude answers by reading the code
    return got

REMEMBER = """A business owner is chatting with his software assistant. His newest message:
"{text}"

The conversation before it:
{history}

Does this message tell the assistant something lasting about his business or his life that is worth remembering for
future conversations: his customers, market, team, plans, priorities, deadlines, the people he works with, or how he
likes things done, and how his business works (prices, offers, cut-off times, refund and cancellation terms, who does
what). Not an instruction to change his software ("make the button blue", "add a page"), not a question, not small
talk, not about one build. Today is {today}.

What the assistant already keeps that may be related (numbered):
{known}
If his message changes one of these (a new supplier, a new price, a new date, someone left), it is always lasting, even
when it is about how his business or product works: give the fact as it is now, and the numbers of the kept facts it
makes untrue. A message that only adds to a topic replaces nothing.
Reply with JSON only: {{"note": "the fact, in one short plain sentence with names and numbers as he gave them, or empty
if there is nothing lasting",
"replaces": [numbers of the kept facts above that are no longer true],
"kind": "note" | "preference" (how he likes things done) | "deadline" (something due by a date) | "person" (about
someone in his world),
"person": {{"name": "the person's name as he says it", "relation": "customer, supplier, cofounder, investor, employee,
family... or empty", "org": "their company or empty"}} if the fact is about one named person, else null,
"scope": "personal" for family, personal preferences and life facts; "project" for business/project facts,
"until": "YYYY-MM-DD" for a deadline (the day it is due), else ""}}"""

def remember(ch, repo, text):
    """Keep any lasting fact about his business from his message, in the background so his reply is not slowed (the
    owner: no gaps; Jarvis knows Tony's world, not just this conversation)."""
    from . import memory_jobs
    return memory_jobs.enqueue(repo, text, ch.recent() if hasattr(ch, 'recent') else '')


def _related(repo, text, k=5):
    """The kept facts (not rules) closest to his message, by words and by meaning: what a change of mind could replace."""
    try:
        from . import store
        project = memory.project_key(repo)
        got = {}
        for f, _ in store.search(text, project=project, k=k) + store.semantic(text, project=project, k=k):
            if f['kind'] != 'rule':
                got.setdefault(f['id'], f)
        return list(got.values())[:k]
    except Exception:
        return []

def keep(repo, got, related=None):
    """Keep what REMEMBER found, with its kind, who it is about and until when it holds, and mark the kept facts it
    makes untrue as replaced by it (memory 2.0)."""
    from . import store
    note = got.get('note')
    if not (isinstance(note, str) and note.strip()):
        return None
    kind = got.get('kind') if got.get('kind') in ('note', 'preference', 'deadline', 'person') else 'note'
    who = got.get('person') if isinstance(got.get('person'), dict) else {}
    name = (who.get('name') or '').strip()
    if name:
        try:
            from . import store
            store.person_id(name, relation=(who.get('relation') or '').strip(), org=(who.get('org') or '').strip())
        except Exception:
            pass
    until = None
    if kind == 'deadline' and re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(got.get('until') or '')):
        import datetime as dt
        from . import register
        until = (dt.datetime.fromisoformat(got['until']).replace(tzinfo=register.zone()) + dt.timedelta(days=1)).timestamp()   # holds through the day it is due
    with store.transaction():
        fid = memory.add_note(repo, note.strip(), kind=kind, person=name or None, valid_until=until,
                              source_ref=policy.context().source_ref, scope=got.get('scope', 'project'))
        if not fid:
            return None
        LAST_KEPT.update(text=note.strip(), at=time.time())
        nums = got.get('replaces')
        if related and isinstance(nums, list):
            supersede(repo, note.strip(), [related[k - 1] for k in nums if isinstance(k, int) and 1 <= k <= len(related)])
    return note.strip()

def supersede(repo, new, old_facts):
    """The facts he has changed his mind about are marked as replaced by the new one, in the store and out of the
    plain notes builds and plans read."""
    from . import store
    now = store.find_fact(new, project=memory.project_key(repo)) or store.find_fact(new, project='')
    gone = [f for f in old_facts if now and f['id'] != now['id'] and store.norm(f['text']) != store.norm(new)]
    for f in gone:
        store.supersede(f['id'], now['id'])
    if gone:
        drop = {store.norm(f['text']) for f in gone}
        kept = [n for n in memory.notes(repo) if store.norm(n) not in drop]
        memory._export(repo)
    return [f['text'] for f in gone]

MEMORY_ASK = re.compile(r"\bwhat (do|did) you (know|remember)\b|\bwhat have i told you\b|\b(kya|kitna) (pata|yaad) hai\b")
# about his memory without doubt: a number from the list, everything about someone, what he told Hive
FORGET_SURE = re.compile(r"\b(forget|delete|remove|erase)\s+(number\s+|no\.?\s*|#)?\d+\b|\b(forget|delete|remove|erase) "
                         r"(everything|all) (about|on)\b|\bforget what i (said|told you)\b")
# "forget that": the fact just kept, only when one was kept in the last 10 minutes and no build is running ("this is
# all wrong, forget it" mid-build means stop the build: tests/test_assistant.py caught the first version taking it)
FORGET_THAT = re.compile(r"^\s*(please\s+|ok(ay)?[,.]?\s+|no[,.]?\s+)?(forget|don'?t remember|bhool ja\w*) (that|this)\b")
SHOWN_FACTS = []   # the facts last listed for him, so "forget 2" knows which
LAST_KEPT = {}     # the fact kept from his latest messages, so "forget that" knows which

def _about(text):
    m = re.search(r"\b(?:about|on|regarding|baare mein)\s+(.+?)[?.!]*$", text.strip(), re.I)
    if m:
        return m.group(1).strip()
    m = re.search(r"\bwho is\s+(.+?)[?.!]*$", text.strip(), re.I)
    return m.group(1).strip() if m else ''

def memory_ask(ch, repo, text):
    """"What do you know about Asha?": what Hive keeps, numbered, with how to correct it (memory 2.0)."""
    from . import recall, store
    about = _about(text)
    p = store.person(about) if about else None
    facts = recall.recall(repo, about or text, k=15)
    if p:
        facts = store.facts_about(p['id'], project=memory.project_key(repo)) + [f for f in facts if f.get('person_id') != p['id']]
    facts = [f for f in facts if f.get('trust') == 'owner'][:12] if about else facts[:12]
    if about and not p:   # only what is about it: the recent filler recall adds would not be
        words = set(re.findall(r'"(\w+)"', store._fts_query(about)))   # its real words, not "the" or "about"
        facts = [f for f in facts if words & set(re.findall(r'\w+', f['text'].lower()))]
    SHOWN_FACTS[:] = facts
    if not facts:
        ch.send(f"🐝 I don't have anything kept{' about ' + telegram.esc(about) if about else ''} yet. Tell me and I'll "
                "remember it.", html=True); return 'memory_none'
    head = (f"About <b>{telegram.esc(p['name'])}</b>" + (f" ({telegram.esc(p['relation'])}" + (f", {telegram.esc(p['org'])}"
            if p.get('org') else '') + ')' if p.get('relation') else '') if p else
            f"What I have{' about ' + telegram.esc(about) if about else ''}")
    lines = '\n'.join(f"{i}. {telegram.esc(f['text'])}" for i, f in enumerate(facts, 1))
    ch.send(f"🐝 {head}:\n{lines}\n\n<i>Say \"forget 2\" to drop one, or tell me what's changed.</i>", html=True)
    return 'memory_shown'

def forget_it(ch, repo, text, poll=20):
    """"Forget that" (the fact kept last), "forget 2" (from the list he saw), "forget everything about Asha": always
    shown first and done on his yes (memory 2.0)."""
    from . import store
    low = text.lower()
    m = re.search(r"\b(?:forget|delete|remove|erase)\s+(?:number\s+|no\.?\s*|#)?(\d+)\b", low)
    about = re.search(r"\b(?:everything|all)\s+(?:about|on)\s+(.+?)[?.!]*$", text.strip(), re.I)
    targets, person = [], None
    if m and SHOWN_FACTS and 1 <= int(m.group(1)) <= len(SHOWN_FACTS):
        targets = [SHOWN_FACTS[int(m.group(1)) - 1]]
    elif about:
        person = store.person(about.group(1).strip())
        targets = store.facts_about(person['id']) if person else [f for f, _ in store.search(about.group(1), project=memory.project_key(repo), k=10)]
    elif LAST_KEPT.get('text'):
        f = store.find_fact(LAST_KEPT['text'])
        targets = [f] if f else []
    if not targets and not person:
        ch.send("🐝 Which one? Ask me \"what do you know about ...\" and tell me its number."); return 'forget_unclear'
    if person:
        msg = (f"🐝 Forget everything about <b>{telegram.esc(person['name'])}</b> ({len(targets)} "
               f"thing{'s' if len(targets) != 1 else ''} kept)?")
    else:
        msg = f"🐝 Forget {'this' if len(targets) == 1 else 'these'}?\n" + \
              '\n'.join(f'• {telegram.esc(f["text"])}' for f in targets[:8])
    ch.send(msg, html=True, buttons=[[('🗑 Forget it', 'fgt|yes'), ('Keep it', 'fgt|no')]])
    choice, other = choose(ch, poll, [('fgt|yes', ('yes', 'forget it', 'haan', 'do it')), ('fgt|no', NO_WORDS)])
    if choice != 'fgt|yes':
        ch.send('Very good. Kept as it is.'); return 'forget_kept'
    # The short conversational context is also a retrieval source. Clear it before
    # reporting success, including the persisted compatibility conversation.
    if hasattr(ch, 'history'):
        ch.history = []
        if getattr(ch, 'keep', False):
            with open(telegram.CONVERSATION, 'w', encoding='utf-8') as fh:
                json.dump([], fh)
    for f in targets:
        if f['kind'] != 'rule':
            memory.forget_note(repo, f['text'])
        store.forget(f['id'])
        if f['kind'] == 'rule':   # a standing rule: out of the builders' instructions too
            rules = memory.load(repo)
            for n, r in enumerate(rules, 1):
                if store.norm(r['text']) == f['norm']:
                    memory.forget(repo, n); break
    if person:
        store.forget_person(person['id'])
    LAST_KEPT.clear(); SHOWN_FACTS.clear()
    ch.send("✅ Forgotten. It won't come up again (it's gone from my records within a week).")
    return 'forgotten'

ROUTER_DEFAULT = 'intent'   # Plan routing remains opt-in until full execution qualification.

def router_mode():
    """'intent', fixed 'plan', or result-driven 'adaptive'; HIVE_ROUTER overrides."""
    m = (os.environ.get('HIVE_ROUTER') or ROUTER_DEFAULT).strip().lower()
    return m if m in ('plan', 'intent', 'adaptive') else ROUTER_DEFAULT

def read(ch, text):
    """What the owner means by his newest message, read in the context of the conversation (Gate 38 live test: "Yes",
    "I already told you" and a corrected request were each read alone, and went wrong)."""
    history = ch.recent() if hasattr(ch, 'recent') else ''
    return explain.ask_json(CLASSIFY.format(history=history, text=text)) or {}

PULSE = {}   # Pulse running in the background now ({"running": True}), so two looks never overlap
BUILD = {}   # the build running in the background: {'proc', 'goal', 'started', 'log'}
CURRENT = {}   # the owner's chat, for news from a background build

CHANGED = """You are Hive, a business owner's assistant, in the manner of J.A.R.V.I.S.: calm, precise, warm, a light dry
touch at most. A build he asked for from his phone has just finished, and you are about to send him its screenshots.
What he asked for: "{goal}"
What the builder wrote about its work:
{log}
{check}

Tell him, in 2 or 3 short plain sentences, as a person reporting back: that it's done, and what changed in what he will
see (colours, layout, buttons, wording), in words he would use. No file names, branches, code or technical words. End
with his next step in one short sentence: tell you what's off (or send a picture), or say "ship it" to send it to his
engineer. Address him as "{who}". Reply with JSON only: {{"reply": "..."}}"""

CHANGED = explain.plain(CHANGED)

def what_changed(repo, ch=None):
    """What a finished build changed, in his words, to go with its screenshots; a plain fallback without a model."""
    st = latest_build(repo) or {}
    who = (_who(ch) if ch else '') or 'sir'
    fallback = (f"It's done, {who}. Here's how it looks. Tell me what's off, or send a picture; or say \"ship it\" "
                "and it goes to your engineer.")
    if not st.get('name'):
        return fallback
    log = subprocess.run(['git', '-C', repo, 'log', '--format=%s%n%b', f"{st.get('branch', 'main')}..hive/{st['name']}"],
                         capture_output=True, text=True, encoding='utf-8', errors='replace').stdout
    log = '\n'.join(l for l in log.splitlines() if l.strip() and not l.startswith(('Lock:', 'hive:', 'Co-Authored', 'Release lock')))
    if not log:
        return fallback
    goal = re.sub(r'\n\n# How to work on the look.*', '', st.get('goal', ''), flags=re.S)
    got = explain.ask_json(CHANGED.format(goal=goal[:1500], log=log[:2500], check=st.get('check', ''), who=who))
    reply = got.get('reply') if isinstance(got, dict) else None
    return reply.strip() if isinstance(reply, str) and reply.strip() else fallback

def _unmerged(repo):
    """His latest build if it isn't in his main version yet (then the next build goes on top of it), else None."""
    st = latest_build(repo)
    if not st or not st.get('name'):
        return None
    ref = f"hive/{st['name']}"
    if subprocess.run(['git', '-C', repo, 'rev-parse', '-q', '--verify', ref], capture_output=True).returncode:
        return None
    from . import deploy
    return None if deploy.merged(repo, ref, st.get('branch') or 'main') else st

def _fold(repo, old):
    """The earlier build went into a newer one: set it aside, and withdraw its own pull request if it had one."""
    from . import ship
    try:
        path = os.path.join(old.get('home') or os.path.join(RUNS, old['name']), 'state.json')
        st = json.load(open(path)); st['folded'] = time.time()
        json.dump(st, open(path, 'w'), indent=1)
        if st.get('shipped'):
            ship.close(repo, st)
    except (OSError, ValueError, KeyError):
        pass

def hive_env(**extra):
    """The environment for a Hive process started from here: it can always import Hive, installed or run from a
    source folder (Gate 108: a build started in his project's folder died with "No module named hive", and he heard
    only "it stopped partway")."""
    pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.environ.get('PYTHONPATH', '')
    if pkg_root not in path.split(os.pathsep):
        path = pkg_root + (os.pathsep + path if path else '')
    return dict(os.environ, PYTHONPATH=path, **extra)

def background_build(repo, goal, ch=None, interview=True, report=True, workers=None):
    """Run `hive start` for this goal in the background, so Hive keeps answering him; if it stops, tell him why at once
    (a cloud build stopped on "unsaved changes", and only the server's log knew)."""
    import subprocess, sys, tempfile, threading
    ch = ch or CURRENT.get('ch')
    gf = tempfile.NamedTemporaryFile('w', suffix='.md', delete=False); gf.write(goal); gf.close()
    log = os.path.join(os.path.expanduser('~'), '.hive', 'build.log')
    os.makedirs(os.path.dirname(log), exist_ok=True)
    prev = _unmerged(repo)   # his latest build, not merged yet: this one builds on top of it (Gate 107)
    cmd = (argv(os.environ['HIVE_BUILD_CMD']) if os.environ.get('HIVE_BUILD_CMD') else   # tests: a stand-in
           [sys.executable, '-m', 'hive', 'start', '--overnight', '--goal', gf.name] +
           (['--on', f"hive/{prev['name']}"] if prev else []) +
           ([] if interview else ['--no-interview']) +   # a plan step: its one question was asked already
           (['--agent', team.chosen()['agent']] if team.chosen().get('agent') else []) +   # the team he chose by phone
           (['--workers', str(workers)] if workers else
            ['--workers', str(team.chosen()['workers'])] if team.chosen().get('workers') else []))
    from . import tasks
    active = tasks.ACTIVE_STEP.get()
    proc = subprocess.Popen(cmd, cwd=repo, start_new_session=os.name != 'nt',   # so a stop ends its builders too
                            stdout=open(log, 'w'), stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                            env=hive_env(HIVE_FROM_PHONE='1', HIVE_PLAN_TASK=active[0] if active else ''))
    BUILD.update(proc=proc, goal=goal, started=time.time(), log=log, stopped=False)

    def watch():
        rc = proc.wait()
        if rc != 0 and (rc < 0 or rc in (130, 137, 143) or BUILD.get('stopped') or BUILD.get('proc') is not proc):
            return   # stopped on purpose (by him, or replaced by a new build): no alarm (live: "technical problem")
        if rc != 0 and ch is not None:
            lines = [l.strip() for l in open(log, encoding='utf-8', errors='replace').read().splitlines() if l.strip()]
            why = plain_reason(lines[-1] if lines else '')   # in his words, with the next step; never a raw error
            try:
                ch.send(f"⚠️ <b>The build stopped before it finished.</b>\n\n{telegram.esc(why)}", html=True)
            except Exception:
                pass
        if rc == 0 and prev:   # the earlier build is part of this one now: one line of work, one pull request
            _fold(repo, prev)
        if rc == 0 and report and ch is not None and BUILD.get('proc') is proc and not BUILD.get('stopped'):
            from . import screens   # a frontend: he sees it, unasked (the owner: "share the screenshot on my phone")
            try:
                if screens.available() and screens.is_frontend(repo):
                    show(ch, repo, intro='🎉 ' + telegram.esc(what_changed(repo, ch)))
            except Exception:
                pass
    threading.Thread(target=watch, daemon=True).start()

    def keep_an_eye():   # speak up unprompted (the owner: no gaps): a builder making no progress is worth his attention
        from . import screens
        seen, told = {}, set()
        while proc.poll() is None:
            time.sleep(float(os.environ.get('HIVE_WATCH_SECONDS', 60)))
            run = team.current_run()
            if not run or ch is None:
                continue
            news = screens.found(run) if run not in told else ''
            if news:   # the research, brought back while the work goes on (the owner: "I'm on the research, and
                told.add(run)   # I'll bring back the results")
                try:
                    ch.send(f"🔎 <b>Had a look, sir.</b> {telegram.esc(news[:600])}\n\n<i>Working it into your page now; "
                            "screenshots when it's done.</i>", html=True)
                except Exception:
                    pass
            for r in team.stuck(run, seen):
                doing = '; '.join(r['holding'])[:160] or 'its piece of the work'
                try:
                    ch.send(f"⏳ <b>{r['name']} ({r['agent']}) may be stuck, sir.</b> It has been on {telegram.esc(doing)} "
                            f"for {r['minutes']} minutes without finishing anything. Say \"stop {r['name']}\" and its work "
                            "goes back to the others, or leave it be; it may simply be a hard piece.", html=True)
                except Exception:
                    pass
    threading.Thread(target=keep_an_eye, daemon=True).start()
    return proc

PLAIN_REASONS = [   # why a build stopped, as he should hear it (the owner: "everyone who depends on Hive is Iron Man")
    (r'unsaved changes', "Your project has edits that aren't saved into it yet, and the builders must start from exactly "
     "what you have. Save them (in git: commit), or ask your engineer to, then say \"build again\"."),
    (r'not a git repository', "I'm not pointed at your project's folder. Start me from inside it, then say \"build again\"."),
    (r'need tests|no results|could not find your tests', "Your project has no tests I can run, and the builders need them "
     "to know when the work is right. Your engineer can add a few, or tell me which command runs them."),
    (r'usage limit', "Claude's usage limit was reached. I'll carry on by myself as soon as it resets; nothing is lost."),
    (r'log ?in|authenticat|login has expired', "Claude's login on this computer has expired. Open Claude once and log in, "
     "and I'll carry on from where the builders stopped."),
    (r'no space left|disk', "This computer is out of disk space. Free some up, then say \"build again\"."),
]

def plain_reason(line):
    """The reason a build stopped, in his words with the next step, never a raw error line."""
    for pattern, said in PLAIN_REASONS:
        if re.search(pattern, line or '', re.I):
            return said
    if line and not re.search(r'error|exception|traceback|failed|fatal|refused|denied|not found|cannot|can\'t|'
                              r'no such|invalid|timed? ?out|killed', line, re.I):   # Hive's own words, not an error
        return "It stopped partway without saying why. Say \"build again\" and I'll pick it up."
    return (f"It hit a technical problem I can't fix from here (for your engineer: {line.strip()[:200]}). Say \"build "
            "again\" to retry, or send that line to your engineer.") if line else "No reason was recorded. Say \"build again\" to retry."

def _stop(p):
    """End a background build and every builder it started."""
    import signal
    if BUILD.get('proc') is p:
        BUILD['stopped'] = True   # before the kill: the watcher must not report it as a failure (Windows exits 1)
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
    if PLAN.get('running'):   # a plan he gave the go-ahead to, step by step
        return (f"A build is running: his plan for \"{PLAN['goal'][:120]}\", step {PLAN['step']} of {len(PLAN['steps'])} "
                f"({PLAN['steps'][PLAN['step'] - 1]['title']}); steps done: {PLAN['step'] - 1}.")
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
    return (f"The last build stopped before it finished: {BUILD['goal'][:200]}. Why, in his words: "
            f"{plain_reason(lines[-1] if lines else '')}")

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

LOOK = """You are Hive, the business owner's assistant, answering him about his own product. You are in a scratch copy
of his project: read the code to find the answer. When the answer depends on a case the code does not make obvious
(a date, an amount, an edge), check it: run the tests or a small script here. This folder is a throwaway copy, so
nothing you do reaches his product; never use the network and never install anything. Answer what the product actually
does today, so he gets it in one glance on his phone: the answer first, in one short sentence ("Cooks get ₹70 a lunch,
paid every Monday."), then at most two more short sentences, only if they add something he needs: three short
sentences and about 45 words in all, at most. No examples, names or counts he didn't ask for; he can ask for more. Everyday words, the
way a sharp assistant talks to a busy founder: no "on paper", "without exception", "I checked it against", no hedging,
no repeating what he asked. If you found something no page or document says, give it in one line with its reason, and
ask one yes-or-no question ("One thing your policy doesn't say: cooks with no complaints in a month get an extra ₹500.
Is that your rule? I can add it to the policy."). If you checked by running it, say so in a few words ("I tried it: ..."). No code,
file names or technical terms unless he asks, or he writes technically himself (then answer in his terms, with the
file and function names). If the code does not settle it, say so plainly and say what would.
Reply in his language and his script: if he writes Hindi-English in English letters, answer the same way, never in
Devanagari. Address him as "{who}".
{data}
The conversation so far:
{history}

His question: "{text}"

Reply with the answer only."""

LOOK = explain.plain(LOOK)

ASK_CMD = os.environ.get('HIVE_LOOK_CMD', __import__('hive').claude_cmd(__import__('hive').READ_TOOLS))

def _scratch(repo):
    """A throwaway copy of his project to read and run (the owner: no gaps; an answer can be checked by running it).
    His own folder is never written to. Dependency folders are linked in, not copied."""
    import shutil, tempfile
    from .start import detect_links, _link
    work = tempfile.mkdtemp(prefix='hive_look_')
    copy = os.path.join(work, 'project')
    links = detect_links(repo)
    shutil.copytree(repo, copy, symlinks=True, ignore=shutil.ignore_patterns('.git', *[os.path.basename(l) for l in links]))
    try:
        _link(repo, copy, links)
    except OSError:   # Windows without symlink rights: the code can still be read, and run where it needs no packages
        pass
    return work, copy

def _data_note(repo):
    """For the code-reading assistant: the data he gave Hive, how to read it, and to explain what only the data shows
    (Gate 108: it found an unwritten Rs 500 payment to some cooks by searching the computer, then asked him what earns
    it, though the data showed the reason: no complaints the month before)."""
    from . import access
    srcs = access.load(repo)
    if not srcs:
        return ''
    lines = []
    for s in srcs:
        if s['kind'] == 'db':
            lines.append(f"- {s['name']} (database): read it with `python3 -m hive access sql --name \"{s['name']}\" "
                         f"\"SELECT ...\"` (one SELECT at a time; anything else is refused)")
        elif s['kind'] == 'file':
            lines.append(f"- {s['name']} (file): {s['where']}")
        else:
            lines.append(f"- {s['name']} ({s['kind']}): ask `python3 -m hive access ask \"<question>\"`")
    return ("\nHe has also given you read-only access to his business data:\n" + '\n'.join(lines) + "\n"
            "When his question is about how his business actually runs (who is paid what, who gets what, what happens "
            "in practice), check his data as well as the code: the code says what should happen, the data what does. If "
            "the data shows something no page or document explains (an extra payment, a discount, a pattern), find what "
            "explains it in the data itself before asking him: compare who gets it with who doesn't, and when, against "
            "everything else you can see (complaints, plans, areas, dates). Then tell him your best reading and ask him "
            "to confirm it.\n")

def look(ch, repo, text):
    """Answer a question about his product by having Claude read his code, and run it where a case needs checking, in a
    throwaway copy: "how do refunds work?" gets what the code does, not a guess. Shows "typing..." while it works.
    None if Claude cannot answer."""
    import shutil, threading
    box, done = {}, threading.Event()

    def run():
        work = None
        try:
            work, copy = _scratch(repo)
            p = subprocess.run(argv(ASK_CMD), cwd=copy, input=LOOK.format(
                who=_who(ch) or 'sir', history=ch.recent() if hasattr(ch, 'recent') else '', text=text,
                data=_data_note(repo)), env=hive_env(HIVE_ACCESS_REPO=os.path.abspath(repo)),
                capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=300)
            reply = json.loads(p.stdout)
            if not reply.get('is_error'):
                box['answer'] = (reply.get('result') or '').strip()
        except Exception:
            pass
        finally:
            if work:
                shutil.rmtree(work, ignore_errors=True)
        done.set()
    threading.Thread(target=run, daemon=True).start()
    typing = getattr(ch, 'typing', None)
    while not done.wait(4):   # keep "typing..." up while Claude works (Telegram shows it for about 5 seconds)
        if callable(typing):
            typing()
    return box.get('answer') or None

WHO_COMPLAINS = r"(customers?|users?|clients?|buyers?|sellers?|creators?)"
COMPLAINT_WORDS = re.compile(rf"\b{WHO_COMPLAINS}\b[^.?!]{{0,40}}\b(complain(s|ed|ing)?|ne shikayat)\b|"
                             rf"^(a |one |my |this )?{WHO_COMPLAINS} (says|said|told me|is angry|is upset|got charged|was "
                             r"charged|didn'?t get|never got)\b")

COMPLAINT = """A customer of his product complained. What the customer says (as he passed it on):
"{text}"

His standing rules for how the product should behave (numbered):
{rules}

Find what in the product makes this happen: read the code, and try the customer's case if you can (a small script).
Then say, in at most 4 short sentences: what happened to the customer, and why. Is the product doing what one of his
rules says (then the rule is the cause: say which, by number, in his words), or is it not doing what he wants (a bug)?
End with one last line, exactly one of:
VERDICT: rule <number>
VERDICT: bug
VERDICT: unclear"""

COMPLAINT = explain.plain(COMPLAINT)

def complaint(ch, repo, text, poll, apply_build=None):
    """A customer's complaint, linked to his rules: Claude reads his code and tries the case; either it is one of his
    own rules at work (he can change it in a message) or a bug (one tap fixes his latest build). The Tony scenario:
    "a customer says X" should get "that's your rule 3, sir; want it changed?", not a search through the code."""
    rules = memory.load(repo)
    listing = '\n'.join(f'{n}. {r["text"]}' for n, r in enumerate(rules, 1)) or '(none yet)'
    from . import numbers
    numbers.mark(repo, text[:200], kind='complaint')   # for the brief: what customers hit
    answer = look(ch, repo, COMPLAINT.format(text=text, rules=listing))
    if not answer:
        ch.send("🐝 I couldn't trace that one just now, sir. Tell me what the customer did, step by step, and I'll try again.")
        return 'complaint_unclear'
    m = re.search(r'VERDICT:\s*(rule\s*(\d+)|bug|unclear)', answer, re.I)
    said = re.sub(r'\n?\s*VERDICT:.*$', '', answer, flags=re.I | re.S).strip()
    verdict = (m.group(1).lower() if m else 'unclear')
    n = int(m.group(2)) if m and m.group(2) else 0
    if verdict.startswith('rule') and 1 <= n <= len(rules):
        ch.send(f"🐝 {telegram.esc(said)}\n\n📌 <b>That's your rule {n}:</b> {telegram.esc(rules[n - 1]['text'])}\n\n"
                "<i>If you want it to work differently, just tell me how, and I'll change the rule and your latest build.</i>",
                html=True)
        return 'complaint_rule'
    st = latest_build(repo)
    if verdict == 'bug' and st and apply_build:
        ch.send(f"🐝 {telegram.esc(said)}\n\n🐞 <b>That's not what you want, so it's a fault.</b> Shall I fix it in your "
                "latest build? Every test is checked again, and it stays a separate copy.", html=True,
                buttons=[[('🛠 Fix it', 'cmp|fix')], [('Leave it', 'cmp|no')]])
        choice, other = choose(ch, poll, [('cmp|fix', ('fix it', 'yes', 'haan', 'go ahead', 'theek karo')), ('cmp|no', NO_WORDS)])
        if other is not None:
            return handle(ch, repo, other, poll, apply_build)
        if choice != 'cmp|fix':
            ch.send('Very good, I have left it as it is.'); return 'complaint_kept'
        ch.send("🛠 On it. I'll tell you when it's fixed.")
        apply_build(st, f'A customer complained: "{text}". This is a fault, not what the owner wants: {said} Fix it so '
                        'this cannot happen to a customer again, and add a test for the customer\'s case.', None)
        ch.send(f"✅ <b>Fixed, sir.</b> {telegram.esc((latest_build(repo) or {}).get('check', ''))} Say \"ship it\" and it "
                "goes to your engineer.", html=True)
        return 'complaint_fixed'
    ch.send('🐝 ' + telegram.esc(said), html=True)
    return 'complaint_bug' if verdict == 'bug' else 'complaint_unclear'

BRIEF_WORDS = re.compile(r"^\s*(what'?s new|whats up|any news|brief( me)?|morning brief|catch me up|update me|kya naya|"
                         r"kya chal raha)\b")

PREVIEW_WORDS = re.compile(r"\b(send me (a|the) link|preview( link)?|let me try it|a link to try|link bhejo|try it on my "
                           r"phone|can i try it)\b")
LIVE_WORDS = re.compile(r"\b(put it live|make it live|go live|take it live|deploy( it)?|launch it|publish it|live kar do|"
                        r"to production|on production|to prod)\b")
SKIP_WORDS = re.compile(r"\b(skip(ping)?|without|no|bina|chhod\w*)\s+(the\s+|any\s+)?tests?\b|\b(main|master)\b")
CONNECT_WORDS = re.compile(r"\b(connect|link|use|set up|setup|we use|we're on|we are on|hosted on|it's on|it is on|"
                           r"deployed on|our site is on|switch to|move to)\b[^.?!]{0,30}"
                           r"\b(vercel|netlify|railway|azure|fly|render)\b")

# a question about his business's own figures, answered from the data he gave (hive/access.py), not from the code
DATA_WORDS = re.compile(r"^\s*(so\s+|and\s+|ok(ay)?\s+)?(how many|how much|kitne|kitna|kitni|total|what('s| is| are| was| were)"
                        r" (my|our|the|today'?s|this week'?s|this month'?s|last month'?s) (revenue|sales|orders?|sign-?ups?|"
                        r"users?|customers?|payouts?|refunds?|numbers|gmv|income|profit|signups|traffic|visitors|"
                        r"subscribers?|churn|conversion)|which (customers?|sellers?|creators?|products?|users?|orders?|"
                        r"items?|cities|plans?)|who (are|is|were|was) (my|our|the) (top|best|biggest|most|latest|newest))\b")

def connect_data(ch, repo, text):
    """'Here's our admin API https://... key ...' / 'postgres://...': keep it read-only, try it now, say what he gave."""
    from . import access
    src = access.detect(text)
    if not src:
        ch.send("I couldn't find the address in that, sir. Send the link itself (https://...) or the database address "
                "(postgres://...).")
        return 'connect_data_none'
    kept = access.add(repo, src['kind'], src['where'], headers=src.get('headers'))
    ok, line = access.check(kept)
    ch.send((f"✅ <b>Connected, read-only: {telegram.esc(kept['name'])}.</b> " if ok else
             f"⚠️ <b>{telegram.esc(kept['name'])}:</b> ") + telegram.esc(line) +
            ("\n\nAsk me anything it holds: <i>\"how many orders this week?\"</i>. I only read; I never change it."
             if ok else "\n\nI kept it; send it again once it's fixed."), html=True)
    return 'connect_data' if ok else 'connect_data_failed'

# he is stepping away (the owner: "if the founder says I'm feeling sleepy, Hive should say: shall we move to the cloud so
# you can shut your computer and I carry on, or would you like me to proceed another way")
AWAY_WORDS = re.compile(r"\b(sleepy|feeling sleepy|going to (sleep|bed)|off to (sleep|bed)|time (for|to) (bed|sleep)|"
                        r"good ?night|(i'?m|i am|feeling|so|very|really|getting) (tired|exhausted|sleepy|knackered)|"
                        r"need (some )?(rest|sleep)|calling it a (day|night)|signing off|logging off|"
                        r"done for (the )?(day|night|today)|"
                        r"(shut|shutting|switch(ing)?( off)?|turn(ing)? off|clos(e|ing)|power(ing)? off) (down )?(my |the )?"
                        r"(laptop|computer|pc|system|mac|machine)( down| off)?|"
                        r"heading (out|home)|leaving (the office|for (the day|home)|now|for a while)|stepping out|"
                        r"be back (later|tomorrow|in the morning)|bye for (now|today|tonight)|"
                        r"so (raha|rahi|jaunga|jaungi|jata|jati) (hu|hoon|hun)?|sone ja\w*|neend\w*|thak (gaya|gayi)|"
                        r"nikal raha|ghar ja (raha|rahi))\b")

REQUEST = re.compile(r"^\s*(please\s+|can you\s+|could you\s+)?(add|make|build|create|change|update|fix|remove|put|write|"
                     r"design|show|send|use|set|rename|move)\b")

def is_away(low):
    """He is stepping away, not asking for something about sleep or nights ("add a good night message" is a build)."""
    return bool(AWAY_WORDS.search(low)) and len(low.split()) <= 25 and not REQUEST.match(low)

def in_cloud(repo):
    """Hive itself is running on the cloud machine (his computer can be off)."""
    return bool(os.environ.get('HIVE_IN_CLOUD') or
                os.path.abspath(repo).startswith(os.path.join(os.path.expanduser('~'), 'hive-cloud')))

RESUME = lambda: os.path.join(os.path.expanduser('~'), '.hive', 'resume.json')   # work for the cloud copy to pick up

def _work_left():
    """What is running, as one goal a build can be given again: the build, or the plan's steps not done yet."""
    if PLAN.get('running') and PLAN.get('steps'):
        from . import plan as planner
        k = max(1, PLAN.get('step', 1))
        answers = PLAN.get('answers') or [''] * len(PLAN['steps'])
        return '\n\n'.join(planner.instruction(s, answers[i]) for i, s in enumerate(PLAN['steps']) if i + 1 >= k)
    p = BUILD.get('proc')
    return BUILD.get('goal', '') if p is not None and p.poll() is None else ''

def away(ch, repo, text, poll, apply_build=None, start_build=None, cloud=None):
    """He is stepping away: say where things stand and offer the way to carry on that fits: the cloud, so his computer
    can be off (recommended when work is running); this computer, left on; stop for tonight; or something overnight."""
    who = _who(ch)
    sir = f', {telegram.esc(who)}' if who else ', sir'
    work = _work_left()
    if in_cloud(repo):
        ch.send(f"😴 Sleep well{sir}. I'm running in the cloud, so your computer can be off. " +
                (f"I'll keep going with: {telegram.esc(BUILD.get('goal', PLAN.get('goal', ''))[:150])}. " if work else '') +
                "Your morning brief will be waiting.", html=True)
        return 'away_cloud'
    if work:
        opts = ([('☁️ Move to the cloud: shut your computer, I carry on', 'awy|cloud')] if cloud else []) + [
            ('💻 Carry on here (I\'ll leave my computer on)', 'awy|here'), ('⏸ Stop for tonight', 'awy|stop')]
        from . import cloud_aws
        size = cloud_aws.preferred() if cloud_aws.preferred() in cloud_aws.PRICE else cloud_aws.SIZES[0][0]
        hour = cloud_aws.PRICE[size] + cloud_aws.ADDRESS
        tip = (f"<b>My suggestion:</b> let me move to the cloud (about ${hour:.2f} an hour while it runs, ${hour * 8:.2f} "
               "for a night; say \"delete the cloud machine\" in the morning and it stops). I'll restart this "
               "work there in about 5 minutes; once I say I'm there, you can shut your computer, and the morning "
               "brief will tell you how it went." if cloud else
               "To finish it, I need this computer on and awake through the night (plugged in, sleep turned off). "
               "If you'd rather shut it, I can stop here and pick it up in the morning.")
        ch.send(f"😴 Of course{sir}, get some rest. Right now I'm working on: "
                f"<i>{telegram.esc((BUILD.get('goal') or PLAN.get('goal') or '')[:160])}</i>.\n\n{tip}\n\n"
                "How would you like me to carry on?", html=True, buttons=[[o] for o in opts])
        options = ([('awy|cloud', ('cloud', 'move', 'shift'))] if cloud else []) + [
            ('awy|here', ('here', 'leave it on', 'carry on', 'keep going')), ('awy|stop', ('stop', 'pause', 'morning'))]
    else:
        ch.send(f"😴 Of course{sir}, get some rest. Nothing is running, so you can shut your computer whenever you "
                "like.\n\nShall I build something while you sleep? Tell me what, and it'll be ready with your morning "
                "brief" + (", built in the cloud so your computer can be off." if cloud else
                           " (this computer needs to stay on for that)."), html=True,
                buttons=[[('🌙 Yes, build something overnight', 'awy|night')], [('😴 Nothing tonight', 'awy|none')]])
        options = [('awy|night', ('overnight', 'build', 'yes')), ('awy|none', ('nothing', 'no'))]
    choice, other = choose(ch, poll, options)
    if other is not None:   # he answered with something else (often the thing to build): that, as a new message
        return handle(ch, repo, other, poll, apply_build, start_build, cloud)
    if choice == 'awy|none':
        ch.send(f"Sleep well{sir}. Your morning brief will be waiting.", html=True); return 'away_none'
    if choice == 'awy|night':
        ch.send("🌙 Very good. What would you like ready by morning? Tell me in a line or two."); return 'away_night'
    if choice == 'awy|here':
        ch.send(f"💻 Very good{sir}. Leave it plugged in, with sleep turned off, and I'll keep going. I'll tell you here "
                "the moment it's done, and the morning brief will have it too. Sleep well.", html=True)
        return 'away_here'
    if choice == 'awy|stop':
        p = BUILD.get('proc')
        if p is not None and p.poll() is None:
            BUILD['stopped'] = True; _stop(p)
        if PLAN.get('running'):
            PLAN['cancel'] = True
        ch.send(f"⏸ Stopped for tonight{sir}. Nothing half-done is handed over. In the morning, say \"build again\" and "
                "I'll pick it up. Sleep well.", html=True)
        return 'away_stopped'
    # to the cloud: leave the work for the cloud copy to restart, move, and only then stop it here
    import json as _json
    os.makedirs(os.path.dirname(RESUME()), exist_ok=True)
    _json.dump({'goal': work, 'said': (BUILD.get('goal') or PLAN.get('goal') or '')[:300], 't': time.time()},
               open(RESUME(), 'w', encoding='utf-8'))
    from . import logins
    if not logins.ensure(ch, 'aws', poll):   # an expired AWS sign-in is renewed from his phone, not a dead end
        os.remove(RESUME())
        ch.send(f"Then I'll carry on here{sir}: please leave your computer on and awake tonight.", html=True)
        return 'away_login_needed'
    ch.send("☁️ Moving to the cloud now: about 5 minutes. Keep your computer on until I say I'm there.")
    try:
        try:
            try:
                rc = cloud(repo, True, True, size=size)   # with his Claude login: builders work there; his size
            except TypeError:
                rc = cloud(repo, True, True)
        except TypeError:
            rc = cloud(repo, True)
    except Exception as e:
        rc = f'{e!r}'[:120]
    if rc != 0:
        try:
            os.remove(RESUME())
        except OSError:
            pass
        ch.send(f"⚠️ I couldn't move to the cloud{sir}" + (f" ({telegram.esc(str(rc))})" if isinstance(rc, str) else '') +
                ", so I'm carrying on here: please leave your computer on and awake tonight. Your morning brief will "
                "say how it went.", html=True)
        return 'away_cloud_failed'
    try:   # handed over: the cloud has its copy; this one must not be handed over again on the next move (Gate 111)
        os.remove(RESUME())
    except OSError:
        pass
    p = BUILD.get('proc')   # the cloud copy restarts it; this copy stops
    if p is not None and p.poll() is None:
        BUILD['stopped'] = True; _stop(p)
    if PLAN.get('running'):
        PLAN['cancel'] = True
    ch.send(f"✅ <b>I'm in the cloud{sir}.</b> You can shut your computer now. I'm picking the work up there, and "
            "I'll tell you here when it's done. Sleep well.", html=True)
    return 'moved'

def resume_here(ch, repo):
    """On waking (the cloud copy's listener): restart the work his computer handed over, and say so. Returns the goal."""
    import json as _json
    try:
        r = _json.load(open(RESUME(), encoding='utf-8'))
        os.remove(RESUME())
    except (OSError, ValueError):
        return ''
    if not r.get('goal') or time.time() - r.get('t', 0) > 12 * 3600:   # stale: not tonight's hand-over (Gate 111
        return ''   # restarted work handed over the night before, and the machine then refused to be deleted mid-build)
    ch.send("☁️ I'm in the cloud and picking up where your computer left off: <i>" +
            telegram.esc((r.get('said') or r['goal'])[:200]) + "</i>. I'll tell you here when it's done.", html=True)
    background_build(repo, r['goal'], ch, interview=False)
    return r['goal']

def _build_ref(st):
    return f"hive/{st['name']}"

def preview_it(ch, repo, poll=20):
    """'Send me a link': the latest build at its own address on his host, to tap and use. His live product untouched.
    With no host set up but AWS on this computer: a test deploy on his cloud machine, for two hours (hive/trydeploy.py)."""
    from . import deploy
    st = latest_build(repo)
    if not st:
        ch.send("Nothing built yet to try, sir. Tell me what to build first."); return 'nothing'
    if deploy.ready(repo)[0] == 'none' and shutil.which('aws') and not in_cloud(repo):
        return try_deploy(ch, repo, st, poll)
    if not host_login(ch, repo, poll):
        return 'login_needed'
    from . import actions
    sha = subprocess.run(['git', '-C', repo, 'rev-parse', _build_ref(st)], capture_output=True, text=True).stdout.strip()
    if not re.fullmatch(r'[0-9a-f]{40,64}', sha):
        return 'no_preview'
    aid = actions.confirm(ch, 'preview', {'ref': sha},
                          f"Publish a preview of <b>{telegram.esc(_build_ref(st))}</b> on your configured host?",
                          poll, yes_label='Publish preview')
    if not aid:
        return 'no_preview'
    r = actions.execute_dict(aid, lambda a: deploy.preview(repo, a['ref']))
    if r.get('why') == 'first':
        ch.send('This host requires a first production deployment. Configure it separately before publishing previews.')
        return 'no_preview'
    if r['ok']:
        wall = ("\n\nVercel keeps previews private: it will ask you to sign in to Vercel first, and only people on your "
                "Vercel team can open it." if deploy.config(repo).get('host') == 'vercel' else '')   # Gate 110
        ch.send(f"🔗 <b>Here it is, sir, to try on your phone:</b>\n{r['url']}{telegram.esc(wall)}\n\n<i>A separate copy: your "
                "live product is untouched. Tell me what's off, or say \"ship it\".</i>", html=True)
        return 'previewed'
    ch.send('🔗 ' + telegram.esc(r['say']), html=True)
    return 'no_preview'

def try_deploy(ch, repo, st, poll):
    """No host set up: offer the build's pages on a test machine on his AWS, at a secret address, for two hours."""
    from . import logins, trydeploy
    ch.send("🔗 You haven't set up a hosting service yet, sir. I can put this build on a test machine on your AWS "
            "account, at a private link, for up to two hours (about $0.03 an hour), then take it down and delete the "
            "machine. Your live product isn't touched.",
            buttons=[[('🔗 Yes, put it up', 'tdp|yes')], [('Not now', 'tdp|no')]])
    choice, other = choose(ch, poll, [('tdp|yes', ('yes', 'put it up', 'go', 'haan')), ('tdp|no', NO_WORDS)])
    if other is not None:
        return handle(ch, repo, other, poll)
    if choice != 'tdp|yes':
        ch.send("Very good. Screenshots it is: say \"show me\"."); return 'no_preview'
    if not logins.ensure(ch, 'aws', poll):
        return 'login_needed'
    ch.send("🛠 Putting it up. If I have to make the test machine first, that's about 5 minutes.")
    try:
        r = trydeploy.up(repo, _build_ref(st), say=lambda *a: None)
    except Exception as e:
        r = {'ok': False, 'say': f"That didn't work ({str(e)[:120]})."}
    if not r['ok']:
        ch.send('🔗 ' + telegram.esc(r['say']), html=True); return 'no_preview'
    ch.send(f"🔗 <b>Here it is, sir, to try on your phone:</b>\n{r['url']}\n\n<i>A private test copy, up for two hours. "
            "Say \"take it down\" when you're done, and I'll remove it" + (" and delete the test machine" if r.get('made')
            else '') + ".</i>", html=True)
    return 'test_deployed'

def take_down(ch, repo):
    from . import trydeploy
    ch.send('🧹 ' + telegram.esc(trydeploy.down(repo)), html=True)
    return 'taken_down'

def go_live(ch, repo, poll):
    """'Put it live': only his own main version, only after his engineer merged the build, only on his yes, and only with
    every test passing (hive/deploy.py). An unmerged build is never put live."""
    from . import deploy, numbers
    st = latest_build(repo)
    if not st:
        ch.send("Nothing built yet to put live, sir."); return 'nothing'
    if deploy.config(repo) and not host_login(ch, repo, poll):
        return 'login_needed'
    state, why = deploy.ready(repo)
    if state != 'ok':
        ch.send('🚀 ' + telegram.esc(why)); return 'not_connected'
    main = deploy.merged(repo, _build_ref(st), st.get('branch') or 'main')
    if not main:
        ch.send("🚀 Not yet, sir: your engineer hasn't merged it into your main version, and I only put live what they "
                "have reviewed. " + ("It's with them now; the moment it's merged, say \"put it live\"." if st.get('shipped')
                                     else "Say \"ship it\" and it goes to them; once merged, I'll put it live."))
        return 'not_merged'
    host = deploy.title(repo)
    from . import actions
    sha = subprocess.run(['git', '-C', repo, 'rev-parse', main], capture_output=True, text=True).stdout.strip()
    if not re.fullmatch(r'[0-9a-f]{40,64}', sha):
        ch.send('I could not identify the exact merged version.'); return 'not_live'
    aid = actions.confirm(ch, 'go_live', {'sha': sha, 'test_cmd': st.get('test_cmd')},
                          f"Deploy merged version <code>{sha[:12]}</code> on {telegram.esc(host)} after its tests pass?",
                          poll, yes_label='Put it live')
    if not aid:
        ch.send('No new deployment was started.'); return 'not_live'
    deploy.note_before(repo, main)   # the first time: what was live before, so "undo that" can go back
    r = actions.execute_dict(aid, lambda a: deploy.live(repo, a['sha'], a['test_cmd']))
    if not r['ok']:
        ch.send('⚠️ ' + telegram.esc(r['say'])); return 'live_failed'
    numbers.mark(repo, f'"{_goal_words(st)}" went live')
    ch.send(f"✅ <b>It's live, sir.</b>" + (f"\n{r['url']}" if r.get('url') else '') + "\n\nI'll tell you in the "
            "morning brief how your numbers move.", html=True)
    return 'live'

def _goal_words(st):
    from . import ship
    return ship.title(st)[6:][:80]

def host_login(ch, repo, poll=20):
    """His host's tool installed and signed in, from his phone if need be (Vercel: hive/logins.py). True when ready."""
    from . import deploy, logins
    host = deploy.config(repo).get('host')
    return logins.ensure(ch, host, poll) if host in logins.SERVICES else True

def connect_host(ch, repo, text, poll=20):
    """'We're on Vercel': remember where his product lives; install its tool and sign in from his phone where Hive can
    (Vercel); otherwise say plainly what his engineer does once."""
    from . import deploy
    host = CONNECT_WORDS.search(text.lower()).group(2)
    deploy.setup(repo, host)
    host_login(ch, repo, poll)
    state, why = deploy.ready(repo)
    if host == 'render':
        ch.send("🔌 Noted: Render. To put it live I need its deploy hook address (Render, Settings, Deploy Hook); your "
                "engineer runs: hive deploy setup render --hook <address>.")
    elif state == 'ok':
        ch.send(f"🔌 <b>Connected: {host.title()}.</b> Say \"send me a link\" to try a build on your phone, and \"put it "
                "live\" once your engineer has merged it.", html=True)
    else:
        ch.send(f"🔌 Noted: {host.title()}. " + telegram.esc(why))
    return 'connected'

PLAN = {}   # the plan he said yes to: {'goal', 'steps', 'step', 'running'}
GOAL_WORDS = re.compile(r"(^|[.!?]\s*)(i want|we need|help me|how (do|can) (i|we))\b[^.?!]{0,60}\b(more|fewer|increase|"
                        r"grow|reduce|boost|get more|get them)\b|\b(badhana|badhao|zyada|kam karna)\b|\b(sign-?ups?|signups|"
                        r"sales|conversions?|retention|churn|engagement)\b[^.?!]{0,30}\b(low|down|dropping|falling|bad|weak)\b")

def pursue(ch, repo, text, poll, apply_build=None, run=True):
    """A business goal ("I want more creators signing up"): read his product, propose a plan in his words, ask the few
    things only he can decide, then build it step by step on one branch, showing each (the owner: "Tony just gives
    him the business"). run=False stops after the plan is agreed (tests)."""
    from . import plan as planner
    ch.send("🔎 On it, sir. Let me look at your product with that in mind; a minute or two.")
    import threading
    def think():
        box, done = {}, threading.Event()
        def go():
            from . import access   # what his data holds: what the product doesn't show may be there (Gate 106's miss)
            try:
                seen = access.for_plan(repo)
            except Exception:
                seen = []
            box['plan'] = planner.make(repo, text, memory.notes(repo) + seen, [r['text'] for r in memory.load(repo)])
            done.set()
        threading.Thread(target=go, daemon=True).start()
        while not done.wait(4):
            if callable(getattr(ch, 'typing', None)):
                ch.typing()
        return box.get('plan')
    p = think()
    asks = p.get('missing') if p else None
    asks = [asks] if isinstance(asks, str) and asks.strip() else (asks or [])
    if asks:   # what the product can't show (Gate 106's one miss: a reward only in his payouts; Gate 115: up to 3)
        if len(asks) == 1:
            head, body = "Before I plan it, one thing your product can't tell me:", telegram.esc(asks[0])
        else:
            head = f"Before I plan it, {len(asks)} things your product can't tell me:"
            body = '\n'.join(f"{k}. {telegram.esc(q)}" for k, q in enumerate(asks, 1)) + "\n\n<i>One message is fine.</i>"
        ch.send(f"❓ <b>{head}</b>\n{body}", html=True, buttons=[[('Nothing to add', 'pm|none')]])
        kind, ans = telegram._wait(ch, poll, {'pm|none'})
        said = (ans or '').strip() if kind != 'tap' else ''
        if said and not re.fullmatch(r"(no|nope|nothing|none|nahi|kuch nahi|no,? nothing)[.! ]*", said.lower()):
            memory.add_note(repo, f"Asked: {' / '.join(asks)} He said: {said}")   # kept for every later plan, and planned with now
            ch.send("Thank you, sir. Planning with that in mind.")
            p = think() or p
    if not p:
        ch.send("🐝 I couldn't find a clear way to that in your product as it stands, sir. Tell me a bit more about what "
                "you're seeing, or what you'd try, and I'll look again.")
        return 'no_plan'
    steps = p['steps']
    lines = '\n'.join(f"{k}. <b>{telegram.esc(s['title'])}</b>: {telegram.esc(s['why'])}" for k, s in enumerate(steps, 1))
    from . import budget
    est = budget.estimate(repo, 'step', steps=len(steps)); warn = budget.over(est)
    ch.send(f"🧭 <b>Here's what I see, sir.</b> {telegram.esc(p['finding'])}\n\n<b>What I'd do:</b>\n{lines}\n\n<i>I'll "
            "build them one after another and show you each. Your main version isn't touched.</i> "
            f"All of it: {budget.say(est)}." + (f"\n⚠️ {telegram.esc(warn)}" if warn else ''), html=True,
            buttons=[[('🚀 Yes, do it all', 'pln|all')], [('Just the first', 'pln|one')], [('Not now', 'pln|no')]])
    choice, other = choose(ch, poll, [('pln|all', ('yes', 'do it', 'do it all', 'go ahead', 'all', 'haan', 'karo')),
                                      ('pln|one', ('just the first', 'only the first', 'first one', 'pehla')),
                                      ('pln|no', NO_WORDS)])
    if other is not None:
        ch.send("Very good, I'll hold the plan."); return handle(ch, repo, other, poll, apply_build)
    if choice not in ('pln|all', 'pln|one'):
        ch.send('Very good. The plan keeps; say "do the plan" when you want it.')
        PLAN.clear(); PLAN.update(goal=text, steps=steps, step=0, running=False)
        from . import buildplans
        PLAN['task_id'] = buildplans.save(ch, repo, PLAN, approved=False)
        return 'plan_held'
    if choice == 'pln|one':
        steps = steps[:1]
    answers = []
    for s in steps:   # the few things only he can decide, all asked now, so the building runs without him
        if not s['decide']:
            answers.append(''); continue
        opts = s['options'] or []
        ch.send(f"❓ <b>One thing only you can decide</b> ({telegram.esc(s['title'])}):\n{telegram.esc(s['decide'])}", html=True,
                buttons=[[(o[:60], f'pq|{k}')] for k, o in enumerate(opts)] or None)
        kind, ans = telegram._wait(ch, poll, {f'pq|{k}' for k in range(len(opts))})
        answers.append(opts[int(ans.split('|')[1])] if kind == 'tap' else (ans or '').strip())
        if answers[-1]:
            memory.add(repo, f"{s['decide']} {answers[-1]}", 'plan')   # his decision is kept for every later build
    PLAN.clear(); PLAN.update(goal=text, steps=steps, step=1, running=True, answers=answers, cost=p.get('cost', 0))
    from . import buildplans
    PLAN['task_id'] = buildplans.save(ch, repo, PLAN)
    from . import numbers
    numbers.refresh(repo)   # where his numbers stand before the change, to compare with later
    numbers.mark(repo, f'you agreed the plan for "{text[:80]}"')
    ch.send(f"🛠 Right, sir. {'Building the first step now' if len(steps) > 1 else 'Building it now'}: "
            f"{telegram.esc(steps[0]['title'])}. I'll show you each step as it lands; say \"status\" any time.", html=True)
    if run:
        from contextvars import copy_context
        threading.Thread(target=copy_context().run, args=(run_plan, ch, repo, apply_build), daemon=True).start()
    return 'planned'

def run_plan(ch, repo, apply_build, wait=None):
    """Compatibility entry point; durable task state owns execution progress."""
    from . import buildplans
    if not PLAN.get('task_id'):
        PLAN['task_id'] = buildplans.save(ch, repo, PLAN)
    return buildplans.resume(ch, repo, PLAN['task_id'], apply_build, wait)

@policy.request
def handle(ch, repo, text, poll=20, apply_build=None, start_build=None, cloud=None, origin='owner'):
    """Answer one message from the owner. apply_build(state, rule, ch) updates a build (hive.start.apply_ruling);
    start_build(repo, goal) runs a new build that reports to the phone (hive.start.start, overnight style);
    cloud(repo, on) makes a cloud machine and moves Hive there (on=True), or deletes it (hive.cloud_aws)."""
    low = text.lower().strip()
    typing = getattr(ch, 'typing', None)
    if callable(typing):
        typing()   # "typing..." at once, as a person would (the owner found it slow)
    from . import register
    if policy.context().origin == 'owner':
        register.notice(text)
    CURRENT['text'] = text   # he writes technically: Hive answers in his terms
    from . import router
    task_reply = router.task_command(ch, repo, text, poll, handle=lambda c, r, t, pl: handle(
        c, r, t, pl, apply_build=apply_build, start_build=start_build, cloud=cloud, origin=origin))
    if task_reply is not None:
        return task_reply
    from . import routines
    routine_reply = routines.command(ch, repo, text)
    if routine_reply is not None:
        return routine_reply
    answer_task = re.fullmatch(r'answer task ([0-9a-f]{12}):\s*(.+)', text.strip(), re.I | re.S)
    if answer_task:
        from . import agent
        return 'chain:' + ','.join(agent.answer(ch, repo, answer_task[1].lower(), answer_task[2], poll))
    if low.startswith('agent:'):
        from . import agent
        return 'chain:' + ','.join(agent.start(ch, repo, text.split(':', 1)[1].strip(), poll))
    # Existing build, account-setup, stop and shipping flows keep their concrete interfaces.
    if (router_mode() == 'adaptive' and not GOAL_WORDS.search(low) and
            not low.startswith('build:') and not is_stop_request(text) and not UNDO_WORDS.search(low) and
            not CONNECT_WORDS.search(low) and not LIVE_WORDS.search(low) and
            not telegram.is_status(text) and low.strip(' !.?') not in GREETINGS and
            not re.search(r'\b(ship it|do the plan|run the plan|start the plan|set me up)\b', low)):
        from . import agent
        return 'chain:' + ','.join(agent.start(ch, repo, text, poll))
    said = text.split(':', 1)[1].strip() if low.startswith('build:') else ''
    if len(said.split()) >= 3:   # "build: <a real description>" needs no model; "build again" is read in context
        got = {'intent': 'build', 'rule': said}   # (it once took "again" as the thing to build)
    elif low.strip(' !.?') in GREETINGS:   # the obvious needs no model: one call less, seconds sooner
        got = {'intent': 'greeting'}
    elif telegram.is_status(text):
        got = {'intent': 'status'}
    elif LIVE_WORDS.search(low) and not SKIP_WORDS.search(low):   # live, the safe way: merged, tested, his yes
        got = {'intent': 'go_live'}
    elif __import__('hive.onboard', fromlist=['x']).START_WORDS.search(low):   # "set me up": get to know his company
        got = {'intent': 'onboard'}
    elif __import__('hive.access', fromlist=['x']).is_handover(text):   # "here's our admin API https://... key ..."
        got = {'intent': 'connect_data'}
    elif CONNECT_WORDS.search(low):
        got = {'intent': 'connect_host'}
    elif PREVIEW_WORDS.search(low):
        got = {'intent': 'preview'}
    elif __import__('hive.trydeploy', fromlist=['x']).TAKE_DOWN.search(low) and             __import__('hive.trydeploy', fromlist=['x']).state():   # "take it down": the test page, when one is up
        got = {'intent': 'take_down'}
    elif is_risky(text):   # never a build, whatever the model reads (the Jarvis bench: once read as one)
        got = {'intent': 'reply'}
    elif is_away(low):   # "I'm sleepy": offer the way to carry on while he's away
        got = {'intent': 'away'}
    elif refs.has(text):   # a picture ("make it like this"): to the builders working now, else to the latest build
        live = _building() and _building().startswith('A build is running')
        got = {'intent': 'instruct' if live else ('amend' if latest_build(repo) and apply_build else 'build'),
               'rule': text}
    elif SHOW_WORDS.search(low) or _device_follow_up(low):
        got = {'intent': 'show'}
    elif SHIP_WORDS.search(low):
        got = {'intent': 'ship'}
    elif __import__('hive.brain', fromlist=['x']).DOC.search(text):   # a document about his business: learned
        got = {'intent': 'document'}
    elif __import__('hive.voice', fromlist=['x']).PREF.search(text):   # "always reply in voice", "no voice replies" (P3)
        got = {'intent': 'voice_pref'}
    elif __import__('hive.pulse', fromlist=['x']).is_setting(text):   # "quiet hours 10 pm to 7 am", "pulse" (P2)
        got = {'intent': 'pulse_set'}
    elif FORGET_SURE.search(low) or (FORGET_THAT.search(low) and time.time() - LAST_KEPT.get('at', 0) < 600 and
                                      not (_building() or '').startswith('A build is running')):   # memory 2.0
        got = {'intent': 'forget'}
    elif MEMORY_ASK.search(low):   # "what do you know about Asha?"
        got = {'intent': 'memory_ask'}
    elif BRIEF_WORDS.search(low):
        got = {'intent': 'brief'}
    elif UNDO_WORDS.search(low):
        got = {'intent': 'undo'}
    elif re.search(r"\b(budget|limit|cap)\b", low) and __import__('hive.budget', fromlist=['x']).SET.search(low):
        got = {'intent': 'budget'}
    elif COMPLAINT_WORDS.search(low) and not (_building() or '').startswith('A build is running'):
        got = {'intent': 'complaint'}
    elif GOAL_WORDS.search(low) and not (_building() or '').startswith('A build is running'):
        got = {'intent': 'goal'}
    elif re.search(r"\b(do|start|run) (the|my|that) plan\b", low) and PLAN.get('steps') and not PLAN.get('running'):
        got = {'intent': 'run_plan'}
    elif __import__('hive.office', fromlist=['x']).route(text, repo):   # his mail, calendar, payments (hive/office.py)
        got = {'intent': 'office'}
    elif DATA_WORDS.search(low) and __import__('hive.access', fromlist=['x']).load(repo):   # "how many orders this week?"
        got = {'intent': 'data'}
    else:
        got = fast_read(ch, text)   # half a second when the trained reader is sure
        if not got and router_mode() == 'plan':   # his message as a plan of steps (hive/router.py, Gate 120)
            from . import router, tools
            try:
                p = router.plan(ch.recent() if hasattr(ch, 'recent') else '', text)
            except tools.Refused as e:
                ch.send(str(e)); return 'refused'
            if len(p['steps']) > 1 or (p['steps'] and p['steps'][0]['tool'] in router.DIRECT):   # steps, in order
                return 'chain:' + ','.join(router.run_chain(ch, repo, p['steps'], text, poll, handle=lambda c, r, t, pl: handle(
                    c, r, t, pl, apply_build=apply_build, start_build=start_build, cloud=cloud, origin=origin), origin=origin))
            if p['steps']:
                got = dict(router.as_intent(p['steps'][0], text), confirmed=p['confirmed'], clarify=p['clarify'])
        if not got:
            got = read(ch, text)   # Claude reads it as one intent
    intent, rule = got.get('intent', 'reply'), (got.get('rule') or text).strip()
    from . import tools   # the one check before any action (hive/tools.py): outside words never act; actions audited
    try:
        tools.allow(intent, origin, text)
    except tools.Refused as e:
        ch.send('🐝 ' + telegram.esc(str(e)), html=True)
        return 'refused'
    who = _who(ch)
    if intent == 'voice_pref':
        from . import voice
        said = voice.set_from(text)
        if voice.provider() is None and voice.preference() != 'never':
            said += (' (This computer has no voice yet: pip install "hive-swarm[speech]", or set HIVE_TTS_KEY for a '
                     'speech API.)')
        ch.send('🐝 ' + telegram.esc(said), html=True)
        return 'voice_pref'
    if intent == 'pulse_set':
        from . import pulse
        ch.send('🐝 ' + telegram.esc(pulse.set_from(text) or pulse.status_line()), html=True)
        return 'pulse_set'
    if intent == 'memory_ask':
        return memory_ask(ch, repo, text)
    if intent == 'forget':
        return forget_it(ch, repo, text, poll)
    if intent == 'show':   # he wants to see it: at phone size, or on the screens and pages he names
        show(ch, repo, text=text)
        return 'shown'
    if intent == 'ship':   # "ship it": the latest build to his engineer, as a pull request
        return ship_it(ch, repo, text, poll)
    if intent == 'go_live':
        return go_live(ch, repo, poll)
    if intent == 'connect_host':
        return connect_host(ch, repo, text, poll)
    if intent == 'office':
        from . import office
        return office.handle(ch, repo, text, poll, kind=got.get('office'))
    if intent == 'away':
        return away(ch, repo, text, poll, apply_build, start_build, cloud)
    if intent == 'onboard':
        from . import onboard
        r = onboard.run(ch, repo, poll)
        home = onboard.progress(repo).get('home')
        if r == 'done' and cloud and home and home not in ('laptop', 'render') and not in_cloud(repo):   # always on, as he chose
            from . import cloud_aws, logins
            if not logins.ensure(ch, 'aws', poll):
                return 'onboard_login_needed'
            ch.send(f"☁️ Moving to the cloud now, as you chose (about ${cloud_aws.monthly(home)} a month): about 5 "
                    "minutes. Keep your computer on until I say I'm there.")
            try:
                rc = cloud(repo, True, True, size=home)
            except TypeError:
                rc = cloud(repo, True, True)
            except Exception as e:
                rc = f'{e!r}'[:120]
            if rc != 0:
                ch.send("⚠️ I couldn't move to the cloud just now, so I'm staying on this computer. Say \"move to the "
                        "cloud\" to try again.")
                return 'onboard_cloud_failed'
            ch.send("✅ <b>I'm in the cloud, always on.</b> You can shut your computer whenever you like; talk to me "
                    "here as before.", html=True)
            return 'onboard_moved'
        if r == 'build':   # someone starting fresh: his idea goes to the usual build proposal (restated, priced, his yes)
            return handle(ch, repo, 'build: ' + onboard.goal_of(repo), poll, apply_build, start_build, cloud)
        return 'onboard_' + r
    if intent == 'connect_data':
        return connect_data(ch, repo, text)
    if intent == 'data':
        from . import access
        if not access.load(repo):
            ch.send("I can't see your data yet, sir. Send me your admin or analytics address with its key, a read-only "
                    "database address, or a spreadsheet link, and I'll answer from it. Or say \"set me up\".")
            return 'no_data'
        ch.send("🔎 Looking in your data.")
        got = access.answer(repo, text) or {}
        ch.send(('📊 ' if got.get('found') else '🤔 ') + telegram.esc(got.get('answer', '')), html=True)
        return 'data_answered' if got.get('found') else 'data_unanswered'
    if intent == 'preview':
        return preview_it(ch, repo, poll)
    if intent == 'take_down':
        return take_down(ch, repo)
    if intent == 'document':   # the company brain: what lasts in his document, kept for plans and answers
        from . import brain
        m = brain.DOC.search(text)
        ch.send("📚 Reading it now, sir.")
        got = brain.learn(repo, m.group(1).strip(), m.group(2).strip())
        if got is None:
            ch.send("📚 I couldn't read that kind of document, sir. Text, PDF, Markdown, or a spreadsheet saved as CSV all "
                    "work; a Word file saved as PDF does too.")
            return 'document_unread'
        facts, rules = got['facts'], got['rules']
        ch.send(f"📚 <b>Read and kept, sir:</b> {len(facts)} thing{'s' if len(facts) != 1 else ''} about your business" +
                (f" and {len(rules)} rule{'s' if len(rules) != 1 else ''} for how your product should behave" if rules else '') +
                ".\n\n" + '\n'.join('• ' + telegram.esc(f) for f in facts[:5]) +
                ("\n\n<i>I'll use them in every plan and answer from now on.</i>"), html=True)
        return 'document'
    if intent == 'undo':   # "undo that": whatever is most recent, taken back after his yes
        return undo(ch, repo, poll)
    if intent == 'budget':   # "set my budget to $50 a month"
        from . import budget
        amount = budget.set_from(text)
        ch.send(f"💰 Done, sir: at most ${amount:g} a month on builds. So far this month: ${budget.spent_month():.2f}. "
                "I'll ask before anything would go past it.")
        return 'budget'
    if intent == 'brief':   # "what's new?": the brief, now
        from . import brief
        brief.send(ch, repo, since=time.time() - 86400)
        return 'brief'
    if intent == 'complaint':   # a customer's complaint: his own rule at work, or a fault to fix
        return complaint(ch, repo, text, poll, apply_build)
    if intent == 'goal':   # a business outcome: Hive works out what to change, and does it on his yes
        return pursue(ch, repo, text, poll, apply_build)
    if intent == 'run_plan':   # the plan he held
        PLAN.update(step=1, running=True); PLAN.setdefault('answers', [''] * len(PLAN['steps']))
        ch.send(f"🛠 Right, sir: the plan, starting with {telegram.esc(PLAN['steps'][0]['title'])}.", html=True)
        import threading
        from contextvars import copy_context
        threading.Thread(target=copy_context().run, args=(run_plan, ch, repo, apply_build), daemon=True).start()
        return 'planned'
    if intent == 'amend' and apply_build and latest_build(repo):   # change what he just saw; before and after
        st = latest_build(repo)
        before = shoot(repo)
        tip = ('' if refs.has(rule) or not LOOK_WORDS.search(rule.lower()) else
               "\n\n<i>If you have a screenshot of a page you like, send it next time (a photo of the screen works too): a "
               "picture lands closer than words.</i>")   # Gates 105, 116: clean 19/19, photo 17/19, busy 18/19, words 11/19
        ch.send(f"🛠 Very good, sir: {telegram.esc(refs.words(rule) or 'as in your picture')}" +
                (" (with your picture)" if refs.has(rule) else '') + ". Changing your latest build now; I'll show you "
                "before and after." + tip, html=True)
        apply_build(st, rule, None)   # (its own message spoke of 'your new ruling' and a branch: Gate 107)
        show(ch, repo, before=before, intro='✅ <b>Done, sir.</b> ' + telegram.esc((latest_build(repo) or {}).get('check', '')))
        return 'amended'
    if intent == 'amend':   # nothing built yet to change: it is a build request
        intent = 'build'
    if intent in ('team', 'set_team', 'stop_builder'):   # the builders themselves, from his phone
        return _team(ch, repo, text, got, poll,
                     lambda other: handle(ch, repo, other, poll, apply_build, start_build, cloud))
    if intent == 'instruct':   # mid-build: a new direction for the builders working now
        run = team.current_run()
        live = bool(run) and _building() and _building().startswith('A build is running')
        say_it = (got.get('rule') or text).strip()
        if not live:   # nothing running to redirect: it is a request for a build
            intent, rule = 'build', say_it
        else:
            me, why = (team.find(run, got['builder']) if got.get('builder') else None), ''
            if not me:   # one owner, the builder whose work it touches (the bench: by load alone it went to the wrong one)
                me, why = route(run, say_it)
            if team.instruct(run, say_it, me):
                ch.send(f"📝 Passed to {me if me else 'the builders'}" + (f", {telegram.esc(why)}" if why else '') +
                        f": {telegram.esc(say_it[:300])}. " + ("It picks" if me else "They pick") +
                        " it up at its next sync, usually within a few minutes.", html=True)
                return 'instructed'
            ch.send("⚠️ I couldn't reach the builders just now. Say it again in a moment, or \"stop the build\" and "
                    "start it afresh with this."); return 'instruct_failed'
    if intent == 'stop_build':   # he can stop a build from his phone, as he can start one
        p = BUILD.get('proc')
        if p is not None and p.poll() is None:
            if not is_stop_request(text):   # read as a stop, not said as one: a wrong stop loses the build (Gate 48)
                ch.send(f"🛑 <b>Stop the build?</b>\n\n{telegram.esc(BUILD.get('goal', '')[:200])}\n\n<i>It is cancelled "
                        "and nothing from it is handed over.</i>", html=True,
                        buttons=[[('🛑 Stop it', 'stp|yes')], [('Keep going', 'stp|no')]])
                choice, other = choose(ch, poll, [('stp|yes', ('stop it', 'cancel it', 'band karo', 'roko')),
                                                  ('stp|no', ('keep going', 'keep it', 'continue', 'carry on'))])
                if other is not None:
                    ch.send("Very good, the build carries on.")
                    return handle(ch, repo, other, poll, apply_build, start_build, cloud)
                if choice != 'stp|yes':
                    ch.send('Very good, the build carries on.'); return 'kept_building'
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
        from . import screens
        tech = register.is_technical(rule) or register.is_technical(text)   # his precise instruction, taken as such
        restated, extra = '', ''
        if tech and not go:   # the normal questions an engineer would ask, only where something real is unclear
            import threading
            box, done = {}, threading.Event()
            threading.Thread(target=lambda: (box.update(c=register.clarify(repo, rule)), done.set()), daemon=True).start()
            while not done.wait(4):   # "typing..." while it reads the code (half a minute or so)
                if callable(typing):
                    typing()
            c = box.get('c') or {}
            restated = c.get('restated', '')
            for q in c.get('questions', []):
                opts = q['options']
                ch.send(f"❓ {telegram.esc(q['q'])}", html=True, buttons=[[(o[:60], f'tq|{k}')] for k, o in enumerate(opts)] or None)
                kind, ans = telegram._wait(ch, poll, {f'tq|{k}' for k in range(len(opts))})
                said = opts[int(ans.split('|')[1])] if kind == 'tap' else (ans or '').strip()
                if said:
                    extra += f"\n- {q['q']} -> {said}"
        if extra:
            rule += "\n\nHis answers:" + extra
        from . import budget
        est = budget.estimate(repo, 'build'); price = f" It'll cost {budget.say(est)}."
        if budget.over(est):
            price = f" ⚠️ {budget.over(est)} Tap to go ahead anyway."
            go = False   # past his cap, even "go ahead" waits for this tap
        for _ in range(3):
            if go:
                break
            short = (got.get('short') or '').strip() if rule == (got.get('rule') or '').strip() else ''
            if tech:
                ch.send(f"👍 <b>Yes, let's do it.</b>\n\n{telegram.esc(restated or rule)}\n\n<i>Shall I build this? Tap, "
                        "or correct me; every test is run before you see it.</i>" + telegram.esc(price), html=True,
                        buttons=[[('🚀 Go', 'bld|yes')], [('Not now', 'bld|no')]])
            else:
                ch.send(f"🏗 <b>Shall I build this?</b>\n\n{telegram.esc(short or rule)}\n\n<i>" +
                        ("I'll do it on a copy and show you how it looks." if screens.is_look_job(rule, repo) else
                         "I'll work on copies, then bring you the decisions to check.") + " Tap, or just tell me.</i>" +
                        telegram.esc(price), html=True,
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
        from . import screens
        ch.send("🛠 On it, sir. " + ("I'll study it, make the change, and come back with screenshots of how it looks. "
                                     if screens.is_look_job(rule, repo) else
                                     "I'll come back with what changed and the test results. " if tech else
                                     "I'll keep you posted, and come back when it's ready for you to look at. ") +
                "Say \"status\" any time.", html=True)
        if tech:   # a precise instruction: no business situations quiz (edge cases of business rules keep theirs)
            try:
                start_build(repo, rule, interview=False)
            except TypeError:
                start_build(repo, rule)
        else:
            start_build(repo, rule)
        return 'built'
    if intent in ('cloud_on', 'cloud_off') and cloud:
        on = intent == 'cloud_on'
        from . import cloud_aws
        small, big = cloud_aws.SIZES   # his choice, at its real monthly price (the owner: "it depends on the user")
        ch.send("☁️ <b>Shall I move to the cloud?</b>\n\nI'll make a machine on your AWS account, move this project "
                "there, and keep working while your computer is off. It bills for as long as it runs; say \"delete the "
                "cloud machine\" any time and it stops.\n\n"
                f"• <b>Small</b>, about ${cloud_aws.monthly(small[0])} a month: {small[1]}.\n"
                f"• <b>Bigger</b>, about ${cloud_aws.monthly(big[0])} a month: {big[1]}.\n\n"
                "<i>Or keep me on this computer, free: I stop when it's off.</i>"
                if on else "☁️ <b>Shall I delete the cloud machine?</b>\n\nBring results back first if you need them; "
                "after this nothing is left running or billing.", html=True,
                buttons=([[(f'☁️ Small, about ${cloud_aws.monthly(small[0])} a month', 'cld|yes')],
                          [(f'☁️ Bigger, about ${cloud_aws.monthly(big[0])} a month', 'cld|big')],
                          [('💻 Stay on this computer', 'cld|no')]] if on else
                         [[('🗑 Yes, delete it', 'cld|yes')], [('Not now', 'cld|no')]]))
        choice, other = choose(ch, poll, [('cld|yes', ('small', 'with login', 'with my login', 'with my claude', 'yes')),
                                          ('cld|big', ('bigger', 'big', 'large')),
                                          ('cld|bare', ('without', 'chat only', 'no login')),
                                          ('cld|no', NO_WORDS + ('stay', 'this computer', 'laptop'))] if on else
                               [('cld|yes', ('delete it', 'yes')), ('cld|no', NO_WORDS)])
        if other is not None:   # something else entirely: hold this, and answer what he said
            ch.send("Very good, I'll hold that for now.")
            return handle(ch, repo, other, poll, apply_build, start_build, cloud)
        if choice not in ('cld|yes', 'cld|bare', 'cld|big'):
            if on:
                cloud_aws.prefer('laptop')
                ch.send("💻 Very good: I'll stay on this computer, free. I stop when it's off; say \"move to the cloud\" "
                        "any time to change that.")
            else:
                ch.send('Very good. Just say the word.')
            return 'not_moved'
        size = big[0] if choice == 'cld|big' else small[0]
        if on:
            cloud_aws.prefer(size)   # "I'm sleepy" moves to the size he chose
        if not in_cloud(repo):   # his AWS sign-in, renewed from his phone if it has expired
            from . import logins
            if not logins.ensure(ch, 'aws', poll):
                return 'login_needed'
        if on:   # (for a delete, say nothing until it is known to be possible: it said "Deleting it now", then that it can't)
            ch.send("🛠 On it. This takes about 5 minutes; I'll tell you when I'm there.")
        try:
            try:
                rc = cloud(repo, on, choice != 'cld|bare', size=size)   # with the login: builders can work there
            except TypeError:
                rc = cloud(repo, on, choice != 'cld|bare')
        except TypeError:
            rc = cloud(repo, on)
        if rc == 9:   # the cloud copy powered its own machine off: no hourly bill, and nothing built there is lost
            ch.send("☁️ <b>Done: the cloud machine is powering off.</b> It no longer bills by the hour. Its disk keeps "
                    "everything built there (about $2.40 a month) until your computer brings it home: run "
                    "<code>hive cloud --stop</code> there. It starts the machine, copies every branch back, checks each "
                    "one, then deletes it completely.\n\nUntil then I'm not listening; on your computer, "
                    "<code>hive listen</code> picks our conversation up again.", html=True)
            return 'cloud_off'
        if rc == 8:
            ch.send("🛠 A build is still running there, so I've kept the machine: powering off now would lose it. "
                    "I'll tell you when it's done, or say \"stop the build\" first.")
            return 'cloud_kept'
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
        from . import onboard
        if onboard.knows_nothing(repo):   # a company Hive has not met: offer to get to know it
            ch.send("We haven't met properly yet. Say <b>\"set me up\"</b> and I'll get to know your business or your "
                    "product in about two minutes, or help you start something new.", html=True)
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
        if policy.context().origin == 'owner':
            remember(ch, repo, text)   # outside data cannot create owner-trusted facts
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
        run = team.current_run()
        live = bool(run) and _building() and _building().startswith('A build is running')
        sent = live and team.instruct(run, f'A new standing rule from the owner: {rule}')   # it reaches the builders now
        ch.send(f"📌 Noted as a standing rule: {rule}" + (" The builders working now have it too." if sent else ''))
    st = latest_build(repo)
    if st and apply_build:
        ch.send("Shall I update your latest build to follow it?",
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
    try:   # one listener only (live, Nov 3: two answered him, the older one from stale facts)
        other = int(open(PIDFILE).read().strip())
        if other != os.getpid() and telegram._alive(other):
            print(f'Hive is already listening on this computer (process {other}). Stop that one first.'); return 1
    except (OSError, ValueError):
        pass
    from . import actions
    interrupted = actions.recover()
    from . import tasks
    interrupted_tasks = tasks.recover(ch, repo)
    if interrupted_tasks:
        ch.send(f'{interrupted_tasks} interrupted tasks have saved progress. Say tasks to inspect or resume them.')
    from . import buildplans
    buildplans.restore(ch, repo)
    from . import memory_jobs
    memory_jobs.recover()
    if interrupted:
        ch.send(f'{interrupted} interrupted actions need checking. I have not repeated them.')
    CURRENT['ch'] = ch   # a background build reports its problems here
    try:   # the meaning model and the local voice load in the background: no reply waits on either
        from . import embed, voice
        embed.warm(); voice.warm()
    except Exception:
        pass
    try:   # work his computer handed over before he shut it ("I'm sleepy" -> to the cloud): pick it up now
        resume_here(ch, repo)
    except Exception as e:
        print(f'Could not pick up the handed-over work: {e!r}', flush=True)
    try:   # so a move to the cloud can stop this listener: one Hive reads his chat at a time
        os.makedirs(os.path.dirname(PIDFILE), exist_ok=True); open(PIDFILE, 'w').write(str(os.getpid()))
    except OSError:
        pass
    print("Listening on Telegram. Tell Hive anything, any time: a change of mind, a new rule, or 'status'. Ctrl+C to stop.",
          flush=True)
    try:
        while not (until and until()):
            memory_jobs.start()
            if not telegram.busy_elsewhere() and not (_building() or '').startswith('A build is running'):
                try:
                    from . import routines
                    routines.tick(ch, repo)
                except Exception as e:
                    print(f'Routine check stopped ({type(e).__name__}).', flush=True)
            try:   # a test page past its two hours: taken down (and its test machine deleted), and he is told
                from . import trydeploy
                if trydeploy.expired():
                    ch.send('⏱ The two-hour test is over. ' + telegram.esc(trydeploy.down(repo)), html=True)
            except Exception as e:
                print(f'Could not take the test page down: {e!r}', flush=True)
            try:   # once a week: near-duplicate facts folded into the newest, forgotten ones removed from the file
                from . import store
                if store.tidy_due(memory.project_key(repo)) and not telegram.busy_elsewhere():
                    store.tidy(memory.project_key(repo)); store.purge_forgotten()
            except Exception as e:
                print(f'Could not tidy the memory: {e!r}', flush=True)
            try:   # the morning brief, unprompted, once a day
                from . import brief
                if brief.due() and not telegram.busy_elsewhere():
                    brief.send(ch, repo)
            except Exception as e:
                print(f'Could not send the brief: {e!r}', flush=True)
            try:   # Pulse: every few minutes, in the background, what needs him is found and said (hive/pulse.py)
                from . import pulse
                if pulse.due() and not PULSE.get('running'):
                    def _pulse():
                        PULSE['running'] = True
                        try:
                            pulse.tick(ch, repo)
                        except Exception as e:
                            print(f'Pulse: {e!r}', flush=True)
                        finally:
                            PULSE['running'] = False
                    import threading
                    threading.Thread(target=_pulse, daemon=True).start()
            except Exception as e:
                print(f'Could not start Pulse: {e!r}', flush=True)
            if telegram.busy_elsewhere():
                time.sleep(poll); continue   # a build or review is talking to the owner: step aside
            try:
                batch = ch.updates(timeout=poll)
            except Exception as e:   # never go silent on the owner: report, wait, listen again
                print(f'Telegram error, retrying: {e}', flush=True); time.sleep(poll); continue
            for _, data, proposal_mid in batch:   # a tap on a Pulse alert (Got it, Reply, In an hour)
                if data and data.startswith('act|'):
                    actions.resume(ch, data, proposal_mid, repo)
                if data and data.startswith('pls|'):
                    try:
                        from . import pulse
                        pulse.tap(ch, data, repo, poll)
                    except Exception as e:
                        print(f'Could not handle the alert tap: {e!r}', flush=True)
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
                    print(f'Could not handle request ({type(e).__name__}).', flush=True)
                    try:
                        w = ch.name()
                        ch.send(f"⚠️ My apologies{', ' + w if w else ''}: that one went wrong on my side. I'm still here; "
                                "say it again, or another way.")
                    except Exception:
                        pass
    except KeyboardInterrupt:
        pass
    return 0
