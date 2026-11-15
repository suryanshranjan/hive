"""Read-only access to the owner's data (hive/access.py) and asking it from the phone, with a fake Telegram and a
stand-in model (no network, no tokens): only reading queries run, a database opened read-only cannot be changed, his
handover is recognised, his questions are answered from his data, keys stay out of what he and builders see.
usage: python3 tests/test_access.py   (run from the hive repo root)"""
import json, os, sqlite3, subprocess, sys, tempfile
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home
from hive import access, assistant, explain, memory, telegram
explain.CMD = '"' + sys.executable.replace(chr(92), '/') + '" tests/fake_explain.py'
memory.DIR = os.path.join(home, '.hive', 'rules'); telegram.BUSY = os.path.join(home, '.hive', 'telegram.busy')
access.DIR = os.path.join(home, '.hive', 'access'); assistant.RUNS = os.path.join(home, '.hive', 'runs')
from test_telegram_fake import FakeTelegram, ME, say

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))
ch = lambda fake: telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=fake)

# 1. only reading queries pass
check('a plain SELECT passes', bool(access.safe_sql('SELECT count(*) FROM orders')), True)
check('a WITH ... SELECT passes', bool(access.safe_sql('WITH p AS (SELECT * FROM orders) SELECT count(*) FROM p;')), True)
check("words inside quotes are data, not commands", bool(access.safe_sql("SELECT * FROM orders WHERE note = 'delete me'")), True)
for bad in ('DELETE FROM orders', 'SELECT 1; DROP TABLE orders', 'UPDATE orders SET status = 1',
            'SELECT * INTO copy FROM orders', 'WITH x AS (DELETE FROM orders RETURNING *) SELECT * FROM x',
            'SELECT pg_terminate_backend(1)', 'PRAGMA writable_schema = 1', 'SELECT pg_sleep(100)', '',
            'SELECT 1 /* ; */ ; DELETE FROM orders'):
    check(f'refused: {bad[:40]!r}', access.safe_sql(bad), None)

# 2. a real SQLite database, read only
db = os.path.join(home, 'shop.db')
con = sqlite3.connect(db)
con.executescript("CREATE TABLE orders (id INTEGER, status TEXT, amount REAL); CREATE TABLE users (id INTEGER, email TEXT);"
                  "INSERT INTO orders VALUES (1, 'paid', 500), (2, 'paid', 250), (3, 'refunded', 100);")
con.commit(); con.close()
check('it sees the tables', access.tables(db), ['orders', 'users'])
check('a count comes back as rows', access.run_sql(db, "SELECT COUNT(*) AS n FROM orders WHERE status = 'paid'").split(),
      ['n', '2'])
try:
    access.run_sql(db, 'DELETE FROM orders'); refused = False
except access.Unreadable:
    refused = True
check('a writing query is never run', (refused, sqlite3.connect(db).execute('SELECT COUNT(*) FROM orders').fetchone()[0]),
      (True, 3))
try:   # even past the check, the connection itself cannot write
    c = sqlite3.connect(f'file:{db}?mode=ro', uri=True); c.execute('DELETE FROM orders'); wrote = True
except sqlite3.OperationalError:
    wrote = False
check('the read-only connection cannot write', wrote, False)
big = os.path.join(home, 'big.db'); c = sqlite3.connect(big); c.execute('CREATE TABLE t (n INTEGER)')
c.executemany('INSERT INTO t VALUES (?)', [(k,) for k in range(500)]); c.commit(); c.close()
out = access.run_sql(big, 'SELECT n FROM t')
check('at most 200 rows come back, and it says so', (len(out.splitlines()), out.splitlines()[-1]), (202, '(first 200 rows only)'))

# 3. his handover, read from his words
check('a database address', access.detect('here is our db postgres://reader:s3cret@db.example.com:5432/shop'),
      {'kind': 'db', 'where': 'postgres://reader:s3cret@db.example.com:5432/shop'})
check('an admin API with its key', access.detect('our admin api https://admin.example.com/api/stats key: abcdef1234567890'),
      {'kind': 'url', 'where': 'https://admin.example.com/api/stats', 'headers': {'Authorization': 'Bearer abcdef1234567890'}})
check('a header he names', access.detect('use https://x.example.com/stats header X-Api-Key: zz99zz99')['headers'],
      {'X-Api-Key': 'zz99zz99'})
check('a Google Sheet is read as its CSV export',
      access.detect('our numbers sheet https://docs.google.com/spreadsheets/d/AbC123/edit#gid=42')['where'],
      'https://docs.google.com/spreadsheets/d/AbC123/export?format=csv&gid=42')
check('a database handover is taken as one', access.is_handover('postgres://u:p@h/db'), True)
check('a data link with a giving word is a handover', access.is_handover("here's our admin dashboard https://a.example.com"), True)
check('a plain reference link is not', access.is_handover('make it look like https://stripe.com'), False)
check('the password is hidden when shown', access.secret_free('postgres://reader:s3cret@db.example.com/shop'),
      'postgres://reader:•••@db.example.com/shop')

# 4. kept on this computer, by name; summary carries no secret
repo = os.path.join(home, 'project'); subprocess.run(['git', 'init', '-q', '-b', 'main', repo])
access.add(repo, 'db', db, name='shop database')
access.add(repo, 'url', 'https://admin.example.com/api', name='admin', headers={'Authorization': 'Bearer topsecret123456'})
kept = open(access._path(repo), encoding='utf-8').read()
check('sources are kept outside his repository', access._path(repo).startswith(access.DIR), True)
check('the summary names them, never the key', ('shop database' in access.summary(repo), 'topsecret' in access.summary(repo)),
      (True, False))
check('the summary reaches what Hive knows when it replies', 'shop database (database)' in assistant.facts(repo), True)
check('removing one by name', (access.remove(repo, 'admin'), [s['name'] for s in access.load(repo)]), (True, ['shop database']))

# 5. from the phone: a question about his figures is answered from his data
fake = FakeTelegram([])
r = assistant.handle(ch(fake), repo, 'how many orders are paid?', poll=1)
check('a figures question is answered from his database', (r, fake.sent[-1]['text']), ('data_answered', '📊 2 paid orders so far.'))
fake = FakeTelegram([])
r = assistant.handle(ch(fake), repo, 'how many orders are paid? DROP-ME', poll=1)
check('a writing query the model writes is refused, and he hears it plainly', r, 'data_unanswered')
check('...and nothing was changed', sqlite3.connect(db).execute('SELECT COUNT(*) FROM orders').fetchone()[0], 3)

fake = FakeTelegram([])
r = assistant.handle(ch(fake), repo, 'how many orders are paid? EMPTY-ME', poll=1)
check('no query comes back: a plain reason, never an empty one (Gate 108 q1)',
      (r, fake.sent[-1]['text'].startswith("🤔 I couldn't work that out from your data just now.")), ('data_unanswered', True))

fake = FakeTelegram([])
r = assistant.handle(ch(fake), repo, 'how many orders are paid? KIND-NAME', poll=1)
check('a query naming its source by kind ("db") still runs (Gate 108 run 2: 5 of 10 dropped)',
      (r, fake.sent[-1]['text']), ('data_answered', '📊 2 paid orders so far.'))

# 6. from the phone: handing over a database
db2 = os.path.join(home, 'more.db'); c = sqlite3.connect(db2); c.execute('CREATE TABLE payouts (id INTEGER)'); c.commit(); c.close()
fake = FakeTelegram([])
r = assistant.handle(ch(fake), repo, f'here is our payouts database {db2}', poll=1)
check('a database file he names is connected and tried', (r, 'I can see 1 table: payouts.' in fake.sent[-1]['text']),
      ('connect_data', True))
fake = FakeTelegram([])
r = assistant.handle(ch(fake), repo, 'connect our admin db postgres://reader:pw@127.0.0.1:1/none', poll=1)
check('a database that cannot be reached is kept and told plainly, its password never shown',
      (r, 'pw@' in fake.sent[-1]['text']), ('connect_data_failed', False))

# 7. with no data given, a figures question says what to send
repo2 = os.path.join(home, 'project2'); subprocess.run(['git', 'init', '-q', '-b', 'main', repo2])
check('no data yet: not routed to data', assistant.DATA_WORDS.search('how many orders this week?') is not None, True)

# psql: the password goes in its environment, never on its command line (the audit, Nov 15)
check('a database password is taken out of the address',
      access._without_password('postgresql://shop:p%40ss@db.example.com:5433/orders?sslmode=require'),
      ('postgresql://shop@db.example.com:5433/orders?sslmode=require', 'p@ss'))
check('an address with no password is left as it is', access._without_password('postgresql://db/orders'),
      ('postgresql://db/orders', None))
seen = {}
real_run = access.subprocess.run
def fake_psql(args, env=None, **k):
    seen.update(args=args, env=env); return subprocess.CompletedProcess(args, 0, 'n\n1\n', '')
access.subprocess.run = fake_psql
real_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__
import builtins
def no_drivers(name, *a, **k):
    if name.split('.')[0] in ('psycopg', 'psycopg2'):
        raise ImportError(name)
    return real_import(name, *a, **k)
builtins.__import__ = no_drivers
try:
    access.run_sql('postgresql://shop:sup3rsecret@db.example.com/orders', 'select 1')
except Exception as e:
    seen['error'] = repr(e)
finally:
    builtins.__import__ = real_import; access.subprocess.run = real_run
check('psql: the password is never on its command line',
      ('sup3rsecret' in ' '.join(seen.get('args', [])), (seen.get('env') or {}).get('PGPASSWORD')), (False, 'sup3rsecret'))
# the guard refuses what writes, not ordinary reads that use REPLACE() or a column named set or comment (the audit)
check('reads with REPLACE(), a set column, a comment column are allowed',
      [bool(access.safe_sql(q)) for q in ("SELECT REPLACE(name, 'x', 'y') FROM t", 'SELECT "set", comment FROM orders',
                                          'SELECT id FROM t WHERE comment IS NOT NULL')], [True, True, True])
check('writing and settings are still refused',
      [access.safe_sql(q) for q in ("REPLACE INTO t VALUES (1)", "SELECT set_config('x', 'y', false)",
                                    'SELECT 1; DELETE FROM t', 'UPDATE t SET a = 1', "SELECT pg_sleep(10)")], [None] * 5)
sys.exit(fail)
