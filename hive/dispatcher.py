"""Single Telegram reader, durable reply routing and two project-serialized workers."""
import copy
import json
import os
import re
import secrets
import threading
import time
from contextlib import contextmanager

from . import actions, agent, policy, store, tasks, tools, verification


@contextmanager
def reader_lock(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'a+b') as lock:
        lock.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            yield False
        else:
            yield True


def prompt(ch, tid, mid, kind, choices, expires):
    if mid is None:
        raise tools.Refused('Telegram did not return a prompt message ID.')
    store.connect().execute(
        'INSERT OR IGNORE INTO task_prompts(owner_id,chat_id,message_id,task_id,kind,choices,expires) '
        'VALUES(?,?,?,?,?,?,?)', (policy.context().owner, str(ch.chat), mid, tid, kind,
                                  json.dumps(list(choices)), expires))


def enqueue(task, context, operation='run'):
    payload = json.dumps(dict(update=context.update_id, source=context.source_ref, operation=operation,
                              project=context.project or task['project']))
    lane = 'chat:' + task['chat_id'] if task['mode'] == 'conversation' else task['project']
    store.connect().execute(
        'INSERT INTO execution_queue(task_id,project,context) VALUES(?,?,?) '
        'ON CONFLICT(task_id) DO UPDATE SET pending=1,context=excluded.context',
        (task['id'], lane, payload))


def is_brokered(ch):
    if getattr(ch, 'brokered', False):
        return True
    if getattr(ch, 'keep', False) and not ch.listener:
        from . import telegram
        pid = store.get('telegram_reader:' + str(ch.chat))
        if pid and telegram._alive(pid):
            return True
        if getattr(ch, 'live_transport', False):
            raise tools.Refused('Start hive listen to receive Telegram replies on this host.')
    return False


def receive(ch, mid, choices, timeout, expires=None):
    """Legacy waits read only their own persisted prompt, including in build subprocesses."""
    task = tasks.ACTIVE_TASK.get() or getattr(ch, 'broker_task', None)
    if not task:
        task = ch.broker_task = 'legacy-' + secrets.token_hex(12)
    if mid is None:
        time.sleep(min(timeout, 0.1))
        return []
    scope = (policy.context().owner, str(ch.chat), mid, task)
    prompt(ch, task, mid, 'legacy', choices, expires or time.time() + 86400)
    deadline = time.monotonic() + max(0.1, timeout)
    while True:
        if getattr(ch, 'worker_stop', None) and ch.worker_stop.is_set():
            raise tools.Refused('The listener is shutting down.')
        tasks.boundary()
        with store.transaction() as con:
            row = con.execute('SELECT reply,expires,consumed FROM task_prompts WHERE owner_id=? '
                              'AND chat_id=? AND message_id=? AND task_id=?', scope).fetchone()
            if row and row['reply'] and not row['consumed']:
                con.execute('UPDATE task_prompts SET consumed=1,reply=NULL WHERE owner_id=? AND chat_id=? '
                            'AND message_id=? AND task_id=?', scope)
                text, data, message_id, source_id = json.loads(row['reply'])
                ch.last_id = source_id
                return [(text, data, message_id)]
            if row and row['expires'] <= time.time():
                raise tools.Refused('The prompt expired. Request a fresh prompt.')
        if time.monotonic() >= deadline:
            return []
        time.sleep(0.05)


class Dispatcher:
    def __init__(self, ch, repo, handler):
        self.ch, self.repo, self.handler = ch, repo, handler
        self.stop = threading.Event()
        self.moved = threading.Event()
        self.workers = []

    def start(self):
        with store.transaction() as con:
            store.put('telegram_reader:' + str(self.ch.chat), os.getpid())
            # The listener holds the process lock before reconciliation. Only abandoned claims exist.
            con.execute("UPDATE execution_queue SET pending=CASE WHEN worker IS NOT NULL AND task_id IN "
                        "(SELECT id FROM tasks WHERE state='queued') THEN 1 ELSE pending END,"
                        'worker=NULL,started=NULL WHERE task_id IN '
                        '(SELECT id FROM tasks WHERE owner_id=? AND chat_id=?)',
                        (policy.context().owner, str(self.ch.chat)))
        for _ in range(2):
            worker = threading.Thread(target=self._worker, daemon=True)
            self.workers.append(worker)
            worker.start()

    def close(self):
        self.stop.set()
        for worker in self.workers:
            worker.join()
        store.put('telegram_reader:' + str(self.ch.chat), 0)

    def _route(self, row, text, button, source_id, ctx):
        con = store.connect()
        scope = (row['owner_id'], row['chat_id'], row['message_id'])
        if row['consumed'] or row['expires'] <= time.time() or row['reply']:
            return 'That prompt has expired or was already answered.'
        if button and button not in json.loads(row['choices']):
            return 'That button does not belong to this prompt.'
        tid = row['task_id']
        task = tasks.get(tid, self.ch, self.repo)
        if row['kind'] == 'legacy':
            reply = json.dumps([text, button, row['message_id'], source_id])
            con.execute('UPDATE task_prompts SET reply=? WHERE owner_id=? AND chat_id=? AND message_id=?',
                        (reply, *scope))
            return ''
        if not task or task['control']:
            return 'This task is no longer waiting for that reply.'
        if row['kind'] == 'approval':
            if not button or task['state'] != 'waiting_approval':
                return 'Use the buttons on the approval message.'
            _, aid, choice = button.split('|')
            if not actions.approve(aid, self.ch, row['message_id'], choice == 'yes'):
                return 'That approval has expired or was already used.'
            state = 'queued' if choice == 'yes' else 'cancelled'
        elif row['kind'] == 'answer' and text and task['state'] == 'paused':
            meta = task['metadata']
            meta['answers'].append({'question': meta.pop('question'), 'answer': text})
            tasks.update(tid, metadata=meta)
            state = 'queued'
        else:
            return 'This task is no longer waiting for that reply.'
        con.execute('UPDATE task_prompts SET reply=?,consumed=1 WHERE owner_id=? AND chat_id=? AND message_id=?',
                    (json.dumps(button or text), *scope))
        con.execute("UPDATE tasks SET state=?,active_step=NULL,detail='' WHERE id=?", (state, tid))
        if state == 'queued':
            enqueue(task, ctx)
        return f'Task {tid} {state}.'

    def dispatch(self, text, button, mid):
        from . import assistant, telegram
        uid = str(self.ch.last_update)
        ctx = policy.RequestContext(chat=str(self.ch.chat), project=str(self.repo), update_id=uid,
                                    source_ref=str(getattr(self.ch, 'last_archive', '')))
        token = policy.CURRENT.set(ctx)
        try:
            with store.transaction() as con:
                if uid and not con.execute('INSERT OR IGNORE INTO dispatched_updates VALUES(?,?)',
                                           (ctx.chat, uid)).rowcount:
                    return
                msg = self._dispatch(text, button, mid, ctx, assistant, telegram)
            if msg:
                self.ch.send(msg)
        except tools.Refused as exc:
            self.ch.send(str(exc))
        finally:
            policy.CURRENT.reset(token)

    def _dispatch(self, text, button, mid, ctx, assistant, telegram):
        con = store.connect()
        words = (text or '').strip()
        scope = (ctx.owner, ctx.chat)
        if words and telegram.is_status(words):
            build = assistant._building()
            if not build:
                latest = assistant.latest_build(self.repo)
                build = f"The latest build is on branch hive/{latest['name']}." if latest else ''
            return '\n'.join(filter(None, (build, tasks.listing(self.ch, self.repo))))
        if words.lower() == 'tasks':
            return tasks.listing(self.ch, self.repo)
        if words.lower().strip(' !.?') in assistant.GREETINGS:
            return 'I’m here. Send work with agent: or talk with chat: while it runs.'
        control = re.fullmatch(r'(?:(pause|cancel|verify|resolve|resume) )?task ([0-9a-f]{12})(?: (complete|incomplete))?', words, re.I)
        if control:
            verb, tid, assessment = (part.lower() if part else '' for part in control.groups())
            task = tasks.get(tid, self.ch, self.repo)
            if not task:
                return 'That task is unavailable in this chat and project.'
            if verb in ('pause','cancel'):
                tasks.control(tid, self.ch, self.repo, verb)
            elif verb == 'resolve':
                verification.resolve(self.ch, self.repo, tid, assessment)
            elif verb == 'verify' and task['state'] == 'waiting_verification':
                enqueue(task, ctx, 'verify')
                return f'Read-only verification queued for {tid}.'
            elif verb == 'resume' and task['state'] in ('queued','paused'):
                con.execute("UPDATE tasks SET state='queued',control='' WHERE id=?", (tid,))
                con.execute("UPDATE task_prompts SET consumed=1 WHERE task_id=? AND kind='answer'", (tid,))
                enqueue(task, ctx)
                return f'Task {tid} queued.'
            return tasks.describe(tasks.get(tid, self.ch, self.repo), detailed=True)
        answer = re.fullmatch(r'answer task ([0-9a-f]{12}):\s*(.+)', words, re.I | re.S)
        if answer:
            row = con.execute("SELECT * FROM task_prompts WHERE owner_id=? AND chat_id=? AND task_id=? "
                              "AND kind='answer' AND consumed=0 ORDER BY message_id DESC LIMIT 1",
                              (*scope, answer[1].lower())).fetchone()
            if not row or (mid and row['message_id'] != mid):
                return 'That task is not waiting for this answer.'
            return self._route(row, answer[2], None, getattr(self.ch,'last_id',None), ctx)
        if mid:
            row = con.execute('SELECT * FROM task_prompts WHERE owner_id=? AND chat_id=? AND message_id=?',
                              (*scope, mid)).fetchone()
            if row:
                return self._route(row, text, button, getattr(self.ch, 'last_id', None), ctx)
            if not (button or '').startswith(('act|','pls|')):
                # Telegram can return the reply before sendMessage returns its message ID.
                con.execute('INSERT OR IGNORE INTO telegram_replies VALUES(?,?,?,?,?,?,?)',
                            (*scope, mid, ctx.update_id, text, button, time.time()))
                return ''
        if button and not button.startswith(('act|','pls|')):
            return 'That button is unavailable.'
        if button and button.startswith('act|'):
            # A newly sent adaptive approval can race prompt registration as well.
            parts = button.split('|')
            if len(parts) != 3:
                return 'Invalid approval.'
            if con.execute("SELECT 1 FROM task_actions l JOIN tasks t ON t.id=l.task_id "
                           "JOIN execution_queue q ON q.task_id=t.id WHERE l.action_id=? AND "
                           "(t.mode='adaptive' OR q.worker IS NOT NULL)",
                           (parts[1],)).fetchone():
                con.execute('INSERT OR IGNORE INTO telegram_replies VALUES(?,?,?,?,?,?,?)',
                            (*scope, mid, ctx.update_id, None, button, time.time()))
                return ''
        from . import routines
        routine_command = routines.is_command(words)
        if words.lower().startswith('chat:'):
            task = tasks.create(self.ch, self.repo, [], words, mode='conversation',
                                metadata={'history': self.ch.recent(max_chars=8000)})
        elif words.lower().startswith('agent:') or (not routine_command and assistant.adaptive_request(words)):
            instruction = words.partition(':')[2].strip() if words.lower().startswith('agent:') else words
            task = agent.accept(self.ch, self.repo, instruction)
        else:
            task = tasks.create(self.ch, self.repo, [{'tool': 'owner_message', 'args': {}}],
                                words or button, mode='message', metadata={
                                    'button': button, 'mid': mid, 'source_id': getattr(self.ch, 'last_id', None),
                                    'voice': getattr(self.ch, 'heard_voice', False)})
        if task['state'] == 'queued':
            enqueue(task, ctx)
        return f"Task {task['id']} {task['state']}."

    def _next(self, worker):
        with store.transaction() as con:
            row = con.execute('SELECT q.* FROM execution_queue q JOIN tasks t ON t.id=q.task_id '
                              'WHERE t.owner_id=? AND t.chat_id=? AND q.pending=1 AND q.worker IS NULL '
                              'AND NOT EXISTS(SELECT 1 FROM execution_queue busy WHERE busy.project=q.project '
                              'AND busy.worker IS NOT NULL) ORDER BY t.created LIMIT 1',
                              (policy.context().owner, str(self.ch.chat))).fetchone()
            if row:
                con.execute('UPDATE execution_queue SET pending=0,worker=?,started=? WHERE task_id=?',
                            (worker, time.time(), row['task_id']))
            return row

    def _worker(self):
        worker = secrets.token_hex(12)
        while not self.stop.is_set():
            self.drain_replies()
            row = self._next(worker)
            if not row:
                self.stop.wait(0.1)
                continue
            tid = row['task_id']
            params = json.loads(row['context'])
            repo = params['project']
            ch = copy.copy(self.ch)
            ch.brokered, ch.last_update, ch.last_archive = True, params['update'], params['source']
            ch.last_prompt = None
            ch.worker_stop = self.stop
            ctx = policy.RequestContext(chat=str(ch.chat), project=repo, update_id=ch.last_update, source_ref=ch.last_archive)
            auth = policy.CURRENT.set(ctx)
            active = tasks.ACTIVE_TASK.set(tid)
            try:
                task = tasks.get(tid, ch, repo)
                if params['operation'] == 'verify':
                    verification.retry(ch, repo, tid)
                    ch.send(tasks.describe(tasks.get(tid, ch, repo), True))
                elif task['state'] == 'queued' and not task['control']:
                    self._run(ch, repo, task)
            except tasks.Controlled:
                with store.transaction():
                    current = tasks.get(tid, ch, repo)
                    if current['state'] == 'running' and current['active_step']:
                        uncertain = any(a['state'] in ('unknown','executing','succeeded')
                                        for a in verification.linked(tid, current['active_step']))
                        tasks.finish_step(tid, current['active_step'], {'status': 'unknown' if uncertain else 'cancelled'})
            except Exception as exc:
                # The handler could have issued a write before raising.
                with store.transaction():
                    current = tasks.get(tid, ch, repo)
                    if current['state'] == 'running':
                        tasks.update(tid, state='waiting_verification', detail='Execution interrupted. Inspect the outcome.')
                print(f'Task {tid} stopped ({type(exc).__name__}).', flush=True)
                ch.send(f'Task {tid} stopped. Say task {tid} for its recorded outcome.')
            finally:
                store.connect().execute('UPDATE execution_queue SET worker=NULL,started=NULL WHERE task_id=? AND worker=?',
                                        (tid, worker))
                tasks.ACTIVE_TASK.reset(active)
                policy.CURRENT.reset(auth)

    def _run(self, ch, repo, task):
        tid = task['id']
        if task['mode'] == 'conversation':
            from . import explain
            if not tasks.claim(tid, ch, repo):
                return
            tasks.boundary(tid)
            reply = explain.ask_json('Reply conversationally in JSON {"reply":"..."}. You can only produce text. '
                'Use the recorded task status for questions about work.\n' + tasks.listing(ch, repo) + '\n' +
                explain.untrusted(task['metadata']['history'], 'conversation') + '\nOwner: ' + task['instruction'][5:])
            tasks.boundary(tid)
            message = reply.get('reply') if isinstance(reply, dict) else None
            ch.send(message[:3800] if isinstance(message, str) and message.strip() else 'I could not generate a chat reply.')
            tasks.update(tid, state='handled', detail='Chat reply returned.')
        elif task['mode'] == 'adaptive':
            agent.run(ch, repo, tid)
        elif task['mode'] == 'message':
            if not tasks.claim(tid, ch, repo):
                return
            tasks.begin_step(tid, 1)
            meta = task['metadata']
            ch.last_id, ch.heard_voice = meta['source_id'], meta['voice']
            with tasks.executing(tid, 1):
                if (meta['button'] or '').startswith('act|'):
                    actions.resume(ch, meta['button'], meta['mid'], repo)
                elif meta['button']:
                    from . import pulse
                    pulse.tap(ch, meta['button'], repo)
                elif self.handler(ch, repo, task['instruction']) == 'moved':
                    self.moved.set()
            with store.transaction():
                tasks.finish_step(tid, 1, {'status': 'answered'})
                current = tasks.get(tid, ch, repo)
                if current['state'] == 'succeeded':
                    if verification.linked(tid):
                        verification.result(tid, 1, None, {'status': 'answered'})
                        verification.assess(current)
                    else:
                        tasks.update(tid, state='handled', detail='Legacy handler returned to chat.')
        else:
            from . import router
            router.resume_chain(ch, repo, tid, handle=lambda c, r, t, p: self.handler(c, r, t))

    def drain_replies(self):
        with store.transaction() as con:
            scope = (policy.context().owner, str(self.ch.chat))
            rows = con.execute('SELECT p.*,r.text,r.button,r.update_id FROM telegram_replies r '
                               'JOIN task_prompts p USING(owner_id,chat_id,message_id) '
                               'WHERE p.owner_id=? AND p.chat_id=? ORDER BY r.created LIMIT 20', scope).fetchall()
            for row in rows:
                ctx = policy.RequestContext(owner=scope[0], chat=scope[1], project=str(self.repo), update_id=row['update_id'])
                self._route(row, row['text'], row['button'], None, ctx)
                con.execute('DELETE FROM telegram_replies WHERE chat_id=? AND update_id=?', (scope[1], row['update_id']))
            con.execute("UPDATE tasks SET state='paused',active_step=NULL,detail='Approval expired. Resume for a fresh approval.' "
                        "WHERE state='waiting_approval' AND id IN (SELECT task_id FROM task_prompts WHERE owner_id=? "
                        "AND chat_id=? AND kind='approval' AND expires<=? AND consumed=0)", (*scope, time.time()))
            con.execute('UPDATE task_prompts SET consumed=1 WHERE owner_id=? AND chat_id=? AND expires<=?', (*scope, time.time()))
            con.execute('DELETE FROM telegram_replies WHERE created<?', (time.time() - 86400,))
