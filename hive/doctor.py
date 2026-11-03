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
    raw_ask = ask
    def ask(q):   # no more input (a closed terminal, a script) is a no, never a crash
        try:
            return raw_ask(q)
        except EOFError:
            return ''
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
    from . import numbers, screens
    if telegram.load() and not screens.available() and yes('Would you like screenshots of what was built on your phone? '
                                                            '(installs a browser for Hive, about 150 MB)'):
        r = subprocess.run([sys.executable, '-m', 'pip', 'install', 'playwright'])
        r = r.returncode == 0 and subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium']).returncode == 0
        print('  Screenshots are ready.' if r else '  That did not install; later: pip install playwright, then '
              'playwright install chromium')
    if not numbers.source(repo) and yes('Can Hive read your business numbers (sign-ups, sales), to tell you whether a '
                                        'change worked?'):
        how = ask("  How? Paste a command that prints them as JSON, a web address that returns JSON, or a JSON file in "
                  "this project. (Your engineer can set this up; Enter to skip. You can also just tell me your numbers on "
                  "Telegram.)\n  > ").strip()
        if how:
            src = numbers.set_source(repo, url=how if how.startswith(('http://', 'https://')) else None,
                                     file=how if how.endswith('.json') and not how.startswith('http') else None,
                                     cmd=how if not how.startswith(('http://', 'https://')) and not how.endswith('.json') else None)
            got = numbers.refresh(repo)
            print(f"  Read {len(got)} number{'s' if len(got) != 1 else ''}: " + ', '.join(f'{k} {v:g}' for k, v in got.items())
                  if got else f"  Saved ({next(iter(src))}), but it gave me no numbers yet; I'll keep trying.")
    from . import deploy
    if not deploy.config(repo):
        where = ask("\nWhere does your product live? (vercel, netlify, railway, azure, fly, render, or Enter to skip; "
                    "you can tell me later on Telegram)\n  > ").strip().lower()
        if where in deploy.HOSTS:
            deploy.setup(repo, where)
            state, why = deploy.ready(repo)
            print(f'  Connected: {where}.' + ('' if state == 'ok' else ' ' + why))
    if telegram.load() and yes('Start me on your phone now? (I keep listening in the background on this computer)'):
        return go_live(repo)
    print("\nAll set. Type `hive` in your project folder and tell me what to build.")
    return 0

def fetch_repo(url):
    """His code from where it lives (a GitHub or GitLab address): fetched once into ~/hive-projects/<name>, brought up
    to date after that. Returns the folder, or None (said plainly)."""
    import re
    name = re.sub(r'\.git$', '', re.split(r'[\\/:]', url.rstrip('/\\'))[-1]) or 'project'   # an address or a folder
    here = os.path.join(os.path.expanduser('~'), 'hive-projects', name)
    if os.path.isdir(os.path.join(here, '.git')):
        subprocess.run(['git', '-C', here, 'pull', '-q', '--ff-only'], capture_output=True)
        print(f'Your project {name} is here: {here} (brought up to date).'); return here
    os.makedirs(os.path.dirname(here), exist_ok=True)
    p = subprocess.run(['git', 'clone', '-q', url, here], capture_output=True, text=True)
    if p.returncode:
        print(f"I couldn't fetch {url}: {(p.stderr or '').strip()[-200:]}\nIf it's private, log in once with your git "
              "host's tool (for GitHub: gh auth login), then run this again.")
        return None
    print(f'Fetched your project {name} into {here}.'); return here

def go_live(repo='.'):
    """Start Jarvis listening in the background on this computer, and say hello on his phone. One listener only."""
    from . import assistant, memory
    try:
        other = int(open(assistant.PIDFILE).read().strip())
        if telegram._alive(other):
            print(f'\nI am already listening on this computer (process {other}). Say hello on Telegram.'); return 0
    except (OSError, ValueError):
        pass
    log = os.path.join(os.path.expanduser('~'), '.hive', 'listen.log')
    os.makedirs(os.path.dirname(log), exist_ok=True)
    flags = dict(creationflags=0x00000008 | 0x00000200) if os.name == 'nt' else dict(start_new_session=True)
    subprocess.Popen([sys.executable, '-m', 'hive', 'listen'], cwd=os.path.abspath(repo), stdout=open(log, 'a'),
                     stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, **flags)
    ch = telegram.Channel(telegram.load())
    name = memory.project_name(repo) or 'your project'
    who = ch.name() or 'sir'
    ch.send(f"🐝 <b>At your service, {telegram.esc(who)}.</b> I'm on {telegram.esc(name)}, and I'll stay here.\n\n"
            "Tell me what you want for the business (\"I want more sign-ups\"), something to build, or send a picture "
            "of what you like. Say \"show me\" any time, \"ship it\" when you're happy, and I'll brief you each morning.",
            html=True)
    print(f'\nI am live on your phone. Close this window if you like; I keep listening (log: {log}).')
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
