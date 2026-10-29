# minisql shared brain

## Complete — sync 3
**TOTAL 1340/1340; 127/127 categories pass** on main at 3d5abef. No category locks remain. Stop new work against this visible-suite objective. Lead pushed the initial plan plus three updates and wrote no engine code or task claims.

All six foundations landed, followed by subqueries, aggregate modifiers, ORDER/COLLATE fixes, USING/NATURAL projection, UPDATE FROM, UPSERT/RETURNING, CTEs, and windows. Library-first separation worked; expression/SELECT wiring was the first bottleneck, and later shared engine edits needed narrow ownership. Dependencies were useful implementation guides, not strict scheduling barriers (recursive CTEs/windows could develop earlier against hooks).

## Interfaces as built (supersedes initial contracts)
- Public API: `minisql.connect()`; `Connection.execute(sql)` returns rows. `engine.Connection.select_with_columns(st,outer=None,ctes=None)` returns `(cols,rows)`; reuse it for derived queries. `run_select` returns rows.
- Lexer tokens `(kind,value)`, EOF sentinel; BLOB added. Contextual words can be IDENT. Parser `word/is_word/expect_word` match words case-insensitively. `Parser.expr(min_precedence)` delegates to `parser_expr.parse_expr`; DML statement parsing delegates to `parser_dml.parse_statement(p)`.
- AST expressions are tuples; authoritative tags in ast.py. Calls: `('call',NAME,args[,opts])` where opts is a tuple of `(key,value)` pairs for distinct/order/filter/over. ORDER terms `(expr,desc,nulls)`. Sources: table/subquery/join/values/tvf tuples documented in parser.py. Qualified star currently parsed as `('star',qualifier)`.
- `expressions.evaluate(expr,env,context=None)` handles SQL NULL/coercion/lazy calls; helpers to_text/to_int/to_real/cast_value/apply_affinity/compare/is_true. `engine.Env` resolves names case-insensitively, with `.parent` for correlation. `QueryContext(conn,group=None,ctes=None).run_select(st,env)` supplies subquery execution; expressions accepts either context.subquery or context.run_select. Storage evaluation passes this context too.
- `functions.call_function(name,args)` lazily merges provider FUNCTIONS from functions_json/functions_datetime/functions_math. Scalars accept positional SQL values. Shared scalar helpers fn_text/fn_num/fn_int/fn_real/like_match/glob_match. NULL behavior is function-specific. JSON `JsonText` subtype must survive nested evaluation.
- `aggregates.AGGREGATES[name](list_of_arg_tuples)->value`; COUNT(*) gets empty argument tuples. Also exposes is_aggregate and make_aggregate(name,distinct=False) with step/inverse/value. `grouping._aggregate` applies FILTER, argument ORDER BY, DISTINCT; substitute replaces calls per group. OVER calls are excluded from group aggregation. Windows reuse the aggregate registry.
- `windows.parse_over(p)` yields `('spec',base,partition,order,frame)` or `('ref',name)` stored in call opts. `windows.annotate([(env,ctx,exprs)],named,evaluate)` after grouping/HAVING stores computed window values at env[call_tuple]. Supports partitions, ranking/value/aggregate functions, named windows, ROWS/RANGE/GROUPS and EXCLUDE.
- `ctes.run_ctes(conn,with_list,ctx,outer)` fills `ctx.ctes[name]=(cols,rows)`; recursive compound execution and UNION deduplication use the same SELECT engine.
- `storage.execute_<type>(conn,st)` handles DML/schema/transactions. Tables preserve columns/rows and add rowids/coldefs/ipk/uniques. engine.RowidRow carries rowid metadata. UPSERT/RETURNING are in storage (try_upsert/returning_rows); no insert_hook. CREATE VIEW stores SELECT AST directly in conn.views, applying explicit result names.
- `engine.Bindings.hidden` hides duplicate right-side USING/NATURAL columns in star projection. sort_keyed honors explicit collations and keeps NULLS FIRST/LAST independent of DESC.

## Now
No tasks to start: all visible categories pass. Future work must preserve this baseline using README's claim/land protocol and record actual interfaces in brain/notes. Existing worker notes retain intermediate history; the interface summary above reflects final code where notes are stale. Exact SQLite behavior beyond these visible cases remains unverified.

## Dependency levels (every category appears once)
Levels describe implementation prerequisites, not a requirement to finish every unrelated category in the previous level. Independent function libraries can start immediately against the interfaces below.

**L0 — syntax, expressions, basic relational and storage substrate:**
basic, arith, bitwise, blob_literal, case, case_nested, cast_int_real, cast_text_numeric, comments_quoted, concat, hex_literal, nulls, real_literal, true_false, typeof, where, order_limit, insert_columns.

**L1 — consumers of L0 (parallel families):**
- Scalar/string/math: abs_sign, ceil_floor, char_unicode, format, glob, hex_unhex, hyperbolic, iif_if, instr, length_octet, like_escape, log_funcs, minmax_scalar, pow_mod, printf, quote, replace_more, round_trunc, sqrt_exp_ln, strings, substr_more, trig, trim_chars.
- SELECT extensions: collate_nocase, distinct, group_by, aggregates, is_distinct, join, limit_expr, order_nulls, row_values, select_star_qualified, values_clause.
- Storage: alter_rename_table, alter_table, check_not_null, create_index_noop, create_table_as, default_values, delete_all_count, drop_table, insert_or_ignore, insert_or_replace, integer_primary_key, transactions, update_delete, update_multi_set.
- JSON scalars: json_array_length, json_arrows, json_build, json_error_position, json_extract, json_minify, json_modify, json_patch, json_remove, json_type, json_valid.
- Date/time scalars: date_basic, date_compare, date_modifiers, date_n_days, datetime_basic, julianday, strftime, time_basic, timediff, unixepoch.

**L2 — consume L0/L1 machinery:**
agg_distinct, agg_empty_null, agg_filter, agg_order_by, group_by_expr_alias, group_concat_sep, json_group, median, percentile, left_join, natural_using, right_full_join, three_way_join, subquery, exists, scalar_subquery_order, union, union_all, except, intersect, insert_select, returning, update_from, upsert, views, window_empty_over, window_agg, window_row_number, window_rank, window_ntile, window_percent, window_lag_lead, window_first_last, window_nth_value.

**L3 — composed query machinery:**
compound_order_limit, cte_basic, window_frames, window_named.

**L4:** cte_multiple, cte_recursive (CTE scope plus compound/recursive query execution).

