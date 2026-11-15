"""Hive: silent coding-agent swarms coordinated through git, with the owner's intent delivered as tests."""
__version__ = '1.1.0'

import os as _os, sys as _sys

# The Python that runs Hive, for the commands builders type: `python3` on Linux and macOS; on Windows, where `python3`
# opens the Store, this interpreter's own path (found running Hive natively on Windows).
# Inside a Python environment (a venv, as on a cloud machine) the builders use that environment's Python, where Hive and
# pytest are installed: with the system python3 there, a cloud build found no pytest.
_in_venv = _sys.prefix != getattr(_sys, 'base_prefix', _sys.prefix)
PY = ('"' + _sys.executable.replace(chr(92), '/') + '"') if (_os.name == 'nt' or _in_venv) else 'python3'

# Copies Hive makes (the builders' clones, the shared upstream, results) are cloned with core.autocrlf=false: Windows
# git rewrote line endings there, so fresh copies showed changes nobody made and the guard's rebase refused to land.
# The owner's own checkout keeps his settings.

def claude_cmd(tools, edits=False):
    """Claude Code, headless, answering in JSON, with these tools (and file edits accepted when edits): the one place
    the command is written (the audit, Nov 15: nine copies of it drifted apart). Each caller keeps its own HIVE_*_CMD
    override."""
    return ('claude -p --output-format json' + (' --permission-mode acceptEdits' if edits else '') +
            ' --allowedTools ' + ' '.join(tools))

READ_TOOLS = ('Read', 'Grep', 'Glob', 'Bash')

def link(src, dst):
    """dst points at src (a dependency folder shared into a copy). A symlink where allowed; on Windows without the
    right to make one (no admin, no Developer Mode), a directory junction, which needs neither (the audit, Nov 15).
    True if linked."""
    try:
        _os.symlink(src, dst, target_is_directory=_os.path.isdir(src)); return True
    except OSError:
        if _os.name != 'nt' or not _os.path.isdir(src):
            return False
    import subprocess
    return subprocess.run(['cmd', '/c', 'mklink', '/J', dst, src], capture_output=True).returncode == 0

def argv(cmd):
    """A command line as a list for subprocess. On Windows `claude`, `codex` and other npm tools are .cmd files that
    CreateProcess cannot find by bare name, so every model call failed there and Hive fell back to canned replies."""
    import shlex, shutil
    parts = shlex.split(cmd)
    if parts and _os.name == 'nt':
        parts[0] = shutil.which(parts[0]) or parts[0]
    return parts
