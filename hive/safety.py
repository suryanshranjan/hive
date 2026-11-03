"""A safety net for a project with no tests (most founders' projects): before anything changes, one builder writes
tests that pin how the product behaves today, in a copy; they travel with every build (and reach his engineer in the
pull request), so "every test passes" means something. His own folder is never written to.

Without it, Hive stopped: "Builders need tests to know when the work is right. Add some and run me again." """
import json, os, shutil, subprocess, tempfile

DIR = os.path.join(os.path.expanduser('~'), '.hive', 'safety')
FOLDER = 'tests_hive'
CMD = os.environ.get('HIVE_SAFETY_CMD', 'claude -p --output-format json --permission-mode acceptEdits '
                                         '--allowedTools Bash Read Edit Write Glob Grep')

NET = """This project has no tests. Before anyone changes it, write a safety net: tests that pin how the product behaves
TODAY, so a later change that breaks something is caught.

- Put them in a new folder {folder}/ as pytest files (test_*.py), whatever the project's language: Python's standard
  library can start the product (a dev server, a script), fetch its pages or call it, and check what it shows or
  returns. Cover what a customer would notice: each page loads and shows its key words, each form and button is there,
  each function or endpoint gives today's answer for a few ordinary inputs.
- Pin today's behaviour, right or wrong; never change any file outside {folder}/.
- Keep them fast (under a minute in all) and runnable with: python -m pytest -q {folder}
- Run them: every test must pass on the product as it is. Then reply with JSON only:
  {{"tests": <number of tests>, "covers": "one plain sentence: what they check"}}"""

def _key(repo):
    from . import memory
    return memory.project_key(repo)

def path(repo):
    return os.path.join(DIR, _key(repo), FOLDER)

def has(repo):
    return os.path.isdir(path(repo)) and any(f.startswith('test_') for f in os.listdir(path(repo)))

def command():
    from . import PY
    return f'{PY} -m pytest -q -p no:cacheprovider --junitxml=.hive/junit.xml {FOLDER}'

def make(repo, timeout=1800):
    """Write the net in a throwaway copy; keep it (outside his folder). Returns {'ok', 'tests', 'covers', 'cost'}."""
    from . import argv
    from .start import run_tests
    work = tempfile.mkdtemp(prefix='hive_safety_'); copy = os.path.join(work, 'project')
    try:
        if subprocess.run(['git', 'clone', '-q', os.path.abspath(repo), copy], capture_output=True).returncode:
            return {'ok': False}
        p = subprocess.run(argv(CMD), cwd=copy, input=NET.format(folder=FOLDER), capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=timeout)
        try:
            out = json.loads(p.stdout); cost = float(out.get('total_cost_usd') or 0)
            res = out.get('result') or ''
            said = json.loads(res[res.index('{'):res.rindex('}') + 1])
        except (ValueError, AttributeError):
            cost, said = 0.0, {}
        if not os.path.isdir(os.path.join(copy, FOLDER)):
            return {'ok': False, 'cost': cost}
        res = run_tests(copy, command())   # it must hold on the product as it is today
        if not res or not all(res.values()):
            return {'ok': False, 'cost': cost, 'why': 'its tests do not all pass on the product as it is'}
        dst = path(repo)
        shutil.rmtree(dst, ignore_errors=True); os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copytree(os.path.join(copy, FOLDER), dst, ignore=shutil.ignore_patterns('__pycache__'))
        return {'ok': True, 'tests': len(res), 'covers': str(said.get('covers', '')).strip(), 'cost': cost}
    except Exception:
        return {'ok': False}
    finally:
        shutil.rmtree(work, ignore_errors=True)

def install(repo, source):
    """Copy his kept net into this build's source and commit it. True if it was added."""
    if not has(repo) or os.path.isdir(os.path.join(source, FOLDER)):
        return False
    shutil.copytree(path(repo), os.path.join(source, FOLDER))
    subprocess.run(['git', '-C', source, 'add', FOLDER], capture_output=True)
    subprocess.run(['git', '-C', source, '-c', 'user.name=hive', '-c', 'user.email=hive@local', 'commit', '-q', '-m',
                    'hive: a safety net of tests pinning how the product behaves today'], capture_output=True)
    return True
