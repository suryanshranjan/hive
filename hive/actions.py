"""Durable, single-use approvals and conservative outcomes for outward actions.

An interrupted executing action is unknown, never automatically replayed. Provider
receipts, not a model's sentence, establish success.
"""
import hashlib
import json
import secrets
import time
from dataclasses import dataclass
from contextvars import ContextVar

EXECUTING = ContextVar('hive_action', default=None)
from . import policy, store


@dataclass(frozen=True)
class ActionResult:
    status: str
    receipt: str = ''


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def account_binding(tool, repo):
    from . import google, mail
    if tool not in ('mail_send', 'add_event'):
        return ''
    if tool == 'mail_send':
        cfg = mail.config(repo) if repo else {}
        if cfg.get('kind') != 'google':
            identity = [cfg.get('user'), cfg.get('smtp')]
            return hashlib.sha256(_json(identity).encode()).hexdigest()
    cfg = google._load()
    return hashlib.sha256(_json([cfg.get('client_id'), cfg.get('refresh_token')]).encode()).hexdigest()


def propose(tool, args, ch, ctx=None):
    from . import tools
    ctx = ctx or policy.context()
    tools.allow(tool, ctx.origin)
    tools.validate(tool, args)
    aid = secrets.token_hex(12)
    payload = _json(args)
    digest = hashlib.sha256((tool + '\n' + payload).encode()).hexdigest()
    request_key = hashlib.sha256((str(ch.chat) + ctx.project + ctx.update_id + digest).encode()).hexdigest() if ctx.update_id else None
    with store.transaction() as con:
        if request_key:
            existing = con.execute('SELECT id FROM actions WHERE request_key=?', (request_key,)).fetchone()
            if existing:
                from . import tasks
                tasks.link_action(existing[0])
                return existing[0]
        con.execute('INSERT INTO actions(id,tool,args,proposal_hash,owner_id,chat_id,origin,state,created,expires,project,request_key,account_binding) '
                    'VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)', (aid, tool, payload, digest, ctx.owner,
                    str(ch.chat), ctx.origin, 'proposed', time.time(), time.time() + 900, ctx.project, request_key,
                    account_binding(tool, ctx.project)))
        con.execute('INSERT INTO action_events(action_id,state,at) VALUES(?,?,?)', (aid, 'proposed', time.time()))
        from . import tasks
        tasks.link_action(aid)
    return aid


def bind(aid, message_id):
    store.connect().execute("UPDATE actions SET message_id=? WHERE id=? AND state='proposed'",
                            (message_id, aid))


def get(aid):
    row = store.connect().execute('SELECT * FROM actions WHERE id=?', (aid,)).fetchone()
    return dict(row) if row else None


def approve(aid, ch, message_id, yes=True):
    ctx = policy.context()
    with store.transaction() as con:
        row = get(aid)
        if not row or row['state'] != 'proposed' or row['expires'] <= time.time():
            return False
        if (row['owner_id'] != ctx.owner or row['chat_id'] != str(ch.chat) or
                row['message_id'] != message_id or ctx.origin != 'owner'):
            return False
        state = 'approved' if yes else 'cancelled'
        con.execute('UPDATE actions SET state=? WHERE id=?', (state, aid))
        con.execute('INSERT INTO action_events(action_id,state,at) VALUES(?,?,?)', (aid, state, time.time()))
        return True


def execute(aid, fn):
    with store.transaction() as con:
        row = get(aid)
        if not row or row['state'] != 'approved' or row['expires'] <= time.time():
            return ActionResult('cancelled')
        if account_binding(row['tool'], row['project']) != row['account_binding']:
            con.execute("UPDATE actions SET state='needs_input' WHERE id=?", (aid,))
            con.execute('INSERT INTO action_events(action_id,state,at) VALUES(?,?,?)', (aid, 'needs_input', time.time()))
            return ActionResult('needs_input')
        digest = hashlib.sha256((row['tool'] + '\n' + row['args']).encode()).hexdigest()
        if digest != row['proposal_hash']:
            raise ValueError('The approved action changed')
        con.execute("UPDATE actions SET state='executing' WHERE id=?", (aid,))
        con.execute('INSERT INTO action_events(action_id,state,at) VALUES(?,?,?)', (aid, 'executing', time.time()))
    token = EXECUTING.set(aid)
    try:
        result = fn(json.loads(row['args']))
        if not isinstance(result, ActionResult):
            raise TypeError('An action must return an ActionResult')
        if result.status not in ('succeeded', 'failed', 'unknown', 'needs_input', 'cancelled'):
            raise ValueError('Invalid action outcome')
    except Exception:
        # A timeout, disconnect or crash may happen after the provider accepted it.
        result = ActionResult('unknown')
    finally:
        EXECUTING.reset(token)
    with store.transaction() as con:
        con.execute('UPDATE actions SET state=?,receipt=? WHERE id=?', (result.status, result.receipt[:500], aid))
        con.execute('INSERT INTO action_events(action_id,state,at) VALUES(?,?,?)', (aid, result.status, time.time()))
    return result


def execute_dict(aid, fn):
    """Adapter for existing provider functions returning an explicit ok field."""
    box = {}
    def run(args):
        box['result'] = fn(args)
        result = box['result']
        return ActionResult('succeeded' if result.get('ok') else 'failed', str(result.get('url') or ''))
    result = execute(aid, run)
    return box.get('result') if result.status in ('succeeded', 'failed') else {
        'ok': False, 'why': 'unknown', 'say': 'The outcome is unconfirmed. I will not repeat it automatically.'}


def cloud_callback(ch, fn, poll=20):
    """Bind cloud lifecycle callbacks to exact durable arguments, including handoffs."""
    if getattr(fn, '_hive_approved', False):
        return fn
    def call(repo, on, *args, **kwargs):
        import inspect
        signature = inspect.signature(fn)
        # Normalize legacy callback signatures before approval. A TypeError after
        # execution begins is ambiguous and must never trigger another attempt.
        candidates = [(args, kwargs), (args, {k: v for k, v in kwargs.items() if k != 'size'}), ((), {})]
        for positional, options in candidates:
            try:
                signature.bind(repo, on, *positional, **options)
                args, kwargs = positional, options
                break
            except TypeError:
                continue
        else:
            raise ValueError('Unsupported cloud callback signature')
        tool = 'cloud_on' if on else 'cloud_off'
        payload = {'repo': str(repo), 'on': bool(on), 'args': list(args), 'options': kwargs}
        aid = confirm(ch, tool, payload,
                      'Start or move Hive to the cloud?' if on else 'Stop and remove Hive\'s cloud machine?',
                      poll, yes_label='Confirm cloud change')
        if not aid:
            return 1
        outcome = {}
        def run(a):
            rc = fn(a['repo'], a['on'], *a['args'], **a['options'])
            outcome['rc'] = rc
            return ActionResult('succeeded' if rc == 0 else 'failed')
        result = execute(aid, run)
        return outcome.get('rc', 1) if result.status in ('succeeded', 'failed') else 1
    call._hive_approved = True
    return call


def confirm(ch, tool, args, text, poll=20, yes_label='Confirm'):
    """Show immutable arguments; only this proposal's fresh button grants approval."""
    from . import telegram
    aid = propose(tool, args, ch)
    if get(aid)['state'] != 'proposed' or get(aid)['expires'] <= time.time():
        ch.send('This request already has a recorded outcome or has expired. No action was repeated.')
        return None
    yes, no = f'act|{aid}|yes', f'act|{aid}|no'
    mid = ch.send(text, html=True, buttons=[[(yes_label, yes), ('Cancel', no)]])
    bind(aid, mid)
    kind, answer = telegram._wait(ch, poll, {yes, no}, current=mid,
                                  expires=get(aid)['expires'])
    if kind != 'tap' or answer not in (yes, no):
        approve(aid, ch, mid, False)
        return None
    return aid if approve(aid, ch, mid, answer == yes) and answer == yes else None


def recover():
    """At listener startup, surface interrupted actions without replaying them."""
    with store.transaction() as con:
        rows = con.execute("SELECT id FROM actions WHERE state='executing'").fetchall()
        for row in rows:
            con.execute("UPDATE actions SET state='unknown' WHERE id=?", (row[0],))
            con.execute('INSERT INTO action_events(action_id,state,at) VALUES(?,?,?)', (row[0], 'unknown', time.time()))
    return len(rows)


def resume(ch, data, message_id, repo):
    """A pending proposal survives restart; execute only its persisted arguments."""
    try:
        _, aid, decision = data.split('|')
    except ValueError:
        return False
    row = get(aid)
    if not row or (row['project'] and row['project'] != str(repo)):
        ch.send('That proposal belongs to another project or is unavailable.')
        return False
    if decision not in ('yes', 'no') or not approve(aid, ch, message_id, decision == 'yes'):
        ch.send('That approval has expired or was already used.')
        return False
    if decision == 'no':
        ch.send('Cancelled.'); return True
    row = get(aid)
    from . import office, google
    if row['tool'] == 'mail_send':
        result = execute(aid, lambda a: office._send_result(repo, a))
    elif row['tool'] == 'add_event':
        import datetime as dt
        def add(a):
            ok, receipt = google.add_event(a['title'], dt.datetime.fromisoformat(a['start']),
                                          dt.datetime.fromisoformat(a['end']), a['where'], a['guests'])
            return ActionResult('succeeded' if ok else 'unknown', receipt)
        result = execute(aid, add)
    elif row['tool'] == 'agent_action':
        from . import runtime_tools
        result = execute(aid, lambda a: runtime_tools.approved_external(repo, a))
    else:
        ch.send('This action cannot be resumed here. Ask me to propose it again.')
        return False
    ch.send('Completed.' if result.status == 'succeeded' else 'The result is unconfirmed; I have not repeated it.')
    return True
