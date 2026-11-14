"""The office on his phone: his mail, his calendar and his payments (the owner, Nov 15 2026: "fix everything" towards a
Jarvis for the whole company). Read-only, except a mail reply he has seen and said yes to.

route(text, repo) says whether a message is for the office; handle() answers it. Setting each one up happens in the
chat: he says "connect my email" (or Stripe, Razorpay, his calendar), Hive asks for what it needs, and any password or
key he sends is deleted from the chat and from Hive's record of the conversation as soon as it is read."""
import re

from . import calendar_, mail, payments, telegram

ADDRESS = re.compile(r'[\w.+-]+@[\w-]+(\.[\w-]+)+')
# "connect my email", "link our inbox", "read my Gmail": his own, to connect; not "add an email signup box" (a build)
CONNECT = r'\b(connect|link|set ?up|hook up|give you( access to)?|access to|read|use)\b.{0,12}\b(my|our)\b.{0,12}'
CONNECT_MAIL = re.compile(CONNECT + r"\b(e-?mails?|mail ?box|inbox|gmail|zoho ?mail|outlook|mails?)\b|"
                          r"^\s*(connect|link) (e-?mail|gmail|mail|inbox)\b", re.I)
CONNECT_CAL = re.compile(CONNECT + r"\b(calendar|google calendar)\b|^\s*(connect|link) (google )?calendar\b", re.I)
CONNECT_PAY = re.compile(CONNECT + r"\b(stripe|razorpay)\b|^\s*(connect|link) (stripe|razorpay)\b", re.I)
KEYS = re.compile(r'\b(sk|rk)_(live|test)_\w{8,}|\brzp_(live|test)_\w{6,}', re.I)
REPLY = re.compile(r"^\s*(please\s+)?(reply|respond|write back|answer|email back|mail back)\b.{0,60}", re.I)
MAIL = re.compile(r"\b(e-?mails?|mails?|inbox|mail ?box|wrote to me|emailed|anyone write|who wrote)\b", re.I)
CAL = re.compile(r"\b(calendar|meetings?|schedule|agenda|appointments?|am i free|free (at|on|tomorrow|today|this)|"
                 r"what'?s on (today|tomorrow)|busy (today|tomorrow|at|on))\b", re.I)
PAY = re.compile(r"\b(revenue|payments?|sales|did we make|we made|made this|earn(ed|ings)?|refunds?|income|collections?|"
                 r"razorpay|stripe|transactions?)\b", re.I)
# a question or a request to look, not a build ("add a payments page" mentions payments, and is a build)
ASK = re.compile(r"^\s*(please\s+)?(what|how|who|when|where|which|any|anything|did|do|does|is|are|am|was|were|show|tell|"
                 r"check|read|summari[sz]e|list|give|have|has|kya|kitna|kaun)\b|\?\s*$", re.I)
BUILD = re.compile(r"^\s*(please\s+)?(add|build|make|create|change|fix|remove|put|design|update|redo)\b", re.I)

def route(text, repo):
    """'connect_mail', 'connect_cal', 'connect_pay', 'reply_mail', 'mail', 'cal', 'pay', or None."""
    if KEYS.search(text) or CONNECT_PAY.search(text):
        return 'connect_pay'
    if calendar_.ICS.search(text) or CONNECT_CAL.search(text):
        return 'connect_cal'
    if CONNECT_MAIL.search(text):
        return 'connect_mail'
    if mail.config(repo) and REPLY.search(text):
        return 'reply_mail'
    if BUILD.search(text) or not ASK.search(text):
        return None
    if mail.config(repo) and MAIL.search(text):
        return 'mail'
    if calendar_.config(repo) and CAL.search(text):
        return 'cal'
    if payments.load(repo) and PAY.search(text):
        return 'pay'
    return None

def _ask(ch, poll, text, buttons=None):
    """One question; his typed answer, or None if he said no or stop."""
    ch.send(text, html=True, buttons=buttons)
    kind, got = telegram._wait(ch, poll, {'off|no'})
    if kind == 'tap' or (got or '').strip().lower() in ('no', 'stop', 'cancel', 'not now', 'later'):
        ch.send('Very good. Nothing was connected.')
        return None
    return got.strip()

def connect_mail(ch, repo, text, poll):
    m = ADDRESS.search(text)
    address = m.group(0) if m else _ask(ch, poll, "📧 <b>Which email address?</b> Any mailbox works: Gmail, Zoho, GoDaddy, "
                                                   "Hostinger, Outlook, or your own.", [[('Not now', 'off|no')]])
    if not address or not ADDRESS.search(address):
        if address:
            ch.send("That doesn't look like an email address. Say \"connect my email\" to try again.")
        return 'not_connected'
    address = ADDRESS.search(address).group(0)
    page = mail.guess(address)[3]
    pw = _ask(ch, poll, f"🔑 <b>Its password, please.</b> " + (f"Use an <b>app password</b>, not your normal one (make it "
              f"at {page}): it can be cancelled any time." if page else "If your provider offers app passwords, use one.") +
              "\n\n<i>I delete your message as soon as I've read it, and keep the password on this computer only. I "
              "only read your mail; nothing is sent without your yes.</i>", [[('Not now', 'off|no')]])
    if not pw:
        return 'not_connected'
    gone = ch.forget(pw)
    ch.typing() if callable(getattr(ch, 'typing', None)) else None
    pw = pw.replace(' ', '') if mail.guess(address)[0] == 'imap.gmail.com' else pw
    ok, said = mail.setup(repo, address, pw)
    if not ok and re.search(r'getaddrinfo|Name or service|nodename|timed out|refused|unreachable', said, re.I):
        # his own domain's mail lives elsewhere than imap.<domain>: ask where, once (GoDaddy, Hostinger, Zoho, ...)
        server = _ask(ch, poll, "📧 I couldn't find your mail server at the usual address. <b>Who provides your mailbox, "
                                "or what is its IMAP server?</b> (e.g. Zoho, GoDaddy, Hostinger, or imap.example.com)",
                      [[('Not now', 'off|no')]])
        if not server:
            return 'not_connected'
        name = next((k for k in mail.PROVIDERS if k in server.lower()), None)
        host = re.search(r'\b(imap\.[\w.-]+|[\w-]+(\.[\w-]+)+)\b', server)
        ok, said = mail.setup(repo, address, pw, provider=name) if name else \
            mail.setup(repo, address, pw, imap=host.group(1), smtp=re.sub(r'^imap\.', 'smtp.', host.group(1))) if host else \
            (False, "I couldn't tell the server from that.")
    ch.send(('✅ ' if ok else '⚠️ ') + telegram.esc(said) +
            ('' if gone else "\n\nPlease delete your message with the password yourself: I couldn't."), html=True)
    return 'mail_connected' if ok else 'not_connected'

def connect_cal(ch, repo, text, poll):
    m = calendar_.ICS.search(text)
    url = m.group(0) if m else _ask(ch, poll, "📅 <b>Your calendar's private address, please.</b>\n\nIn Google Calendar on a "
                                             "computer: Settings, click your calendar on the left, then \"Integrate "
                                             "calendar\", and copy the <b>Secret address in iCal format</b>. I can only "
                                             "read it; it can't be used to change anything.", [[('Not now', 'off|no')]])
    if not url or not calendar_.ICS.search(url):
        if url:
            ch.send("That isn't a calendar address (it ends in .ics). Say \"connect my calendar\" to try again.")
        return 'not_connected'
    url = calendar_.ICS.search(url).group(0)
    gone = ch.forget(url)
    ok, said = calendar_.setup(repo, url)
    ch.send(('✅ ' if ok else '⚠️ ') + telegram.esc(said) +
            ('' if gone else "\n\nPlease delete your message with the address yourself: it's a secret."), html=True)
    return 'cal_connected' if ok else 'not_connected'

def connect_pay(ch, repo, text, poll):
    which = 'razorpay' if re.search(r'razorpay|rzp_', text, re.I) else 'stripe' if re.search(r'stripe|\b[sr]k_', text, re.I) else None
    if not which:
        ch.send("Stripe or Razorpay?", buttons=[[('Stripe', 'pay|stripe'), ('Razorpay', 'pay|razorpay')]])
        kind, got = telegram._wait(ch, poll, {'pay|stripe', 'pay|razorpay'})
        which = got.split('|')[1] if kind == 'tap' else ('razorpay' if 'razor' in (got or '').lower() else 'stripe')
    keys = KEYS.findall(text) and text
    if which == 'stripe':
        got = keys or _ask(ch, poll, "💳 <b>A read-only Stripe key, please.</b>\n\nStripe Dashboard, Developers, API keys, "
                           "<b>Create restricted key</b>: give it <i>Read</i> on Charges, Customers and Refunds, nothing "
                           "else. It starts with <code>rk_</code>. With it I can't move money even by mistake.\n\n<i>I delete "
                           "your message as soon as I've read it.</i>", [[('Not now', 'off|no')]])
        k = re.search(r'\b[sr]k_(live|test)_\w+', got or '')
        if not k:
            if got:
                ch.send("That isn't a Stripe key (it starts with rk_ or sk_). Say \"connect Stripe\" to try again.")
            return 'not_connected'
        gone = ch.forget(k.group(0))
        ok, said = payments.add(repo, 'stripe', k.group(0))
    else:
        got = keys or _ask(ch, poll, "💳 <b>Your Razorpay key ID and secret, please</b>, in one message.\n\nRazorpay "
                           "Dashboard, Account &amp; Settings, API Keys. Razorpay keys can't be limited to reading, so know "
                           "that I only ever read with them: I never refund, capture or move money.\n\n<i>I delete your "
                           "message as soon as I've read it.</i>", [[('Not now', 'off|no')]])
        kid = re.search(r'\brzp_(live|test)_\w+', got or '')
        rest = [w for w in re.split(r'[\s,:;]+', (got or '').replace(kid.group(0), '') if kid else '') if len(w) >= 12]
        if not kid or not rest:
            if got:
                ch.send("I need both: the key ID (rzp_live_...) and its secret. Say \"connect Razorpay\" to try again.")
            return 'not_connected'
        gone = ch.forget(rest[0]); ch.forget(kid.group(0))
        ok, said = payments.add(repo, 'razorpay', rest[0], kid.group(0))
    ch.send(('✅ ' if ok else '⚠️ ') + telegram.esc(said) +
            ('' if gone else "\n\nPlease delete your message with the key yourself: I couldn't."), html=True)
    return 'pay_connected' if ok else 'not_connected'

def reply_mail(ch, repo, text, poll):
    """'Reply to Asha saying Thursday works': find her mail, draft it in his voice, show it, send only on his yes."""
    ch.send("📧 Finding that email and drafting your reply; a moment.")
    msg = mail.find(repo, text)
    if not msg:
        ch.send("I couldn't tell which email you mean from the last two weeks. Who is it from, or what was it about?")
        return 'mail_not_found'
    while True:
        body = mail.draft(repo, msg, text)
        if not body:
            ch.send("I couldn't draft it just now. Try again in a minute."); return 'draft_failed'
        ch.send(f"📧 <b>Your reply to {telegram.esc(msg['from'])}</b>\n<i>Re: {telegram.esc(msg['subject'])}</i>\n\n"
                f"{telegram.esc(body)}\n\n<i>Send it from your address?</i>", html=True,
                buttons=[[('📤 Send it', 'mlr|send')], [('✏️ Change it', 'mlr|edit')], [("Don't send", 'mlr|no')]])
        kind, got = telegram._wait(ch, poll, {'mlr|send', 'mlr|edit', 'mlr|no'})
        low = (got or '').strip().lower()
        if got == 'mlr|send' or (kind == 'text' and low in ('send', 'send it', 'yes', 'yes send it', 'haan', 'ok send')):
            to = (mail.email.utils.parseaddr(msg['from'])[1] or msg['from'])
            ok, why = mail.send(repo, to, msg['subject'], body, reply_to=msg)
            ch.send(f"✅ Sent to {telegram.esc(to)}." if ok else f"⚠️ It wasn't sent ({telegram.esc(why)}). Nothing went out.",
                    html=True)
            return 'mail_sent' if ok else 'mail_failed'
        if got == 'mlr|no' or low in ('no', "don't send", 'dont send', 'cancel', 'stop'):
            ch.send("Very good. Nothing was sent."); return 'mail_not_sent'
        if got == 'mlr|edit':
            ch.send("What should it say differently?")
            kind, got = telegram._wait(ch, poll, set())
        text = f"{text}\n\nHe changed his mind about the draft: {got}"

def handle(ch, repo, text, poll, kind=None):
    kind = kind or route(text, repo)
    if kind == 'connect_mail':
        return connect_mail(ch, repo, text, poll)
    if kind == 'connect_cal':
        return connect_cal(ch, repo, text, poll)
    if kind == 'connect_pay':
        return connect_pay(ch, repo, text, poll)
    if kind == 'reply_mail':
        return reply_mail(ch, repo, text, poll)
    mod = {'mail': mail, 'cal': calendar_, 'pay': payments}.get(kind)
    if not mod:
        return None
    # an answer takes 7-10 seconds (Gate 112); say at once what is happening, as a person would
    ch.send({'mail': '📧 Reading your mail…', 'cal': '📅 Checking your calendar…', 'pay': '💳 Adding up your payments…'}[kind])
    try:
        r = mod.answer(repo, text)
    except Exception as e:
        r = {'ok': False, 'say': f"I couldn't reach it just now ({str(e)[:100]})."}
    ch.send(('📧 ' if kind == 'mail' else '📅 ' if kind == 'cal' else '💳 ') + telegram.esc(r['say']), html=True)
    return kind + ('_answered' if r.get('ok') else '_failed')

def summary(repo):
    """What of his office Hive can see, for what it tells the model about him."""
    return [s for s in (mail.summary(repo), calendar_.summary(repo), payments.summary(repo)) if s]
