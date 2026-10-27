#!/usr/bin/env python3
"""Create a swarm run: one bare repo per team (arm), one clone per worker, one rendered prompt per worker.

usage:
  make_swarm.py --run scale12 --seed gate3/seed_scale.bundle --prompt gate3/prompts/prompt_scale.md --arm F12:12
  make_swarm.py --run g8 --seed runs/g8/seed --prompt gate5/prompt_builder.md --ask-texts gate8/prompts/ask_texts.md \\
                --example-file runs/g8/example.txt --arm D0:3:none --arm D30:3:budget:7401:30 --arm NQ:3:quota:7402

--arm NAME:WORKERS[:none | :budget:PORT:BUDGET | :quota:PORT]  (default none). The arm decides tools/ask.py.
Prompt placeholders filled: {ME} {N} {WORK} {LOG} {ASK} {EXAMPLE}. {ASK} comes from the "## NAME" section of
--ask-texts (the format of gate5/prompts/ask_texts.md), with {EXAMPLE} inside it filled too.
Everything is written under runs/<run>/ (git-ignored)."""
import argparse, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASK_TEMPLATE = '''#!/usr/bin/env python3
"""Ask the product owner how a business function should behave.
usage: tools/ask.py "SELECT FUNC(...), FUNC(...)"      one SELECT returning one row of at most 3 values
       tools/ask.py --allowance                         what is left of the budget or allowances
Refused questions are not charged. The answer is the intended result."""
import json, socket, subprocess, sys
PORT = __PORT__
if PORT is None:
    print('No product owner is available for this project. Work from README.md and the visible tests.'); sys.exit(1)
if len(sys.argv) < 2:
    print(__doc__); sys.exit(2)
who = subprocess.run(['git', 'config', 'user.name'], capture_output=True, text=True).stdout.strip()
req = {'allowance': True, 'worker': who} if sys.argv[1] == '--allowance' else {'sql': sys.argv[1], 'worker': who}
s = socket.create_connection(('127.0.0.1', PORT))
s.sendall((json.dumps(req) + '\\n').encode())
print(s.makefile().readline().strip())
'''

def sh(*args, cwd=None):
    r = subprocess.run(list(args), cwd=cwd, capture_output=True, text=True)
    if r.returncode: sys.exit(f'failed: {" ".join(args)}\n{r.stderr}')
    return r.stdout

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', required=True); ap.add_argument('--seed', required=True)
    ap.add_argument('--prompt', required=True); ap.add_argument('--arm', action='append', required=True)
    ap.add_argument('--ask-texts'); ap.add_argument('--example-file')
    a = ap.parse_args()
    run = os.path.join(ROOT, 'runs', a.run); os.makedirs(os.path.join(run, 'logs'), exist_ok=True)
    template = open(a.prompt).read()
    asks = {}
    if a.ask_texts:
        t = open(a.ask_texts).read()
        asks = {m.group(1): m.group(2).strip() for m in re.finditer(r'^## (\S+)[^\n]*\n(.*?)(?=^## |\Z)', t, re.S | re.M)}
    example = open(a.example_file).read().strip() if a.example_file else ''
    seed = os.path.abspath(a.seed)
    for spec in a.arm:
        parts = spec.split(':'); name, n = parts[0], int(parts[1]); kind = parts[2] if len(parts) > 2 else 'none'
        port = 'None' if kind == 'none' else parts[3]
        up = os.path.join(run, f'up{name}.git'); shutil.rmtree(up, ignore_errors=True)
        sh('git', 'clone', '-q', '--bare', seed, up)
        tmp = os.path.join(run, f'.tmp{name}'); shutil.rmtree(tmp, ignore_errors=True)
        sh('git', 'clone', '-q', up, tmp)
        os.makedirs(os.path.join(tmp, 'tools'), exist_ok=True)
        p = os.path.join(tmp, 'tools', 'ask.py'); open(p, 'w').write(ASK_TEMPLATE.replace('__PORT__', port)); os.chmod(p, 0o755)
        sh('git', 'add', 'tools/ask.py', cwd=tmp)
        if subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=tmp).returncode:
            sh('git', '-c', 'user.name=hive', '-c', 'user.email=hive@local', 'commit', '-q', '-m', 'tools/ask.py for this run', cwd=tmp)
            sh('git', 'push', '-q', 'origin', 'HEAD:main', cwd=tmp)
        shutil.rmtree(tmp)
        ask = asks.get(name, '').replace('{EXAMPLE}', example)
        if '{ASK}' in template and not ask: sys.exit(f'no "## {name}" section in --ask-texts')
        for k in range(1, n + 1):
            me = f'{name}-w{k}'; work = os.path.join(run, 'work', me)
            shutil.rmtree(work, ignore_errors=True); sh('git', 'clone', '-q', up, work)
            sh('git', 'config', 'user.name', me, cwd=work); sh('git', 'config', 'user.email', f'{me.lower()}@hive.local', cwd=work)
            text = (template.replace('{ME}', me).replace('{N}', str(n)).replace('{WORK}', work)
                    .replace('{LOG}', os.path.join(run, 'logs', f'{me}.log')).replace('{ASK}', ask).replace('{EXAMPLE}', example))
            left = sorted(set(re.findall(r'\{[A-Z]+\}', text)))
            if left: sys.exit(f'unfilled placeholders in prompt: {left}')
            open(os.path.join(run, f'p_{me}.md'), 'w').write(text)
        print(f'{name}: {n} workers, tools/ask.py port {port}, repo {up}')
    print('next: python3 lab/launch.py --run', a.run)

if __name__ == '__main__':
    main()
