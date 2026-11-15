"""Running other programs with a time limit that really holds (the audit, Nov 15: the test suite and builders ran with
none, so one hung test or agent blocked a swarm or an overnight build for ever).

subprocess.run(..., timeout=) kills only the program it started. A shell command (`npm test`, `pytest ...`) starts
children of its own, and those kept running, holding the pipes open, so the call still never returned. Here the
command gets its own process group, and on timeout the whole group goes (taskkill /T on Windows)."""
import os, signal, subprocess

def _kill_tree(p):
    if os.name == 'nt':
        subprocess.run(['taskkill', '/F', '/T', '/PID', str(p.pid)], capture_output=True)
    else:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except OSError:
            pass
    try:
        p.kill()
    except OSError:
        pass

def run(cmd, timeout, shell=False, **kw):
    """Like subprocess.run(cmd, capture_output=True, text=True), but timeout is required and kills everything the command
    started. Returns a CompletedProcess, or None if the time ran out."""
    if not timeout or timeout <= 0:
        raise ValueError('run() needs a time limit')
    kw.setdefault('stdout', subprocess.PIPE); kw.setdefault('stderr', subprocess.PIPE)
    kw.setdefault('text', True)
    if kw.get('text'):
        kw.setdefault('encoding', 'utf-8'); kw.setdefault('errors', 'replace')
    if os.name == 'nt':
        kw.setdefault('creationflags', subprocess.CREATE_NEW_PROCESS_GROUP)
    else:
        kw.setdefault('start_new_session', True)
    p = subprocess.Popen(cmd, shell=shell, **kw)
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_tree(p)
        try:
            p.communicate(timeout=10)
        except Exception:
            pass
        return None
    return subprocess.CompletedProcess(cmd, p.returncode, out, err)

def seconds(name, default):
    """A time limit from the environment (seconds), or the default."""
    try:
        v = float(os.environ.get(name, default))
        return v if v > 0 else default
    except ValueError:
        return default
