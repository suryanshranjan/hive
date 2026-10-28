"""hive doctor: check, in plain words, that this machine and project are ready for Hive, and say how to fix what isn't.

Checks: git; the Claude Code CLI and its login (the builders run on it); the project is a git repository with no unsaved
changes; tests Hive can run; and the optional extras (a container, the owner's phone on Telegram, a backup model).
Nothing is changed; it only looks."""
import os, shutil, subprocess

from . import explain, start, telegram

def _run(cmd, cwd=None, timeout=60):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
    except Exception:
        return None

def checks(repo='.', claude_probe=True):
    """[(ok, required, what, how to fix)]."""
    out = []
    git = shutil.which('git')
    out.append((bool(git), True, 'git is installed', 'Install git from git-scm.com.'))
    claude = shutil.which('claude')
    out.append((bool(claude), True, 'Claude Code is installed (the builders run on it)',
                'Install it: npm install -g @anthropic-ai/claude-code, then run claude once to log in.'))
    if claude and claude_probe:
        p = _run(['claude', '-p', 'Reply with the single word OK'], timeout=90)
        ok = bool(p and p.returncode == 0 and 'OK' in p.stdout.upper())
        out.append((ok, True, 'Claude Code is logged in and answering',
                    'Run claude in a terminal and log in (or /login), then try again.'))
    inside = git and _run(['git', '-C', repo, 'rev-parse', '--is-inside-work-tree'])
    is_repo = bool(inside and inside.returncode == 0)
    out.append((is_repo, True, 'this folder is a git repository', 'Run Hive inside your project folder (git init if new).'))
    if is_repo:
        dirty = _run(['git', '-C', repo, 'status', '--porcelain'])
        out.append((bool(dirty) and not dirty.stdout.strip(), True, 'no unsaved changes',
                    'Commit or stash your changes, so the builders start from what you see.'))
        cfg = os.path.join(repo, '.hive', 'config.json')
        cmd, how = (None, None)
        if os.path.exists(cfg):
            cmd, how = 'yes', 'your hive settings'
        else:
            cmd, how = start.detect_tests(os.path.abspath(repo))
        out.append((bool(cmd), True, f'tests found ({how})' if cmd else 'tests found',
                    "Add tests (Node's built-in test runner or pytest), or tell Hive the command when it asks."))
    in_container = os.path.exists('/.dockerenv') or bool(os.environ.get('HIVE_SANDBOX'))
    out.append((in_container, False, 'running in a container (safer: builders run commands)',
                'Optional: run Hive inside Docker or a spare VM for code you do not fully trust.'))
    out.append((bool(telegram.load()), False, "the owner's phone is connected (Telegram)",
                'Optional: hive telegram setup, so questions and reviews reach your phone.'))
    out.append((os.path.exists(explain.BACKUP), False, 'a backup model for plain words',
                'Optional: hive llm setup (for example NVIDIA NIM), used only if Claude cannot be reached.'))
    return out

def main(repo='.', claude_probe=True):
    rows = checks(repo, claude_probe)
    print("\nHive here. Let me check everything is ready.\n")
    for ok, required, what, fix in rows:
        mark = 'ok  ' if ok else ('MISSING' if required else 'optional')
        print(f'  [{mark}] {what}' + ('' if ok else f'\n           {fix}'))
    missing = [r for r in rows if r[1] and not r[0]]
    print('\n' + ("All set. Type `hive` and tell me what to build." if not missing else
                  f"{len(missing)} thing{'s' if len(missing) != 1 else ''} to fix first; after that, type `hive`."))
    return 0 if not missing else 1
