"""Hive: silent coding-agent swarms coordinated through git, with the owner's intent delivered as tests."""
__version__ = '1.1.0'

import os as _os, sys as _sys

# The Python that runs Hive, for the commands builders type: `python3` on Linux and macOS; on Windows, where `python3`
# opens the Store, this interpreter's own path (found running Hive natively on Windows).
PY = 'python3' if _os.name != 'nt' else '"' + _sys.executable.replace(chr(92), '/') + '"'

# Copies Hive makes (the builders' clones, the shared upstream, results) are cloned with core.autocrlf=false: Windows
# git rewrote line endings there, so fresh copies showed changes nobody made and the guard's rebase refused to land.
# The owner's own checkout keeps his settings.
