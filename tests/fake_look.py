"""A stand-in for Claude reading (and trying) the code (no tokens): checks it works in a throwaway copy of the project,
not the project itself, then answers. It writes a file, as a script it ran might, to show that never reaches his folder."""
import json, os, sys
prompt = sys.stdin.read()
copy = 'scratch copy' in prompt and not os.path.isdir('.git') and os.path.basename(os.getcwd()) == 'project' \
    and 'hive_look_' in os.getcwd()
open('tried_it.txt', 'w').write('a script ran here')
if copy and 'He is checking these rules' in prompt and 'what does rule 6 mean' in prompt:   # a question during the review
    print(json.dumps({'result': 'In the code, a brand that invites another brand gets 500 rupees once the new brand pays.'}))
else:
    print(json.dumps({'result': 'Refunds go back to the brand within 7 days, sir.' if copy and 'How do refunds work' in prompt
                      else 'wrong question'}))
