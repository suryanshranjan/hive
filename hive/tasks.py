"""Durable checkpoints for router chains, scoped to the requesting owner/chat/project.

Only an explicit resume retries an interrupted read. An interrupted mutation is
unknown and blocks the chain unless its separate action ledger confirms success.
Recovery runs once when the single listener starts, never alongside an executor.
"""
import hashlib
import json
import os
import secrets
import time
from contextlib import contextmanager
from contextvars import ContextVar

from . import policy, store, tools

SUCCESS = {'done', 'succeeded', 'mail_sent', 'event_added', 'answered', 'mail_answered',
           'cal_answered', 'memory_shown', 'chat'}
# Deliberately narrower than tools.READ: a generic handler may launch other work.
RETRYABLE = {'mail_find', 'calendar_check'}
ACTIVE_STEP = ContextVar('hive_task_step', default=None)
ACTIVE_TASK = ContextVar('hive_task', default=None)


class Controlled(Exception):
    """A persisted owner control stopped execution at a boundary."""


class AwaitingReply(Exception):
    """A durable continuation has released its worker."""


def boundary(tid=None):
    tid = tid or ACTIVE_TASK.get() or os.getenv('HIVE_PLAN_TASK')
    if tid:
        row = store.connect().execute('SELECT control FROM tasks WHERE id=?', (tid,)).fetchone()
        if row and row[0]:
            raise Controlled(row[0])


@contextmanager
def executing(tid, n):
    token = ACTIVE_STEP.set((tid, n))
    try:
        yield
    finally:
        ACTIVE_STEP.reset(token)


def link_action(aid):
    step = ACTIVE_STEP.get()
    if step:
        store.connect().execute('INSERT OR IGNORE INTO task_actions VALUES(?,?,?)', (*step, aid))


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _project(repo):
    return os.path.normcase(os.path.realpath(os.path.abspath(repo)))


def _scope(ch, repo):
    ctx = policy.context()
    if ctx.origin != 'owner':
        raise tools.Refused('Only your own chat can manage saved tasks.')
    project = _project(repo)
    if ctx.project and _project(ctx.project) != project:
        raise tools.Refused('This task belongs to another project.')
    return ctx.owner, str(ch.chat), project


def bindings(repo, steps):
    """Hashes only; never copy credentials into task records."""
    from . import actions, calendar_, mail
    names = {s['tool'] for s in steps}
    got = {}
    if names & {'mail_find', 'mail_read', 'mail_reply', 'mail_send'}:
        got['mail'] = hashlib.sha256(_json([
            mail.config(repo), actions.account_binding('mail_send', repo)]).encode()).hexdigest()
    if names & {'calendar_check', 'calendar_add'}:
        got['calendar'] = hashlib.sha256(_json([
            calendar_.config(repo), actions.account_binding('add_event', repo)]).encode()).hexdigest()
    for name in sorted(names):
        if name.startswith('mcp.'):
            from . import connectors
            got[name] = connectors.fingerprint(name.split('.', 2)[1])
        elif name.startswith('browser_'):
            from . import browser
            got['browser'] = browser.fingerprint(repo)
        elif name in ('business_query','document_get','payment_summary'):
            from . import work_tools
            got[name] = next((tool.identity for tool in work_tools.catalog(repo) if tool.name == name), 'missing')
    return got


def _decode(row):
    if row is None:
        return None
    got = dict(row)
    for key in ('steps', 'results', 'bindings', 'metadata'):
        got[key] = json.loads(got[key])
    return got


def get(tid, ch, repo):
    return _decode(store.connect().execute(
        'SELECT * FROM tasks WHERE id=? AND owner_id=? AND chat_id=? AND project=?',
        (tid, *_scope(ch, repo))).fetchone())


def create(ch, repo, steps, instruction, mode='chain', metadata=None):
    from . import handoff, projects, verification

    scope = _scope(ch, repo)
    ctx = policy.context()
    update = ctx.update_id or str(getattr(ch, 'last_update', '') or '')
    # A redelivered update must not rerun just because the model made a new plan.
    identity = [*scope, update, instruction]
    if mode == 'message':
        identity.append('listener message')
    if mode == 'build' and ACTIVE_STEP.get():
        identity.append(ACTIVE_STEP.get())
    key = hashlib.sha256(_json(identity).encode()).hexdigest() if update else None
    bound = bindings(repo, steps)
    with store.transaction() as con:
        handoff.available(repo)
        if key:
            old = con.execute('SELECT id FROM tasks WHERE request_key=?', (key,)).fetchone()
            if old:
                return get(old[0], ch, repo)
        tid, now = secrets.token_hex(6), time.time()
        exact_provider_request = instruction.partition(':')[0].strip().lower() in ('send email', 'create event')
        criterion = (verification.criteria(instruction) if mode == 'adaptive' or (mode == 'chain' and exact_provider_request)
                     else {'kind': 'owner_request', 'request': instruction})
        if mode == 'chain' and criterion.get('kind') in ('mail_send', 'add_event'):
            writes = [s['tool'] for s in steps if tools.risk(s['tool']) != tools.READ]
            expected = 'calendar_add' if criterion['kind'] == 'add_event' else 'mail_send'
            if writes != [expected]:
                raise tools.Refused('The plan must contain the one change specified in the request.')
        con.execute(
            'INSERT INTO tasks(id,owner_id,chat_id,project,request_key,instruction,steps,bindings,created,updated,mode,metadata,criteria,project_id) '
            'VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (
                tid,
                *scope,
                key,
                instruction,
                _json(steps),
                _json(bound),
                now,
                now,
                mode,
                _json(metadata or {}),
                _json(criterion),
                projects.ensure(repo)['id'],
            ),
        )
    return get(tid, ch, repo)


def claim(tid, ch, repo, resume=False):
    """One executor; no duplicate update or second resume may run it twice."""
    with store.transaction() as con:
        task = get(tid, ch, repo)
        from . import handoff

        handoff.available(repo)
        if not task or task['state'] not in (('queued', 'paused') if resume else ('queued',)):
            return None
        if task['mode'] == 'build' and con.execute("SELECT 1 FROM tasks WHERE project=? AND mode='build' "
                                                  "AND state='running' AND id<>?", (task['project'], tid)).fetchone():
            raise tools.Refused('Another build plan is already running for this project.')
        if task['bindings'] != bindings(repo, task['steps']):
            con.execute("UPDATE tasks SET state='blocked',detail=?,updated=? WHERE id=?",
                        ('A connected account changed. Start a new request with the current account.', time.time(), tid))
            return None
        con.execute("UPDATE tasks SET state='running',control='',updated=? WHERE id=?", (time.time(), tid))
    return get(tid, ch, repo)


def begin_step(tid, n):
    with store.transaction() as con:
        boundary(tid)
        changed = con.execute("UPDATE tasks SET active_step=?,updated=? WHERE id=? AND state='running' "
                              'AND next_step=? AND active_step IS NULL', (n, time.time(), tid, n)).rowcount
        if not changed:
            raise RuntimeError('Task step is already claimed or no longer runnable')


def finish_step(tid, n, result):
    with store.transaction() as con:
        task = _decode(con.execute('SELECT * FROM tasks WHERE id=?', (tid,)).fetchone())
        if not task or task['state'] != 'running' or task['active_step'] != n:
            raise RuntimeError('Task step is no longer running')
        task['results'][str(n)] = result
        ok = result.get('status') in SUCCESS
        adaptive_read = task['mode'] == 'adaptive' and task['steps'][n - 1].get('retry_safe', False)
        advance = ok or (adaptive_read and result.get('status') in ('failed', 'not_found', 'needs_input'))
        state = ('succeeded' if n == len(task['steps']) and task['mode'] != 'adaptive' else 'running') if advance else (
            'paused' if adaptive_read or task['steps'][n - 1]['tool'] in RETRYABLE else 'blocked')
        if (task['mode'] in ('chain', 'adaptive') and not adaptive_read
                and task['steps'][n - 1]['tool'] not in RETRYABLE and result.get('status') == 'unknown'):
            state = 'waiting_verification'
        if (task['mode'] == 'adaptive' and not adaptive_read and ok and
                result.get('verification') not in ('provider_verified','locally_verified')):
            state = 'waiting_verification'
        if con.execute('SELECT 1 FROM child_builds WHERE parent=? AND step=?', (tid, n)).fetchone():
            state, advance = 'waiting_child', False
        if task['control'] and state != 'waiting_verification':
            uncertain = not adaptive_read and (result.get('status') == 'unknown' or
                (ok and result.get('verification') != 'provider_verified' and
                 task['steps'][n-1]['tool'] not in RETRYABLE))
            state = 'waiting_verification' if uncertain else (
                'cancelled' if task['control'] == 'cancel' else 'paused')
        con.execute('UPDATE tasks SET results=?,next_step=?,active_step=NULL,state=?,detail=?,updated=? WHERE id=?',
                    (_json(task['results']), n + 1 if advance else n, state,
                     'Outcome needs readback or owner assessment.' if state == 'waiting_verification' else
                     '' if ok else str(result.get('why') or result.get('status') or 'No outcome recorded'),
                     time.time(), tid))
        if state == 'succeeded' and task['mode'] == 'chain' and task['criteria']:
            from . import verification
            verification.assess(_decode(con.execute('SELECT * FROM tasks WHERE id=?', (tid,)).fetchone()))


def recover(ch, repo):
    """Checkpointed successes survive; uncertain writes never become runnable."""
    scope = _scope(ch, repo)
    with store.transaction() as con:
        rows = con.execute("SELECT * FROM tasks WHERE owner_id=? AND chat_id=? AND project=? AND state='running'",
                           scope).fetchall()
        for row in rows:
            task = _decode(row)
            n = task['active_step']
            state, detail = 'paused', 'Interrupted between steps. Completed steps are saved.'
            if n:
                safe = task['steps'][n - 1]['tool'] in RETRYABLE or (
                    task['mode'] == 'adaptive' and task['steps'][n - 1].get('retry_safe', False))
                state = 'paused' if safe else ('blocked' if task['mode'] == 'build' else 'waiting_verification')
                detail = ('An interrupted read can be retried when you resume.' if safe else
                          'An action was interrupted. Check its outcome; Hive will not repeat it.')
                task['results'][str(n)] = {'status': 'unknown', 'why': detail}
            if task['control'] == 'cancel' and state == 'paused':
                state = 'cancelled'
            if n and con.execute('SELECT 1 FROM child_builds WHERE parent=? AND step=?', (task['id'], n)).fetchone():
                state, detail = 'waiting_child', 'Waiting for the saved child build.'
            con.execute('UPDATE tasks SET state=?,detail=?,results=?,active_step=NULL,updated=? WHERE id=?',
                        (state, detail, _json(task['results']), time.time(), task['id']))
    return len(rows)


def reconcile(tid, ch, repo):
    """Only the action ledger can establish a previously interrupted write's success."""
    with store.transaction() as con:
        task = get(tid, ch, repo)
        if not task or task['state'] not in ('blocked','waiting_verification') or task['control']:
            return task
        n = task['next_step']
        rows = con.execute('SELECT a.state,a.receipt FROM actions a JOIN task_actions t ON a.id=t.action_id '
                           'WHERE t.task_id=? AND t.step=?', (tid, n)).fetchall()
        if not rows or any(r['state'] != 'succeeded' for r in rows):
            return task
        from . import verification
        task['results'][str(n)] = verification.result(tid, n, None, {
            'status': 'succeeded', 'receipt': rows[-1]['receipt'], 'recovered': True})
        state = 'succeeded' if task['mode'] != 'adaptive' and n == len(task['steps']) else 'paused'
        con.execute('UPDATE tasks SET results=?,next_step=?,state=?,detail=?,updated=? WHERE id=?',
                    (_json(task['results']), n + 1, state, 'Recovered a confirmed action receipt.', time.time(), tid))
        if state == 'succeeded' and task['criteria']:
            verification.assess(get(tid, ch, repo))
    return get(tid, ch, repo)


def update(tid, **changes):
    if not set(changes) <= {'metadata', 'state', 'detail'}:
        raise ValueError('Unsupported task update')
    changes['updated'] = time.time()
    if 'metadata' in changes:
        changes['metadata'] = _json(changes['metadata'])
    store.connect().execute('UPDATE tasks SET ' + ','.join(k + '=?' for k in changes) + ' WHERE id=?',
                            (*changes.values(), tid))


def append_step(tid, ch, repo, step):
    """Persist the chosen operation before executing any part of it."""
    with store.transaction() as con:
        task = get(tid, ch, repo)
        if (not task or task['mode'] != 'adaptive' or task['state'] != 'running' or
                task['active_step'] is not None or task['next_step'] != len(task['steps']) + 1):
            raise tools.Refused('The task has an unfinished step.')
        old_bindings = bindings(repo, task['steps'])
        if task['bindings'] != old_bindings:
            raise tools.Refused('A connected account changed.')
        steps = task['steps'] + [step]
        con.execute('UPDATE tasks SET steps=?,bindings=?,updated=? WHERE id=?',
                    (_json(steps), _json(bindings(repo, steps)), time.time(), tid))
    return len(steps)


def outcomes(task):
    return [task['results'][str(n)]['status'] for n in range(1, len(task['steps']) + 1)
            if str(n) in task['results']]


def describe(task, detailed=False):
    completed = task['next_step'] - 1
    line = f"Task {task['id']}: {task['state']}, {completed}/{len(task['steps'])} steps completed."
    instruction = ' '.join(task['instruction'].split())
    line += '\nRequest: ' + instruction[:160] + ('…' if len(instruction) > 160 else '')
    if task['detail']:
        line += '\n' + task['detail']
    if task['state'] == 'waiting_verification':
        line += f"\nSay verify task {task['id']} or resolve task {task['id']} complete|incomplete."
    if task['state'] in ('queued', 'paused'):
        line += f"\nSay resume task {task['id']} to continue."
    if detailed:
        from . import verification
        line += (
            f"\nReported model spend: ${task['reported_spend']:.4f}"
            if task['spend_reports']
            else '\nModel spend: no cost reported.'
        )
        if task['control']:
            line += '\nOwner requested: ' + task['control']
        if not task['criteria'] and task['state'] == 'succeeded':
            line += '\nHistorical completion. Independent verification was not recorded.'
        for item in verification.evidence(task['id']):
            line += f"\n{item['kind']}: {item['reference'][:160]}"
        for n, step in enumerate(task['steps'], 1):
            state = task['results'].get(str(n), {}).get('status',
                    'running' if task['active_step'] == n else 'pending')
            line += f"\n{n}. {step['tool']}: {state}"
    return line[:3950]


def listing(ch, repo):
    rows = store.connect().execute('SELECT * FROM tasks WHERE owner_id=? AND chat_id=? AND project=? '
                                   'ORDER BY created DESC,id DESC LIMIT 5', _scope(ch, repo)).fetchall()
    return '\n\n'.join(describe(_decode(row))[:720] for row in rows) or 'No saved tasks for this project.'


def control(tid, ch, repo, request):
    if request not in ('cancel', 'pause'):
        raise ValueError('Invalid task control')
    with store.transaction() as con:
        task = get(tid, ch, repo)
        if not task or task['state'] in ('succeeded','cancelled','owner_confirmed','owner_reported_incomplete'):
            raise tools.Refused('The task is unavailable or already closed.')
        if task['control'] == 'cancel':
            request = 'cancel'
        for child in con.execute('SELECT child FROM child_builds WHERE parent=?', (tid,)).fetchall():
            saved = get(child[0], ch, repo)
            if saved and saved['state'] not in ('succeeded','cancelled','owner_confirmed','owner_reported_incomplete'):
                control(child[0], ch, repo, request)
        linked = con.execute('SELECT a.id,a.state FROM actions a JOIN task_actions t ON a.id=t.action_id '
                             'WHERE t.task_id=?', (tid,)).fetchall()
        for row in linked:
            if row['state'] in ('proposed', 'approved'):
                con.execute("UPDATE actions SET state='cancelled' WHERE id=?", (row['id'],))
                con.execute('INSERT INTO action_events(action_id,state,at) VALUES(?,?,?)',
                            (row['id'], 'cancelled', time.time()))
        con.execute('UPDATE tasks SET control=? WHERE id=?', (request, tid))
        con.execute('UPDATE task_prompts SET consumed=1 WHERE task_id=?', (tid,))
        con.execute('UPDATE execution_queue SET pending=0 WHERE task_id=?', (tid,))
        state = 'cancelled' if request == 'cancel' else 'paused'
        if task['state'] == 'running' and task['active_step'] is not None:
            state = 'running'
        elif task['state'] == 'waiting_verification' or any(r['state'] in ('executing','unknown') for r in linked):
            state = 'waiting_verification'
        con.execute('UPDATE tasks SET active_step=CASE WHEN ? THEN active_step ELSE NULL END,state=?,detail=?,updated=? WHERE id=?',
                    (state == 'running', state, 'Owner requested ' + request + '. Earlier effects are retained.', time.time(), tid))
    return get(tid, ch, repo)


def cancel(tid, ch, repo):
    return control(tid, ch, repo, 'cancel')
