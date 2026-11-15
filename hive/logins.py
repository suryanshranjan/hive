"""Logins Hive depends on, renewed from the owner's phone when they expire (the owner: "these activities Hive must be
able to handle autonomously": an expired AWS sign-in stopped a move to the cloud until he typed at the computer).

Before Hive uses a service that needs his login, it checks the login. If it has expired, Hive starts the sign-in that
works from another device, sends him the link on Telegram, takes the code it shows him (when there is one), finishes the
sign-in, checks it worked and carries on. He never needs to be at the computer:
- AWS: `aws login --remote` shows a link; after he signs in, AWS shows a code he sends back.
- GitHub: `gh auth login --web` shows a one-time code; he opens github.com/login/device and types it in.
- Vercel: `vercel login` shows a link with the code in it; he opens it and approves.
A missing tool that installs with one command (Vercel's, through npm) is installed first, so "we're on Vercel" works
from the phone with nobody at the computer.
A login on a different account than before is not switched silently: he is asked."""
import os, queue, re, shutil, subprocess, threading, time

from . import telegram

SERVICES = {
    'aws': {'name': 'AWS', 'check': ['aws', 'sts', 'get-caller-identity', '--output', 'json'],
            'login': ['aws', 'login', '--remote'], 'pastes_code': True},
    'github': {'name': 'GitHub', 'check': ['gh', 'auth', 'status', '--hostname', 'github.com'],
               'login': ['gh', 'auth', 'login', '--web', '--hostname', 'github.com', '--git-protocol', 'https'],
               'pastes_code': False},
    'vercel': {'name': 'Vercel', 'check': ['vercel', 'whoami'], 'login': ['vercel', 'login'], 'pastes_code': False,
               'install': ['npm', 'install', '-g', 'vercel'], 'device': 'https://vercel.com/oauth/device'},
}

def _exe(cmd):
    """The command with its program found on this computer, or None when it is not installed. On Windows npm's tools
    are .cmd files, which a bare program name does not start (found setting up Gate 110)."""
    path = shutil.which(cmd[0])
    return [path] + list(cmd[1:]) if path else None

def install(ch, service):
    """Install a missing tool that installs with one command; True when it is there afterwards."""
    s = SERVICES[service]
    if _exe(s['login']):
        return True
    if not s.get('install') or not _exe(s['install']):
        return False
    ch.send(f"🔧 Installing {s['name']}'s tool on this computer first; a minute or two.")
    try:
        subprocess.run(_exe(s['install']), capture_output=True, text=True, timeout=600)
    except (subprocess.TimeoutExpired, OSError):
        return False
    return bool(_exe(s['login']))
URL = re.compile(r'https://\S+')
DEVICE_CODE = re.compile(r'\b([A-Z0-9]{4}-[A-Z0-9]{4})\b')
SWITCH = re.compile(r'already configured to use .*overwrite it.*\(y/n\)', re.I | re.S)

def ok(service, timeout=60):
    """True when the login works now."""
    s = SERVICES[service]
    cmd = _exe(s['check'])
    if not cmd:
        return False
    if service == 'aws':   # the login Hive itself uses: the limited profile once made (its keys do not expire)
        from . import cloud_aws
        prof = cloud_aws.default_profile()
        if prof:
            cmd = cmd + ['--profile', prof]
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False

def _reader(proc, q):
    """Pass the sign-in's output on as it comes, character by character (its prompts end without a newline)."""
    buf = ''
    while True:
        c = proc.stdout.read(1)
        if not c:
            q.put(('end', buf)); return
        buf += c
        if c == '\n' or buf.endswith(('(y/n): ', ': ')):
            q.put(('line', buf)); buf = ''

def _until(q, want, seconds, seen):
    """Read the sign-in's output until want(text so far) or it ends; returns the text so far."""
    t0 = time.time()
    while time.time() - t0 < seconds:
        try:
            kind, text = q.get(timeout=1)
        except queue.Empty:
            continue
        seen.append(text)
        if want(''.join(seen)) or kind == 'end':
            break
    return ''.join(seen)

def ensure(ch, service, poll=20, popen=subprocess.Popen, wait_s=900):
    """Make sure the login works, renewing it from his phone if it has expired. True when it works (now or after)."""
    s = SERVICES[service]
    if ok(service):
        return True
    if not install(ch, service):
        ch.send(f"🔑 I need the {s['name']} command line on this computer to do that, and it isn't installed. Your "
                f"engineer installs it once; then I can carry on from here.")
        return False
    if ok(service):
        return True
    proc = popen(_exe(s['login']), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                 bufsize=0)
    q, seen = queue.Queue(), []
    threading.Thread(target=_reader, args=(proc, q), daemon=True).start()
    try:
        if s['pastes_code']:
            text = _until(q, lambda t: URL.search(t), 60, seen)
            m = URL.search(text)
            if not m:
                ch.send(f"⚠️ I couldn't start the {s['name']} sign-in just now. Try again in a minute."); return False
            ch.send(f"🔑 Your {s['name']} sign-in has expired, so I'll renew it.\n\n1. Tap this link and sign in:\n"
                    f"{m.group(0)}\n2. Send me the code it shows you.",
                    buttons=[[('Not now', f'lgn|skip|{service}')]])
            kind, got = telegram._wait(ch, poll, {f'lgn|skip|{service}'})
            if kind == 'tap':
                ch.send("Very good. I'll leave it for now."); return False
            code = next((w for w in re.split(r'\s+', got.strip()) if len(w) >= 6), got.strip())
            proc.stdin.write(code + '\n'); proc.stdin.flush()
        else:
            text = _until(q, lambda t: DEVICE_CODE.search(t) and URL.search(t), 60, seen)
            code, m = DEVICE_CODE.search(text), URL.search(text)
            if not code:
                ch.send(f"⚠️ I couldn't start the {s['name']} sign-in just now. Try again in a minute."); return False
            proc.stdin.write('\n'); proc.stdin.flush()   # "press Enter to open the browser": not on this computer
            link = m.group(0) if m else s.get('device', 'https://github.com/login/device')
            how = "Check it shows this code, then approve" if code.group(1) in link else "Type this code"
            ch.send(f"🔑 I need you to sign in to {s['name']} (it isn't signed in on this computer, or it has expired)."
                    f"\n\n1. Tap this link: {link}\n2. {how}: <b>{code.group(1)}</b>\n\n"
                    "I'll carry on by myself once you've approved it.", html=True)
        text = _until(q, lambda t: bool(SWITCH.search(t[-400:])), wait_s, seen)
        if SWITCH.search(text[-400:]):   # signed in with another account than before: his choice, never silent
            ch.send(f"🔑 You signed in to a different {s['name']} account than this computer used before. Switch to it?",
                    buttons=[[('Yes, switch', f'lgn|switch|{service}')], [('No, keep the old one', f'lgn|keep|{service}')]])
            kind, got = telegram._wait(ch, poll, {f'lgn|switch|{service}', f'lgn|keep|{service}'})
            yes = got == f'lgn|switch|{service}' or (kind == 'text' and got.strip().lower().startswith(('y', 'haan', 'switch')))
            proc.stdin.write('y\n' if yes else 'n\n'); proc.stdin.flush()
        try:
            proc.wait(timeout=wait_s)
        except subprocess.TimeoutExpired:
            proc.kill()
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
    if ok(service):
        ch.send(f"✅ Signed in to {s['name']}. Carrying on."); return True
    tail = ' '.join(''.join(seen).split())[-160:]
    ch.send(f"⚠️ That {s['name']} sign-in didn't go through" + (f" ({telegram.esc(tail)})" if tail else '') +
            ". Say it again when you're ready and I'll start a fresh one.", html=True)
    return False
