#!/usr/bin/env python3
"""The team's notes: one line each, carried in landing commits as "Team-note: ...". Shows the latest, newest first.
usage: tools/notes.py [n]"""
import re, subprocess, sys
n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
subprocess.run(['git', 'fetch', '-q', 'origin', 'main'], capture_output=True)
out = subprocess.run(['git', 'log', 'origin/main', '-n', '300', '--format=%an%x00%B%x01'], capture_output=True, text=True).stdout
got = []
for entry in out.split('\x01'):
    if '\x00' not in entry:
        continue
    who, body = entry.split('\x00', 1)
    for line in body.splitlines():
        if line.strip().startswith('Team-note:'):
            got.append(f"{who.strip()}: {re.sub(r' \(lock \S+ released\)$', '', line.split('Team-note:', 1)[1].strip())}")
print('\n'.join(got[:n]) if got else '(no team notes yet)')
