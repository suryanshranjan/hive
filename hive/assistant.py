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

Classify it. Reply with JSON only: {{"intent": "change" | "rule" | "status" | "greeting" | "other",
"rule": "the rule he now wants, in one plain sentence, or empty"}}
- "change": he says he has changed his mind, or now wants something different from before.
- "rule": he states a new rule for how the product should behave.
- "status": he asks how things are going.
- "greeting": a hello, or waking Hive up with no request yet."""

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

def handle(ch, repo, text, poll=20, apply_build=None):
    """Answer one message from the owner. apply_build(state, rule) updates a build (hive.start.apply_ruling)."""
    got = explain.ask_json(CLASSIFY.format(text=text)) or {}
    intent, rule = got.get('intent', 'other'), (got.get('rule') or text).strip()
    who = _who(ch)
    if intent == 'greeting':
        ch.send(f"At your service{', ' + who if who else ''}. Tell me if you've changed your mind about anything, give me "
                "a new rule, or ask for the status.")
        return 'greeting'
    if intent == 'status':
        st = latest_build(repo)
        ch.send((f"The latest build is on branch hive/{st['name']}. {st.get('check', '')}".strip()) if st else
                'Nothing has been built on this project yet.')
        return 'status'
    if intent not in ('change', 'rule'):
        ch.send("Noted. Shall I keep this as a standing rule for the builders?",
                buttons=[[('Yes, keep it as a rule', 'as|rule')], [('No, just a note', 'as|note')]])
        if telegram._wait(ch, poll, {'as|rule', 'as|note'})[1] != 'as|rule':
            ch.send('Very good.'); return 'note'
    rulings = memory.load(repo)
    listing = '\n'.join(f'{n}. {r["text"]}' for n, r in enumerate(rulings, 1))
    found = (explain.ask_json(RELATED.format(rulings=listing, rule=rule)) or {}).get('replaces', []) if rulings else []
    old = [n - 1 for n in found if isinstance(n, int) and 1 <= n <= len(rulings)]
    if old:
        before = '\n'.join(f'- {rulings[i]["text"]}' for i in old)
        ch.send(f"Understood. Earlier you ruled:\n{before}\n\nNow: {rule}\n\nShall I replace the earlier ruling with this?",
                buttons=[[('Replace it', 'chg|replace')], [('Keep both', 'chg|both')], [('Cancel', 'chg|cancel')]])
        choice = telegram._wait(ch, poll, {'chg|replace', 'chg|both', 'chg|cancel'})[1]
        if choice == 'chg|cancel':
            ch.send('Of course. Nothing changed.'); return 'cancelled'
        if choice == 'chg|replace':
            memory.replace(repo, old, rule)
        else:
            memory.add(repo, rule, 'changed')
    else:
        memory.add(repo, rule, 'owner')
        ch.send(f"Noted as a standing rule: {rule}")
    st = latest_build(repo)
    if st and apply_build:
        ch.send(f"Shall I update the latest build (branch hive/{st['name']}) to follow it?",
                buttons=[[('Yes, update it', 'upd|yes')], [('Not now', 'upd|no')]])
        if telegram._wait(ch, poll, {'upd|yes', 'upd|no'})[1] == 'upd|yes':
            ch.send("Right away. I'll let you know the moment it's done.")
            apply_build(st, rule, ch)
            return 'applied'
    ch.send('Very good. The builders will follow it from the next build.')
    return 'kept'

def listen(repo='.', poll=10, apply_build=None, until=None):
    """Stay on the owner's Telegram between builds and handle whatever he sends. Ctrl+C to stop."""
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
            for text, data, _ in ch.updates(timeout=poll):
                if text:
                    handle(ch, repo, text, apply_build=apply_build)
    except KeyboardInterrupt:
        pass
    return 0
