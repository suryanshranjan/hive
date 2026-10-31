#!/usr/bin/env python3
"""Ask the product owner a question in plain words. usage: ask_owner.py <port> "your question"
He is busy: one decision per question. His answer is printed."""
import json, socket, subprocess, sys
if len(sys.argv) < 3:
    print(__doc__); sys.exit(2)
who = subprocess.run(['git', 'config', 'user.name'], capture_output=True, text=True).stdout.strip()
s = socket.create_connection(('127.0.0.1', int(sys.argv[1])), timeout=600)
s.sendall((json.dumps({'question': ' '.join(sys.argv[2:]), 'worker': who}) + '\n').encode())
print('The owner says: ' + json.loads(s.makefile().readline())['answer'])
