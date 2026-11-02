"""The owner's own examples as checks, before delivery (Gate 103, under test).

Gate 101: twice the owner's new rule never reached the code the product runs. In one flight he corrected seven points
rules on the code sheet, one builder changed only the refund rules, and Hive told him "your changes are in". In
another the builder wrote the new points rate in a new module nothing calls, beside the old function. Builders' own
tests passed both times: they test what the builder wrote, not what the owner said, through the product's own
functions. MAST (Cemri et al. 2025) finds missing or incomplete verification in about a quarter of multi-agent
failures; the fix it reports is a check against the task's own objective. Here the objective is the owner's examples.

`check` gives a throwaway copy of the build to one coding agent: for every rule of the owner's with a concrete example,
it writes a test that calls the function the product already uses (what the existing code and tests call), runs them,
and reports the examples the code does not follow. It never changes the build."""
import glob, json, os, shutil, subprocess, tempfile

from . import argv

CMD = os.environ.get('HIVE_EXAMPLES_CMD', 'claude -p --output-format json --permission-mode acceptEdits '
                                          '--allowedTools Bash Read Write Glob Grep')

BRIEF = """You are checking a just-built feature against its business owner's own words. The folder {code} holds the
product's code. The goal was:

{goal}

These are the owner's rules for this build, in the order he gave them (a later rule replaces an earlier one it
contradicts):

{rules}

1. Read the code and its existing tests. For each rule, find the function the product itself uses for it: the one the
   rest of the code and the existing tests call, not a helper or a new module that nothing calls.
2. For every rule that states a concrete example (amounts, days, an outcome), write one pytest test in
   {code}/test_owner_examples.py that calls that function with the example's inputs, built the way the existing tests
   build them, and asserts the owner's outcome. Skip rules with no concrete example, and examples a later rule
   replaced. Change no other file.
3. Run it. When a test fails, first make sure the test itself follows the owner's words and the code's own way of
   calling the function; fix the test if it was wrong. Only a real difference between the product and his example
   counts.
4. Write {out} as JSON: {{"checks": <number of examples tested>, "failing": [{{"rule": "<the owner's rule, short>",
   "example": "<his example>", "got": "<what the product gives>", "where": "<module.function>"}}]}}

Reply in one line: how many examples you tested and how many fail."""


def rules_of(home):
    """The owner's words for this build: interview and hand-over rules (state['asked']), his answers to the builders'
    questions, and his review corrections, in order."""
    out = []
    try:
        st = json.load(open(os.path.join(home, 'state.json'), encoding='utf-8'))
        out += [r for r in (st.get('asked') or []) if isinstance(r, str)]
    except Exception:
        pass
    owner = os.path.join(home, 'build', 'owner')
    for p in sorted(glob.glob(os.path.join(owner, 'answers', '*.json'))):
        try:
            a = json.load(open(p, encoding='utf-8'))
            q = json.load(open(os.path.join(owner, 'questions', os.path.basename(p)), encoding='utf-8'))
            out.append(f"Asked: {q.get('question') or q.get('q') or ''} His answer: {a.get('answer', '')}".strip())
        except Exception:
            continue
    try:
        c = open(os.path.join(owner, 'corrections.md'), encoding='utf-8').read().strip()
        if c:
            out.append('His review corrections:\n' + c[:4000])
    except Exception:
        pass
    return out


def check(code_dir, goal, rules, timeout=1500):
    """{'checks': n, 'failing': [...], 'cost': dollars}; None if the check could not run. Never changes code_dir."""
    rules = [r.strip() for r in rules if r and r.strip()]
    if not rules or os.environ.get('HIVE_EXAMPLE_CHECK') == '0':
        return None
    work = tempfile.mkdtemp(prefix='hive_examples_')
    try:
        code = os.path.join(work, 'code')
        shutil.copytree(code_dir, code, ignore=shutil.ignore_patterns('.git', 'node_modules', '__pycache__', '.hive'))
        out = os.path.join(work, 'examples.json')
        listing = '\n'.join(f'{n}. {r}' for n, r in enumerate(rules[-60:], 1))
        cost = None
        try:
            p = subprocess.run(argv(os.environ.get('HIVE_EXAMPLES_CMD') or CMD), cwd=work,
                               input=BRIEF.format(code=code, goal=goal.strip()[:6000], rules=listing, out=out),
                               capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
            try:
                cost = json.loads(p.stdout).get('total_cost_usd')
                from . import explain
                explain.spend(cost, 'examples.check')
            except Exception:
                pass
            got = json.load(open(out, encoding='utf-8'))
        except Exception:
            return None
        failing = [f for f in (got.get('failing') or []) if isinstance(f, dict)]
        return {'checks': int(got.get('checks') or 0), 'failing': failing, 'cost': cost}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def note(failing):
    """What the fix builder is told."""
    return ("\n\n# The owner's own examples do not hold yet\n\nA check called the product's own functions (the ones the "
            "rest of the code and the existing tests use) with the owner's examples. These come out differently from "
            "what he said. Make those functions give his outcome, so every caller gets it (do not add a second "
            "version beside them), encode each example as a test, change any existing test that asserts the old "
            "behaviour, and leave everything else alone. If one example contradicts a later rule of his, follow the "
            "later rule.\n\n" +
            '\n'.join(f"- {f.get('where', '')}: his rule \"{f.get('rule', '')}\"; his example: {f.get('example', '')}; "
                      f"the product gives: {f.get('got', '')}" for f in failing) + '\n')
