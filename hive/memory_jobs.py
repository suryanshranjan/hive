"""Ordered durable extraction: a reply may be immediate, its memory write cannot vanish."""
from dataclasses import asdict
import json
import threading
import time
from . import policy, store

_WORKER = threading.Lock()


def enqueue(repo, text, history):
    store.connect().execute('INSERT INTO memory_jobs(repo,text,history,context) VALUES(?,?,?,?)',
                            (str(repo), text, history, json.dumps(asdict(policy.context()))))
    return start()


def start():
    thread = threading.Thread(target=drain, daemon=True)
    thread.start()
    return thread


def drain():
    if not _WORKER.acquire(False):
        return
    try:
        from . import assistant, explain, register
        while True:
            with store.transaction() as con:
                job = con.execute("SELECT * FROM memory_jobs WHERE state IN ('queued','running') ORDER BY id LIMIT 1").fetchone()
                if not job or job['retry_at'] > time.time() or job['state'] == 'running':
                    return
                con.execute("UPDATE memory_jobs SET state='running',attempts=attempts+1 WHERE id=?", (job['id'],))
            token = policy.CURRENT.set(policy.RequestContext(**json.loads(job['context'])))
            try:
                related = assistant._related(job['repo'], job['text'])
                got = explain.ask_small(assistant.REMEMBER.format(text=job['text'], history=job['history'],
                    today=time.strftime('%Y-%m-%d (%A)', register.his_time()),
                    known='\n'.join(f'{i}. {f["text"]}' for i, f in enumerate(related, 1)) or '(nothing yet)'))
                if not isinstance(got, dict) or 'note' not in got:
                    raise RuntimeError('Memory extraction unavailable')
                with store.transaction() as con:
                    if not con.execute('SELECT 1 FROM memory_jobs WHERE id=?', (job['id'],)).fetchone():
                        continue  # forgotten while the model was working
                    assistant.keep(job['repo'], got, related)
                    # Drop source copies after extraction; the fact keeps its message reference.
                    con.execute('DELETE FROM memory_jobs WHERE id=?', (job['id'],))
            except Exception:
                store.connect().execute("UPDATE memory_jobs SET state=?,retry_at=? WHERE id=?",
                    ('needs_input' if job['attempts'] >= 2 else 'queued', time.time() + 60, job['id']))
                return
            finally:
                policy.CURRENT.reset(token)
    finally:
        _WORKER.release()


def recover():
    store.connect().execute("UPDATE memory_jobs SET state='queued' WHERE state='running'")
    return start()
