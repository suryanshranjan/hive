"""Hive's memory, structured (memory 2.0, P1 of docs/jarvis_plan.md): one SQLite file, ~/.hive/hive.db, beside the
rules folder.

What it holds, every row with owner_id (one owner today; the column keeps a second one possible later):
  facts      everything Hive knows about him and his business, one sentence each: kind (note, rule, preference,
             deadline, person, number), where it came from (chat, document, email, build, interview...), trust
             (owner: he said it; outside: read from mail or a document), when, until when it holds, what it replaced,
             and whether he asked Hive to forget it. Searched with SQLite's full-text index (FTS5).
  people     who is who in his world: name, other names, relation, company, how to reach them.
  profile    how to address him, his time zone, how technical he is, quiet hours (one row per key).
  messages   the whole conversation, not only the last 16 messages, so an old thread can be found again.

SQLite is authoritative. Legacy JSON is imported once; memory.py writes derived compatibility exports.
Action proposals, extraction jobs, notification claims and received Telegram updates share this durable store.

Plain text on disk, owner-only, as the owner chose (Nov 15): search works, and keys and passwords are never put here
(they live encrypted in hive/vault.py)."""
import json, os, re, sqlite3, threading, time
from contextlib import contextmanager

OWNER = 'owner'
_LOCK = threading.RLock()
_CONN = {}
_TX = threading.local()


class _Connection(sqlite3.Connection):
    """Single statements also respect a transaction held by another thread.

    Pulse and extraction share this connection with the listener. Without the
    same lock here, an unrelated write could join somebody else's savepoint
    and disappear when that transaction rolls back.
    """
    def execute(self, *args, **kwargs):
        with _LOCK:
            return super().execute(*args, **kwargs)

    def executemany(self, *args, **kwargs):
        with _LOCK:
            return super().executemany(*args, **kwargs)

    def executescript(self, *args, **kwargs):
        with _LOCK:
            return super().executescript(*args, **kwargs)


MIGRATIONS = [
    # 1: the first shape
    """
    CREATE TABLE IF NOT EXISTS facts (
        id INTEGER PRIMARY KEY, owner_id TEXT NOT NULL, project TEXT NOT NULL DEFAULT '', kind TEXT NOT NULL,
        text TEXT NOT NULL, norm TEXT NOT NULL, person_id INTEGER, source TEXT NOT NULL DEFAULT 'chat',
        source_ref TEXT NOT NULL DEFAULT '', trust TEXT NOT NULL DEFAULT 'owner', created REAL NOT NULL,
        valid_until REAL, superseded_by INTEGER, deleted_at REAL, extra TEXT NOT NULL DEFAULT '{}');
    CREATE UNIQUE INDEX IF NOT EXISTS facts_once ON facts(owner_id, project, kind, norm);
    CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts USING fts5(text, content='facts', content_rowid='id',
        tokenize='unicode61 remove_diacritics 2');
    CREATE TRIGGER IF NOT EXISTS facts_ai AFTER INSERT ON facts BEGIN
        INSERT INTO facts_fts(rowid, text) VALUES (new.id, new.text); END;
    CREATE TRIGGER IF NOT EXISTS facts_ad AFTER DELETE ON facts BEGIN
        INSERT INTO facts_fts(facts_fts, rowid, text) VALUES ('delete', old.id, old.text); END;
    CREATE TRIGGER IF NOT EXISTS facts_au AFTER UPDATE OF text ON facts BEGIN
        INSERT INTO facts_fts(facts_fts, rowid, text) VALUES ('delete', old.id, old.text);
        INSERT INTO facts_fts(rowid, text) VALUES (new.id, new.text); END;
    CREATE TABLE IF NOT EXISTS people (
        id INTEGER PRIMARY KEY, owner_id TEXT NOT NULL, name TEXT NOT NULL, norm TEXT NOT NULL,
        aliases TEXT NOT NULL DEFAULT '[]', relation TEXT NOT NULL DEFAULT '', org TEXT NOT NULL DEFAULT '',
        contact TEXT NOT NULL DEFAULT '', created REAL NOT NULL, last_seen REAL NOT NULL, deleted_at REAL);
    CREATE UNIQUE INDEX IF NOT EXISTS people_once ON people(owner_id, norm);
    CREATE TABLE IF NOT EXISTS profile (
        owner_id TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL, updated REAL NOT NULL,
        PRIMARY KEY (owner_id, key));
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY, owner_id TEXT NOT NULL, channel TEXT NOT NULL, who TEXT NOT NULL, text TEXT NOT NULL,
        at REAL NOT NULL);
    CREATE INDEX IF NOT EXISTS messages_at ON messages(owner_id, at);
    CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(text, content='messages', content_rowid='id',
        tokenize='unicode61 remove_diacritics 2');
    CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
        INSERT INTO messages_fts(rowid, text) VALUES (new.id, new.text); END;
    CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
        INSERT INTO messages_fts(messages_fts, rowid, text) VALUES ('delete', old.id, old.text); END;
    CREATE TABLE IF NOT EXISTS synced (path TEXT PRIMARY KEY, mtime REAL NOT NULL);
    """,
    # 2: meaning (hive/embed.py): one vector per fact, made when first needed, gone with the fact
    """
    CREATE TABLE IF NOT EXISTS embeddings (fact_id INTEGER PRIMARY KEY, model TEXT NOT NULL, vec BLOB NOT NULL);
    CREATE TRIGGER IF NOT EXISTS embeddings_ad AFTER DELETE ON facts BEGIN
        DELETE FROM embeddings WHERE fact_id = old.id; END;
    CREATE TRIGGER IF NOT EXISTS embeddings_au AFTER UPDATE OF text ON facts BEGIN
        DELETE FROM embeddings WHERE fact_id = old.id; END;
    """,
    """
    CREATE TABLE actions (
        id TEXT PRIMARY KEY, tool TEXT NOT NULL, args TEXT NOT NULL, proposal_hash TEXT NOT NULL,
        owner_id TEXT NOT NULL, chat_id TEXT NOT NULL, origin TEXT NOT NULL, state TEXT NOT NULL,
        created REAL NOT NULL, expires REAL NOT NULL, message_id INTEGER, receipt TEXT NOT NULL DEFAULT '',
        project TEXT NOT NULL DEFAULT '', request_key TEXT UNIQUE, account_binding TEXT NOT NULL DEFAULT '');
    CREATE TABLE action_events (id INTEGER PRIMARY KEY, action_id TEXT NOT NULL REFERENCES actions(id),
        state TEXT NOT NULL, at REAL NOT NULL);
    ALTER TABLE facts ADD COLUMN due_at REAL;
    ALTER TABLE facts ADD COLUMN valid_from REAL;
    ALTER TABLE facts ADD COLUMN confidence TEXT NOT NULL DEFAULT 'stated';
    UPDATE facts SET due_at=valid_until, valid_until=NULL WHERE kind='deadline';
    UPDATE facts SET trust='outside' WHERE source IN ('document','email','web');
    CREATE TABLE memory_tombstones (owner_id TEXT NOT NULL, project TEXT NOT NULL, norm TEXT NOT NULL,
        PRIMARY KEY(owner_id,project,norm));
    CREATE TABLE forgotten_sources (owner_id TEXT NOT NULL, source_ref TEXT NOT NULL,
        PRIMARY KEY(owner_id,source_ref));
    CREATE TABLE notifications (event_id INTEGER PRIMARY KEY, state TEXT NOT NULL, updated REAL NOT NULL,
        receipt TEXT NOT NULL DEFAULT '');
    CREATE TABLE source_health (source TEXT PRIMARY KEY, checked REAL NOT NULL, ok INTEGER NOT NULL);
    CREATE TABLE telegram_inbox (chat_id TEXT NOT NULL, update_id INTEGER NOT NULL, payload TEXT NOT NULL,
        PRIMARY KEY(chat_id,update_id));
    CREATE TABLE memory_jobs (id INTEGER PRIMARY KEY, repo TEXT NOT NULL, text TEXT NOT NULL, history TEXT NOT NULL,
        context TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'queued', attempts INTEGER NOT NULL DEFAULT 0,
        retry_at REAL NOT NULL DEFAULT 0);
    """,
    # 4: restart-safe checkpoints for the assistant's general step runner.
    """
    CREATE TABLE tasks (
        id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, chat_id TEXT NOT NULL, project TEXT NOT NULL,
        request_key TEXT UNIQUE, instruction TEXT NOT NULL, steps TEXT NOT NULL, bindings TEXT NOT NULL,
        results TEXT NOT NULL DEFAULT '{}', next_step INTEGER NOT NULL DEFAULT 1, active_step INTEGER,
        state TEXT NOT NULL DEFAULT 'queued', detail TEXT NOT NULL DEFAULT '',
        created REAL NOT NULL, updated REAL NOT NULL);
    CREATE INDEX tasks_scope ON tasks(owner_id,chat_id,project,created);
    """,
    # 5: adaptive tasks, build plans, action reconciliation and scheduled jobs.
    """
    ALTER TABLE tasks ADD COLUMN mode TEXT NOT NULL DEFAULT 'chain';
    ALTER TABLE tasks ADD COLUMN metadata TEXT NOT NULL DEFAULT '{}';
    CREATE TABLE task_actions (task_id TEXT NOT NULL REFERENCES tasks(id), step INTEGER NOT NULL,
        action_id TEXT NOT NULL REFERENCES actions(id), PRIMARY KEY(task_id,step,action_id));
    CREATE TABLE routines (
        id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, chat_id TEXT NOT NULL, project TEXT NOT NULL,
        instruction TEXT NOT NULL, interval_seconds INTEGER NOT NULL, next_run REAL NOT NULL,
        enabled INTEGER NOT NULL DEFAULT 1, task_id TEXT, created REAL NOT NULL, detail TEXT NOT NULL DEFAULT '');
    CREATE UNIQUE INDEX routines_once ON routines(owner_id,chat_id,project,instruction,interval_seconds);
    """,
    # 6: listener jobs, safe-boundary controls, bound prompts and completion evidence.
    """
    ALTER TABLE tasks ADD COLUMN control TEXT NOT NULL DEFAULT '';
    ALTER TABLE tasks ADD COLUMN criteria TEXT;
    ALTER TABLE tasks ADD COLUMN reported_spend REAL NOT NULL DEFAULT 0;
    ALTER TABLE tasks ADD COLUMN active_seconds REAL NOT NULL DEFAULT 0;
    UPDATE tasks SET reported_spend=COALESCE(json_extract(metadata,'$.spent'),0);
    CREATE TABLE execution_queue (
        task_id TEXT PRIMARY KEY REFERENCES tasks(id), project TEXT NOT NULL, context TEXT NOT NULL,
        pending INTEGER NOT NULL DEFAULT 1, worker TEXT, started REAL);
    CREATE UNIQUE INDEX worker_project ON execution_queue(project) WHERE worker IS NOT NULL;
    CREATE TABLE task_prompts (
        owner_id TEXT NOT NULL, chat_id TEXT NOT NULL, message_id INTEGER NOT NULL, task_id TEXT NOT NULL,
        kind TEXT NOT NULL, choices TEXT NOT NULL DEFAULT '[]', expires REAL NOT NULL,
        reply TEXT, consumed INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(owner_id,chat_id,message_id));
    CREATE TABLE task_evidence (
        task_id TEXT NOT NULL REFERENCES tasks(id), step INTEGER NOT NULL, kind TEXT NOT NULL,
        reference TEXT NOT NULL, at REAL NOT NULL, PRIMARY KEY(task_id,step,kind,reference));
    CREATE TABLE dispatched_updates (
        chat_id TEXT NOT NULL, update_id TEXT NOT NULL, PRIMARY KEY(chat_id,update_id));
    CREATE TABLE telegram_replies (
        owner_id TEXT NOT NULL, chat_id TEXT NOT NULL, message_id INTEGER NOT NULL, update_id TEXT NOT NULL,
        text TEXT, button TEXT, created REAL NOT NULL, PRIMARY KEY(chat_id,update_id));
    """,
]


@contextmanager
def transaction():
    """Serialize a connection's transactions; nested callers use savepoints."""
    with _LOCK:
        con = connect()
        outer = getattr(_TX, 'callbacks', None) is None
        if outer:
            _TX.callbacks = []
        start = len(_TX.callbacks)
        name = 'sp_' + str(time.monotonic_ns())
        con.execute('SAVEPOINT ' + name)
        try:
            yield con
            con.execute('RELEASE SAVEPOINT ' + name)
        except BaseException:
            con.execute('ROLLBACK TO SAVEPOINT ' + name)
            con.execute('RELEASE SAVEPOINT ' + name)
            del _TX.callbacks[start:]
            if outer:
                del _TX.callbacks
            raise
        if outer:
            callbacks = _TX.callbacks
            del _TX.callbacks
            for callback in callbacks:
                try:
                    callback()
                except OSError:
                    import warnings
                    warnings.warn('A memory compatibility export failed; SQLite remains authoritative.', RuntimeWarning)


def after_commit(callback):
    callbacks = getattr(_TX, 'callbacks', None)
    if callbacks is None:
        return False
    callbacks.append(callback)
    return True

def path():
    from . import memory   # beside the rules folder, so whatever moves memory (tests, a cloud copy) moves this too
    return os.path.join(os.path.dirname(memory.DIR), 'hive.db')

def norm(text):
    """The same fact however it is spaced, cased or punctuated at the end."""
    return re.sub(r'\s+', ' ', (text or '').strip().lower()).rstrip(' .!')

def connect():
    """One connection per thread so a cursor cannot race another thread's statement cache."""
    p = path()
    key = (p, threading.get_ident())
    with _LOCK:
        con = _CONN.get(key)
        if con is not None:
            return con
        os.makedirs(os.path.dirname(p), exist_ok=True)
        from .vault import private_permissions
        private_permissions(os.path.dirname(p), directory=True)
        new = not os.path.exists(p)
        con = sqlite3.connect(p, check_same_thread=False, timeout=30, isolation_level=None, factory=_Connection)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA journal_mode=WAL'); con.execute('PRAGMA foreign_keys=ON')
        con.execute('PRAGMA secure_delete=ON')   # what he asks Hive to forget is overwritten, not left in free pages
        if new:
            try:
                os.chmod(p, 0o600)
            except OSError:
                pass
        _migrate(con)
        _CONN[key] = con
        return con

def close():
    with _LOCK:
        for con in _CONN.values():
            con.close()
        _CONN.clear()

def _migrate(con):
    # Two independently started listeners/Pulse processes must not race migrations.
    con.execute('BEGIN IMMEDIATE')
    try:
        con.execute('CREATE TABLE IF NOT EXISTS schema_version (v INTEGER NOT NULL)')
        row = con.execute('SELECT max(v) FROM schema_version').fetchone()
        version = (row[0] if row else 0) or 0
        con.execute('DELETE FROM schema_version')
        con.execute('INSERT INTO schema_version VALUES(?)', (version,))
        for n, sql in enumerate(MIGRATIONS, 1):
            if n > version:
                statement = ''
                for line in sql.splitlines(keepends=True):
                    statement += line
                    if sqlite3.complete_statement(statement):
                        con.execute(statement)
                        statement = ''
                if statement.strip():
                    raise ValueError('Incomplete migration')
                con.execute('UPDATE schema_version SET v=?', (n,))
        con.commit()
    except BaseException:
        con.rollback()
        raise

def version():
    return connect().execute('SELECT v FROM schema_version').fetchone()[0]

def fingerprint(con=None):
    """Logical snapshot identity for conservative single-owner handoffs."""
    import hashlib
    con = con or connect()
    digest = hashlib.sha256()
    with _LOCK:
        tables = con.execute("SELECT name,sql FROM sqlite_master WHERE type='table' "
                             "AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '%_fts%' ORDER BY name").fetchall()
        for name, schema in tables:
            digest.update(repr((name, schema)).encode())
            quoted = '"' + name.replace('"', '""') + '"'
            for row in con.execute('SELECT * FROM ' + quoted + ' ORDER BY rowid'):
                digest.update(repr(tuple(row)).encode('utf-8'))
    return digest.hexdigest()

# ---------------------------------------------------------------------------------------------------------------- facts

def add_fact(text, kind='note', project='', source='chat', source_ref='', trust='owner', person=None, valid_until=None,
             extra=None, when=None, owner=OWNER, due_at=None, valid_from=None):
    """Keep one fact (or bring a forgotten or replaced one back if he says it again). Returns its id."""
    text = ' '.join((text or '').split())
    if not text:
        return None
    if source_ref and connect().execute('SELECT 1 FROM forgotten_sources WHERE owner_id=? AND source_ref=?',
                                       (owner, str(source_ref))).fetchone():
        return None
    pid = person_id(person, owner) if person else None
    con = connect(); n = norm(text); now = when or time.time()
    if kind == 'deadline' and due_at is None:
        due_at, valid_until = valid_until, None
    with _LOCK:
        row = con.execute('SELECT id FROM facts WHERE owner_id=? AND project=? AND kind=? AND norm=?',
                          (owner, project, kind, n)).fetchone()
        if row and when is None:
            con.execute('DELETE FROM memory_tombstones WHERE owner_id=? AND project=? AND norm=?', (owner, project, n))
        if row:   # said again: it holds again, and is the newest
            con.execute('UPDATE facts SET deleted_at=NULL, superseded_by=NULL, created=?, '
                        'person_id=COALESCE(?, person_id), valid_until=?, due_at=? WHERE id=?',
                        (now if when is None else created_of(row[0]), pid, valid_until, due_at, row[0]))
            if trust == 'owner':
                con.execute('UPDATE facts SET source=?,source_ref=?,trust=?,valid_from=? WHERE id=?',
                            (source, source_ref, trust, valid_from, row[0]))
            return row[0]
        cur = con.execute('INSERT INTO facts (owner_id, project, kind, text, norm, person_id, source, source_ref, trust, '
                          'created, valid_until, extra) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                          (owner, project, kind, text, n, pid, source, source_ref[:200], trust, now, valid_until,
                           json.dumps(extra or {}, ensure_ascii=False)))
        con.execute('UPDATE facts SET due_at=?,valid_from=? WHERE id=?', (due_at, valid_from, cur.lastrowid))
        return cur.lastrowid

def created_of(fid):
    row = connect().execute('SELECT created FROM facts WHERE id=?', (fid,)).fetchone()
    return row[0] if row else time.time()

def find_fact(text, kind=None, project=None, owner=OWNER):
    q, args = 'SELECT * FROM facts WHERE owner_id=? AND norm=?', [owner, norm(text)]
    if kind:
        q += ' AND kind=?'; args.append(kind)
    if project is not None:
        q += ' AND project=?'; args.append(project)
    row = connect().execute(q + ' ORDER BY created DESC', args).fetchone()
    return dict(row) if row else None

def supersede(old_id, new_id):
    """He changed his mind: old_id is replaced by new_id (kept, for the record, but no longer true)."""
    connect().execute('UPDATE facts SET superseded_by=? WHERE id=? AND id<>?', (new_id, old_id, new_id))

def forget(fact_id, purge=False):
    """Remove retrieval sources and retain a tombstone against legacy resurrection."""
    with transaction() as con:
        row = con.execute('SELECT * FROM facts WHERE id=?', (fact_id,)).fetchone()
        if not row:
            return
        con.execute('INSERT OR IGNORE INTO memory_tombstones VALUES(?,?,?)',
                    (row['owner_id'], row['project'], row['norm']))
        if row['source_ref']:
            con.execute('INSERT OR IGNORE INTO forgotten_sources VALUES(?,?)', (row['owner_id'], row['source_ref']))
            con.execute("DELETE FROM memory_jobs WHERE json_extract(context,'$.source_ref')=?", (row['source_ref'],))
        con.execute('DELETE FROM messages WHERE owner_id=? AND (instr(lower(text),lower(?))>0 OR id=?)',
                    (row['owner_id'], row['text'], row['source_ref'] if str(row['source_ref']).isdigit() else -1))
        con.execute('DELETE FROM embeddings WHERE fact_id=?', (fact_id,))
        con.execute('DELETE FROM memory_jobs WHERE instr(lower(text),lower(?))>0 OR instr(history,?)>0', (row['text'], row['text']))
        if purge:
            con.execute('DELETE FROM facts WHERE id=?', (fact_id,))
        else:
            con.execute('UPDATE facts SET deleted_at=? WHERE id=?', (time.time(), fact_id))

def purge_forgotten(older_than_days=7):
    """Forgotten facts are kept a week (so "undo" can bring one back), then removed from the file."""
    con = connect()
    cur = con.execute('DELETE FROM facts WHERE deleted_at IS NOT NULL AND deleted_at < ?',
                      (time.time() - older_than_days * 86400,))
    if cur.rowcount:   # out of the search index's own pages and the write-ahead log too
        con.execute("INSERT INTO facts_fts(facts_fts) VALUES ('optimize')")
        con.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    return cur.rowcount

def live_facts(project=None, kinds=None, owner=OWNER, limit=None):
    """Facts that hold now: not forgotten, not replaced, not past their date. Newest last."""
    q = ('SELECT * FROM facts WHERE owner_id=? AND deleted_at IS NULL AND superseded_by IS NULL '
         'AND (valid_until IS NULL OR valid_until > ?) AND (valid_from IS NULL OR valid_from <= ?)')
    args = [owner, time.time(), time.time()]
    if project is not None:
        q += " AND project IN (?, '')"; args.append(project)
    if kinds:
        q += f" AND kind IN ({','.join('?' * len(kinds))})"; args += list(kinds)
    q += ' ORDER BY created DESC' + (f' LIMIT {int(limit)}' if limit else '')
    return [dict(r) for r in connect().execute(q, args).fetchall()][::-1]

def _fts_query(text):
    """His words as a forgiving full-text query: each word (3+ letters, or a number) may match, prefixes too."""
    words = [w for w in re.findall(r'\w+', (text or '').lower()) if len(w) >= 3 or w.isdigit()]
    stop = {'the', 'and', 'for', 'are', 'was', 'what', 'who', 'how', 'his', 'her', 'with', 'that', 'this', 'you', 'did',
            'does', 'about', 'have', 'has', 'can', 'tell', 'know', 'kya', 'hai', 'from', 'when', 'where', 'which'}
    words = [w for w in dict.fromkeys(words) if w not in stop][:12]
    return ' OR '.join(f'"{w}"*' for w in words)

def search(text, project=None, k=12, owner=OWNER, include_forgotten=False):
    """Facts matching his words, best first: [(fact, score)] with score from the full-text rank (higher is better)."""
    q = _fts_query(text)
    if not q:
        return []
    cond = '' if include_forgotten else ('AND f.deleted_at IS NULL AND f.superseded_by IS NULL '
                                          'AND (f.valid_until IS NULL OR f.valid_until > ?) AND (f.valid_from IS NULL OR f.valid_from <= ?)')
    args = [q, owner] + ([] if include_forgotten else [time.time(), time.time()])
    if project is not None:
        cond += " AND f.project IN (?, '')"; args.append(project)
    try:
        rows = connect().execute(f'SELECT f.*, bm25(facts_fts) AS rank FROM facts_fts JOIN facts f ON f.id = facts_fts.rowid '
                                 f'WHERE facts_fts MATCH ? AND f.owner_id=? {cond} ORDER BY rank LIMIT ?',
                                 args + [k]).fetchall()
    except sqlite3.OperationalError:
        return []
    return [(dict(r), -r['rank']) for r in rows]

def semantic(text, project=None, k=12, owner=OWNER):
    """Facts close in meaning to his words, best first: [(fact, similarity 0-1)]. [] without the embedding model."""
    from . import embed
    if not (text or '').strip() or not embed.available() or not embed.ready():   # never waits on the model
        return []
    import numpy as np
    facts = live_facts(project, owner=owner)
    if not facts:
        return []
    con = connect()
    have = {r[0]: r[1] for r in con.execute('SELECT fact_id, vec FROM embeddings WHERE model=?', (embed.MODEL,)).fetchall()}
    missing = [f for f in facts if f['id'] not in have]
    if missing:   # made once per fact, the first time it could be recalled
        for f, v in zip(missing, embed.vectors([f['text'] for f in missing])):
            blob = v.astype(np.float32).tobytes(); have[f['id']] = blob
            con.execute('INSERT OR REPLACE INTO embeddings (fact_id, model, vec) VALUES (?,?,?)', (f['id'], embed.MODEL, blob))
    q = embed.vectors([text])[0]
    m = np.stack([np.frombuffer(have[f['id']], dtype=np.float32) for f in facts])
    sims = m @ q
    order = np.argsort(-sims)[:k]
    return [(facts[i], float(sims[i])) for i in order]

# --------------------------------------------------------------------------------------------------------------- people

def person_id(name, owner=OWNER, relation='', org='', contact=''):
    """The person's id, kept if new; what is given about them (relation, company, contact) fills in what was blank."""
    name = ' '.join((name or '').split())
    if not name:
        return None
    con = connect(); n = norm(name); now = time.time()
    with _LOCK:
        row = con.execute('SELECT id FROM people WHERE owner_id=? AND (norm=? OR aliases LIKE ?)',
                          (owner, n, f'%"{n}"%')).fetchone()
        if not row and ' ' not in n:   # "Asha" for the one known Asha ("Asha Mehta"; Gate 118: two people were made)
            same = con.execute("SELECT id, aliases FROM people WHERE owner_id=? AND deleted_at IS NULL AND norm LIKE ?",
                               (owner, n + ' %')).fetchall()
            if len(same) == 1:
                row = same[0]
                con.execute('UPDATE people SET aliases=? WHERE id=?',
                            (json.dumps(sorted(set(json.loads(row[1] or '[]')) | {n})), row[0]))
        if row:
            con.execute("UPDATE people SET last_seen=?, deleted_at=NULL, relation=CASE WHEN ?<>'' THEN ? ELSE relation END, "
                        "org=CASE WHEN ?<>'' THEN ? ELSE org END, contact=CASE WHEN ?<>'' THEN ? ELSE contact END "
                        'WHERE id=?', (now, relation, relation, org, org, contact, contact, row[0]))
            return row[0]
        return con.execute('INSERT INTO people (owner_id, name, norm, relation, org, contact, created, last_seen) '
                           'VALUES (?,?,?,?,?,?,?,?)', (owner, name, n, relation, org, contact, now, now)).lastrowid

def people(owner=OWNER):
    return [dict(r) for r in connect().execute('SELECT * FROM people WHERE owner_id=? AND deleted_at IS NULL '
                                               'ORDER BY last_seen DESC', (owner,)).fetchall()]

def person(name, owner=OWNER):
    n = norm(name)
    row = connect().execute('SELECT * FROM people WHERE owner_id=? AND deleted_at IS NULL AND (norm=? OR aliases LIKE ?)',
                            (owner, n, f'%"{n}"%')).fetchone()
    return dict(row) if row else None

def facts_about(pid, owner=OWNER, project=None):
    return [f for f in live_facts(project, owner=owner) if f['person_id'] == pid]


def forget_person(pid):
    with transaction() as con:
        for row in con.execute('SELECT id FROM facts WHERE person_id=?', (pid,)).fetchall():
            forget(row[0])
        person = con.execute('SELECT name FROM people WHERE id=?', (pid,)).fetchone()
        if person:
            con.execute('DELETE FROM memory_jobs WHERE instr(lower(text),lower(?))>0 OR instr(lower(history),lower(?))>0', (person[0],person[0]))
            con.execute('DELETE FROM messages WHERE instr(lower(text),lower(?))>0', (person[0],))
        con.execute("UPDATE people SET deleted_at=?,relation='',org='',contact='',aliases='[]' WHERE id=?",
                    (time.time(), pid))

# -------------------------------------------------------------------------------------------------------------- profile

def get(key, default=None, owner=OWNER):
    row = connect().execute('SELECT value FROM profile WHERE owner_id=? AND key=?', (owner, key)).fetchone()
    return json.loads(row[0]) if row else default

def put(key, value, owner=OWNER):
    connect().execute('INSERT INTO profile (owner_id, key, value, updated) VALUES (?,?,?,?) ON CONFLICT(owner_id, key) '
                      'DO UPDATE SET value=excluded.value, updated=excluded.updated',
                      (owner, key, json.dumps(value, ensure_ascii=False), time.time()))

# ------------------------------------------------------------------------------------------------------------- messages

def log_message(who, text, channel='telegram', at=None, owner=OWNER):
    text = (text or '').strip()
    if text:
        return connect().execute('INSERT INTO messages (owner_id, channel, who, text, at) VALUES (?,?,?,?,?)',
                          (owner, channel, who, text[:4000], at or time.time())).lastrowid

def search_messages(text, k=6, owner=OWNER):
    q = _fts_query(text)
    if not q:
        return []
    try:
        return [dict(r) for r in connect().execute(
            'SELECT m.* FROM messages_fts JOIN messages m ON m.id = messages_fts.rowid WHERE messages_fts MATCH ? '
            'AND m.owner_id=? ORDER BY bm25(messages_fts) LIMIT ?', (q, owner, k)).fetchall()]
    except sqlite3.OperationalError:
        return []

def forget_messages_with(secret, owner=OWNER):
    """A password he sent by mistake: taken out of the archive too (telegram.Channel.forget)."""
    if secret:
        connect().execute('UPDATE messages SET text=REPLACE(text, ?, ?) WHERE owner_id=? AND instr(text, ?) > 0',
                          (secret, '••••', owner, secret))
        connect().execute("INSERT INTO messages_fts(messages_fts) VALUES ('rebuild')")

# ----------------------------------------------------------------------------------------------- the JSON files, synced

def sync(repo):
    """Take in what the JSON files hold that the store does not (an older Hive, a cloud copy brought home). Cheap when
    nothing changed: each file is read again only when it has changed."""
    from . import memory
    try:
        project = memory.project_key(repo)
    except Exception:
        return 0
    n = 0
    for p, kind in ((memory._notes_path(repo), 'note'), (memory._path(repo), 'rule')):
        try:
            mtime = os.path.getmtime(p)
        except OSError:
            continue
        con = connect()
        row = con.execute('SELECT mtime FROM synced WHERE path=?', (p,)).fetchone()
        if row:  # legacy import is one-time; compatibility exports are never reimported
            continue
        try:
            with open(p, encoding='utf-8') as fh:
                items = json.load(fh)
        except (OSError, ValueError):
            continue
        for it in items if isinstance(items, list) else []:
            text = it if isinstance(it, str) else (it or {}).get('text', '')
            if text and not con.execute('SELECT 1 FROM memory_tombstones WHERE owner_id=? AND project=? AND norm=?',
                                       (OWNER, project, norm(text))).fetchone() and not find_fact(text, None if kind == 'note' else kind, project):   # a note may be kept as a
                # person, preference or deadline fact (Gate 118: imported again as a plain note, it showed twice)
                when = None
                if isinstance(it, dict) and it.get('when'):
                    try:
                        when = time.mktime(time.strptime(it['when'], '%Y-%m-%d'))
                    except ValueError:
                        pass
                add_fact(text, kind, project, source=(it.get('kind') if isinstance(it, dict) else '') or 'memory',
                         when=when); n += 1
        con.execute('INSERT INTO synced (path, mtime) VALUES (?,?) ON CONFLICT(path) DO UPDATE SET mtime=excluded.mtime',
                    (p, mtime))
    return n

# --------------------------------------------------------------------------------------------------- hive memory (CLI)

def cli(repo, action=None, arg=None):
    """hive memory [list|search <words>|people|forget <id>|export [file]|purge]"""
    from . import memory
    sync(repo)
    project = memory.project_key(repo)
    show = lambda f: print(f"{f['id']:>5}  [{f['kind']}{', ' + f['source'] if f['source'] not in ('chat', '') else ''}"
                           f"{', from outside' if f['trust'] != 'owner' else ''}]  {f['text']}")
    if action in (None, 'list'):
        facts = live_facts(project)
        for f in facts:
            show(f)
        print(f'\n{len(facts)} fact(s) kept for this project; {len(people())} people. The file: {path()}'); return 0
    if action == 'search':
        for f, _ in search(arg or '', project, k=20):
            show(f)
        return 0
    if action == 'people':
        for p in people():
            print(f"{p['name']}" + (f" ({p['relation']}" + (f", {p['org']}" if p['org'] else '') + ')' if p['relation'] else ''))
        return 0
    if action == 'forget':
        if not (arg or '').isdigit():
            print('Say which: hive memory forget <id> (the number hive memory list shows).'); return 1
        forget(int(arg)); print(f'Forgotten: {arg}. It is removed from the file within a week (hive memory purge: now).'); return 0
    if action == 'purge':
        con = connect(); n = con.execute('DELETE FROM facts WHERE deleted_at IS NOT NULL').rowcount
        con.execute("INSERT INTO facts_fts(facts_fts) VALUES ('optimize')"); con.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        print(f'{n} forgotten fact(s) removed from the file.'); return 0
    if action == 'export':
        out = {'facts': live_facts(project), 'people': people(),
               'profile': {r['key']: json.loads(r['value']) for r in connect().execute(
                   'SELECT key, value FROM profile WHERE owner_id=?', (OWNER,)).fetchall()}}
        dest = arg or 'hive-memory.json'
        json.dump(out, open(dest, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print(f'Everything Hive keeps about this project and you, in {dest}.'); return 0
    print('hive memory [list|search <words>|people|forget <id>|export [file]|purge]'); return 1

# ------------------------------------------------------------------------------------------------- the weekly tidy

TIDY_DAYS = 7

def tidy(project, owner=OWNER, close=0.95):
    """Fold exact duplicates only. Different wording or word order is not proof of equivalence.

    `close` is retained for callers of the earlier API; semantic merging is disabled.
    """
    facts = [f for f in live_facts(project, owner=owner) if f['kind'] != 'rule']
    folded, exact = 0, {}
    for f in facts:
        key = (f['project'], f['kind'], f['trust'], f['person_id'], f['norm'], f['due_at'])
        if key in exact:
            supersede(exact[key], f['id']); folded += 1
        exact[key] = f['id']
    put(f'tidied:{project}', time.time(), owner)
    return folded

def tidy_due(project, owner=OWNER):
    return time.time() - (get(f'tidied:{project}', 0, owner) or 0) > TIDY_DAYS * 86400
