This repository is sqlglot, a SQL parser, transpiler and optimizer in pure Python (about 85,000 lines). Users reported the bugs below. Each report shows one case; the same cause may break other cases and other dialects too, and a report may have more than one cause. For each, find the cause in the code and fix it so sqlglot behaves correctly in every case, not only the one reported, and keep every existing test passing. Put a test for bug k in `tests/test_bugk.py` (for example `tests/test_bug03.py`), and claim bug k as area `bugk`. Do not install, download or look at any other copy of sqlglot: work only from this repository.

### Bug 01: Transpiling a BigQuery query that unnests a monthly GENERATE_DATE_ARRAY to Snowflake
```python
>>> sqlglot.transpile("SELECT id, mnth FROM t CROSS JOIN UNNEST(GENERATE_DATE_ARRAY(start_month, DATE_TRUNC(CURRENT_DATE, MONTH), INTERVAL '1' MONTH)) AS mnth", read="bigquery", write="snowflake")[0]
"SELECT id, mnth FROM t CROSS JOIN TABLE(FLATTEN(INPUT => GENERATE_DATE_ARRAY(start_month, DATE_TRUNC('MONTH', CURRENT_DATE), INTERVAL '1 MONTH'))) AS _t0(seq, key, path, index, mnth, this)"
```
Expected:
```python
"SELECT id, DATEADD(MONTH, CAST(mnth AS INT), CAST(start_month AS DATE)) AS mnth FROM t, LATERAL FLATTEN(INPUT => ARRAY_GENERATE_RANGE(0, DATEDIFF(MONTH, start_month, DATE_TRUNC('MONTH', CURRENT_DATE)) + 1)) AS _t0(seq, key, path, index, mnth, this)"
```

### Bug 02: Parsing a quoted BigQuery table name that includes INFORMATION_SCHEMA, the table's own name part
```python
>>> sqlglot.parse_one("`c.db.INFORMATION_SCHEMA.X`", read="bigquery", into=sqlglot.exp.Table).this.name
'c.db.INFORMATION_SCHEMA.X'
```
Expected:
```python
'INFORMATION_SCHEMA.X'
```

### Bug 03: Transpiling a star next to another column to Exasol
```python
>>> sqlglot.transpile("SELECT *, 1 FROM TEST", write="exasol")[0]
'SELECT *, 1 FROM TEST'
```
Expected:
```python
'SELECT TEST.*, 1 FROM TEST'
```

### Bug 04: Transpiling JSON_EXTRACT_SCALAR to T-SQL
```python
>>> sqlglot.transpile("JSON_EXTRACT_SCALAR(x, '$.y')", write="tsql")[0]
"JSON_VALUE(x, '$.y')"
```
Expected:
```python
"ISNULL(JSON_QUERY(x, '$.y'), JSON_VALUE(x, '$.y'))"
```

### Bug 05: Transpiling BigQuery LAST_DAY to Postgres
```python
>>> sqlglot.transpile("SELECT LAST_DAY(CAST('2008-11-25' AS DATE), MONTH)", read="bigquery", write="postgres")[0]
"SELECT CAST(DATE_TRUNC('MONTH', CAST('2008-11-25' AS DATE)) + (INTERVAL '1 MONTH' * 1) - (INTERVAL '1 DAY' * 1) AS DATE)"
```
Expected:
```python
"SELECT CAST(DATE_TRUNC('MONTH', CAST('2008-11-25' AS DATE)) + INTERVAL '1 MONTH' - INTERVAL '1 DAY' AS DATE)"
```

### Bug 06: Round-tripping a DuckDB BIT_OR over a DECIMAL(10, 2)
```python
>>> sqlglot.transpile("SELECT BIT_OR(CAST(val AS DECIMAL(10, 2))) FROM t", read="duckdb", write="duckdb")[0]
'SELECT BIT_OR(CAST(CAST(val AS DECIMAL(18, 3)) AS INT)) FROM t'
```
Expected:
```python
'SELECT BIT_OR(CAST(CAST(val AS DECIMAL(10, 2)) AS INT)) FROM t'
```

### Bug 07: Round-tripping an Exasol DATE_TRUNC on a timestamp literal
```python
>>> sqlglot.transpile("SELECT DATE_TRUNC('MM', TIMESTAMP '2006-12-31T23:59:59') DATE_TRUNC", read="exasol", write="exasol")[0]
"SELECT DATE_TRUNC('MM', TIMESTAMP '2006-12-31T23:59:59') AS DATE_TRUNC"
```
Expected:
```python
"SELECT DATE_TRUNC('MM', TIMESTAMP '2006-12-31 23:59:59') AS DATE_TRUNC"
```

### Bug 08: Transpiling Snowflake TO_TIMESTAMP with a scale to BigQuery
```python
>>> sqlglot.transpile("SELECT TO_TIMESTAMP(16599817290000, 4)", read="snowflake", write="bigquery")[0]
'SELECT TIMESTAMP_SECONDS(CAST(16599817290000 / POWER(11, 4) AS INT64))'
```
Expected:
```python
'SELECT TIMESTAMP_SECONDS(CAST(16599817290000 / POWER(10, 4) AS INT64))'
```

### Bug 09: Transpiling MySQL STR_TO_DATE to Presto
```python
>>> sqlglot.transpile("STR_TO_DATE(x, '%Y-%m-%d')", read="mysql", write="presto")[0]
"CAST(DATE_PARSE('%Y-%m-%d', '%Y-%m-%d') AS DATE)"
```
Expected:
```python
"CAST(DATE_PARSE(x, '%Y-%m-%d') AS DATE)"
```

### Bug 10: Round-tripping BigQuery FORMAT_DATE
```python
>>> sqlglot.transpile("SELECT FORMAT_DATE('%Y%m%d', '2023-12-25')", read="bigquery", write="bigquery")[0]
"SELECT FORMAT_DATE('2023-12-25', '2023-12-25')"
```
Expected:
```python
"SELECT FORMAT_DATE('%Y%m%d', '2023-12-25')"
```

### Bug 11: Transpiling BigQuery DATETIME_DIFF in weeks to Presto
```python
>>> sqlglot.transpile("SELECT DATETIME_DIFF(DATETIME '2017-10-15 00:00:00', DATETIME '2017-10-14 00:00:00', WEEK)", read="bigquery", write="presto")[0]
"SELECT DATE_DIFF('WEEK', DATE_TRUNC('WEEK', CAST('2017-10-14 00:00:00' AS TIMESTAMP) + INTERVAL '-6' DAY), DATE_TRUNC('WEEK', CAST('2017-10-15 00:00:00' AS TIMESTAMP) + INTERVAL '-6' DAY))"
```
Expected:
```python
"SELECT DATE_DIFF('WEEK', DATE_TRUNC('WEEK', CAST('2017-10-14 00:00:00' AS TIMESTAMP) + INTERVAL '1' DAY), DATE_TRUNC('WEEK', CAST('2017-10-15 00:00:00' AS TIMESTAMP) + INTERVAL '1' DAY))"
```

