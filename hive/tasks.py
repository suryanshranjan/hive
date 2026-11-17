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
            got['browser'] = browser.fingerprint()
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
    scope = _scope(ch, repo)
    ctx = policy.context()
    update = ctx.update_id or str(getattr(ch, 'last_update', '') or '')
    # A redelivered update must not rerun just because the model made a new plan.
    key = hashlib.sha256(_json([*scope, update, instruction]).encode()).hexdigest() if update else None
    bound = bindings(repo, steps)
    with store.transaction() as con:
        if key:
            old = con.execute('SELECT id FROM tasks WHERE request_key=?', (key,)).fetchone()
            if old:
                return get(old[0], ch, repo)
        tid, now = secrets.token_hex(6), time.time()
        con.execute('INSERT INTO tasks(id,owner_id,chat_id,project,request_key,instruction,steps,bindings,created,updated,mode,metadata) '
                    'VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                    (tid, *scope, key, instruction, _json(steps), _json(bound), now, now, mode, _json(metadata or {})))
    return get(tid, ch, repo)


def claim(tid, ch, repo, resume=False):
    """One executor; no duplicate update or second resume may run it twice."""
    with store.transaction() as con:
        task = get(tid, ch, repo)
        if not task or task['state'] not in (('queued', 'paused') if resume else ('queued',)):
            return None
        if task['mode'] == 'build' and con.execute("SELECT 1 FROM tasks WHERE project=? AND mode='build' "
                                                  "AND state='running' AND id<>?", (task['project'], tid)).fetchone():
            raise tools.Refused('Another build plan is already running for this project.')
        if task['bindings'] != bindings(repo, task['steps']):
            con.execute("UPDATE tasks SET state='blocked',detail=?,updated=? WHERE id=?",
                        ('A connected account changed. Start a new request with the current account.', time.time(), tid))
            return None
        con.execute("UPDATE tasks SET state='running',updated=? WHERE id=?", (time.time(), tid))
    return get(tid, ch, repo)


def begin_step(tid, n):
    with store.transaction() as con:
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
        con.execute('UPDATE tasks SET results=?,next_step=?,active_step=NULL,state=?,detail=?,updated=? WHERE id=?',
                    (_json(task['results']), n + 1 if advance else n, state,
                     '' if ok else str(result.get('why') or result.get('status') or 'No outcome recorded'),
                     time.time(), tid))


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
                state = 'paused' if safe else 'blocked'
                detail = ('An interrupted read can be retried when you resume.' if safe else
                          'An action was interrupted. Check its outcome; Hive will not repeat it.')
                task['results'][str(n)] = {'status': 'unknown', 'why': detail}
            con.execute('UPDATE tasks SET state=?,detail=?,results=?,active_step=NULL,updated=? WHERE id=?',
                        (state, detail, _json(task['results']), time.time(), task['id']))
    return len(rows)


def reconcile(tid, ch, repo):
    """Only the action ledger can establish a previously interrupted write's success."""
    with store.transaction() as con:
        task = get(tid, ch, repo)
        if not task or task['state'] != 'blocked':
            return task
        n = task['next_step']
        rows = con.execute('SELECT a.state,a.receipt FROM actions a JOIN task_actions t ON a.id=t.action_id '
                           'WHERE t.task_id=? AND t.step=?', (tid, n)).fetchall()
        if not rows or any(r['state'] != 'succeeded' for r in rows):
            return task
        task['results'][str(n)] = {'status': 'succeeded', 'receipt': rows[-1]['receipt'],
                                  'recovered': True}
        state = 'succeeded' if task['mode'] != 'adaptive' and n == len(task['steps']) else 'paused'
        con.execute('UPDATE tasks SET results=?,next_step=?,state=?,detail=?,updated=? WHERE id=?',
                    (_json(task['results']), n + 1, state, 'Recovered a confirmed action receipt.', time.time(), tid))
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
    if task['state'] in ('queued', 'paused'):
        line += f"\nSay resume task {task['id']} to continue."
    if detailed:
        for n, step in enumerate(task['steps'], 1):
            state = task['results'].get(str(n), {}).get('status',
                    'running' if task['active_step'] == n else 'pending')
            line += f"\n{n}. {step['tool']}: {state}"
    return line


def listing(ch, repo):
    rows = store.connect().execute('SELECT * FROM tasks WHERE owner_id=? AND chat_id=? AND project=? '
                                   'ORDER BY created DESC,id DESC LIMIT 5', _scope(ch, repo)).fetchall()
    return '\n\n'.join(describe(_decode(row)) for row in rows) or 'No saved tasks for this project.'


def cancel(tid, ch, repo):
    with store.transaction() as con:
        task = get(tid, ch, repo)
        if not task or task['state'] == 'running':
            raise tools.Refused('The task is unavailable or still executing. Stop its current action first.')
        linked = con.execute('SELECT a.id,a.state FROM actions a JOIN task_actions t ON a.id=t.action_id '
                             'WHERE t.task_id=?', (tid,)).fetchall()
        if any(row['state'] == 'executing' for row in linked):
            raise tools.Refused('An action is still executing; its outcome must be checked first.')
        for row in linked:
            if row['state'] in ('proposed', 'approved'):
                con.execute("UPDATE actions SET state='cancelled' WHERE id=?", (row['id'],))
                con.execute('INSERT INTO action_events(action_id,state,at) VALUES(?,?,?)',
                            (row['id'], 'cancelled', time.time()))
        update(tid, state='cancelled', detail='Cancelled by the owner. Earlier effects were not undone.')
