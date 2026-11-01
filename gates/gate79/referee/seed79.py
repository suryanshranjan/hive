"""Gate 79: build the job: sqlglot 30.27.0 (MIT) with the 12 bugs pick79.py planted (seed 79), described to the builders
only as users' bug reports (what they ran, what they got, what they expected), never by file or function.
usage: python3 seed79.py <sqlglot_src> <pick.json> <seed_dir> <hidden.json> <goal.md>
Every fast-suite test method that fails with the bugs is removed from the seed (the hidden suite: those methods, run from
the original test files). Each report's "got" and "expected" are computed by running it on the seed and on the original."""
import ast, json, os, shutil, subprocess, sys
import xml.etree.ElementTree as ET
SRC, PICK, SEED, HIDDEN, GOAL = sys.argv[1:6]
FAST = ['--ignore=tests/test_parser.py', '--ignore=tests/test_executor.py', '--ignore=tests/test_optimizer.py']
TEST_CMD = 'python3 -m pytest -q -p no:cacheprovider tests ' + ' '.join(FAST) + ' --junitxml=.hive/junit.xml'
DATES = "SELECT id, mnth FROM t CROSS JOIN UNNEST(GENERATE_DATE_ARRAY(start_month, DATE_TRUNC(CURRENT_DATE, MONTH), INTERVAL '1' MONTH)) AS mnth"
REPORTS = [   # (what the user did, in words; the Python they ran)
    ("Transpiling a BigQuery query that unnests a monthly GENERATE_DATE_ARRAY to Snowflake",
     f'sqlglot.transpile("{DATES}", read="bigquery", write="snowflake")[0]'),
    ("Parsing a quoted BigQuery table name that includes INFORMATION_SCHEMA, the table's own name part",
     'sqlglot.parse_one("`c.db.INFORMATION_SCHEMA.X`", read="bigquery", into=sqlglot.exp.Table).this.name'),
    ("Transpiling a star next to another column to Exasol",
     'sqlglot.transpile("SELECT *, 1 FROM TEST", write="exasol")[0]'),
    ("Transpiling JSON_EXTRACT_SCALAR to T-SQL",
     'sqlglot.transpile("JSON_EXTRACT_SCALAR(x, \'$.y\')", write="tsql")[0]'),
    ("Transpiling BigQuery LAST_DAY to Postgres",
     'sqlglot.transpile("SELECT LAST_DAY(CAST(\'2008-11-25\' AS DATE), MONTH)", read="bigquery", write="postgres")[0]'),
    ("Round-tripping a DuckDB BIT_OR over a DECIMAL(10, 2)",
     'sqlglot.transpile("SELECT BIT_OR(CAST(val AS DECIMAL(10, 2))) FROM t", read="duckdb", write="duckdb")[0]'),
    ("Round-tripping an Exasol DATE_TRUNC on a timestamp literal",
     'sqlglot.transpile("SELECT DATE_TRUNC(\'MM\', TIMESTAMP \'2006-12-31T23:59:59\') DATE_TRUNC", read="exasol", write="exasol")[0]'),
    ("Transpiling Snowflake TO_TIMESTAMP with a scale to BigQuery",
     'sqlglot.transpile("SELECT TO_TIMESTAMP(16599817290000, 4)", read="snowflake", write="bigquery")[0]'),
    ("Transpiling MySQL STR_TO_DATE to Presto",
     'sqlglot.transpile("STR_TO_DATE(x, \'%Y-%m-%d\')", read="mysql", write="presto")[0]'),
    ("Round-tripping BigQuery FORMAT_DATE",
     'sqlglot.transpile("SELECT FORMAT_DATE(\'%Y%m%d\', \'2023-12-25\')", read="bigquery", write="bigquery")[0]'),
    ("Transpiling BigQuery DATETIME_DIFF in weeks to Presto",
     'sqlglot.transpile("SELECT DATETIME_DIFF(DATETIME \'2017-10-15 00:00:00\', DATETIME \'2017-10-14 00:00:00\', WEEK)", read="bigquery", write="presto")[0]'),
]

def failing(root):
    j = os.path.abspath(os.path.join(root, '.junit_tmp.xml'))
    subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', 'tests', *FAST, f'--junitxml={j}'], cwd=root, capture_output=True)
    bad, n = set(), 0
    for tc in ET.parse(j).iter('testcase'):
        n += 1
        if tc.find('failure') is not None or tc.find('error') is not None: bad.add((tc.get('classname'), tc.get('name')))
    os.remove(j); return bad, n

def run(root, code):
    r = subprocess.run([sys.executable, '-c', f'import sqlglot\ntry:\n    print(repr({code}))\nexcept Exception as e:\n    print("raises " + type(e).__name__ + ": " + str(e)[:200])'],
                       cwd=root, capture_output=True, text=True, env=dict(os.environ, PYTHONPATH=root))
    return r.stdout.strip() or r.stderr.strip()[-300:]

shutil.rmtree(SEED, ignore_errors=True)
shutil.copytree(SRC, SEED, ignore=shutil.ignore_patterns('.git', '__pycache__', 'junit*.xml'))
chosen = json.load(open(PICK))['chosen']
for c in sorted(chosen, key=lambda c: (c['file'], -c['a'])):
    p = os.path.join(SEED, c['file']); t = open(p).read(); assert t[c['a']:c['b']] == c['old'], c
    open(p, 'w').write(t[:c['a']] + c['new'] + t[c['b']:])
reports = []
for what, code in REPORTS:
    got, want = run(SEED, code), run(SRC, code)
    assert got != want, f'report does not show a bug: {what}'
    reports.append(dict(what=what, code=code, got=got, want=want))
bad, n = failing(SEED)
print(f'{len(bad)} of {n} fast-suite test methods fail with the 12 bugs')
by = {}
for cls, name in bad:
    mod = cls.rsplit('.', 1)[0]; by.setdefault(mod.replace('.', '/') + '.py', []).append((cls.rsplit('.', 1)[1], name))
for f, items in by.items():
    p = os.path.join(SEED, f); text = open(p).read(); L = text.split('\n'); cut = []
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.ClassDef):
            for m in node.body:
                if isinstance(m, ast.FunctionDef) and (node.name, m.name) in items:
                    cut.append((min([m.lineno] + [d.lineno for d in m.decorator_list]), m.end_lineno))
    for s, e in sorted(cut, reverse=True): del L[s - 1:e]
    open(p, 'w').write('\n'.join(L))
left, n2 = failing(SEED); assert not left, sorted(left)[:5]
print(f'visible: {n2} test methods, all pass')
areas = {f'bug{k:02d}': [f'tests/test_bug{k:02d}*'] for k in range(1, len(reports) + 1)}
os.makedirs(os.path.join(SEED, '.hive'), exist_ok=True)
json.dump({'test_cmd': TEST_CMD, 'branch': 'main', 'junit': '.hive/junit.xml', 'areas': areas}, open(os.path.join(SEED, '.hive', 'config.json'), 'w'), indent=1)
open(os.path.join(SEED, '.gitignore'), 'a').write('\n.hive/junit.xml\n.hive/guard_cache/\n__pycache__/\n')
for c in (['init', '-q', '-b', 'main'], ['add', '-A'], ['-c', 'user.name=referee', '-c', 'user.email=referee@local', 'commit', '-qm', 'sqlglot 30.27.0']):
    subprocess.run(['git', *c], cwd=SEED, check=True)
goal = ("This repository is sqlglot, a SQL parser, transpiler and optimizer in pure Python (about 85,000 lines). Users "
        "reported the bugs below. Each report shows one case; the same cause may break other cases and other dialects too, "
        "and a report may have more than one cause. For each, find the cause in the code and fix it so sqlglot behaves "
        "correctly in every case, not only the one reported, and keep every existing test passing. Put a test for bug k in "
        "`tests/test_bugk.py` (for example `tests/test_bug03.py`), and claim bug k as area `bugk`. Do not install, download or "
        "look at any other copy of sqlglot: work only from this repository.\n\n")
for k, r in enumerate(reports, 1):
    goal += f"### Bug {k:02d}: {r['what']}\n```python\n>>> {r['code']}\n{r['got']}\n```\nExpected:\n```python\n{r['want']}\n```\n\n"
open(GOAL, 'w').write(goal)
json.dump(dict(hidden=sorted(f'{c}::{m}' for c, m in bad), bugs=[{k: c[k] for k in ('file', 'name', 'kind', 'line', 'old', 'new')} for c in chosen],
               reports=reports), open(HIDDEN, 'w'), indent=1)
