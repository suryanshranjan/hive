"""Ship it, from the owner's phone: his latest build goes to his engineer as a pull request (a merge request on GitLab).
Hive pushes only its own branch, hive/<name>, to his project's remote and asks for a merge into his main branch; it
never pushes to, or merges into, his main branch itself (the hard limit Jarvis states: every build arrives as a separate
tested copy that a person merges).

The owner (the Tony scenario): "Ship it" should mean the engineer gets it, ready to review and merge, with what was
asked, what was checked and what it cost, not a branch name he has to pass on by hand."""
import json, os, re, shutil, subprocess

def _git(repo, *a):
    return subprocess.run(['git', '-C', repo, *a], capture_output=True, text=True, encoding='utf-8', errors='replace')

def _run(cmd, cwd):   # gh and glab (tests replace this)
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')

def web(url):
    """(host kind, 'owner/name' path) of a remote URL: ('github', 'acme/shop'), ('gitlab', ...), or (None, None)."""
    m = re.match(r'^(?:https?://(?:[^@/]+@)?|ssh://git@|git@)([^/:]+)[:/](.+?)(?:\.git)?/?$', url.strip())
    if not m:
        return None, None
    host, path = m.group(1).lower(), m.group(2)
    return ('github' if 'github' in host else 'gitlab' if 'gitlab' in host else None), (host, path)

def body(state):
    """What the engineer reads: what the owner asked for, what Hive checked, what it cost, and that he asked to ship it."""
    goal = re.sub(r'\(his picture: [^)]*\)', '(with a picture he sent, in .hive/refs)', state.get('goal', '')).strip()
    lines = ['Built by Hive. The owner asked to ship it from his phone.', '', '**What he asked for**', '', goal[:3000], '',
             '**Checked**', '', state.get('check') or 'Every test was run on the result.']
    if state.get('cost'):
        lines += ['', f"Builders' cost: about ${state['cost']:.2f}."]
    lines += ['', 'This branch never touched your main branch. Review it, and merge it when you are happy.']
    return '\n'.join(lines)

def title(state):
    goal = re.sub(r'\s+', ' ', re.sub(r'\(his picture: [^)]*\)|\[photo: [^\]]*\]', '', state.get('goal', ''))).strip()
    return 'Hive: ' + (goal[:70] + ('...' if len(goal) > 70 else '') if goal else state['name'])

def ship(repo, state):
    """Push hive/<name> and open (or find) its pull request. Returns {'ok', 'branch', 'url', 'how', 'why'}:
    how is 'pr' (a pull/merge request opened or already open), 'link' (pushed; url opens a new one in the browser) or
    'pushed' (pushed to a remote Hive cannot open requests on). why, when not ok: 'no_build', 'no_remote', 'push'."""
    branch, base = f"hive/{state['name']}", state.get('branch') or 'main'
    out = {'ok': False, 'branch': branch, 'url': None, 'how': None, 'why': None}
    if not branch.startswith('hive/') or branch == base or _git(repo, 'rev-parse', '--verify', '-q', branch).returncode:
        out['why'] = 'no_build'; return out
    url = _git(repo, 'remote', 'get-url', 'origin').stdout.strip()
    if not url:
        out['why'] = 'no_remote'; return out
    # only Hive's own branch, by its full name; a fix round rewrites it in place, so it is replaced, never merged into
    p = _git(repo, 'push', '-q', 'origin', f'+refs/heads/{branch}:refs/heads/{branch}')
    if p.returncode:
        out.update(why='push', error=(p.stderr or p.stdout).strip()[-300:]); return out
    out['ok'] = True
    kind, where = web(url)
    if kind == 'github' and shutil.which('gh'):
        r = _run(['gh', 'pr', 'view', branch, '--json', 'url,state'], repo)
        try:
            j = json.loads(r.stdout)
        except ValueError:
            j = {}
        if r.returncode == 0 and j.get('state') == 'OPEN':
            out.update(url=j['url'], how='pr', again=True); return out
        r = _run(['gh', 'pr', 'create', '--head', branch, '--base', base, '--title', title(state), '--body', body(state)], repo)
        found = re.findall(r'https://\S+/pull/\d+', r.stdout + r.stderr)
        if found:
            out.update(url=found[-1], how='pr'); return out
    if kind == 'gitlab' and shutil.which('glab'):
        r = _run(['glab', 'mr', 'create', '--source-branch', branch, '--target-branch', base, '--title', title(state),
                  '--description', body(state), '--yes'], repo)
        found = re.findall(r'https://\S+/merge_requests/\d+', r.stdout + r.stderr)
        if found:
            out.update(url=found[-1], how='pr'); return out
    if kind == 'github':
        out.update(url=f'https://{where[0]}/{where[1]}/compare/{base}...{branch}?expand=1', how='link')
    elif kind == 'gitlab':
        out.update(url=f'https://{where[0]}/{where[1]}/-/merge_requests/new?merge_request%5Bsource_branch%5D={branch}'
                       f'&merge_request%5Btarget_branch%5D={base}', how='link')
    else:
        out['how'] = 'pushed'
    return out
