"""A map of the codebase for the builders, made with graphify (https://graphify.com, Apache-2.0; `pip install graphifyy`).

Gate 78 (under test): before the builders start, Hive builds one map of the code from its syntax (tree-sitter, on this
computer, no model, under a minute; its groups are then named by one cheap model call) and copies it into every
builder's clone. Each builder can then ask the map where
things are and what calls what, instead of each reading the same files to find its way.
Off unless the swarm is prepared with code_map=True (or HIVE_CODE_MAP=1)."""
import json, os, shutil, subprocess

OUT = 'graphify-out'

def tool():
    """The graphify command, or None if it is not installed here."""
    t = os.environ.get('HIVE_GRAPHIFY') or shutil.which('graphify')
    return t if t and os.path.exists(t) else None

def wanted():
    return os.environ.get('HIVE_CODE_MAP') == '1'

def build(src, into):
    """Build the map of the code in `src` into `into`/graphify-out. Returns the report's path, or None."""
    g = tool()
    if not g:
        return None
    os.makedirs(into, exist_ok=True)
    tmp = os.path.join(into, 'src')
    shutil.copytree(src, tmp, ignore=shutil.ignore_patterns('.git', OUT, '__pycache__', 'node_modules', '.venv'))
    for cmd in ([g, 'extract', tmp, '--code-only'], [g, 'cluster-only', tmp, '--no-label', '--no-viz']):
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        if r.returncode != 0:
            return None
    if shutil.which('claude') and os.environ.get('HIVE_MAP_LABEL') != '0':   # name its groups ("Dialect Registry", not "Community 12"): one cheap model call, ~1 min
        subprocess.run([g, 'label', tmp, '--backend=claude-cli'], capture_output=True, text=True, timeout=900,
                       env=dict(os.environ, GRAPHIFY_CLAUDE_CLI_MODEL=os.environ.get('GRAPHIFY_CLAUDE_CLI_MODEL', 'claude-haiku-5-5')))
    shutil.move(os.path.join(tmp, OUT), os.path.join(into, OUT)); shutil.rmtree(tmp, ignore_errors=True)
    rep = os.path.join(into, OUT, 'GRAPH_REPORT.md')
    return rep if os.path.exists(rep) else None

def guided():
    """Gate 79 (under test): also steer the builder to the map, as graphify does for Claude Code (a CLAUDE.local.md rule,
    and a hook that reminds it of the map before each search or file read). Off unless HIVE_MAP_GUIDE=1."""
    return os.environ.get('HIVE_MAP_GUIDE') == '1'

def _exclude(work, *names):
    ex = os.path.join(work, '.git', 'info', 'exclude'); os.makedirs(os.path.dirname(ex), exist_ok=True)
    lines = open(ex).read().splitlines() if os.path.exists(ex) else []
    with open(ex, 'a') as f:
        for n in names:
            if n not in lines:
                f.write(n + '\n')

RULE = """## graphify (a map of this codebase)

This clone has a knowledge graph of its code at graphify-out/graph.json.
- Run `{g} query "<question>"` before your first grep, search or source-file read for a question about the code. Read raw
  files only for lines the graph or an earlier read already located.
- Use `{g} explain "<name>"` for one function or class (what it calls, what calls it) and `{g} path "<A>" "<B>"` for how
  two things connect; `{g} affected "<name>"` before you change something others use.
- After modifying code, or after you pull, run `{g} update .` (seconds, no cost).
"""

def install(built, work, guide=None):
    """Copy a built map into a builder's clone, kept out of git; with guide, also graphify's rule and search hook."""
    shutil.copytree(os.path.join(built, OUT), os.path.join(work, OUT), dirs_exist_ok=True)
    _exclude(work, OUT + '/')
    if guide if guide is not None else guided():
        g = tool() or 'graphify'
        open(os.path.join(work, 'CLAUDE.local.md'), 'a').write(RULE.format(g=g))
        os.makedirs(os.path.join(work, '.claude'), exist_ok=True)
        hooks = {'hooks': {'PreToolUse': [
            {'matcher': 'Bash|Grep', 'hooks': [{'type': 'command', 'command': f'{g} hook-guard search', 'timeout': 10}]},
            {'matcher': 'Read|Glob', 'hooks': [{'type': 'command', 'command': f'{g} hook-guard read', 'timeout': 10}]}]}}
        json.dump(hooks, open(os.path.join(work, '.claude', 'settings.local.json'), 'w'), indent=1)
        _exclude(work, 'CLAUDE.local.md', '.claude/settings.local.json')

def path_env(run, env):
    """Put graphify on the builders' PATH when their clones have a map (the hook's reminders name it bare)."""
    g = tool()
    if g and os.path.isdir(os.path.join(run, 'map')):
        env = dict(env, PATH=os.path.dirname(g) + os.pathsep + env.get('PATH', ''))
    return env

def text():
    g = tool() or 'graphify'
    return ("\n## A map of this codebase\n`graphify-out/GRAPH_REPORT.md` is a map of this codebase, built from its code before "
            "you started: its groups of related code and its most connected functions. Use it to find your way instead of "
            "reading file after file. Ask it, from your clone: "
            f"`{g} query \"<question>\"` (what is relevant), `{g} explain \"<name>\"` (a function and what it calls and what "
            f"calls it), `{g} path \"<A>\" \"<B>\"` (how two things connect), and, before you change something others use, "
            f"`{g} affected \"<name>\"` (what depends on it). After you pull, `{g} update .` refreshes the map in a few "
            "seconds, at no cost. The map is never committed.\n")
