#!/usr/bin/env python3
"""The team's message board: every worker can post, and read what the others posted.

usage: tools/board.py post "<message>"     post to everyone (one or two lines)
       tools/board.py read                 messages you have not seen yet
       tools/board.py read --all           every message so far"""
import fcntl, os, subprocess, sys, time

def git(*a):
    return subprocess.run(['git', *a], capture_output=True, text=True).stdout.strip()

board, me = git('config', 'hive.board'), git('config', 'user.name') or 'someone'
if not board:
    print('No message board is set up for this clone.'); sys.exit(1)
if len(sys.argv) < 2 or sys.argv[1] not in ('post', 'read'):
    print(__doc__); sys.exit(2)
seen_path = f'{board}.seen.{me}'
if sys.argv[1] == 'post':
    msg = ' '.join(sys.argv[2:]).strip().replace('\n', ' ')
    if not msg:
        print('Nothing to post.'); sys.exit(2)
    with open(board, 'a') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(f'{time.strftime("%H:%M:%S")} {me}: {msg[:600]}\n')
    print('posted')
else:
    lines = open(board).read().splitlines() if os.path.exists(board) else []
    start = 0 if '--all' in sys.argv else int(open(seen_path).read() or 0) if os.path.exists(seen_path) else 0
    new = lines[start:]
    print('\n'.join(new) if new else '(no new messages)')
    open(seen_path, 'w').write(str(len(lines)))
