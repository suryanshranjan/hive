"""A stand-in for Claude reading the code (no tokens): checks it was asked read-only, in the project, then answers."""
import json, os, sys
prompt = sys.stdin.read()
ok = 'read only' in prompt and 'How do refunds work' in prompt and os.path.isdir('.git')
print(json.dumps({'result': 'Refunds go back to the brand within 7 days, sir.' if ok else 'wrong question'}))
