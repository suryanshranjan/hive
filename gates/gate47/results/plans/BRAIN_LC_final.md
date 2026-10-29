# BRAIN — minisql team plan (read at every sync)

State at plan time: 9/1340 visible tests pass (part of `basic`). Engine is a 221-line skeleton.
Claim and land only via `tools/claim.py` / `tools/land.py` (README "Protocol"). Leave a short note
in `brain/notes/<you>.md` when you land: what you built, the interface, what is now unblocked.

## Interfaces (build on these; do not invent parallel ones)

Values: Python `None` (NULL), `int`, `float`, `str`, `bytes` (BLOB). Booleans are int 1/0.

**AST (minisql/ast.py documents it).** Expressions are *tuples, all children tuples* (so nodes are
hashable and can be dict keys):
- `('lit', v)` `('col', table_or_None, name)` `('star', table_or_None)`
- `('unary', op, e)` op in `'-' '+' '~' 'NOT'`
- `('binop', op, l, r)` op uppercase string: `+ - * / % || = == <> != < <= > >= AND OR & | << >> IS ISNOT -> ->>`
- `('between', e, lo, hi, negated)` `('in', e, items_tuple_or_select_st, negated)`
- `('like', 'LIKE'|'GLOB'|'REGEXP', l, pattern, escape_or_None, negated)`
- `('isnull', e, negated)` for `ISNULL/NOTNULL/IS NULL` shortcuts (or use binop IS with lit None)
- `('case', base_or_None, ((when, then), ...), else_or_None)`
- `('cast', e, type_name_upper)` `('collate', e, name_upper)`
- `('func', name_lower, args_tuple, opts)` where `opts` is a tuple of sorted `(key, value)` pairs
  (keys: `distinct`, `star`, `filter`, `over`, `order_by`); helper `fopt(e, key)` in ast.py.
- `('subquery', select_st)` `('exists', select_st)` `('row', exprs_tuple)` for `(a, b)` row values.
Statements are dicts with `'type'`. SELECT:
`{'type':'select','with':None|[(name, cols, st)],'recursive':bool,'distinct':bool,'items':[(e, alias)],
'from':from_node|None,'where':e,'group_by':[e],'having':e,'windows':{name: spec},
'order_by':[(e, 'ASC'|'DESC', None|'FIRST'|'LAST')],'limit':e,'offset':e}`.
Compound: `{'type':'compound','ops':[('UNION'|'UNION ALL'|'INTERSECT'|'EXCEPT', select_st)],'first':select_st, 'order_by','limit','offset'}`.
`VALUES (...),(...)` as a query: `{'type':'values','rows':[[e,...]]}`.
FROM nodes: `('table', name, alias)` `('subq', st, alias)` `('join', kind, left, right, on_e, using_cols, natural)`
with kind in `INNER LEFT RIGHT FULL CROSS`.

**Lexer** `minisql/lexer.py`: tokens `(kind, value)`, kinds `KW IDENT NUM STR BLOB OP EOF`. Quoted
identifiers (`"x"`, `[x]`, `` `x` ``) become IDENT. Comments `--` and `/* */` skipped. Add keywords to
`KEYWORDS`; parser may also accept a KW where an identifier is allowed via `Parser.name()`.

**Values/types** `minisql/values.py`: `compare(a, b, collation=None)` (SQLite cross-type order NULL<num<text<blob,
returns -1/0/1), `sort_key(v, collation=None)`, `truthy(v)` -> True/False/None, `to_num(v)` (text->num
prefix rule), `cast(v, type_name)`, `affinity(decl_type)` + `apply_affinity(v, aff)`, `to_text(v)`
(SQLite formatting of floats: `1.0`, `1e+20`, 15 significant digits), `typeof(v)`.

**Evaluator** `minisql/evaluator.py`: `evaluate(e, env)`. `env` is `Env(values, outer=None, conn=None, aggs=None)`:
`env.get(table, name)` looks up `values` by `(alias.lower(), name.lower())` or bare `name.lower()`, then `outer`
(correlated subqueries). `aggs` maps aggregate/window `('func', ...)` node -> precomputed value; the evaluator
returns `env.aggs[e]` when present. Subqueries call `env.conn.run_select(st, outer=env)`.

**Scalar functions** `minisql/functions.py`: registry `SCALARS = {}` and decorator
`@scalar('name', 'alias', ...)` on `def f(*args)` receiving evaluated values. Functions that need
lazy args (iif, coalesce short-circuit) are fine evaluated eagerly. One file per family is fine
(`functions_json.py`, `functions_date.py`, `functions_math.py`): each does `from .functions import scalar`
and is imported at the bottom of `functions.py`. **Never define the same function name twice** (land.py rejects it).

**Aggregates** `minisql/aggregates.py`: `AGGREGATES = {}` and `@aggregate('name')` on a class with
`__init__(self)`, `step(self, *args)`, `final(self)`. The executor handles DISTINCT, FILTER and
`ORDER BY` inside aggregates generically before calling `step`.

**Windows** `minisql/windows.py`: `compute_windows(rows, envs, nodes, conn)` fills `env.aggs[node]` for every
`('func', ..., over=...)` node; window-only functions (row_number, rank, lag, ...) register in `WINDOW_FUNCS`.

**Executor** `minisql/engine.py`: `Connection.execute(sql)` -> list of tuples. `Connection.run_select(st, outer=None)`
returns `(column_names, rows)`; everything that needs a query (subqueries, INSERT..SELECT, views, CTEs,
CREATE TABLE AS) calls it. Tables: `self.tables[name.lower()] = Table(name, columns=[Column(name, decl_type,
notnull, default, pk, unique, check)], rows=[list])` (class in `minisql/schema.py`). DML/DDL live in
`minisql/dml.py` / `minisql/ddl.py` as functions `exec_insert(conn, st)` etc., dispatched from `execute`.

## Levels (every failing category)

**Level 0 — foundations (everything needs these)**
- L0-A lexer+expression parser: `arith where nulls true_false comments_quoted real_literal hex_literal blob_literal case case_nested bitwise`
- L0-B values/types+evaluator: `typeof cast_int_real cast_text_numeric concat is_distinct`
- L0-C SELECT core executor (FROM, WHERE, aliases, ORDER BY, LIMIT/OFFSET, DISTINCT): `basic order_limit order_nulls distinct limit_expr select_star_qualified`
- L0-D aggregates + GROUP BY/HAVING: `aggregates group_by group_by_expr_alias agg_empty_null agg_distinct agg_filter`
- L0-E INSERT/DDL/DML: `insert_columns update_delete default_values delete_all_count integer_primary_key`
- L0-F scalar function registry + core string/math functions: `strings abs_sign minmax_scalar instr substr_more length_octet trim_chars replace_more`

**Level 1 — needs L0 only**
- functions (needs L0-B,F): `quote char_unicode hex_unhex round_trunc ceil_floor pow_mod sqrt_exp_ln log_funcs trig hyperbolic iif_if printf format glob like_escape collate_nocase`
- joins (L0-C): `join left_join right_full_join three_way_join natural_using`
- subqueries (L0-C): `subquery exists scalar_subquery_order row_values`
- set ops (L0-C): `union union_all intersect except compound_order_limit values_clause`
- DML/DDL more (L0-E): `insert_select insert_or_ignore insert_or_replace check_not_null returning update_multi_set alter_table alter_rename_table drop_table create_index_noop create_table_as transactions`
- aggregates more (L0-D): `group_concat_sep agg_order_by median percentile json_group`(json_group also needs JSON)
- dates (L0-F): `date_basic datetime_basic time_basic julianday unixepoch strftime date_modifiers date_n_days date_compare timediff`
- JSON (L0-F): `json_extract json_arrows json_type json_valid json_array_length json_build json_modify json_remove json_patch json_minify json_error_position`

**Level 2**
- CTEs/views (subqueries+set ops): `cte_basic cte_multiple cte_recursive views`
- windows (L0-D + ORDER BY): `window_row_number window_rank window_ntile window_percent window_lag_lead window_first_last window_nth_value window_agg window_frames window_named window_empty_over`
- `upsert update_from` (DML + joins)

## Now (6 workers, one file each, so nobody collides)
1. **A** — `lexer.py` + the expression half of `parser.py` (`expr()` downwards: full precedence climbing,
   all expression node kinds above, function-call syntax incl. `DISTINCT`, `*`, `FILTER (WHERE)`, `OVER`, in-call `ORDER BY`).
   Land the grammar early even if eval is missing.
2. **B** — `values.py` + `evaluator.py` (all expression kinds above; NULL logic; integer vs real arithmetic,
   integer division, `/0` -> NULL; LIKE case-insensitive ASCII). Delete `evaluate` from engine.py and import it.
3. **C** — statement half of `parser.py` (`select()` and upward: full SELECT clause grammar, joins, compound, WITH, VALUES)
   + `engine.py` `run_select` core (FROM single table/joins, WHERE, ORDER BY, LIMIT, DISTINCT). Coordinate with A only
   through the AST above: A owns methods `expr*`/`primary`/`func_call`, C owns the rest.
4. **D** — `aggregates.py` + the GROUP BY/HAVING step inside `run_select` (put it in a helper `group_rows(...)`
   in `minisql/grouping.py` so C and D don't edit the same function).
5. **E** — `schema.py`, `dml.py`, `ddl.py`: CREATE TABLE with constraints/defaults/types, INSERT (columns, defaults,
   rowid/INTEGER PRIMARY KEY), UPDATE, DELETE; parse them in `parser_dml.py` (a mixin class or functions called from `statement()`).
6. **F** — `functions.py` registry + strings/abs/min/max/instr/substr/length/trim/replace.
Until A and B land, test your piece directly in Python on AST tuples. Land small and often; pull before every land.
When a level-0 lock frees, take level-1 work in the matching family (A→functions syntax/glob/like, B→cast/collate,
C→joins/subqueries/set ops, D→group_concat/median/percentile, E→DML-more, F→dates/JSON).

## Landed (update 3, t+9min): TOTAL 1340/1340, 127/127 categories pass, no locks held
Everything on the plan has landed: windows.py (`@window_func('name')` f(ctx), frames, named windows), functions_date.py
(SQLite date.c port), views_tx.py, upsert.py, update_from.py, alter.py, aggregates_json.py, JSON modify/patch/remove.
Nothing is left in tests/visible. If you have time: no new features. Only refactor where land.py stays green.
