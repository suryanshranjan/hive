"""hive doctor: check, in plain words, that this machine and project are ready for Hive, and say how to fix what isn't.

Checks: git; the Claude Code CLI and its login (the builders run on it); the project is a git repository with no unsaved
changes; tests Hive can run; and the optional extras (a container, the owner's phone on Telegram, a backup model).
Nothing is changed; it only looks."""
import os, shutil, subprocess, sys

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
    out.append((bool(claude), True, 'Claude Code is installed (Hive thinks with it; builders run on it by default)',
                'Install it: npm install -g @anthropic-ai/claude-code, then run claude once to log in.'))
    from . import swarm
    try:
        chosen = swarm.agents()
    except SystemExit:
        chosen = []
    for agent in chosen:   # builders on another agent (or a mix): each must be there too
        if agent == 'claude':
            continue
        exe = swarm.AGENTS[agent][1]
        out.append((bool(shutil.which(exe)), True, f'{agent} is installed (your builders run on it)',
                    swarm.AGENT_HELP.get(agent, f'Install {agent} and log in once in a terminal ({exe})') +
                    ' Or build with --agent claude.'))
    if claude and claude_probe:
        p = _run([claude, '-p', 'Reply with the single word OK'], timeout=90)   # the full path: on Windows it is a .cmd
        ok = bool(p and p.returncode == 0 and 'OK' in p.stdout.upper())
        out.append((ok, True, 'Claude Code is logged in and answering',
                    'Run claude in a terminal and log in (or /login), then try again.'))
    inside = git and _run(['git', '-C', repo, 'rev-parse', '--is-inside-work-tree'])
    is_repo = bool(inside and inside.returncode == 0)
    out.append((is_repo, True, 'this folder is a git repository', 'Run Hive inside your project folder (git init if new).'))
    if is_repo:
        dirty = _run(['git', '-C', repo, 'status', '--porcelain', '--untracked-files=no'])
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
    from . import voice
    out.append((voice.available(), False, 'voice notes (answer Hive by talking on Telegram)',
                'Optional: pip install "hive-swarm[voice]" (transcribes on this machine; your voice never leaves it).'))
    out.append((os.path.exists(explain.BACKUP), False, 'a backup model for plain words',
                'Optional: hive llm setup (for example NVIDIA NIM), used only if Claude cannot be reached.'))
    return out

def setup(repo='.', ask=input, claude_probe=True):
    """hive setup: the first run for a new owner. Check what's required, then offer each optional extra in turn."""
    rows = checks(repo, claude_probe)
    print("\nHive here. Let's get you set up; it takes a few minutes.\n")
    missing = [r for r in rows if r[1] and not r[0]]
    for ok, required, what, fix in rows:
        if required:
            print(f'  [{"ok  " if ok else "MISSING"}] {what}' + ('' if ok else f'\n           {fix}'))
    if missing:
        print(f"\nFix {'that' if len(missing) == 1 else 'those'} first, then run hive setup again.")
        return 1
    yes = lambda q: ask(f'\n{q} [y/N] > ').strip().lower() in ('y', 'yes')
    from . import voice
    if not telegram.load() and yes('Would you like questions and reviews on your phone, through Telegram?'):
        telegram.setup()
    if telegram.load() and not voice.available() and yes('Would you like to answer by voice note too? '
                                                          '(installs Whisper, about 500 MB; your voice stays on this machine)'):
        r = subprocess.run([sys.executable, '-m', 'pip', 'install', 'faster-whisper'])
        print('  Voice notes are ready.' if r.returncode == 0 else
              '  That did not install; you can try later: pip install "hive-swarm[voice]"')
    if not os.path.exists(explain.BACKUP) and yes('Add a backup model, used only if Claude cannot be reached?'):
        explain.setup_backup()
    print("\nAll set. Type `hive` in your project folder and tell me what to build.")
    return 0

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
