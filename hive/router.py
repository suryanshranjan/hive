"""Reading what he means as a plan of steps, not one intent (P4: "find Asha's mail and put a call with her on
Thursday" is two things, the second using the first).

The reader before this (assistant.CLASSIFY) picks one intent per message. This one returns a short plan: one step for
almost every message (then it is the same intent, handled by the same code), up to 4 for a message that asks for
several things in order. A later step can use an earlier one's result: "$1.email" is the sender's address from step 1.

  {"steps": [{"tool": "mail_find", "args": {"about": "Asha's mail about the tasting"}},
             {"tool": "calendar_add", "args": {"what": "call with Asha", "when": "Thursday 4 pm", "guests": ["$1.email"]}}]}

Plan routing remains opt-in (HIVE_ROUTER=plan) while real execution is qualified. Chains checkpoint in SQLite;
explicit resume skips completed steps, and uncertain writes block recovery. Each step still goes through the policy
check (hive/tools.py), and every step that reaches outside still asks for his yes."""
import re
from contextvars import ContextVar
from dataclasses import replace

from . import explain

# The legacy callback accepts text. Carry its validated intent through that one
# callback so text returned by a tool never re-enters the owner command parser.
PLANNED_INTENT = ContextVar('hive_planned_intent', default=None)
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

DIRECT = {'mail_send', 'remember', 'mail_find'}   # steps only the step runner does, even alone

KNOWN = set(re.findall(r'^- "([a-z_]+)"', TOOLS, re.M)) | {'cloud_on', 'cloud_off'}

def plan(history, text):
    """His message as a validated plan; unsupported tools/references refuse the whole plan."""
    got = explain.ask_json(PLAN.format(history=history or '(nothing yet)', text=text, tools=TOOLS)) or {}
    from .tools import Refused
    if not isinstance(got, dict):
        raise Refused('I could not read that plan. Nothing was started.')
    steps = validate_steps(got.get('steps', []))
    return {'steps': steps, 'confirmed': bool(got.get('confirmed')), 'clarify': got.get('clarify') or ''}


REFERENCE = re.compile(r'\$(\d+)(?:\.(\w+))?')


def references(value):
    if isinstance(value, (list, dict)):
        for child in value.values() if isinstance(value, dict) else value:
            yield from references(child)
    elif isinstance(value, str):
        match = REFERENCE.fullmatch(value.strip())
        if match:
            yield int(match[1])


def validate_steps(steps):
    """Reject the whole plan before acting, including invalid forward references."""
    from .tools import Refused
    if not isinstance(steps, list) or len(steps) > 4:
        raise Refused('Please split this into requests of at most four steps.')
    clean = []
    for n, step in enumerate(steps, 1):
        if (not isinstance(step, dict) or not isinstance(step.get('tool'), str) or
                step['tool'] not in KNOWN or not isinstance(step.get('args', {}), dict)):
            raise Refused('The proposed plan contains an unsupported action. Nothing was started.')
        if any(not 1 <= prior < n for prior in references(step.get('args', {}))):
            raise Refused('A step can only use an earlier result. Nothing was started.')
        clean.append({'tool': step['tool'], 'args': step.get('args', {})})
    return clean

INTENT_ARG = {'build': 'what', 'change': 'rule', 'rule': 'rule', 'instruct': 'rule', 'amend': 'rule', 'goal': 'goal',
              'complaint': 'text', 'data': 'question', 'reply': 'text'}
OFFICE = {'mail_find', 'mail_read', 'mail_reply', 'mail_send', 'calendar_check', 'calendar_add', 'remember',
          'memory_ask', 'forget', 'pulse_set'}

def as_intent(step, text):
    """One step as the reader's old answer ({'intent', 'rule', ...}), so a one-step plan runs through the same code."""
    tool, args = step['tool'], step['args']
    office = {'mail_read': 'mail', 'mail_find': 'mail', 'mail_reply': 'reply_mail', 'calendar_check': 'cal',
              'calendar_add': 'add_event'}
    if tool in office:
        return {'intent': 'office', 'office': office[tool], 'rule': text}
    if tool == 'mail_send':
        return {'intent': 'reply', 'rule': text}
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
    if isinstance(value, dict):
        return {k: _ref(v, results) for k, v in value.items()}
    if not isinstance(value, str):
        return value
    m = REFERENCE.fullmatch(value.strip())
    if not m:
        return value
    if int(m.group(1)) not in results:
        raise ValueError('A required earlier step has no result')
    r = results[int(m.group(1))]
    if m.group(2) and m.group(2) not in r:
        raise ValueError('An earlier step did not provide the required detail')
    return r.get(m.group(2)) if m.group(2) else r

def run_chain(ch, repo, steps, text, poll=20, handle=None, origin='owner'):
    """Persist before executing; redelivered requests reuse their existing task."""
    from . import tasks, tools
    try:
        if origin != 'owner':
            raise tools.Refused('Only your own chat can start saved tasks.')
        steps = validate_steps(steps)
        if not steps:
            return []
        task = tasks.create(ch, repo, steps, text)
        claimed = tasks.claim(task['id'], ch, repo)
        if claimed:
            return _run_task(ch, repo, claimed, poll, handle)
        task = tasks.get(task['id'], ch, repo)
        ch.send(tasks.describe(task))
        return tasks.outcomes(task)
    except tools.Refused as e:
        ch.send(str(e))
        return ['refused']


def _run_task(ch, repo, task, poll, handle):
    from . import tasks, telegram, tools
    steps, tid = task['steps'], task['id']
    results = {int(n): r for n, r in task['results'].items() if int(n) < task['next_step']}
    if task['next_step'] == 1 and len(steps) > 1:
        ch.send(f"On it: {len(steps)} things, in order. Task {tid}.")
    for n in range(task['next_step'], len(steps) + 1):
        step = steps[n - 1]
        tool = step['tool']
        tasks.begin_step(tid, n)
        try:
            if task['bindings'] != tasks.bindings(repo, steps):
                raise tools.Refused('A connected account changed. Start a new request with the current account.')
            tools.allow(tool, 'owner', task['instruction'])
            args = _ref(step['args'], results)
        except (ValueError, tools.Refused) as e:
            r = {'status': 'refused' if isinstance(e, tools.Refused) else 'needs_input', 'why': str(e)}
        else:
            try:
                with tasks.executing(tid, n):
                    run_step = _observed_step if any(references(step['args'])) else _step
                    r = run_step(ch, repo, tool, args, task['instruction'], poll, handle)
                if not isinstance(r, dict) or not isinstance(r.get('status'), str):
                    r = {'status': 'unknown', 'why': 'The step did not report a confirmed outcome.'}
            except tools.Refused as exc:
                r = {'status': 'refused', 'why': str(exc)}
            except Exception:
                # The provider may have accepted a write before a connection failed.
                r = {'status': 'failed' if tool in tasks.RETRYABLE else 'unknown',
                     'why': 'The step was interrupted. Its outcome needs checking.'}
        from . import store, verification
        with store.transaction():
            r = verification.result(tid, n, None, r)
            tasks.finish_step(tid, n, r)
        results[n] = r
        if r['status'] not in tasks.SUCCESS:
            saved = tasks.get(tid, ch, repo)
            ch.send('🐝 ' + telegram.esc(f"I stopped at step {n}: {r.get('why') or r['status']}. " +
                                        tasks.describe(saved)), html=True)
            break
    return tasks.outcomes(tasks.get(tid, ch, repo))


def resume_chain(ch, repo, tid, poll=20, handle=None):
    from . import tasks
    saved = tasks.reconcile(tid, ch, repo)
    if saved and saved['mode'] == 'adaptive':
        from . import agent
        return agent.resume(ch, repo, tid, poll)
    if saved and saved['mode'] == 'build':
        from . import buildplans
        buildplans.resume(ch, repo, tid)
        return tasks.outcomes(tasks.get(tid, ch, repo))
    task = tasks.claim(tid, ch, repo, resume=True)
    if task:
        ch.send(f"Continuing task {tid} from step {task['next_step']}.")
        return _run_task(ch, repo, task, poll, handle)
    task = tasks.get(tid, ch, repo)
    ch.send(tasks.describe(task) if task else 'That task is unavailable in this chat and project.')
    return tasks.outcomes(task) if task else []


def task_command(ch, repo, text, poll=20, handle=None):
    """Explicit task controls work even while plan routing is opt-in."""
    from . import tasks, tools
    match = re.fullmatch(r'(resume task|pause task|cancel task|verify task|resolve task|task) ([0-9a-f]{12})(?: (complete|incomplete))?', text.strip(), re.I)
    if text.strip().lower() != 'tasks' and not match:
        return None
    try:
        if match and match[1].lower() in ('pause task','cancel task'):
            tools.allow('run_plan', detail=text)
            task = tasks.control(match[2].lower(), ch, repo, match[1].lower().split()[0])
            ch.send(tasks.describe(task))
            return 'task_' + ('cancelled' if match[1].lower() == 'cancel task' else 'paused')
        if match and match[1].lower() in ('resolve task','verify task'):
            from . import verification
            if match[1].lower() == 'resolve task':
                verification.resolve(ch, repo, match[2].lower(), (match[3] or '').lower())
            else:
                verification.retry(ch, repo, match[2].lower())
            ch.send(tasks.describe(tasks.get(match[2].lower(), ch, repo), detailed=True))
            return 'task_checked'
        if match and match[1].lower() == 'resume task':
            tools.allow('run_plan', detail=text)
            return 'chain:' + ','.join(resume_chain(ch, repo, match[2].lower(), poll, handle))
        tools.allow('status', detail=text)
        if match:
            task = tasks.get(match[2].lower(), ch, repo)
            ch.send(tasks.describe(task, detailed=True) if task else 'That task is unavailable in this chat and project.')
        else:
            ch.send(tasks.listing(ch, repo))
        return 'tasks_shown'
    except tools.Refused as e:
        ch.send(str(e))
        return 'refused'

def _observed_step(ch, repo, tool, args, text, poll, handle):
    """Pass observed data to an explicit adapter, retaining its origin in legacy handlers."""
    from . import memory, policy, tasks, tools
    if tool in ('mail_find', 'mail_reply', 'mail_send', 'calendar_check', 'calendar_add'):
        return _step(ch, repo, tool, args, text, poll, handle)
    if tool == 'remember':
        fact = args.get('fact')
        if not isinstance(fact, str) or not fact.strip():
            raise tools.Refused('The earlier result did not contain a text fact.')
        tid, n = tasks.ACTIVE_STEP.get()
        memory.add_note(repo, fact, source='tool', trust='outside', source_ref=f'{tid}:{n}')
        return {'status': 'done'}
    tools.allow(tool, 'outside')
    auth = policy.CURRENT.set(replace(policy.context(), origin='outside'))
    try:
        return _step(ch, repo, tool, args, text, poll, handle)
    finally:
        policy.CURRENT.reset(auth)


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
        status = office.reply_mail(ch, repo, how, poll)
        return {'status': 'unknown' if status in (None, 'mail_unknown') else status}
    if tool == 'mail_send':
        to = args.get('to') if isinstance(args.get('to'), str) else ''
        if not office.ADDRESS.fullmatch((to or '').strip()):
            return {'status': 'failed', 'why': "I don't have an address to send it to"}
        body = args.get('say') or ''
        from . import actions
        payload = {'to': to, 'subject': args.get('subject') or '(no subject)', 'body': body}
        aid = actions.confirm(ch, 'mail_send', payload,
                              f"To {telegram.esc(to)}: <b>{telegram.esc(payload['subject'])}</b>\n{telegram.esc(body)}",
                              poll, yes_label='Send it')
        if not aid:
            return {'status': 'cancelled'}
        result = actions.execute(aid, lambda a: office._send_result(repo, a))
        ch.send('Sent.' if result.status == 'succeeded' else 'The send is unconfirmed; I will not repeat it automatically.')
        return {'status': result.status}
    if tool == 'calendar_add':
        guests = [g for g in (args.get('guests') or []) if isinstance(g, str) and '@' in g]
        how = f"put {args.get('what') or 'it'} on my calendar {args.get('when') or ''}" + \
              (f" with {', '.join(guests)}" if guests else '')
        status = office.add_event(ch, repo, how, poll)
        return {'status': 'unknown' if status in (None, 'event_unknown') else status}
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
    if handle is not None:
        words = args.get('text') or args.get('what') or args.get('rule') or args.get('question') or \
                args.get('about') or args.get('goal') or text
        token = PLANNED_INTENT.set(as_intent({'tool': tool, 'args': args}, str(words)))
        try:
            return {'status': handle(ch, repo, str(words), poll) or 'unknown'}
        finally:
            PLANNED_INTENT.reset(token)
    return {'status': 'failed', 'why': f'no way to do {tool} here'}
