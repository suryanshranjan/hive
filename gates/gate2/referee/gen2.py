"""Gate 2 test generator: ~110 feature categories of SQLite behaviour. SQLite is the referee.
usage: gen2.py <out_dir> <first_seed> <per_category> [category ...]"""
import json, os, random, sqlite3, sys

def lit(v):
    if v is None: return 'NULL'
    if isinstance(v, str): return "'" + v.replace("'", "''") + "'"
    return repr(v)

def base_tables(rng):
    n = rng.randint(4, 9)
    t = [(i, rng.choice([None] + list(range(-5, 15))), rng.choice([None] + list(range(0, 8))),
          rng.choice([None, 'apple', 'Banana', 'cherry', 'date', 'Elder', 'fig', 'grape', 'kiwi', 'apple', 'Apple']),
          rng.choice([None, 0.5, 1.25, 2.0, 3.5, -1.5, 10.0, 2.75])) for i in range(1, n + 1)]
    m = rng.randint(3, 7)
    u = [(j, rng.choice([None] + list(range(1, n + 3))), rng.randint(-3, 9), rng.choice(['red', 'green', 'blue', None, 'Red']))
         for j in range(1, m + 1)]
    s = ['CREATE TABLE t (id INTEGER, a INTEGER, b INTEGER, s TEXT, x REAL)',
         'CREATE TABLE u (id INTEGER, t_id INTEGER, v INTEGER, name TEXT)',
         'INSERT INTO t VALUES ' + ', '.join('(' + ', '.join(lit(v) for v in r) + ')' for r in t),
         'INSERT INTO u VALUES ' + ', '.join('(' + ', '.join(lit(v) for v in r) + ')' for r in u)]
    return s

DATES = ['2024-01-15', '2024-02-29 13:45:00', '2023-12-31 23:59:59', '2000-01-01', '1999-07-04 08:30',
         '2024-03-10T12:00:00', '2021-06-15 06:07:08.250', '1970-01-01', '2038-01-19 03:14:07']
JSONS = ['{"a":1,"b":[1,2,3],"c":{"d":"x"}}', '[1,2,{"k":"v"},null,true]', '{"name":"kiwi","tags":["g","f"],"n":2.5}',
         '{"a":{"b":{"c":42}}}', '[]', '{}', '"str"', '3', '{"x":null,"y":false}', '[[1,2],[3,[4,5]]]']
PATHS = ['$', '$.a', '$.b', '$.b[1]', '$.c.d', '$[2]', '$[2].k', '$.tags[0]', '$.n', '$.a.b.c', '$[#-1]', '$.x', '$[1][1]', '$.missing']

def extra_tables(rng):
    d = [(i, rng.choice(DATES), rng.randint(-40, 40)) for i in range(1, rng.randint(3, 6) + 1)]
    j = [(i, rng.choice(JSONS)) for i in range(1, rng.randint(3, 6) + 1)]
    return ['CREATE TABLE d (id INTEGER, ts TEXT, n INTEGER)', 'CREATE TABLE j (id INTEGER, doc TEXT)',
            'INSERT INTO d VALUES ' + ', '.join('(' + ', '.join(lit(v) for v in r) + ')' for r in d),
            'INSERT INTO j VALUES ' + ', '.join('(' + ', '.join(lit(v) for v in r) + ')' for r in j)]

def N(rng): return rng.choice(['a', 'b', 'x', 'id', str(rng.randint(-5, 15)), rng.choice(['0.5', '1.25', '-2.75', '3.14159', '100', '-7']), 'NULL'])
def P(rng): return rng.choice(['b', 'id', 'x', str(rng.randint(0, 20)), rng.choice(['0.5', '2.25', '9', '0.1'])])  # mostly non-negative
def U(rng): return rng.choice(['0.5', '-0.5', '0', '1', '-1', '0.25', 'x / 20.0', 'b / 10.0'])  # in [-1, 1]
def S(rng): return rng.choice(['s', "'hello'", "'Hello World'", "'  pad  '", "'abc'", "''", 'NULL', "'a-b-c'", "'xXx'", 'name'])
def I(rng): return rng.choice([str(rng.randint(-3, 8)), 'b', 'id'])

def q_t(expr_fn):  # SELECT id, f(...) FROM t ORDER BY id
    return lambda rng: ([], f'SELECT id, {expr_fn(rng)} FROM t ORDER BY id', True)
def q_lit(expr_fn):
    return lambda rng: ([], f'SELECT {expr_fn(rng)}, {expr_fn(rng)}', True)
def mix(*fs):
    return lambda rng: rng.choice(fs)(rng)
def q_u(expr_fn):
    return lambda rng: ([], f'SELECT id, {expr_fn(rng)} FROM u ORDER BY id', True)
def q_d(expr_fn):
    return lambda rng: ([], f'SELECT id, {expr_fn(rng)} FROM d ORDER BY id', True)
def q_j(expr_fn):
    return lambda rng: ([], f'SELECT id, {expr_fn(rng)} FROM j ORDER BY id', True)

def modifier(rng):
    return rng.choice(["'+1 day'", "'-3 days'", "'+2 months'", "'-1 year'", "'+5 hours'", "'-30 minutes'", "'+45 seconds'",
                       "'start of month'", "'start of year'", "'start of day'", "'weekday 0'", "'weekday 3'", "'+1.5 days'"])

def win(rng, fn):
    part = rng.choice(['', 'PARTITION BY b ', 'PARTITION BY a % 2 '])
    order = rng.choice(['ORDER BY id', 'ORDER BY a, id', 'ORDER BY x DESC, id', 'ORDER BY s, id'])
    return f'SELECT id, {fn} OVER ({part}{order}) FROM t ORDER BY id'

C = {}
# ---- math
C['abs_sign'] = mix(q_t(lambda r: f'ABS({N(r)}), SIGN({N(r)})'), q_lit(lambda r: f'ABS({N(r)})'))
C['round_trunc'] = mix(q_t(lambda r: f'ROUND({N(r)}), ROUND({N(r)}, {r.randint(0, 3)})'), q_t(lambda r: f'TRUNC({N(r)})'))
C['ceil_floor'] = q_t(lambda r: f'CEIL({N(r)}), CEILING({N(r)}), FLOOR({N(r)})')
C['sqrt_exp_ln'] = q_t(lambda r: f'SQRT({P(r)}), EXP({r.choice(["b", "x", "1", "0.5"])}), LN({P(r)})')
C['log_funcs'] = q_t(lambda r: f'LOG({P(r)}), LOG10({P(r)}), LOG2({P(r)}), LOG({r.choice(["2", "3", "10"])}, {P(r)})')
C['pow_mod'] = q_t(lambda r: f'POW({N(r)}, {r.choice(["2", "0.5", "b", "3"])}), POWER({P(r)}, 2), MOD({N(r)}, {r.choice(["3", "b", "2.5", "-4"])})')
C['trig'] = q_t(lambda r: f'SIN({N(r)}), COS({N(r)}), TAN({U(r)}), ASIN({U(r)}), ACOS({U(r)}), ATAN({N(r)}), ATAN2({N(r)}, {N(r)}), PI(), DEGREES({N(r)}), RADIANS({N(r)})')
C['hyperbolic'] = q_t(lambda r: f'SINH({U(r)}), COSH({U(r)}), TANH({N(r)}), ASINH({N(r)}), ACOSH({r.choice(["1", "2", "b + 1", "10"])}), ATANH({U(r)})')
C['bitwise'] = q_t(lambda r: f'{I(r)} & {I(r)}, {I(r)} | {I(r)}, ~{I(r)}, {I(r)} << {r.randint(0, 4)}, {I(r)} >> {r.randint(0, 3)}')
# ---- strings
C['length_octet'] = q_t(lambda r: f'LENGTH({S(r)}), OCTET_LENGTH({S(r)}), LENGTH({N(r)})')
C['substr_more'] = q_t(lambda r: f'SUBSTR({S(r)}, {r.randint(-4, 6)}), SUBSTRING({S(r)}, {r.randint(-3, 5)}, {r.randint(-2, 4)})')
C['instr'] = q_t(lambda r: f"INSTR({S(r)}, {r.choice([chr(39)+'a'+chr(39), chr(39)+'l'+chr(39), chr(39)+'pp'+chr(39), chr(39)+chr(39), 'NULL'])})")
C['trim_chars'] = q_t(lambda r: f"TRIM({S(r)}), LTRIM({S(r)}, 'ah '), RTRIM({S(r)}, 'eo '), TRIM({S(r)}, 'x')")
C['replace_more'] = q_t(lambda r: f"REPLACE({S(r)}, {r.choice([chr(39)+'a'+chr(39), chr(39)+'l'+chr(39), chr(39)+'-'+chr(39)])}, {r.choice([chr(39)+'Z'+chr(39), chr(39)+chr(39), chr(39)+'++'+chr(39)])})")
C['concat'] = q_t(lambda r: f"CONCAT({S(r)}, {N(r)}, {S(r)}), CONCAT_WS('-', {S(r)}, {N(r)}, {S(r)})")
C['char_unicode'] = q_t(lambda r: f"CHAR({r.randint(65, 90)}, {r.randint(97, 122)}), UNICODE({S(r)})")
C['hex_unhex'] = q_t(lambda r: f"HEX({S(r)}), HEX({N(r)}), HEX(UNHEX('{r.choice(['4142', '616263', '00ff', 'zz', ''])}')), TYPEOF(UNHEX('{r.choice(['41', 'zz'])}'))")
C['quote'] = q_t(lambda r: f'QUOTE({S(r)}), QUOTE({N(r)})')
C['printf'] = q_t(lambda r: f"PRINTF('{r.choice(['%d', '%5d', '%-5d|', '%05d', '%x', '%o'])}', {I(r)}), PRINTF('{r.choice(['%s', '%10s', '%-8s|', '%.2s'])}', {S(r)}), PRINTF('{r.choice(['%f', '%.2f', '%8.3f', '%e', '%g'])}', {N(r)})")
C['format'] = q_t(lambda r: f"FORMAT('{r.choice(['%d-%s', '[%5.1f]', '%s%%', '%c'])}', {N(r)}, {S(r)})")
LIKE_PATS = ['a%', '%E%', '_i%', '%\\_%']   # outside the f-string: Python < 3.12 forbids backslashes in f-string expressions
C['like_escape'] = q_t(lambda r: f"s LIKE '{r.choice(LIKE_PATS)}' ESCAPE '\\', LIKE('{r.choice(['%a%', 'b%'])}', s)")
C['glob'] = q_t(lambda r: f"s GLOB '{r.choice(['a*', '*e', '[A-C]*', '?i*', '*[lp]*'])}', GLOB('{r.choice(['*a*', 'B*'])}', s)")
C['collate_nocase'] = mix(lambda r: ([], f"SELECT id FROM t WHERE s = '{r.choice(['apple', 'APPLE', 'banana'])}' COLLATE NOCASE ORDER BY id", True),
                          lambda r: ([], 'SELECT s, id FROM t ORDER BY s COLLATE NOCASE, id', True),
                          lambda r: ([], "SELECT 'abc' = 'ABC' COLLATE NOCASE, 'abc' < 'ABD' COLLATE NOCASE", True))
# ---- null / logic / types
C['iif_if'] = q_t(lambda r: f"IIF({N(r)} > {r.randint(0, 5)}, 'yes', 'no'), IF({N(r)} IS NULL, {N(r)}, -1)")
C['typeof'] = q_t(lambda r: f'TYPEOF({N(r)}), TYPEOF({S(r)}), TYPEOF({N(r)} / 2), TYPEOF({N(r)} * 1.0)')
C['cast_int_real'] = q_t(lambda r: f"CAST({r.choice(['x', 's', chr(39)+'12abc'+chr(39), chr(39)+'3.9'+chr(39), 'a'])} AS INTEGER), CAST({N(r)} AS REAL)")
C['cast_text_numeric'] = q_t(lambda r: f"CAST({N(r)} AS TEXT), CAST({r.choice([chr(39)+'1e3'+chr(39), chr(39)+'  42 '+chr(39), chr(39)+'0x10'+chr(39), 's', 'x'])} AS NUMERIC)")
C['is_distinct'] = q_t(lambda r: f'{N(r)} IS DISTINCT FROM {N(r)}, {N(r)} IS NOT DISTINCT FROM {N(r)}, {N(r)} IS {N(r)}')
C['true_false'] = q_t(lambda r: f'{N(r)} IS TRUE, {N(r)} IS NOT FALSE, TRUE + {N(r)}, FALSE')
C['minmax_scalar'] = q_t(lambda r: f'MIN({N(r)}, {N(r)}, {N(r)}), MAX({N(r)}, {N(r)})')
# ---- literals
C['hex_literal'] = q_lit(lambda r: f'0x{r.choice(["1F", "ff", "10", "7FFFFFFF", "0"])} + {r.randint(0, 9)}')
C['real_literal'] = q_lit(lambda r: r.choice(['1e3', '2.5e-2', '.5', '5.', '1E2 + 1', '-3.0e1']))
C['blob_literal'] = q_lit(lambda r: f"HEX(x'{r.choice(['41', '4142', '00', 'ff10'])}'), TYPEOF(x'41')")
# ---- aggregates
C['group_concat_sep'] = mix(lambda r: ([], f"SELECT b, GROUP_CONCAT(s, '{r.choice([';', ' | ', ''])}') FROM t GROUP BY b", False),
                            lambda r: ([], "SELECT STRING_AGG(name, ',') FROM u", True))
C['agg_distinct'] = lambda r: ([], f'SELECT SUM(DISTINCT {r.choice(["a", "b"])}), AVG(DISTINCT b), COUNT(DISTINCT s), TOTAL(DISTINCT a) FROM t', True)
C['agg_filter'] = lambda r: ([], f'SELECT COUNT(*) FILTER (WHERE a > {r.randint(0, 6)}), SUM(b) FILTER (WHERE s IS NOT NULL) FROM t', True)
C['median'] = lambda r: ([], f'SELECT MEDIAN({r.choice(["a", "b", "x"])}) FROM t', True)
C['percentile'] = lambda r: ([], f'SELECT PERCENTILE({r.choice(["a", "b", "x"])}, {r.choice([25, 50, 90, 100])}), PERCENTILE_CONT({r.choice(["a", "x"])}, {r.choice([0.25, 0.5, 0.9])}), PERCENTILE_DISC(b, 0.5) FROM t', True)
C['agg_order_by'] = lambda r: ([], f"SELECT GROUP_CONCAT(s, ',' ORDER BY {r.choice(['s', 'id DESC', 'a, id'])}) FROM t", True)
C['agg_empty_null'] = lambda r: ([], f'SELECT COUNT(*), SUM(a), AVG(a), MIN(a), MAX(s), TOTAL(a), GROUP_CONCAT(s) FROM t WHERE id > {r.randint(8, 20)}', True)
# ---- dates (tables d)
C['date_basic'] = mix(q_lit(lambda r: f"DATE('{r.choice(DATES)}')"), q_d(lambda r: 'DATE(ts)'))
C['time_basic'] = mix(q_lit(lambda r: f"TIME('{r.choice(DATES)}')"), q_d(lambda r: 'TIME(ts)'))
C['datetime_basic'] = mix(q_lit(lambda r: f"DATETIME('{r.choice(DATES)}')"), q_d(lambda r: 'DATETIME(ts)'))
C['date_modifiers'] = q_d(lambda r: f"DATETIME(ts, {modifier(r)}), DATE(ts, {modifier(r)}, {modifier(r)})")
C['date_n_days'] = q_d(lambda r: f"DATE(ts, n || ' days'), DATE(ts, '+' || n || ' months')")
C['julianday'] = q_d(lambda r: f"ROUND(JULIANDAY(ts), 4), JULIANDAY('{r.choice(DATES)}') - JULIANDAY(ts)")
C['unixepoch'] = q_d(lambda r: f"UNIXEPOCH(ts), DATETIME({r.choice(['0', '1700000000', '86400', 'n * 100000'])}, 'unixepoch')")
C['strftime'] = q_d(lambda r: f"STRFTIME('{r.choice(['%Y', '%m/%d/%Y', '%H:%M', '%j', '%w', '%W', '%s', '%Y-%m-%dT%H:%M:%S', '%d.%m'])}', ts)")
C['timediff'] = q_d(lambda r: f"TIMEDIFF(ts, '{r.choice(DATES)}')")
C['date_compare'] = lambda r: ([], f"SELECT id FROM d WHERE ts {r.choice(['<', '>=', '>'])} '{r.choice(DATES)}' ORDER BY id", True)
# ---- json (table j)
JSON_VALID_DOCS = ['{', '[1,]', '{"a":1}', 'nul', '12']
C['json_valid'] = q_j(lambda r: f"JSON_VALID(doc), JSON_VALID('{r.choice(JSON_VALID_DOCS)}')")
C['json_minify'] = q_j(lambda r: 'JSON(doc), JSON_QUOTE(doc)')
C['json_build'] = mix(q_t(lambda r: f"JSON_ARRAY(id, {N(r)}, {S(r)}), JSON_OBJECT('k', {N(r)}, 's', {S(r)})"),
                      q_lit(lambda r: f"JSON_ARRAY({r.randint(1, 5)}, 'x', NULL, JSON('[1,2]'))"))
C['json_extract'] = q_j(lambda r: f"JSON_EXTRACT(doc, '{r.choice(PATHS)}'), JSON_EXTRACT(doc, '{r.choice(PATHS)}', '{r.choice(PATHS)}')")
C['json_arrows'] = q_j(lambda r: f"doc -> '{r.choice(PATHS)}', doc ->> '{r.choice(PATHS)}'")
C['json_type'] = q_j(lambda r: f"JSON_TYPE(doc), JSON_TYPE(doc, '{r.choice(PATHS)}')")
C['json_array_length'] = q_j(lambda r: f"JSON_ARRAY_LENGTH(doc), JSON_ARRAY_LENGTH(doc, '{r.choice(PATHS)}')")
C['json_modify'] = q_j(lambda r: f"{r.choice(['JSON_INSERT', 'JSON_REPLACE', 'JSON_SET'])}(doc, '{r.choice(PATHS[1:])}', {r.choice(['99', chr(39)+'z'+chr(39), 'NULL', 'JSON(' + chr(39) + '[7]' + chr(39) + ')'])})")
C['json_remove'] = q_j(lambda r: f"JSON_REMOVE(doc, '{r.choice(PATHS[1:])}')")
JSON_PATCHES = ['{"a":null}', '{"z":1}', '{"c":{"e":2}}', '[9]']
C['json_patch'] = q_j(lambda r: f"JSON_PATCH(doc, '{r.choice(JSON_PATCHES)}')")
C['json_group'] = mix(lambda r: ([], 'SELECT JSON_GROUP_ARRAY(s) FROM t', True), lambda r: ([], 'SELECT JSON_GROUP_OBJECT(id, a) FROM t', True),
                      lambda r: ([], 'SELECT b, JSON_GROUP_ARRAY(id) FROM t GROUP BY b', False))
JSON_BAD_DOCS = ['{', '[1,]', '{"a":1}', 'nul', '[1,2']
C['json_error_position'] = q_lit(lambda r: f"JSON_ERROR_POSITION('{r.choice(JSON_BAD_DOCS)}')")
# ---- windows
C['window_row_number'] = lambda r: ([], win(r, 'ROW_NUMBER()'), True)
C['window_rank'] = lambda r: ([], win(r, r.choice(['RANK()', 'DENSE_RANK()'])), True)
C['window_percent'] = lambda r: ([], win(r, r.choice(['PERCENT_RANK()', 'CUME_DIST()'])), True)
C['window_ntile'] = lambda r: ([], win(r, f'NTILE({r.randint(1, 4)})'), True)
C['window_lag_lead'] = lambda r: ([], win(r, f'{r.choice(["LAG", "LEAD"])}({r.choice(["a", "s", "id"])}{r.choice(["", ", 2", ", 1, -1"])})'), True)
C['window_first_last'] = lambda r: ([], win(r, f'{r.choice(["FIRST_VALUE", "LAST_VALUE"])}({r.choice(["a", "s"])})'), True)
C['window_nth_value'] = lambda r: ([], win(r, f'NTH_VALUE({r.choice(["a", "s"])}, {r.randint(1, 3)})'), True)
C['window_agg'] = lambda r: ([], win(r, f'{r.choice(["SUM", "COUNT", "MAX", "AVG"])}({r.choice(["a", "b"])})'), True)
C['window_frames'] = lambda r: ([], f"SELECT id, SUM(a) OVER (ORDER BY id ROWS BETWEEN {r.choice(['1 PRECEDING', 'UNBOUNDED PRECEDING', '2 PRECEDING'])} AND {r.choice(['CURRENT ROW', '1 FOLLOWING', 'UNBOUNDED FOLLOWING'])}) FROM t ORDER BY id", True)
C['window_named'] = lambda r: ([], 'SELECT id, ROW_NUMBER() OVER w, SUM(b) OVER w FROM t WINDOW w AS (PARTITION BY b ORDER BY id) ORDER BY id', True)
C['window_empty_over'] = lambda r: ([], f'SELECT id, {r.choice(["COUNT(*)", "SUM(a)", "MAX(x)"])} OVER () FROM t ORDER BY id', True)
# ---- set operations
C['union'] = lambda r: ([], f'SELECT b FROM t UNION SELECT v FROM u', False)
C['union_all'] = lambda r: ([], f'SELECT b FROM t WHERE id < {r.randint(3, 8)} UNION ALL SELECT v FROM u', False)
C['intersect'] = lambda r: ([], 'SELECT b FROM t INTERSECT SELECT v FROM u', False)
C['except'] = lambda r: ([], f'SELECT {r.choice(["b", "a"])} FROM t EXCEPT SELECT v FROM u', False)
C['compound_order_limit'] = lambda r: ([], f'SELECT id, b FROM t UNION SELECT id, v FROM u ORDER BY 1, 2 LIMIT {r.randint(2, 6)}', True)
# ---- CTE / subquery extras / misc select
C['cte_basic'] = lambda r: ([], f'WITH big AS (SELECT * FROM t WHERE a > {r.randint(0, 6)}) SELECT id, a FROM big ORDER BY id', True)
C['cte_multiple'] = lambda r: ([], 'WITH x1 AS (SELECT b, COUNT(*) AS c FROM t GROUP BY b), x2 AS (SELECT * FROM x1 WHERE c > 1) SELECT b, c FROM x2', False)
C['cte_recursive'] = lambda r: ([], f'WITH RECURSIVE cnt(n) AS (SELECT 1 UNION ALL SELECT n + {r.randint(1, 3)} FROM cnt WHERE n < {r.randint(5, 30)}) SELECT n FROM cnt', False)
C['exists'] = lambda r: ([], f'SELECT id FROM t WHERE {r.choice(["", "NOT "])}EXISTS (SELECT 1 FROM u WHERE u.t_id = t.id AND u.v > {r.randint(-2, 6)}) ORDER BY id', True)
C['row_values'] = lambda r: ([], f'SELECT id FROM t WHERE (a, b) {r.choice(["=", "<", ">="])} ({r.randint(0, 6)}, {r.randint(0, 6)}) ORDER BY id', True)
C['values_clause'] = lambda r: ([], f'VALUES ({r.randint(1, 9)}, \'a\'), ({r.randint(1, 9)}, NULL), (3, \'c\')', True)
C['natural_using'] = lambda r: ([], r.choice(['SELECT * FROM t JOIN u USING (id) ORDER BY id', 'SELECT id, a, v FROM t NATURAL JOIN u ORDER BY id']), True)
C['right_full_join'] = lambda r: ([], r.choice(['SELECT t.id, u.id FROM t RIGHT JOIN u ON t.id = u.t_id', 'SELECT t.id, u.id FROM t FULL OUTER JOIN u ON t.id = u.t_id']), False)
C['three_way_join'] = lambda r: ([], 'SELECT t.id, u.id, w.id FROM t JOIN u ON t.id = u.t_id JOIN u AS w ON w.v = u.v', False)
C['order_nulls'] = lambda r: ([], f'SELECT id, a FROM t ORDER BY a {r.choice(["ASC", "DESC"])} NULLS {r.choice(["FIRST", "LAST"])}, id', True)
C['limit_expr'] = lambda r: ([], f'SELECT id FROM t ORDER BY id LIMIT {r.randint(1, 3)} + 1 OFFSET (SELECT COUNT(*) FROM u) % 3', True)
C['select_star_qualified'] = lambda r: ([], 'SELECT u.*, t.s FROM t JOIN u ON t.id = u.t_id', False)
C['case_nested'] = q_t(lambda r: f"CASE WHEN a IS NULL THEN 'n' WHEN a > {r.randint(0, 8)} THEN CASE WHEN b > 3 THEN 'hb' ELSE 'hl' END ELSE 'l' END")
C['group_by_expr_alias'] = lambda r: ([], 'SELECT a % 3 AS k, COUNT(*) FROM t GROUP BY k HAVING k IS NOT NULL', False)
C['scalar_subquery_order'] = lambda r: ([], 'SELECT id, (SELECT MAX(v) FROM u WHERE u.t_id = t.id) AS mv FROM t ORDER BY mv, id', True)
# ---- DML / DDL (setup statements then a query)
def dml(stmts, query, ordered=False):
    return lambda r: (stmts(r), query, ordered)
C['insert_columns'] = dml(lambda r: [f"INSERT INTO t (id, s) VALUES ({r.randint(20, 30)}, 'new')", 'INSERT INTO u (name, id) VALUES (\'z\', 99)'], 'SELECT * FROM t ORDER BY id', True)
C['insert_select'] = dml(lambda r: [f'INSERT INTO u (id, t_id, v) SELECT id + 100, id, a FROM t WHERE a > {r.randint(0, 6)}'], 'SELECT * FROM u ORDER BY id', True)
C['default_values'] = dml(lambda r: ["CREATE TABLE w (id INTEGER, k TEXT DEFAULT 'dflt', n INTEGER DEFAULT 7)", "INSERT INTO w (id) VALUES (1)", "INSERT INTO w DEFAULT VALUES", f"INSERT INTO w (id, n) VALUES (3, {r.randint(0, 9)})"], 'SELECT * FROM w', False)
C['integer_primary_key'] = dml(lambda r: ['CREATE TABLE p (pk INTEGER PRIMARY KEY, v TEXT)', "INSERT INTO p (v) VALUES ('a')", "INSERT INTO p (v) VALUES ('b')", f"INSERT INTO p VALUES ({r.randint(5, 20)}, 'c')", "INSERT INTO p (v) VALUES ('d')"], 'SELECT pk, v, rowid FROM p ORDER BY pk', True)
C['insert_or_replace'] = dml(lambda r: ['CREATE TABLE k (id INTEGER PRIMARY KEY, v TEXT)', "INSERT INTO k VALUES (1, 'a'), (2, 'b')", f"INSERT OR REPLACE INTO k VALUES ({r.randint(1, 3)}, 'z')", "REPLACE INTO k VALUES (2, 'y')"], 'SELECT * FROM k ORDER BY id', True)
C['insert_or_ignore'] = dml(lambda r: ['CREATE TABLE k (id INTEGER PRIMARY KEY, v TEXT UNIQUE)', "INSERT INTO k VALUES (1, 'a'), (2, 'b')", f"INSERT OR IGNORE INTO k VALUES ({r.randint(1, 4)}, '{r.choice(['a', 'c', 'b'])}')"], 'SELECT * FROM k ORDER BY id', True)
C['upsert'] = dml(lambda r: ['CREATE TABLE k (id INTEGER PRIMARY KEY, n INTEGER)', 'INSERT INTO k VALUES (1, 10), (2, 20)', f'INSERT INTO k VALUES ({r.randint(1, 3)}, 5) ON CONFLICT(id) DO UPDATE SET n = n + excluded.n', 'INSERT INTO k VALUES (1, 1) ON CONFLICT DO NOTHING'], 'SELECT * FROM k ORDER BY id', True)
C['returning'] = lambda r: (['CREATE TABLE k (id INTEGER PRIMARY KEY, n INTEGER)'], f'INSERT INTO k (n) VALUES ({r.randint(1, 9)}), ({r.randint(1, 9)}) RETURNING id, n * 2', True)
C['update_from'] = dml(lambda r: [f'UPDATE t SET a = u.v FROM u WHERE u.t_id = t.id AND u.v > {r.randint(-2, 5)}'], 'SELECT id, a FROM t ORDER BY id', True)
C['update_multi_set'] = dml(lambda r: [f'UPDATE t SET (a, b) = (b, a) WHERE id <= {r.randint(1, 5)}', "UPDATE t SET s = s || '!', x = x * 2 WHERE b > 3"], 'SELECT id, a, b, s, x FROM t ORDER BY id', True)
C['create_table_as'] = dml(lambda r: [f'CREATE TABLE c2 AS SELECT id, a * 2 AS dbl FROM t WHERE id > {r.randint(1, 4)}'], 'SELECT * FROM c2 ORDER BY id', True)
C['drop_table'] = dml(lambda r: ['CREATE TABLE tmp (q)', 'DROP TABLE tmp', 'CREATE TABLE tmp (q, r)', f'INSERT INTO tmp VALUES ({r.randint(1, 9)}, 2)', 'DROP TABLE IF EXISTS nothere'], 'SELECT * FROM tmp', True)
C['alter_table'] = dml(lambda r: ["ALTER TABLE u ADD COLUMN extra TEXT DEFAULT 'e'", 'ALTER TABLE u RENAME COLUMN v TO vv', f'UPDATE u SET extra = name WHERE vv > {r.randint(0, 5)}'], 'SELECT id, vv, extra FROM u ORDER BY id', True)
C['alter_rename_table'] = dml(lambda r: ['ALTER TABLE u RENAME TO uu'], f'SELECT COUNT(*), MAX(v) FROM uu', True)
C['views'] = dml(lambda r: [f'CREATE VIEW vt AS SELECT id, a + b AS ab FROM t WHERE id > {r.randint(1, 4)}'], 'SELECT * FROM vt WHERE ab IS NOT NULL ORDER BY id', True)
C['delete_all_count'] = dml(lambda r: [f'DELETE FROM u WHERE t_id IN (SELECT id FROM t WHERE a > {r.randint(0, 8)})'], 'SELECT COUNT(*), SUM(v) FROM u', True)
C['transactions'] = dml(lambda r: ['BEGIN', 'DELETE FROM u', 'ROLLBACK', 'BEGIN TRANSACTION', f'DELETE FROM u WHERE id > {r.randint(1, 4)}', 'COMMIT'], 'SELECT id FROM u ORDER BY id', True)
C['create_index_noop'] = dml(lambda r: ['CREATE INDEX ix ON t (a)', 'CREATE UNIQUE INDEX IF NOT EXISTS ix2 ON u (id)', 'DROP INDEX ix'], 'SELECT id FROM t WHERE a > 2 ORDER BY id', True)
C['check_not_null'] = dml(lambda r: ['CREATE TABLE cn (id INTEGER NOT NULL, v INTEGER CHECK (v > 0))', 'INSERT INTO cn VALUES (1, 5)', f'INSERT OR IGNORE INTO cn VALUES (NULL, {r.randint(1, 3)})', 'INSERT OR IGNORE INTO cn VALUES (3, -1)'], 'SELECT * FROM cn', True)
C['comments_quoted'] = lambda r: ([], r.choice(['SELECT "id", [a] FROM t -- trailing comment\n ORDER BY id', 'SELECT /* c */ `id` FROM t ORDER BY id']), True)

CATS = sorted(C)

def make(cat, seed):
    rng = random.Random(seed)
    setup = base_tables(rng) + extra_tables(rng)
    extra, q, ordered = C[cat](rng)
    setup = setup + extra
    con = sqlite3.connect(':memory:', isolation_level=None)
    try:
        for s in setup: con.execute(s)
        rows = [list(r) for r in con.execute(q).fetchall()]
    except sqlite3.Error:
        return None
    rows = [[(v.hex() if isinstance(v, bytes) else v) for v in r] for r in rows]
    return dict(category=cat, setup=setup, query=q, expected=rows, ordered=ordered)

if __name__ == '__main__':
    out, first, per = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    cats = sys.argv[4:] or CATS
    os.makedirs(out, exist_ok=True)
    n = 0; weak = []
    for cat in cats:
        made = 0; seed = first + CATS.index(cat) * 100000; tries = 0
        while made < per and tries < per * 40:
            t = make(cat, seed); seed += 1; tries += 1
            if t is None: continue
            t['id'] = f'{cat}_{made:03d}'
            json.dump(t, open(os.path.join(out, t['id'] + '.json'), 'w'))
            made += 1; n += 1
        if made < per: weak.append((cat, made))
    print(n, 'tests,', len(cats), 'categories in', out, '; short categories:', weak)
