"""Completion criteria and evidence. Only local adapters can issue evidence."""
import json
import time

from . import actions, policy, store, tools


def criteria(instruction):
    label, sep, value = instruction.partition(':')
    label = label.strip().lower()
    if sep and value.strip():
        if label == 'output':
            return {'kind': 'output', 'request': value.strip()}
        tool = {'send email': 'mail_send', 'create event': 'add_event'}.get(label)
        if tool:
            try:
                args = json.loads(value)
            except ValueError:
                raise tools.Refused('Supply the complete requested arguments as a JSON object.') from None
            tools.validate(tool, args)
            if set(args) != set(tools.spec(tool).required):
                raise tools.Refused('Supply exactly the documented fields for this operation.')
            return {'kind': tool, 'args': args}
    return {'kind': 'owner_request', 'request': instruction}


def record(tid, step, kind, reference):
    store.connect().execute('INSERT OR IGNORE INTO task_evidence VALUES(?,?,?,?,?)',
                            (tid, step, kind, reference, time.time()))


def evidence(tid):
    return [dict(row) for row in store.connect().execute(
        'SELECT step,kind,reference FROM task_evidence WHERE task_id=? ORDER BY at', (tid,))]


def linked(tid, n=None):
    sql = ('SELECT a.*,t.step FROM actions a JOIN task_actions t ON t.action_id=a.id '
           'WHERE t.task_id=?')
    return [dict(r) for r in store.connect().execute(sql + (' AND t.step=?' if n is not None else ''),
                                                     (tid, n) if n is not None else (tid,))]


def guard(task, tool, args):
    criterion = json.loads(task['criteria']) if task['criteria'] else {}
    if tool.risk == tools.READ:
        return
    if criterion.get('kind') == 'output':
        raise tools.Refused('This request authorizes an output in chat only.')
    if criterion.get('kind') in ('mail_send', 'add_event') and (
            {'calendar_add': 'add_event'}.get(tool.name, tool.name) != criterion['kind'] or
            args != criterion['args']):
        raise tools.Refused('The proposed action differs from the saved success criteria.')


def result(tid, step, tool, raw):
    """Keep untrusted observations in data. Rebuild all evidence fields locally."""
    raw = dict(raw)
    for key in ('verification', 'evidence', 'execution'):
        raw.pop(key, None)
    rows = linked(tid, step)
    raw['execution'] = raw['status']
    for row in rows:
        if row['state'] != 'succeeded':
            continue
        if row['tool'] == 'mail_send' and row['receipt'] == 'smtp-submitted':
            record(tid, step, 'smtp_submission', row['id'])
        elif row['tool'] in ('mail_send', 'add_event'):
            from . import google
            sent = google._outbox().execute("SELECT result FROM outbox WHERE action_id=? AND state='sent'",
                                            (row['id'],)).fetchone()
            if sent and sent[0]:
                record(tid, step, 'provider_readback', row['id'])
        else:
            record(tid, step, 'execution_receipt', row['id'])
            approved = json.loads(row['args'])
            if row['tool'] == 'agent_action' and approved['tool'] in ('memory_add','memory_update','memory_forget'):
                from . import memory
                try:
                    fid = json.loads(row['receipt'])['data']['id']
                    fact = store.connect().execute('SELECT text,deleted_at FROM facts WHERE id=? AND project=? AND owner_id=?',
                        (fid,memory.project_key(row['project']),row['owner_id'])).fetchone()
                    if fact and ((approved['tool'] == 'memory_forget' and fact['deleted_at'] is not None) or
                                 (approved['tool'] != 'memory_forget' and fact['deleted_at'] is None and
                                  fact['text'] == approved['args']['text'])):
                        record(tid,step,'local_readback',row['id'])
                except (TypeError, KeyError, ValueError):
                    pass
    refs = [e for e in evidence(tid) if e['step'] == step]
    raw.update(evidence=refs, verification='provider_verified' if any(
        e['kind'] == 'provider_readback' for e in refs) else
        'locally_verified' if any(e['kind'] == 'local_readback' for e in refs) else 'unverified')
    return raw


def assess(task, proposal='', artifact=False):
    from . import tasks
    tid = task['id']
    criterion = json.loads(task['criteria'] or '{}')
    rows = linked(tid)
    if criterion.get('kind') == 'output' and artifact and proposal.strip() and not rows:
        record(tid, 0, 'chat_artifact', proposal)
        tasks.update(tid, state='succeeded', detail=proposal)
        return
    refs = {e['reference'] for e in evidence(tid) if e['kind'] == 'provider_readback'}
    if (len(rows) == 1 and rows[0]['id'] in refs and criterion.get('kind') == rows[0]['tool']
            and actions.account_binding(rows[0]['tool'],task['project']) == rows[0]['account_binding']
            and criterion.get('args') == json.loads(rows[0]['args'])):
        tasks.update(tid, state='succeeded', detail='Provider readback matches the saved request.')
        return
    tasks.update(tid, state='waiting_verification',
                 detail='The full requested outcome still needs verification. '
                 + (f'Model proposal (unverified): {proposal}' if proposal else ''))


def retry(ch, repo, tid):
    from . import google, tasks, mail
    task = tasks.get(tid, ch, repo)
    if not task or task['state'] != 'waiting_verification':
        raise tools.Refused('That task is not waiting for verification.')
    for row in linked(tid):
        if (row['tool'] not in ('mail_send', 'add_event') or
                row['state'] not in ('succeeded', 'unknown') or
                actions.account_binding(row['tool'], repo) != row['account_binding'] or
                (row['tool'] == 'mail_send' and mail.config(repo).get('kind') != 'google')):
            continue
        args = json.loads(row['args'])
        try:
            receipt = google.readback(row['id'], row['tool'], args)
        except Exception:
            receipt = ''
        with store.transaction():
            if tasks.get(tid, ch, repo)['state'] != 'waiting_verification':
                return
            if receipt and actions.account_binding(row['tool'], repo) == row['account_binding']:
                record(tid, row['step'], 'provider_readback', row['id'])
            else:
                store.connect().execute("DELETE FROM task_evidence WHERE task_id=? AND kind='provider_readback' AND reference=?",
                                        (tid, row['id']))
    with store.transaction():
        task = tasks.get(tid, ch, repo)
        if task['state'] == 'waiting_verification':
            assess(task)


def resolve(ch, repo, tid, assessment):
    from . import tasks
    with store.transaction():
        task = tasks.get(tid, ch, repo)
        if not task or task['state'] != 'waiting_verification':
            raise tools.Refused('That task is not waiting for an owner assessment.')
        if assessment not in ('complete', 'incomplete'):
            raise tools.Refused(f'Reply resolve task {tid} complete or resolve task {tid} incomplete.')
        record(tid, 0, 'owner_attestation', f'{policy.context().owner}: {assessment}')
        tasks.update(tid, state='owner_confirmed' if assessment == 'complete' else 'owner_reported_incomplete',
                     detail='Owner assessment: ' + assessment)
