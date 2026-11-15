"""Reading what he means as a plan of steps, not one intent (P4: "find Asha's mail and put a call with her on
Thursday" is two things, the second using the first).

The reader before this (assistant.CLASSIFY) picks one intent per message. This one returns a short plan: one step for
almost every message (then it is the same intent, handled by the same code), up to 4 for a message that asks for
several things in order. A later step can use an earlier one's result: "$1.email" is the sender's address from step 1.

  {"steps": [{"tool": "mail_find", "args": {"about": "Asha's mail about the tasting"}},
             {"tool": "calendar_add", "args": {"what": "call with Asha", "when": "Thursday 4 pm", "guests": ["$1.email"]}}]}

It ships only if Gate 120 says it reads single messages no worse than the reader it replaces (HIVE_ROUTER=plan turns it
on before that; the gate decides the default). Each step still goes through the one check before any action
(hive/tools.py), and every step that reaches outside still asks for his yes."""
import re

from . import explain

TOOLS = '''
- "build": he wants something built, added or made in his product (or agrees to / corrects a build you proposed).
  args: {"what": what to build, as he said it}
- "stop_build": stop the build that is running.
- "change": he has changed his mind about an earlier rule. args: {"rule": the rule he now wants}
- "rule": he states, plainly and on purpose, a rule for how the product should behave from now on. args: {"rule": ...}
- "status": how things are going.
- "team": about the builders themselves (who is doing what, which agents, what one did).
- "set_team": he chooses the builders (which agents, how many). args: {"agent": "claude"|"codex"|"gemini"|a mix,
  "workers": a number or 0}
- "stop_builder": stop one builder. args: {"builder": as he named it, "drop_work": true|false}
- "instruct": mid-build, tell the builders to do something different or extra in this build. args: {"rule": the
  instruction, "builder": if he names one}
- "show": he wants to see how it looks (screenshots).
- "amend": right after seeing a build, he wants it changed. args: {"rule": the change}
- "ship": send his latest build to his engineer as a pull request.
- "go_live": put it live.
- "undo": undo the last thing done.
- "complaint": he passes on a customer's complaint. args: {"text": what the customer says}
- "goal": a business outcome he wants, not a particular change. args: {"goal": ...}
- "data": a question about his business's own figures or records. args: {"question": ...}
- "onboard": set his company up with you.
- "away": he is stepping away (tired, sleeping, leaving).
- "greeting": a hello, with no request yet.
- "cloud_on" / "cloud_off": move Hive to the cloud / shut the cloud machine down.
- "mail_find": find one mail he means. args: {"about": who it is from and what about}. Result: from, email, subject,
  text.
- "mail_read": a question about his mail ("any important emails?"). args: {"question": ...}
- "mail_reply": reply to a mail. args: {"to": "$N" (a mail found in an earlier step) or who, "say": what to say}
- "mail_send": a new mail. args: {"to": an address or "$N.email", "subject": ..., "say": what to say}
- "calendar_check": is he free, what is on. args: {"when": as he said it}. Result: free (true|false), busy.
- "calendar_add": put something on his calendar. args: {"what": ..., "when": as he said it, "minutes": a number,
  "guests": [addresses or "$N.email"]}
- "remember": keep a fact about his business or his people. args: {"fact": one plain sentence, "until": "YYYY-MM-DD"
  if it is due by a date, else ""}
- "memory_ask": what do you know about someone or something. args: {"about": ...}
- "forget": forget something kept. args: {"what": ...}
- "pulse_set": what Hive should tell him about, quiet hours. args: {"text": his words}
- "reply": anything else: a question, frustration, small talk. args: {"text": ...}
A technical instruction ("add an index on users.email") is "build" (or "instruct" mid-build).'''

PLAN = """You are Hive, a business owner's assistant on his phone. The conversation so far (oldest first):
{history}

His newest message: "{text}"

What does he want done? Read it as a person would, using the conversation ("yes" answers what you last proposed; "that
one" points back). Most messages are one step. Make several steps only when he asks for several separate things, in
the order he wants them ("find X and then do Y", "ship it and put it live"); one thing with several parts ("add a share
button and a download button") is one step. A step may use an earlier step's result: "$1" is step 1's result,
"$1.email" its email address.
The steps you can use:
{tools}

Reply with JSON only: {{"steps": [{{"tool": "...", "args": {{...}}}}], "confirmed": true if he is agreeing to what you
just proposed, else false, "clarify": one short question if a build is too vague to build, else ""}}"""

KNOWN = set(re.findall(r'^- "([a-z_]+)"', TOOLS, re.M)) | {'cloud_on', 'cloud_off'}

def plan(history, text):
    """His message as {'steps': [{'tool', 'args'}], 'confirmed', 'clarify'}; steps with unknown tools are dropped;
    {'steps': []} if the model gave nothing usable."""
    got = explain.ask_json(PLAN.format(history=history or '(nothing yet)', text=text, tools=TOOLS)) or {}
    steps = []
    for s in (got.get('steps') or [])[:4]:
        if isinstance(s, dict) and s.get('tool') in KNOWN:
            steps.append({'tool': s['tool'], 'args': s.get('args') if isinstance(s.get('args'), dict) else {}})
    return {'steps': steps, 'confirmed': bool(got.get('confirmed')), 'clarify': got.get('clarify') or ''}

INTENT_ARG = {'build': 'what', 'change': 'rule', 'rule': 'rule', 'instruct': 'rule', 'amend': 'rule', 'goal': 'goal',
              'complaint': 'text', 'data': 'question', 'reply': 'text'}
OFFICE = {'mail_find', 'mail_read', 'mail_reply', 'mail_send', 'calendar_check', 'calendar_add', 'remember',
          'memory_ask', 'forget', 'pulse_set'}

def as_intent(step, text):
    """One step as the reader's old answer ({'intent', 'rule', ...}), so a one-step plan runs through the same code."""
    tool, args = step['tool'], step['args']
    if tool in ('mail_read', 'mail_find', 'mail_reply', 'mail_send', 'calendar_check', 'calendar_add'):
        return {'intent': 'office', 'rule': text}
    if tool == 'remember':
        return {'intent': 'reply', 'rule': text}
    got = {'intent': tool, 'rule': str(args.get(INTENT_ARG.get(tool, 'rule')) or text)}
    for k in ('agent', 'workers', 'builder', 'drop_work'):
        if k in args:
            got[k] = args[k]
    return got

def _ref(value, results):
    """"$2.email" -> step 2's email; "$1" -> step 1's whole result; anything else as it is."""
    if isinstance(value, list):
        return [_ref(v, results) for v in value]
    if not isinstance(value, str):
        return value
    m = re.fullmatch(r'\$(\d)(?:\.(\w+))?', value.strip())
    if not m:
        return value
    r = results.get(int(m.group(1))) or {}
    return r.get(m.group(2)) if m.group(2) else r

def run_chain(ch, repo, steps, text, poll=20, handle=None):
    """Several steps in order, each through the one check, each external one on his yes, a later one using an earlier
    one's result. Stops at the first step that cannot be done, and says which and why. Returns [what each step did]."""
    from . import telegram, tools
    results, done = {}, []
    ch.send('🐝 ' + telegram.esc(f"On it: {len(steps)} things, in order."), html=True)
    for n, step in enumerate(steps, 1):
        tool, args = step['tool'], {k: _ref(v, results) for k, v in step['args'].items()}
        try:
            tools.allow({'mail_send': 'mail_send', 'mail_reply': 'mail_send', 'calendar_add': 'add_event'}.get(tool, tool),
                        'owner', text)
        except tools.Refused as e:
            ch.send('🐝 ' + telegram.esc(str(e)), html=True); done.append('refused'); break
        r = _step(ch, repo, tool, args, text, poll, handle)
        results[n] = r if isinstance(r, dict) else {'said': r}
        done.append(results[n].get('status', 'done'))
        if results[n].get('status') in ('failed', 'no', 'not_found'):
            ch.send('🐝 ' + telegram.esc(f"I stopped at step {n}: {results[n].get('why') or 'it could not be done'}."),
                    html=True)
            break
    return done

def _step(ch, repo, tool, args, text, poll, handle):
    from . import calendar_, mail, office, telegram
    if tool == 'mail_find':
        m = mail.find(repo, args.get('about') or text)
        if not m:
            return {'status': 'not_found', 'why': f"I couldn't find that mail ({args.get('about') or ''})"}
        email = mail.email.utils.parseaddr(m['from'])[1]
        ch.send(f"📧 Found it: {telegram.esc(m['subject'])}, from {telegram.esc(m['from'])}.", html=True)
        return dict(m, email=email, status='done')
    if tool == 'mail_reply':
        target = args.get('to')
        how = f"reply to {target.get('from', '') if isinstance(target, dict) else target} saying {args.get('say', '')}"
        return {'status': office.reply_mail(ch, repo, how, poll) or 'done'}
    if tool == 'mail_send':
        to = args.get('to') if isinstance(args.get('to'), str) else ''
        if not office.ADDRESS.fullmatch((to or '').strip()):
            return {'status': 'failed', 'why': "I don't have an address to send it to"}
        body = args.get('say') or ''
        ch.send(f"📧 To {telegram.esc(to)}: <b>{telegram.esc(args.get('subject') or '')}</b>\n{telegram.esc(body)}\n\n"
                "<i>Send it from your address?</i>", html=True, buttons=[[('📤 Send it', 'mls|yes'), ("Don't", 'mls|no')]])
        kind, got = telegram._wait(ch, poll, {'mls|yes', 'mls|no'})
        if got != 'mls|yes' and not (kind == 'text' and (got or '').strip().lower() in ('yes', 'send', 'send it', 'haan')):
            ch.send('Very good. Nothing was sent.'); return {'status': 'no'}
        ok, why = mail.send(repo, to, args.get('subject') or '(no subject)', body)
        ch.send('✅ Sent.' if ok else f"⚠️ Not sent ({telegram.esc(why)}).", html=True)
        return {'status': 'done' if ok else 'failed', 'why': why}
    if tool == 'calendar_add':
        guests = [g for g in (args.get('guests') or []) if isinstance(g, str) and '@' in g]
        how = f"put {args.get('what') or 'it'} on my calendar {args.get('when') or ''}" + \
              (f" with {', '.join(guests)}" if guests else '')
        return {'status': office.add_event(ch, repo, how, poll) or 'done'}
    if tool == 'calendar_check':
        r = calendar_.answer(repo, f"am I free {args.get('when') or ''}?")
        ch.send('📅 ' + telegram.esc(r['say']), html=True)
        return {'status': 'done' if r.get('ok') else 'failed', 'free': 'yes' in r['say'].lower()[:12], 'why': r['say']}
    if tool == 'remember':
        from . import assistant
        until = args.get('until') if re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(args.get('until') or '')) else ''
        fact = args.get('fact') or text
        assistant.keep(repo, {'note': fact, 'kind': 'deadline' if until else 'note', 'until': until})
        ch.send('🧠 Kept: ' + telegram.esc(fact), html=True)
        return {'status': 'done'}
    if handle is not None:   # any other step runs as a message of its own, through the usual code
        words = args.get('text') or args.get('what') or args.get('rule') or args.get('question') or \
                args.get('about') or args.get('goal') or text
        return {'status': handle(ch, repo, str(words), poll) or 'done'}
    return {'status': 'failed', 'why': f'no way to do {tool} here'}
