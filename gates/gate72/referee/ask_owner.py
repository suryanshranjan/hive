#!/usr/bin/env python3
"""Ask the product owner a question in plain words. usage: ask_owner.py <port> "your question"
       ask_owner.py <port> --answers     every answer so far, and the questions he has not answered yet
He answers one question at a time. If he has not answered within 90 seconds, your question stays with him: work on
another part meanwhile, and read --answers before you build the part it decides."""
import json, socket, subprocess, sys, time
def req(r):
    s = socket.create_connection(('127.0.0.1', int(sys.argv[1])), timeout=60)
    s.sendall((json.dumps(r) + '\n').encode()); return json.loads(s.makefile().readline())
if len(sys.argv) < 3:
    print(__doc__); sys.exit(2)
if sys.argv[2] == '--answers':
    print(req({'answers': True})['answer']); sys.exit(0)
who = subprocess.run(['git', 'config', 'user.name'], capture_output=True, text=True).stdout.strip()
qid = req({'question': ' '.join(sys.argv[2:]), 'worker': who})['id']; t0 = time.time()
while time.time() - t0 < 90:
    a = req({'get': qid})['answer']
    if a:
        print('The owner says: ' + a); sys.exit(0)
    time.sleep(3)
print("He has your question but has not answered yet (he answers one at a time). Work on another part meanwhile, and read "
      f"`{sys.argv[0]} {sys.argv[1]} --answers` before you build the part this question decides.")
