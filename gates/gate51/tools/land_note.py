#!/usr/bin/env python3
"""Land with a one-line note for the team: tools/land_note.py <short_name> "<what you did>" "<one line others must know>"
(the note rides in the landing commit; everything else is exactly tools/land.py)."""
import os, subprocess, sys
if len(sys.argv) != 4:
    print(__doc__); sys.exit(2)
name, msg, note = sys.argv[1:]
here = os.path.dirname(os.path.abspath(__file__))
sys.exit(subprocess.run([sys.executable, os.path.join(here, 'land.py'), name,
                         f"{msg}\n\nTeam-note: {' '.join(note.split())[:300]}"]).returncode)
