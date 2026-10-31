#!/usr/bin/env python3
"""The owner is away until the morning: record a question for him. usage: queue_question.py <queue file> "your question"
He will answer every recorded question in the morning; build your best guess for now."""
import json, subprocess, sys, time
if len(sys.argv) < 3:
    print(__doc__); sys.exit(2)
who = subprocess.run(['git', 'config', 'user.name'], capture_output=True, text=True).stdout.strip()
open(sys.argv[1], 'a').write(json.dumps({'t': int(time.time()), 'worker': who, 'question': ' '.join(sys.argv[2:])[:2000]}) + '\n')
print('Recorded. The owner will answer it in the morning; build your best guess for now, and keep going.')
