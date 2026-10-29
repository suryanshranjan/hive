"""A stand-in for Claude reading the code (no tokens): checks it was asked read-only, in the project, then answers."""
import json, os, sys
prompt = sys.stdin.read()
ok = 'read only' in prompt and os.path.isdir('.git')
if ok and 'He is checking these rules' in prompt and 'what does rule 6 mean' in prompt:   # a question during the review
    print(json.dumps({'result': 'In the code, a brand that invites another brand gets 500 rupees once the new brand pays.'}))
else:
    print(json.dumps({'result': 'Refunds go back to the brand within 7 days, sir.' if ok and 'How do refunds work' in prompt
                      else 'wrong question'}))
