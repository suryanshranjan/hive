#!/usr/bin/env python3
"""Ask the product owner how a business function should behave.
usage: tools/ask.py "SELECT FUNC(...), FUNC(...)"     one SELECT about exactly one function, at most 3 values
       tools/ask.py --allowance                       each function's question allowance and how much is used
Questions refused (wrong shape, several functions, allowance used up) are not charged."""
import json, socket, subprocess, sys
PORT = __PORT__
if len(sys.argv) < 2:
    print(__doc__); sys.exit(2)
who = subprocess.run(['git', 'config', 'user.name'], capture_output=True, text=True).stdout.strip()
req = {'allowance': True, 'worker': who} if sys.argv[1] == '--allowance' else {'sql': sys.argv[1], 'worker': who}
s = socket.create_connection(('127.0.0.1', PORT))
s.sendall((json.dumps(req) + '\n').encode())
print(s.makefile().readline().strip())
