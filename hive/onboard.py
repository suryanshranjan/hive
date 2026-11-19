"""Getting to know whoever starts with Hive, in one conversation on the phone (the owner: "the onboarding of a company
should be easy in Hive"; "a developer may be onboarding too: then there is no company, just a product, or he just wants
to build something new").

The first question is who he is, and the path follows from it. Every step can be skipped, is checked as it is given,
and is kept as it comes, so a stop never costs him what he already gave ("set me up" again picks up where he left off).

- a business: what it is and who its customers are; where to see the product; his data, read-only (admin or analytics
  address with its key, a read-only database login, a spreadsheet; hive/access.py); what is written about how he runs
  things (policies, FAQ, price list; hive/brain.py); where it runs live (hive/deploy.py).
- a developer with a product: what it is and who uses it; where it runs; its data, read-only; how it is built (what
  to keep to, what never to touch); where it is hosted.
- something new: what to build and for whom; what it must do on day one; then Hive offers to start building it.
The code itself is connected once on the computer (hive doctor setup); Hive says so if it has none."""
import os, re, subprocess, time

from . import access, memory, telegram

DIR = os.path.join(os.path.expanduser('~'), '.hive', 'onboarding')
START_WORDS = re.compile(r"^\s*(ok(ay)?[,.]?\s+|so[,.]?\s+)?(let'?s\s+(begin|start)|(let'?s\s+)?get (me |us )?started)[.! ]*$|"
                         r"\b(onboard(ing)?( me)?|set (me|us) up|set ?up (my|our) (company|business|shop|startup|product|project)|get to know (my|our) "
                         r"(company|business|product)|connect (my|our) (company|business|product)|start (the )?setup)\b")
SKIP = {'skip', 'later', 'no', 'none', 'nope', 'pass', 'next', 'not now', "don't have", 'dont have', 'nahi', 'nahin',
        "i don't know", 'dont know', "don't know", 'na', 'n/a', 'nothing', "it isn't live yet", 'not live yet'}
DONE = {'done', 'that is all', "that's all", 'thats all', 'finished', 'ho gaya', 'bas', 'enough', 'no more'}
STOP = {'stop', 'later please', 'finish later', 'pause', 'cancel', 'exit', 'baad mein'}
HOSTS = re.compile(r'\b(vercel|netlify|railway|azure|fly|render)\b', re.I)
WHO = {'business': re.compile(r'\b(business|company|shop|store|startup|brand|agency|founder|owner|run a|i sell|we sell)\b'),
       'developer': re.compile(r'\b(developer|dev|engineer|programmer|coder|my (app|product|project|code|repo)|side project|'
                               r'freelanc\w*|i code|i build apps)\b'),
       'new': re.compile(r'\b(new|from scratch|an idea|build something|make something|start fresh|nothing yet|'
                         r'naya|banana hai)\b')}
PATHS = {'business': ('about_business', 'site', 'data', 'documents', 'host', 'home'),
         'developer': ('about_product', 'site', 'data', 'conventions', 'host', 'home'),
         'new': ('idea', 'day_one')}

ABOUT = """Someone describes {what} to his new assistant: "{text}"
What is it called (only if he says it; else empty), and what lasting facts does this give (what it does, who it is
for, where, how it earns if he says), each one short plain sentence in his terms, at most 6?
Reply with JSON only: {{"name": "...", "facts": ["..."]}}"""

def _path(repo):
    return os.path.join(DIR, memory.project_key(repo) + '.json')

def progress(repo):
    return telegram._load(_path(repo))

def _keep(repo, **kw):
    telegram._save(_path(repo), {**progress(repo), **kw})

def done(repo):
    return bool(progress(repo).get('done'))

def knows_nothing(repo):
    """Someone Hive has not met: no setup started, nothing told, no rules, no data, nothing built."""
    from . import assistant
    return not (done(repo) or progress(repo).get('who') or memory.notes(repo) or memory.load(repo)
                or access.load(repo) or assistant.latest_build(repo))

def _norm(t):
    return ' '.join((t or '').lower().replace('’', "'").split()).strip(' .!')

def _reply(ch, poll, step):
    """His next answer: ('skip' | 'done' | 'stop' | 'text', words)."""
    kind, got = telegram._wait(ch, poll, {f'onb|skip|{step}', f'onb|done|{step}', 'onb|stop'})
    if kind == 'tap':
        return got.split('|')[1], ''
    n = _norm(got)
    if n in STOP:
        return 'stop', got
    if n in DONE:
        return 'done', got
    if n in SKIP:
        return 'skip', got
    return 'text', got

def _code_files(repo):
    p = subprocess.run(['git', '-C', repo, 'ls-files'], capture_output=True, text=True)
    return len([l for l in p.stdout.splitlines() if l.strip() and not l.startswith('.hive/')]) if p.returncode == 0 else 0

def who_from(text):
    """'business' | 'developer' | 'new' from his own words, or None."""
    low = _norm(text)
    for k in ('new', 'developer', 'business'):   # "a developer building something new" is starting something new
        if WHO[k].search(low):
            return k
    return None

class _Paused(Exception):
    pass

# ---- the steps ------------------------------------------------------------------------------------------------------

def _about(ch, repo, poll, k, n, title, ask, what):
    ch.send(f"<b>{k} of {n}. {title}</b>\n{ask}", html=True, buttons=[[('Skip', f'onb|skip|{k}')]])
    kind, text = _reply(ch, poll, k)
    if kind == 'stop':
        raise _Paused
    if kind != 'text':
        return ''
    from . import explain
    got = explain.ask_json(ABOUT.format(what=what, text=text)) or {}
    facts = [str(f).strip() for f in (got.get('facts') or []) if str(f).strip()][:6] or [text.strip()[:300]]
    for f in facts:
        memory.add_note(repo, f)
    name = str(got.get('name') or '').strip()
    if name and len(name) <= 40:
        memory.set_name(repo, name)
    ch.send(f"✅ Got it{', ' + telegram.esc(name) if name else ''}: " + telegram.esc(' '.join(facts[:3]))[:400], html=True)
    return text

def step_about_business(ch, repo, poll, k, n):
    _about(ch, repo, poll, k, n, 'Your business.', "What is it called, what does it do, and who are your customers? A "
           "line or two is plenty (🎙 a voice note works too).", 'his business')

def step_about_product(ch, repo, poll, k, n):
    _about(ch, repo, poll, k, n, 'Your product.', "What is it called, what does it do, and who uses it? A line or two "
           "(🎙 a voice note works too).", 'his product')

def step_site(ch, repo, poll, k, n):
    ch.send(f"<b>{k} of {n}. Where it runs.</b>\nWhere can I see it? Send its web address.", html=True,
            buttons=[[("It isn't live yet", f'onb|skip|{k}')]])
    while True:
        kind, text = _reply(ch, poll, k)
        if kind == 'stop':
            raise _Paused
        if kind != 'text':
            return
        m = access.WEB.search(text)
        if not m:
            ch.send("I need its address, starting with https:// (or tap the button if it isn't live yet).",
                    buttons=[[("It isn't live yet", f'onb|skip|{k}')]])
            continue
        src = access.add(repo, 'url', m.group(1).rstrip('.,)'), name='your site')
        ok, line = access.check(src)
        ch.send(('✅ ' if ok else '⚠️ ') + line + ('' if ok else ' I kept the address; I will try again when I need it.'))
        return

def step_data(ch, repo, poll, k, n):
    from . import brain
    files = _code_files(repo)
    ch.send(f"<b>{k} of {n}. Numbers and data.</b>\n" +
            (f"I already have the code here ({files} files). " if files else
             "I don't have the code on this computer yet; it is connected once with <code>hive doctor setup</code>. ") +
            "So I can answer things like <i>\"how many orders this week?\"</i>, send me any of these, as many as you "
            "like:\n• an admin or analytics address, with its key\n• a database address (please a <b>read-only</b> "
            "login)\n• a shared spreadsheet link, or a CSV or Excel file\n\n<i>I only ever read; I never change your "
            "data. Keys stay on this computer.</i> Say <i>done</i> when finished.", html=True,
            buttons=[[('✅ Done', f'onb|done|{k}'), ('Skip', f'onb|skip|{k}')]])
    while True:
        kind, text = _reply(ch, poll, k)
        if kind == 'stop':
            raise _Paused
        if kind != 'text':
            return
        doc = brain.DOC.search(text)
        if doc and not telegram.inbox_file(doc[1].strip()):
            ch.send('Please attach the data file in this chat.')
            continue
        src = ({'kind': 'file', 'where': doc.group(1).strip(), 'name': doc.group(2).strip()} if doc and
               os.path.splitext(doc.group(2))[1].lower() in ('.csv', '.xlsx', '.json', '.tsv') else access.detect(text))
        if not src:
            ch.send("I couldn't find an address or a file in that. Send the link itself (https://..., or a database "
                    "address such as postgres://...), or say done.", buttons=[[('✅ Done', f'onb|done|{k}')]])
            continue
        kept = access.add(repo, src['kind'], src['where'], name=src.get('name'), headers=src.get('headers'))
        ok, line = access.check(kept)
        ch.send(f"{'✅' if ok else '⚠️'} <b>{telegram.esc(kept['name'])}:</b> " + telegram.esc(line) +
                ('' if ok else ' I kept it; fix it and send it again, or say done.') + "\n\nAnything else? Or say done.",
                html=True, buttons=[[('✅ Done', f'onb|done|{k}')]])

def _gather(ch, repo, poll, k, n, title, ask, prefix=''):
    from . import brain
    ch.send(f"<b>{k} of {n}. {title}</b>\n{ask} Say <i>done</i> when finished.", html=True,
            buttons=[[('✅ Done', f'onb|done|{k}'), ('Skip', f'onb|skip|{k}')]])
    while True:
        kind, text = _reply(ch, poll, k)
        if kind == 'stop':
            raise _Paused
        if kind != 'text':
            return
        doc = brain.DOC.search(text)
        if doc:
            if not telegram.inbox_file(doc[1].strip()):
                ch.send('Please attach the document in this chat.')
                continue
            got = brain.learn(repo, doc.group(1).strip(), doc.group(2).strip())
            ch.send("📚 " + (f"Read: {len(got['facts'])} things kept"
                             + (f", and {len(got['rules'])} rules for how the product behaves" if got['rules'] else '')
                             + '.' if got else "I couldn't read that kind of file; a PDF or text works.") +
                    " Anything else, or done?", buttons=[[('✅ Done', f'onb|done|{k}')]])
        else:
            memory.add_note(repo, prefix + text.strip()[:400])
            ch.send("📝 Noted. Anything else, or done?", buttons=[[('✅ Done', f'onb|done|{k}')]])

def step_documents(ch, repo, poll, k, n):
    _gather(ch, repo, poll, k, n, 'How you run things.', "Anything written down: policies, FAQ, price list, a pitch deck? "
            "Send the files here (PDF, text, CSV), or tell me in a few lines.")

def step_conventions(ch, repo, poll, k, n):
    _gather(ch, repo, poll, k, n, 'How it is built.', "Anything builders must keep to: the stack, conventions, what "
            "never to touch, how to run its tests? A few lines, or send a doc.", prefix='How the product is built: ')

def step_host(ch, repo, poll, k, n):
    ch.send(f"<b>{k} of {n}. Hosting.</b>\nVercel, Netlify, Render, Railway, Fly or Azure? Or say <i>don't know</i>.",
            html=True, buttons=[[("Don't know", f'onb|skip|{k}')]])
    kind, text = _reply(ch, poll, k)
    if kind == 'stop':
        raise _Paused
    m = HOSTS.search(text or '') if kind == 'text' else None
    if m:
        from . import deploy
        try:
            deploy.setup(repo, m.group(1).lower())
            state, why = deploy.ready(repo)
            ch.send(f"✅ {m.group(1).title()}." + ('' if state == 'ok' else ' ' + why))
        except Exception as e:
            ch.send(f"⚠️ I noted {m.group(1).title()}, but couldn't set it up yet ({str(e)[:100]}).")
    elif kind == 'text':
        memory.add_note(repo, f'Where the product runs: {text.strip()[:200]}')
        ch.send("📝 Noted.")

def step_home(ch, repo, poll, k, n):
    """Where Hive runs: his choice, at real monthly prices (the owner: "it depends on the user"). A machine he picks is
    made after set-up, once the rest is done (Hive moves there and keeps listening while his computer is off)."""
    from . import cloud_aws
    if cloud_aws.on_render():   # set up from his phone on Render: already always on, nothing to choose
        cloud_aws.prefer('render'); _keep(repo, home='render')
        ch.send(f"☁️ <b>{k} of {n}.</b> I'm already always on, on your Render account (about "
                f"${cloud_aws.render_monthly()} a month there). Nothing to choose.", html=True)
        return
    (small, what_s), (big, what_b) = cloud_aws.SIZES
    ch.send(f"<b>{k} of {n}. Where should I run?</b>\n\n"
            "• <b>On this computer</b>: free, but I stop when it's off or asleep.\n"
            f"• <b>Always on, small</b>: about ${cloud_aws.monthly(small)} a month on your AWS account; {what_s}.\n"
            f"• <b>Always on, bigger</b>: about ${cloud_aws.monthly(big)} a month; {what_b}.\n"
            f"• <b>Always on, on Render</b>: about ${cloud_aws.render_monthly()} a month on your own Render account; "
            "set up from any phone, no computer needed.\n\n"
            "<i>You can change this any time: \"move to the cloud\" or \"delete the cloud machine\".</i>", html=True,
            buttons=[[('💻 This computer, free', f'onb|home|laptop')],
                     [(f'☁️ Small, ~${cloud_aws.monthly(small)}/month', f'onb|home|{small}')],
                     [(f'☁️ Bigger, ~${cloud_aws.monthly(big)}/month', f'onb|home|{big}')],
                     [(f'☁️ Render, ~${cloud_aws.render_monthly()}/month', 'onb|home|render')]])
    while True:
        kind, got = telegram._wait(ch, poll, {'onb|home|laptop', f'onb|home|{small}', f'onb|home|{big}',
                                              'onb|home|render', f'onb|skip|{k}', 'onb|stop'})
        if kind == 'tap':
            choice = got.split('|')[2] if got.startswith('onb|home|') else None
            if got == 'onb|stop':
                raise _Paused
        else:
            n_ = _norm(got)
            if n_ in STOP:
                raise _Paused
            choice = ('render' if re.search(r'\brender\b', n_) else
                      big if re.search(r'\b(big|bigger|large)\b', n_) else small if re.search(r'\b(small|cloud|always)\b', n_)
                      else 'laptop' if re.search(r'\b(computer|laptop|free|here|this)\b', n_) else
                      None if n_ in SKIP else '?')
            if choice == '?':
                ch.send("Tap one, or say \"this computer\", \"small\", \"bigger\" or \"Render\"."); continue
        break
    if not choice:
        return
    cloud_aws.prefer(choice)
    _keep(repo, home=choice)
    if choice == 'render':   # his own Render account: he starts it there; none of his keys pass through here
        ch.send("☁️ <b>Very good: Render.</b> About five minutes, all from your phone:\n"
                "1. Your project needs to be on GitHub (your engineer can do it, or say \"put it on GitHub\").\n"
                f"2. Open {cloud_aws.RENDER_DEPLOY} and sign in to Render (or make an account).\n"
                "3. Make a new bot for it: send /newbot to @BotFather (two bots can't share one chat).\n"
                "4. Fill in the form: the new bot's token, an Anthropic API key (console.anthropic.com), and your "
                "project's GitHub name with a GitHub token.\n"
                "5. Tap <b>Deploy</b>, then send the new bot a message from this phone.\n\n"
                f"About ${cloud_aws.render_monthly()} a month, on your Render bill. Until it says hello, I carry on "
                "here; then you can switch this computer off.",
                html=True)
        return
    ch.send("💻 Very good: I'll run on this computer." if choice == 'laptop' else
            f"☁️ Very good: always on, about ${cloud_aws.monthly(choice)} a month. I'll move there when we've finished "
            "setting up.")

def step_idea(ch, repo, poll, k, n):
    text = _about(ch, repo, poll, k, n, 'Your idea.', "What do you want to build, and who is it for? Say it the way you'd "
                  "tell a friend (🎙 a voice note works too).", 'what he wants to build')
    if text:
        _keep(repo, idea=text.strip())

def step_day_one(ch, repo, poll, k, n):
    ch.send(f"<b>{k} of {n}. Day one.</b>\nWhat must it do on day one? A few lines, one thing each; say <i>done</i> when "
            "finished. (Anything you're unsure of, leave it: I'll ask you about the unusual cases as I build.)",
            html=True, buttons=[[('✅ Done', f'onb|done|{k}'), ('Skip', f'onb|skip|{k}')]])
    musts = list(progress(repo).get('musts') or [])
    while True:
        kind, text = _reply(ch, poll, k)
        if kind == 'stop':
            raise _Paused
        if kind != 'text':
            return
        musts += [l.strip(' -•*\t') for l in text.splitlines() if l.strip(' -•*\t')]
        _keep(repo, musts=musts)
        ch.send(f"📝 Noted ({len(musts)} so far). Anything else, or done?", buttons=[[('✅ Done', f'onb|done|{k}')]])

STEPS = {'about_business': step_about_business, 'about_product': step_about_product, 'site': step_site,
         'data': step_data, 'documents': step_documents, 'conventions': step_conventions, 'host': step_host, 'home': step_home,
         'idea': step_idea, 'day_one': step_day_one}

# ---- the conversation -----------------------------------------------------------------------------------------------

def ask_who(ch, repo, poll):
    ch.send("🐝 <b>Let's get you set up.</b> First, which of these is you?", html=True,
            buttons=[[('🏢 I run a business', 'onb|who|business')], [('🧑‍💻 I have a product I build', 'onb|who|developer')],
                     [('✨ I want to build something new', 'onb|who|new')]])
    while True:
        kind, got = telegram._wait(ch, poll, {'onb|who|business', 'onb|who|developer', 'onb|who|new'})
        if kind == 'tap':
            return got.split('|')[2]
        if _norm(got) in STOP:
            raise _Paused
        who = who_from(got)
        if who:
            return who
        ch.send("Tap the one that fits best, or say it in a few words (\"I'm a developer\", \"I have a shop\", \"I want "
                "to build an app\").")

def goal_of(repo):
    """What to build, from his idea and his day-one list, as the goal a build is given."""
    st = progress(repo)
    musts = st.get('musts') or []
    return ((st.get('idea') or '').strip() + ('\n\nOn day one it must:\n' + '\n'.join(f'- {m}' for m in musts)
                                              if musts else '')).strip()

def run(ch, repo, poll=20):
    """The whole conversation. Returns 'done', 'paused' (he picks it up with "set me up"), or 'build' for a new idea
    to build (the caller proposes the build of goal_of(repo), with its price, and he says yes or no there)."""
    st = progress(repo)
    try:
        who = st.get('who')
        if not who:
            who = ask_who(ch, repo, poll)
            _keep(repo, who=who, step=0)
            st = progress(repo)
        steps = PATHS[who]
        at = st.get('step', 0)
        if at == 0:
            ch.send(f"Very good. {len(steps)} quick steps" + (', about two minutes' if len(steps) > 2 else '') +
                    ". Say <i>skip</i> to any, or <i>stop</i> to carry on later; I keep everything as you go.", html=True)
        else:
            ch.send(f"🐝 Picking up where we left off: step {at + 1} of {len(steps)}.")
        for k, name in enumerate(steps, 1):
            if k <= at:
                continue
            STEPS[name](ch, repo, poll, k, len(steps))
            _keep(repo, step=k)
    except (_Paused, telegram.Stopped):   # "stop" mid-setup is a pause: nothing is lost
        ch.send("👍 Paused. Everything you gave me is kept; say \"set me up\" to carry on.")
        return 'paused'
    _keep(repo, done=time.time())
    if who == 'new':
        goal = goal_of(repo)
        if not goal:
            ch.send("✅ Whenever you're ready, just tell me what to build, and I'll take it from there.")
            return 'done'
        return 'build'   # the build itself restates it, says the price and asks once (no second "shall I?")
    ch.send(wrap_up(repo, who), html=True)
    return 'done'

def wrap_up(repo, who='business'):
    """What Hive now knows, and what he can say, in a few plain lines."""
    name = memory.project_name(repo)
    srcs = access.load(repo)
    know = [f"{len(memory.notes(repo))} things about your {'business' if who == 'business' else 'product'}"]
    if srcs:
        know.append('read-only access to ' + ', '.join(s['name'] for s in srcs))
    asks = (["\"how many orders this week?\""] if any(s['name'] != 'your site' for s in srcs) else []) + \
        ["\"show me the pricing page on desktop\""] + \
        (["\"I want more repeat buyers\"", "\"add a referral page\""] if who == 'business' else
         ["\"add an index on users.email\"", "\"make /products paginate, 20 a page\""])
    return (f"✅ <b>All set{', ' + telegram.esc(name) if name else ''}.</b> I know " + telegram.esc('; '.join(know)) +
            ".\n\nFrom now on, just tell me what you want. For example:\n" + '\n'.join(f'• {a}' for a in asks) +
            "\n\nI'll ask only what I can't work out myself: your own rules for the unusual cases.")
