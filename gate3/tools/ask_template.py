#!/usr/bin/env python3
"""Ask the product owner how a business function should behave.
usage: tools/ask.py "SELECT MASK('ab'), MASK('')"
One question = one SELECT returning one row of at most 3 values. Your whole team shares a budget of
__BUDGET__ questions; refused questions are not charged. The answer is the intended result."""
import json, socket, subprocess, sys
PORT = __PORT__
if PORT is None:
    print('No product owner is available for this project. Work from README.md and the visible tests.'); sys.exit(1)
if len(sys.argv) < 2:
    print(__doc__); sys.exit(2)
who = subprocess.run(['git', 'config', 'user.name'], capture_output=True, text=True).stdout.strip()
s = socket.create_connection(('127.0.0.1', PORT))
s.sendall((json.dumps({'sql': sys.argv[1], 'worker': who}) + '\n').encode())
print(s.makefile().readline().strip())
