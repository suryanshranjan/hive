"""Persistent recurring owner instructions, one outstanding task per routine."""
import re
import secrets
import time

from . import policy, store, tasks, tools

CREATE = re.compile(r'^every\s+(\d+)\s+(minutes?|hours?|days?)\s*:\s*(.+)$', re.I | re.S)
CONTROL = re.compile(r'^(pause|enable|run) routine ([0-9a-f]{12})$', re.I)


def create(ch, repo, instruction, interval, now=None):
    tools.allow('routine_set')
    scope = tasks._scope(ch, repo)
    if not 300 <= interval <= 366 * 86400 or not instruction.strip() or len(instruction) > 8000:
        raise ValueError('Use a nonempty instruction and an interval from 5 minutes to 366 days.')
    now = time.time() if now is None else now
    with store.transaction() as con:
        old = con.execute('SELECT id FROM routines WHERE owner_id=? AND chat_id=? AND project=? '
                          'AND instruction=? AND interval_seconds=?', (*scope, instruction, interval)).fetchone()
        if old:
            return old[0]
        rid = secrets.token_hex(6)
        con.execute('INSERT INTO routines(id,owner_id,chat_id,project,instruction,interval_seconds,next_run,created) '
                    'VALUES(?,?,?,?,?,?,?,?)', (rid, *scope, instruction, interval, now + interval, now))
    return rid


def rows(ch, repo):
    return [dict(row) for row in store.connect().execute('SELECT * FROM routines WHERE owner_id=? AND chat_id=? '
                                                       'AND project=? ORDER BY created', tasks._scope(ch, repo))]


def command(ch, repo, text):
    match, control = CREATE.fullmatch(text.strip()), CONTROL.fullmatch(text.strip())
    if not match and not control and text.strip().lower() != 'routines':
        return None
    try:
        tools.allow('routine_set' if match or control else 'status')
        available = rows(ch, repo)
        if match:
            seconds = int(match[1]) * {'minute': 60, 'hour': 3600, 'day': 86400}[match[2].lower().rstrip('s')]
            rid = create(ch, repo, match[3].strip(), seconds)
            ch.send(f'Routine {rid} saved, every {match[1]} {match[2]}. External actions still need your approval.')
        elif control:
            routine = next((r for r in available if r['id'] == control[2].lower()), None)
            if not routine:
                ch.send('That routine is unavailable.'); return 'routine_missing'
            verb = control[1].lower()
            with store.transaction() as con:
                if verb == 'run':
                    con.execute("UPDATE routines SET next_run=?,detail='manual_run' WHERE id=?", (time.time(), routine['id']))
                else:
                    con.execute("UPDATE routines SET enabled=?,next_run=?,detail='' WHERE id=?",
                                (int(verb == 'enable'), time.time() + routine['interval_seconds'], routine['id']))
            ch.send(f"Routine {routine['id']}: {'queued for the listener' if verb == 'run' else verb + 'd'}.")
        else:
            ch.send('\n'.join(f"{r['id']}: {'active' if r['enabled'] else 'paused'}; every {r['interval_seconds']}s; "
                              f"{r['instruction'][:120]}" for r in available[:15]) or 'No routines for this project.')
        return 'routine_set'
    except (ValueError, tools.Refused) as exc:
        ch.send(str(exc)); return 'refused'


def tick(ch, repo, now=None):
    """Coalesce missed intervals. Persist the task and next run in one transaction."""
    from . import agent
    now = time.time() if now is None else now
    scope = tasks._scope(ch, repo)
    launched = []
    # One per listener tick avoids monopolizing the chat when several jobs are due.
    with store.transaction() as con:
        row = con.execute('SELECT * FROM routines WHERE owner_id=? AND chat_id=? AND project=? '
                          "AND (enabled=1 OR detail='manual_run') AND next_run<=? ORDER BY next_run LIMIT 1", (*scope, now)).fetchone()
        if not row:
            return []
        routine = dict(row)
        previous = tasks.get(routine['task_id'], ch, repo) if routine['task_id'] else None
        if previous and previous['state'] not in ('succeeded', 'cancelled', 'queued'):
            con.execute('UPDATE routines SET next_run=?,detail=? WHERE id=?',
                        (now + routine['interval_seconds'], 'Waiting for the previous task: ' + previous['id'], routine['id']))
            return []
        context = policy.RequestContext(owner=scope[0], chat=scope[1], project=str(repo),
            update_id=f"routine:{routine['id']}:{routine['next_run']}")
        token = policy.CURRENT.set(context)
        try:
            task = previous if previous and previous['state'] == 'queued' else tasks.create(ch, repo, [], routine['instruction'], mode='adaptive',
                                metadata={'max_steps': 12, 'max_cost': 2.0, 'spent': 0.0, 'answers': [],
                                          'routine': routine['id']})
        finally:
            policy.CURRENT.reset(token)
        con.execute('UPDATE routines SET task_id=?,next_run=?,detail=? WHERE id=?',
                    (task['id'], now + routine['interval_seconds'], 'Task queued.', routine['id']))
    token = policy.CURRENT.set(context)
    try:
        agent.run(ch, repo, task['id'])
        launched.append(task['id'])
    finally:
        policy.CURRENT.reset(token)
    return launched
