"""Persistent recurring owner instructions, one outstanding task per routine."""
import re
import secrets
import time
import json
import datetime as dt

from . import policy, schedules, store, tasks, tools

CREATE = re.compile(r'^every\s+(\d+)\s+(minutes?|hours?|days?)\s*:\s*(.+)$', re.I | re.S)
CONTROL = re.compile(r'^(pause|enable|run) routine ([0-9a-f]{12})$', re.I)


def is_command(text):
    return bool(
        CREATE.fullmatch(text)
        or CONTROL.fullmatch(text)
        or text.lower() == 'routines'
        or schedules.CIVIL.fullmatch(text)
        or schedules.EVENT.fullmatch(text)
    )


def create(ch, repo, instruction, interval, now=None, definition=None):
    tools.allow('routine_set')
    scope = tasks._scope(ch, repo)
    if (
        (not definition and not 300 <= interval <= 366 * 86400)
        or not instruction.strip()
        or len(instruction) > 8000
    ):
        raise ValueError('Use a nonempty instruction and an interval from 5 minutes to 366 days.')
    now = time.time() if now is None else now
    definition = definition or {}
    normalized = tasks._json(definition)
    with store.transaction() as con:
        from . import handoff

        handoff.available(repo)
        old = con.execute(
            'SELECT id FROM routines WHERE owner_id=? AND chat_id=? AND project=? '
            'AND instruction=? AND interval_seconds=? AND definition=?',
            (*scope, instruction, interval, normalized),
        ).fetchone()
        if old:
            return old[0]
        rid = secrets.token_hex(6)
        from . import projects

        con.execute(
            'INSERT INTO routines(id,owner_id,chat_id,project,instruction,interval_seconds,next_run,created,definition,project_id) '
            'VALUES(?,?,?,?,?,?,?,?,?,?)',
            (
                rid,
                *scope,
                instruction,
                interval,
                schedules.next_run(definition, interval, now),
                now,
                normalized,
                projects.ensure(repo)['id'],
            ),
        )
    return rid


def rows(ch, repo):
    return [dict(row) for row in store.connect().execute('SELECT * FROM routines WHERE owner_id=? AND chat_id=? '
                                                       'AND project=? ORDER BY created', tasks._scope(ch, repo))]


def command(ch, repo, text):
    match, control = CREATE.fullmatch(text.strip()), CONTROL.fullmatch(text.strip())
    if not is_command(text.strip()):
        return None
    try:
        tools.allow('routine_set' if match or control else 'status')
        available = rows(ch, repo)
        parsed = schedules.parse(text, repo)
        if parsed:
            tools.allow('routine_set')
            from . import actions, telegram

            definition, instruction = parsed
            label = schedules.label(definition)
            preview = label
            if definition['kind'] == 'calendar':
                zone = schedules.ZoneInfo(definition['zone'])
                preview += '\n' + '\n'.join(
                    dt.datetime.fromtimestamp(t, zone).isoformat()
                    for t in schedules.occurrences(definition, time.time())
                )
            args = {'definition': definition, 'instruction': instruction}
            aid = actions.confirm(
                ch, 'routine_set', args, telegram.esc(f'Save this routine?\n{preview}\n{instruction}')
            )
            if not aid:
                return 'routine_cancelled'

            def save(a):
                rid = create(ch, repo, a['instruction'], 0, definition=a['definition'])
                return actions.ActionResult('succeeded', rid)

            result = actions.execute(aid, save)
            ch.send(
                f'Routine {result.receipt} saved.' if result.status == 'succeeded' else 'Routine save unconfirmed.'
            )
        elif match:
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
                    con.execute(
                        "UPDATE routines SET enabled=?,next_run=?,detail='' WHERE id=?",
                        (
                            int(verb == 'enable'),
                            schedules.next_run(
                                json.loads(routine['definition']), routine['interval_seconds'], time.time()
                            ),
                            routine['id'],
                        ),
                    )
            ch.send(f"Routine {routine['id']}: {'queued for the listener' if verb == 'run' else verb + 'd'}.")
        else:
            ch.send(
                '\n'.join(
                    f"{r['id']}: {'active' if r['enabled'] else 'paused'}; "
                    f"{schedules.label(json.loads(r['definition'])) if r['definition']!='{}' else 'every '+str(r['interval_seconds'])+'s'}; "
                    f"{r['instruction'][:120]}"
                    for r in available[:15]
                )
                or 'No routines for this project.'
            )
        return 'routine_set'
    except (ValueError, tools.Refused) as exc:
        ch.send(str(exc)); return 'refused'


def tick(ch, repo, now=None, enqueue=False):
    """Coalesce missed intervals. Persist the task and next run in one transaction."""
    from . import agent
    now = time.time() if now is None else now
    scope = tasks._scope(ch, repo)
    launched = []
    # One per listener tick avoids monopolizing the chat when several jobs are due.
    with store.transaction() as con:
        row = con.execute(
            'SELECT r.* FROM routines r LEFT JOIN tasks t ON t.id=r.task_id '
            'WHERE r.owner_id=? AND r.chat_id=? AND r.project=? '
            "AND (r.enabled=1 OR r.detail='manual_run') AND r.next_run<=? "
            "AND (t.id IS NULL OR t.state IN ('succeeded','cancelled','owner_confirmed','owner_reported_incomplete','queued')) "
            "AND (?=0 OR t.id IS NULL OR t.state<>'queued' OR NOT EXISTS("
            "SELECT 1 FROM execution_queue q WHERE q.task_id=t.id AND (q.pending=1 OR q.worker IS NOT NULL))) "
            "ORDER BY r.next_run,r.created LIMIT 1",
            (*scope, now, int(enqueue)),
        ).fetchone()
        if not row:
            return []
        routine = dict(row)
        previous = tasks.get(routine['task_id'], ch, repo) if routine['task_id'] else None
        definition = json.loads(routine['definition'])
        event = con.execute(
            'SELECT e.* FROM event_runs o JOIN trigger_events e USING(source,event_id) '
            'WHERE e.project=? AND o.routine_id=? AND o.task_id IS NULL ORDER BY e.received,o.rowid LIMIT 1',
            (scope[2], routine['id']),
        ).fetchone()
        if definition.get('kind') == 'event' and not event and routine['detail'] != 'manual_run':
            con.execute('UPDATE routines SET next_run=? WHERE id=?', (schedules.NEVER, routine['id']))
            return []
        occurrence = event['event_id'] if event else routine['next_run']
        context = policy.RequestContext(
            owner=scope[0], chat=scope[1], project=str(repo), update_id=f"routine:{routine['id']}:{occurrence}"
        )
        token = policy.CURRENT.set(context)
        try:
            task = (
                previous
                if previous and previous['state'] == 'queued'
                else tasks.create(
                    ch,
                    repo,
                    [],
                    routine['instruction'],
                    mode='adaptive',
                    metadata={
                        'max_steps': 12,
                        'max_cost': 2.0,
                        'spent': 0.0,
                        'answers': [],
                        'routine': routine['id'],
                        'trigger_event': json.loads(event['data']) if event else None,
                    },
                )
            )
        finally:
            policy.CURRENT.reset(token)
        if event and not (previous and previous['state'] == 'queued'):
            con.execute(
                'UPDATE event_runs SET task_id=? WHERE routine_id=? AND source=? AND event_id=?',
                (task['id'], routine['id'], event['source'], event['event_id']),
            )
        pending = con.execute(
            'SELECT 1 FROM event_runs WHERE routine_id=? AND task_id IS NULL', (routine['id'],)
        ).fetchone()
        following = now if pending else schedules.next_run(definition, routine['interval_seconds'], now)
        con.execute(
            'UPDATE routines SET task_id=?,next_run=?,detail=? WHERE id=?',
            (task['id'], following, 'Task queued.', routine['id']),
        )
        if enqueue:
            from . import dispatcher
            dispatcher.enqueue(task, context)
            return [task['id']]
    token = policy.CURRENT.set(context)
    try:
        agent.run(ch, repo, task['id'])
        launched.append(task['id'])
    finally:
        policy.CURRENT.reset(token)
    return launched
