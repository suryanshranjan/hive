"""The rule sheet written from the built code (Gate 42): complete by construction, so the owner only marks what is wrong.

The first build already decides every case, including the unusual ones nobody asked about. A describer reads and runs
the built code (read-only) and writes every business behaviour as a plain rule. The owner sees the whole sheet, marks
the rules that are not his policy and says each one right, then adds anything missing; the changes go to a fix round.

Gate 42 (synthetic owner who knows his rules): the corrected code sheet took fresh builders to 99.6% hidden, against
68.4% from Hive's interview and 100% from the owner's own complete sheet. The cost moved to the owner's reading: 68
rules, 34 marked. A real owner reading such a sheet is not yet tested."""
import json, os, shlex, shutil, subprocess, tempfile

CMD = os.environ.get('HIVE_DESCRIBE_CMD', 'claude -p --output-format json --permission-mode acceptEdits '
                                          '--allowedTools Bash Read Write Glob Grep')

BRIEF = """You are documenting what a piece of software does, so that its business owner can check it. The folder
{code} holds the code, just built for this feature:

{goal}

Read it and run it, but do not change anything in that folder. Write {out}: a JSON list of strings, one rule per
string, in plain words the owner can check ("Whenever ..., ..."), each naming the part of the product it is about.
- Cover every business behaviour of this feature: the normal outcome, and what happens with missing, blank or
  unreadable values, wrong formats, letter case, spaces and separators, zero, negative or very large numbers,
  boundaries and rounding. Describe what the code actually does, even where it looks odd.
- Check each rule by running the code or its tests.
- One behaviour per rule, one or two sentences each. Business words, no code, no file or function internals.
Reply in one line: how many rules you wrote."""

def describe(code_dir, goal, timeout=1800):
    """Every business behaviour of the built code, as plain rules ([] if the describer could not run)."""
    work = tempfile.mkdtemp(prefix='hive_sheet_')
    try:
        code = os.path.join(work, 'code')
        shutil.copytree(code_dir, code, ignore=shutil.ignore_patterns('.git', 'node_modules', '__pycache__'))
        out = os.path.join(work, 'rules.json')
        try:
            subprocess.run(shlex.split(CMD), cwd=work, input=BRIEF.format(code=code, goal=goal.strip()[:6000], out=out),
                           capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
            got = json.load(open(out, encoding='utf-8'))
        except Exception:
            return []
        return [r.strip() for r in got if isinstance(r, str) and r.strip()] if isinstance(got, list) else []
    finally:
        shutil.rmtree(work, ignore_errors=True)
