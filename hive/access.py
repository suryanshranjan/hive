"""What the owner has given Hive access to, read-only (the owner: "the hive can read the admin numbers, everything, the
access given"). He runs his company through Hive, so Hive should answer "how many sign-ups this week?" or "which seller
has the most unpaid payouts?" from his own data, and plan from what his data shows, not only from his pages (Gate 106:
the one miss was a reward that lived in his payouts, never on the site).

A source is one of:
- url: his site, an admin or analytics address that returns JSON or CSV (with its key, if it needs one), a shared
  spreadsheet (a Google Sheets link is read as its CSV export);
- db: his database, read-only: SQLite (a file), Postgres or MySQL (an address). Hive only ever runs one SELECT at a
  time, inside a read-only session, at most 200 rows back;
- file: a CSV, JSON, text, PDF or Excel file on this computer;
- cmd: a command that prints his data (set up by his engineer on this computer, never from the phone).

Sources are kept on this computer only (~/.hive/access/<project>.json), never in his repository, and secrets in them
are never sent back to him or shown to builders. Hive asks for read-only logins and keys, and says so."""
import csv, io, json, os, re, sqlite3, subprocess, time, urllib.parse, urllib.request

DIR = os.path.join(os.path.expanduser('~'), '.hive', 'access')
ROWS = 200            # rows back from any one query, at most
PREVIEW = 6000        # characters of one source shown to the model

def _path(repo):
    from . import memory
    return os.path.join(DIR, f'{memory.project_key(repo)}.json')

def load(repo):
    from . import vault
    got = vault.load_json(_path(repo), [])
    return got if isinstance(got, list) else []

def _save(repo, sources):
    from . import vault
    vault.save_json(_path(repo), sources)   # database addresses and keys, encrypted when Hive can (hive/vault.py)

def add(repo, kind, where, name=None, headers=None):
    """Keep one source (replacing one of the same name). Returns it."""
    src = {'name': (name or default_name(kind, where))[:60], 'kind': kind, 'where': where, 'added': time.time()}
    if headers:
        src['headers'] = headers
    _save(repo, [s for s in load(repo) if s['name'] != src['name']] + [src])
    return src

def remove(repo, name):
    keep = [s for s in load(repo) if s['name'].lower() != name.lower()]
    gone = len(keep) < len(load(repo))
    _save(repo, keep)
    return gone

def default_name(kind, where):
    if kind == 'db':
        u = urllib.parse.urlparse(where)
        return f"{(u.path.strip('/') or u.hostname or 'your')} database" if u.scheme else \
            os.path.splitext(os.path.basename(where))[0] + ' database'
    if kind == 'url':
        u = urllib.parse.urlparse(where)
        if 'docs.google.com' in (u.hostname or ''):
            return 'your spreadsheet'
        return (u.hostname or where).removeprefix('www.') + (u.path.rstrip('/') if u.path not in ('', '/') else '')
    if kind == 'file':
        return os.path.basename(where)
    return 'your data command'

def secret_free(where):
    """An address with its password hidden, for anything he or a builder sees."""
    return re.sub(r'(://[^:/@\s]+):[^@\s]+@', r'\1:•••@', where)

# ---- reading his message: what he is giving Hive -------------------------------------------------------------------

DB_URL = re.compile(r'\b((?:postgres(?:ql)?|mysql|mariadb)://\S+)', re.I)
DB_FILE = re.compile(r'(\S+\.(?:sqlite3?|db))\b', re.I)
WEB = re.compile(r'(https?://[^\s<>"]+)', re.I)
FILE = re.compile(r'(\S+\.(?:csv|json|xlsx|tsv|txt|pdf))\b', re.I)
KEY = re.compile(r'\b(?:bearer|token|api[ _-]?key|key|secret)\s*(?:is|:|=)?\s*([A-Za-z0-9._~+/=-]{12,})', re.I)
HEADER = re.compile(r'\bheader\s+([A-Za-z][A-Za-z0-9-]{1,40})\s*:\s*(\S+)', re.I)

def detect(text):
    """The source he is handing over in a message, as {'kind', 'where', 'headers'?}, or None. A plain web link with
    no data words is not taken here (it may be his site, a reference, or a host)."""
    t = (text or '').strip()
    m = DB_URL.search(t)
    if m:
        return {'kind': 'db', 'where': m.group(1).rstrip('.,)')}
    m = DB_FILE.search(t)
    if m and os.path.exists(m.group(1)):
        return {'kind': 'db', 'where': os.path.abspath(m.group(1))}
    m = WEB.search(t)
    if m:
        url = m.group(1).rstrip('.,)')
        g = re.match(r'https://docs\.google\.com/spreadsheets/d/([\w-]+)', url)
        if g:   # a shared Google Sheet: its CSV export (shared as "anyone with the link can view")
            gid = re.search(r'[#&?]gid=(\d+)', url)
            url = f'https://docs.google.com/spreadsheets/d/{g.group(1)}/export?format=csv' + (f'&gid={gid.group(1)}' if gid else '')
        src = {'kind': 'url', 'where': url}
        h = HEADER.search(t)
        k = KEY.search(t.replace(m.group(1), ' '))
        if h:
            src['headers'] = {h.group(1): h.group(2)}
        elif k:
            src['headers'] = {'Authorization': f'Bearer {k.group(1)}'}
        return src
    m = FILE.search(t)
    if m and os.path.exists(m.group(1)):
        return {'kind': 'file', 'where': os.path.abspath(m.group(1))}
    return None

DATA_WORDS = re.compile(r"\b(admin|api|dashboard|analytics|database|db|data|numbers|stats|metrics|sheet|spreadsheet|"
                        r"report|export|orders|payouts|sales|token|key|read[- ]?only)\b", re.I)
GIVE_WORDS = re.compile(r"\b(here'?s|here is|here are|this is|use|read|connect|access|link|login|my|our)\b", re.I)

def is_handover(text):
    """He is giving Hive access to his data in this message (a database address; or a link with data words and a
    giving word: "here's our admin API https://... key abc...")."""
    t = text or ''
    if DB_URL.search(t):
        return True
    f = DB_FILE.search(t)
    if f and os.path.exists(f.group(1)):   # a database file on this computer he names
        return True
    return bool(WEB.search(t) and DATA_WORDS.search(WEB.sub(' ', t)) and GIVE_WORDS.search(t))

# ---- reading a source ----------------------------------------------------------------------------------------------

class Unreadable(RuntimeError):
    """A source Hive could not read, with the reason in plain words."""

def _fetch(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers={'User-Agent': 'Hive/1 (read-only)', **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.headers.get('Content-Type', ''), r.read(2_000_000).decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise Unreadable("it asked for a login I don't have: send its read-only key with it "
                             "(\"key: ...\"), or ask your engineer for one") from None
        raise Unreadable(f'it answered with an error ({e.code})') from None
    except Exception as e:
        raise Unreadable(f"I couldn't reach it ({str(e)[:80]})") from None

def _text_of_web(ctype, body):
    b = body.lstrip()
    if 'json' in ctype or b[:1] in ('{', '['):
        try:
            return json.dumps(json.loads(body), ensure_ascii=False, indent=1)
        except ValueError:
            pass
    if 'html' in ctype or b[:1] == '<':
        title = re.search(r'<title[^>]*>(.*?)</title>', body, re.S | re.I)
        t = re.sub(r'<(script|style|noscript)[^>]*>.*?</\1>', ' ', body, flags=re.S | re.I)
        t = re.sub(r'<[^>]+>', ' ', t)
        t = re.sub(r'\s+', ' ', t).strip()
        return (f'Page title: {title.group(1).strip()}\n' if title else '') + t
    return body

def _text_of_file(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.xlsx':
        try:
            import openpyxl
        except ImportError:
            raise Unreadable("I can't open Excel files on this computer yet. Save it as CSV and send it again, or have your "
                             "engineer run once: pip install \"hive-swarm[data] @ git+https://github.com/suryanshranjan/hive\"") from None
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        out = []
        for ws in wb.worksheets[:5]:
            out.append(f'Sheet: {ws.title}')
            for row in ws.iter_rows(max_row=400, values_only=True):
                out.append(','.join('' if v is None else str(v) for v in row))
        return '\n'.join(out)
    from . import brain
    t = brain.text_of(path, limit=400_000)
    if not t.strip():
        raise Unreadable("I couldn't read that kind of file")
    return t

# -- databases: read-only, one SELECT at a time --

FORBIDDEN = re.compile(r'\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|copy|attach|detach|pragma|'
                       # REPLACE( is the string function, a column may be called set or comment: a statement that
                       # writes with them cannot start a single SELECT (the audit, Nov 15: they refused real reads)
                       r'vacuum|call|exec|execute|merge|replace(?!\s*\()|lock|reindex|into|load|outfile|dumpfile|set_config|'
                       r'handler|rename|analyze|refresh|listen|notify|begin|commit|rollback|savepoint|release|'
                       # functions that act rather than read (stop sessions, sleep, touch files, reach other servers)
                       r'pg_terminate_backend|pg_cancel_backend|pg_reload_conf|pg_rotate_logfile|pg_sleep\w*|pg_read_\w+|'
                       r'pg_ls_\w+|pg_stat_file|pg_advisory\w*|lo_\w+|dblink\w*|sleep|benchmark|load_file|'
                       r'readfile|writefile|load_extension|nextval|setval)\b', re.I)

def safe_sql(q):
    """The query if it only reads (one SELECT or WITH ... SELECT, nothing that writes or changes a setting), else None."""
    q = re.sub(r'--[^\n]*|/\*.*?\*/', ' ', q or '', flags=re.S).strip().rstrip(';').strip()
    bare = re.sub(r"'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\"|`[^`]*`", "''", q)   # words inside quotes are data
    if not q or ';' in bare or not re.match(r'(select|with)\b', bare, re.I) or FORBIDDEN.search(bare):
        return None
    return q

def _db_kind(where):
    s = urllib.parse.urlparse(where).scheme.lower()
    return 'postgres' if s.startswith('postgres') else 'mysql' if s in ('mysql', 'mariadb') else 'sqlite'

def _rows_text(cols, rows):
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(cols)
    for r in rows[:ROWS]:
        w.writerow(['' if v is None else v for v in r])
    return out.getvalue() + (f'(first {ROWS} rows only)\n' if len(rows) > ROWS else '')

def _without_password(url):
    """A database address with its password taken out, and the password: (address, password or None)."""
    from urllib.parse import unquote, urlsplit, urlunsplit
    try:
        u = urlsplit(url)
    except ValueError:
        return url, None
    if '://' not in url or u.password is None:
        return url, None
    host = u.hostname or ''
    host = f'[{host}]' if ':' in host else host
    netloc = (u.username or '') + '@' + host + (f':{u.port}' if u.port else '')
    return urlunsplit((u.scheme, netloc, u.path, u.query, u.fragment)), unquote(u.password)

def run_sql(where, query, timeout=30):
    """Run one read-only query; returns its rows as CSV text. Raises Unreadable for a query that would write."""
    q = safe_sql(query)
    if not q:
        raise Unreadable('I only read your data, never change it, so I did not run that')
    limited = f'SELECT * FROM ({q}) AS hive_q LIMIT {ROWS + 1}'
    kind = _db_kind(where)
    if kind == 'sqlite':
        path = where.removeprefix('sqlite:///').removeprefix('sqlite://')
        if not os.path.exists(path):
            raise Unreadable(f'there is no database file at {path}')
        con = sqlite3.connect(f'file:{urllib.parse.quote(os.path.abspath(path))}?mode=ro', uri=True, timeout=timeout)
        try:
            cur = con.execute(limited)
            return _rows_text([d[0] for d in cur.description], cur.fetchall())
        except sqlite3.Error as e:
            raise Unreadable(f'the query failed ({str(e)[:120]})') from None
        finally:
            con.close()
    if kind == 'postgres':
        try:
            import psycopg   # psycopg 3
            with psycopg.connect(where, connect_timeout=timeout) as con:
                con.read_only = True
                cur = con.execute(limited)
                return _rows_text([d.name for d in cur.description], cur.fetchall())
        except ImportError:
            pass
        except Exception as e:
            raise Unreadable(f'the query failed ({str(e)[:120]})') from None
        try:
            import psycopg2
            con = psycopg2.connect(where, connect_timeout=timeout)
            try:
                con.set_session(readonly=True)
                cur = con.cursor(); cur.execute(limited)
                return _rows_text([d[0] for d in cur.description], cur.fetchall())
            finally:
                con.close()
        except ImportError:
            pass
        except Exception as e:
            raise Unreadable(f'the query failed ({str(e)[:120]})') from None
        env = dict(os.environ, PGOPTIONS='-c default_transaction_read_only=on', PGCONNECT_TIMEOUT=str(timeout))
        where, password = _without_password(where)
        if password:   # never on the command line, where any user of the machine can read it (the audit, Nov 15)
            env['PGPASSWORD'] = password
        try:
            p = subprocess.run(['psql', where, '-X', '-q', '--csv', '-v', 'ON_ERROR_STOP=1', '-c', limited], env=env,
                               capture_output=True, text=True, timeout=timeout + 30)
        except FileNotFoundError:
            raise Unreadable("I can't read a Postgres database on this computer yet. Your engineer runs this once: "
                             "pip install \"hive-swarm[data] @ git+https://github.com/suryanshranjan/hive\"") from None
        if p.returncode:
            raise Unreadable(f'the query failed ({p.stderr.strip()[-160:]})')
        return p.stdout
    try:   # MySQL / MariaDB
        import pymysql
        u = urllib.parse.urlparse(where)
        con = pymysql.connect(host=u.hostname, port=u.port or 3306, user=urllib.parse.unquote(u.username or ''),
                              password=urllib.parse.unquote(u.password or ''), database=u.path.strip('/'),
                              connect_timeout=timeout, read_timeout=timeout)
        try:
            cur = con.cursor()
            cur.execute('SET SESSION TRANSACTION READ ONLY'); cur.execute('START TRANSACTION READ ONLY')
            cur.execute(limited)
            return _rows_text([d[0] for d in cur.description], cur.fetchall())
        finally:
            con.close()
    except ImportError:
        raise Unreadable("I can't read a MySQL database on this computer yet. Your engineer runs this once: "
                             "pip install \"hive-swarm[data] @ git+https://github.com/suryanshranjan/hive\"") from None
    except Exception as e:
        raise Unreadable(f'the query failed ({str(e)[:120]})') from None

def schema(where):
    """His database's tables and their columns, as text."""
    kind = _db_kind(where)
    q = {'sqlite': "SELECT name AS table_name, sql AS columns FROM sqlite_master WHERE type IN ('table','view') "
                   "AND name NOT LIKE 'sqlite_%' ORDER BY name",
         'postgres': "SELECT table_schema || '.' || table_name AS table_name, string_agg(column_name || ' ' || data_type, "
                     "', ' ORDER BY ordinal_position) AS columns FROM information_schema.columns WHERE table_schema NOT IN "
                     "('pg_catalog', 'information_schema') GROUP BY table_schema, table_name ORDER BY 1",
         'mysql': "SELECT table_name, GROUP_CONCAT(CONCAT(column_name, ' ', data_type) ORDER BY ordinal_position "
                  "SEPARATOR ', ') AS columns FROM information_schema.columns WHERE table_schema = DATABASE() "
                  "GROUP BY table_name ORDER BY table_name"}[kind]
    return run_sql(where, q)

def tables(where):
    rows = list(csv.reader(io.StringIO(schema(where))))[1:]
    return [r[0] for r in rows if r and r[0] and not r[0].startswith('(first ')]

def read(src):
    """What a source holds now, as text for the model (a database gives its tables and columns)."""
    kind, where = src['kind'], src['where']
    if kind == 'db':
        return 'Tables and columns:\n' + schema(where)
    if kind == 'url':
        return _text_of_web(*_fetch(where, src.get('headers')))
    if kind == 'file':
        if not os.path.exists(where):
            raise Unreadable(f'the file {os.path.basename(where)} is no longer on this computer')
        return _text_of_file(where)
    if kind == 'cmd':
        p = subprocess.run(where, shell=True, capture_output=True, text=True, timeout=120)
        if p.returncode:
            raise Unreadable(f'the command failed ({p.stderr.strip()[-120:]})')
        return p.stdout
    raise Unreadable('I do not know that kind of source')

def check(src):
    """(True, what Hive can now see, in one plain line) or (False, why not)."""
    try:
        if src['kind'] == 'db':
            ts = tables(src['where'])
            names = ', '.join(t.split('.')[-1] for t in ts[:8]) + (f' and {len(ts) - 8} more' if len(ts) > 8 else '')
            return True, (f"I can see {len(ts)} table{'s' if len(ts) != 1 else ''}: {names}." if ts else
                          "I'm in, but I see no tables yet.")
        text = read(src)
        title = re.match(r'Page title: (.*)', text)
        if title:
            return True, f'I can read it: "{title.group(1)[:80]}".'
        lines = [l for l in text.splitlines() if l.strip()]
        if src['kind'] == 'url' and text.lstrip()[:1] in ('{', '['):
            return True, 'I can read it: its numbers come back as data.'
        return True, f"I can read it: {len(lines)} line{'s' if len(lines) != 1 else ''}" + \
            (f', starting "{lines[0][:60]}".' if lines else '.')
    except Unreadable as e:
        return False, str(e)
    except Exception as e:
        return False, f"I couldn't read it ({str(e)[:100]})"

# ---- answering his questions from his data -------------------------------------------------------------------------

PICK = """A business owner asks his assistant a question about his own business: "{question}"

Here is the data he has given read-only access to:
{sources}

Write read-only SQL to answer it from his databases, if they hold the answer: plain SELECT (or WITH ... SELECT) queries,
one statement each, at most 3, using only the tables and columns listed, aggregated where you can (counts, sums, top
10) rather than raw rows. Before adding two money columns, check how they relate (does one already include the other?
compare a total with its parts in a query); Gate 108 added a bonus to a total that already held it. The same for taking
one off: a deduction may already be taken out of the amount paid (Gate 113 took Rs 900 off a total that was already net).
So whenever a table has an amount next to a bonus, deduction, fee or discount column, add one query that shows a few
rows with the amount, that column and the parts it is made of, so the answer can see which already includes which; the
stored amount paid is the answer unless those rows show otherwise.
Today is {today}. If
the other sources above already answer it, or nothing does, write none.
Reply with JSON only: {{"queries": [{{"source": "<source name>", "sql": "SELECT ..."}}]}}"""

ANSWER = """Answer his question from his own data. A business owner asked his assistant: "{question}"

What his data shows:
{data}

Answer him so he gets it in one glance on his phone: the answer first, in one short sentence with the number exactly as
the data gives it ("62 new subscribers signed up in October."), then at most one more short sentence, only if it
changes what he'd do. Everyday words; no technical words (no table, column or SQL), no hedging, no repeating his
question. Never add a part to a total that may already contain it, or take off a part already taken off: if the data
shows a total equals its parts (say amount = rate x count + bonus - deduction), the total is the answer. If the data does not answer it, say plainly what is
missing and what would answer it. Today is {today}.
Reply with JSON only: {{"answer": "...", "found": true or false}}"""

from . import explain as _explain
ANSWER = _explain.plain(ANSWER)

def _today():
    return time.strftime('%A %d %B %Y')

def previews(repo, sources=None):
    """[(source, text or None, problem or None)] for each source he has given."""
    out = []
    for s in sources if sources is not None else load(repo):
        try:
            out.append((s, read(s)[:PREVIEW], None))
        except Unreadable as e:
            out.append((s, None, str(e)))
        except Exception as e:
            out.append((s, None, str(e)[:100]))
    return out

def _source_named(srcs, said):
    """The database a query names: by its name, else loosely (the model wrote "db", the kind, for "dabba database",
    and every query was dropped: Gate 108 run 2, 5 of 10 questions), else the only database he gave."""
    dbs = [s for s in srcs if s['kind'] == 'db']
    said = str(said or '').strip().strip('[]').lower()
    exact = [s for s in dbs if s['name'].lower() == said]
    if exact:
        return exact[0]
    loose = [s for s in dbs if said and (said in s['name'].lower() or s['name'].lower() in said)]
    if len(loose) == 1:
        return loose[0]
    return dbs[0] if len(dbs) == 1 else None

def answer(repo, question):
    """His question answered from his data: {'answer', 'found', 'sources'} or None when he has given Hive none."""
    from . import explain
    srcs = load(repo)
    if not srcs:
        return None
    seen = previews(repo, srcs)
    listing = '\n\n'.join(f"[{s['name']}] ({s['kind']}): " + (t if t is not None else f'unreadable now: {p}')
                          for s, t, p in seen)
    data = [f"[{s['name']}]\n{t}" for s, t, _ in seen if t is not None and s['kind'] != 'db']
    if any(s['kind'] == 'db' and t is not None for s, t, _ in seen):
        got = {}
        for _ in range(2):   # Gate 108: one model call came back empty and he heard "couldn't read your data: ."
            got = explain.ask_json(PICK.format(question=question, sources=listing, today=_today())) or {}
            if got.get('queries'):
                break
        for q in (got.get('queries') or [])[:3]:
            s = _source_named(srcs, (q or {}).get('source')) if isinstance(q, dict) else None
            if not s or s['kind'] != 'db':
                continue
            try:
                data.append(f"[{s['name']}] {q.get('sql')}\n{run_sql(s['where'], q.get('sql', ''))}")
            except Unreadable as e:
                data.append(f"[{s['name']}] a query could not run: {e}")
    if not data:
        why = '; '.join(p for _, t, p in seen if p)
        return {'answer': (f"I couldn't read your data just now: {why}." if why else
                           "I couldn't work that out from your data just now. Ask me again in a moment, or put it "
                           "another way."), 'found': False, 'sources': []}
    got = explain.ask_json(ANSWER.format(question=question, data='\n\n'.join(data)[:40000], today=_today())) or {}
    return {'answer': (got.get('answer') or "I looked, but couldn't work that out from your data.").strip(),
            'found': bool(got.get('found')), 'sources': [s['name'] for s, t, _ in seen if t is not None]}

def summary(repo):
    """One plain line of what he has given Hive to read, for its replies; '' if nothing."""
    srcs = load(repo)
    if not srcs:
        return ''
    kinds = {'db': 'database', 'url': 'link', 'file': 'file', 'cmd': 'command'}
    return 'Data he has given you to read (read-only): ' + '; '.join(
        f"{s['name']} ({kinds.get(s['kind'], s['kind'])})" for s in srcs) + '.'

def for_plan(repo, limit=3000):
    """What his data holds, briefly, for planning a goal (what the product doesn't show may be in his data)."""
    parts = []
    for s, t, _ in previews(repo):
        if t:
            parts.append(f"From {s['name']}: {t[:limit // max(1, len(load(repo)))]}")
    return parts
