"""Publish and reconcile the exact commit validated by a task-bound builder."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

from . import store, tasks, tools


def git(repo, *args, required=True):
    proc = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True, timeout=60)
    if proc.returncode and required:
        raise tools.Refused('The recorded build branch or commit is unavailable.')
    return proc.stdout.strip() if proc.returncode == 0 else ''


def identity():
    step = tasks.ACTIVE_STEP.get()
    if step:
        return step
    tid = os.getenv('HIVE_PLAN_TASK')
    return (tid, int(os.getenv('HIVE_PLAN_STEP', '1'))) if tid else None


def begin(repo, source, base_ref, branch, home):
    key = identity()
    if not key:
        return
    with store.transaction() as con:
        row = con.execute('SELECT project,active_step,state,mode FROM tasks WHERE id=?', (key[0],)).fetchone()
        if not row or row['mode'] != 'build':
            return
        if row['project'] != tasks._project(repo) or row['active_step'] != key[1] or row['state'] != 'running':
            raise tools.Refused('The build no longer owns this task step.')
        base = git(source, 'rev-parse', 'HEAD')
        dest = 'refs/heads/' + branch
        old = git(repo, 'rev-parse', '--verify', dest, required=False)
        if (key[1] == 1 and old) or (key[1] > 1 and old != base):
            raise tools.Refused('The build branch changed before this step started.')
        con.execute('INSERT INTO build_manifests(task_id,step,project,base_ref,base_sha,branch,previous_sha,state_path) '
                    'VALUES(?,?,?,?,?,?,?,?)', (*key, row['project'], base_ref, base, dest, old, str(Path(home)/'state.json')))


def manifest(key):
    if key:
        row = store.connect().execute('SELECT * FROM build_manifests WHERE task_id=? AND step=?', key).fetchone()
        return dict(row) if row else None


def publish(state, result, tests):
    key = identity()
    saved = manifest(key)
    if not saved:
        return False
    tasks.boundary(key[0])
    repo = state['repo']
    sha = git(result, 'rev-parse', 'HEAD')
    if (tasks._project(repo) != saved['project'] or saved['branch'] != 'refs/heads/hive/' + state['name']
            or git(repo, 'rev-parse', saved['base_ref']) != saved['base_sha']):
        raise tools.Refused('The project or base branch diverged during validation.')
    store.connect().execute('UPDATE build_manifests SET result_sha=?,tests=? WHERE task_id=? AND step=?',
                            (sha, json.dumps(tests), *key))
    git(repo, 'fetch', '--no-tags', result, sha)
    git(repo, 'merge-base', '--is-ancestor', saved['base_sha'], sha)
    git(repo, 'update-ref', saved['branch'], sha, saved['previous_sha'] or '0' * len(sha))
    if tests and all(tests.values()) and state['code'] == 0:
        store.connect().execute('UPDATE build_manifests SET receipt=? WHERE task_id=? AND step=?',
                                (time.time(), *key))
    return True


def validate(tid, n, repo):
    saved = manifest((tid, n))
    if not saved or saved['project'] != tasks._project(repo) or not saved['result_sha']:
        return None
    sha = saved['result_sha']
    def matches():
        return (git(repo, 'rev-parse', '--verify', saved['branch'], required=False) == sha and
                (saved['base_ref'] == saved['branch'] or
                 git(repo, 'rev-parse', '--verify', saved['base_ref'], required=False) == saved['base_sha']))
    if not matches():
        return None
    try:
        path = Path(saved['state_path'])
        state = json.loads(path.read_text('utf-8'))
        if (state.get('plan_task') != tid or tasks._project(state['repo']) != saved['project'] or
                'refs/heads/hive/' + state['name'] != saved['branch'] or state.get('code') != 0):
            return None
        artifact = Path(state['final']) / 'up.git'
        if git(artifact, 'rev-parse', '--verify', state['b'], required=False) != sha:
            return None
        tests = json.loads(saved['tests'] or '{}')
        if not saved['receipt'] or not tests:
            from . import start
            with tempfile.TemporaryDirectory(prefix='hive-revalidate-') as tmp:
                git(repo, 'clone', '--quiet', '--no-checkout', '--no-local', repo, tmp)
                git(tmp, 'checkout', '--quiet', '--detach', sha)
                tests = start.run_tests(tmp, state['test_cmd'])
        if not tests or not all(tests.values()) or not matches():
            return None
        store.connect().execute('UPDATE build_manifests SET tests=?,receipt=COALESCE(receipt,?) WHERE task_id=? AND step=?',
                                (json.dumps(tests), time.time(), tid, n))
        return {'commit': sha, 'base': saved['base_sha'], 'branch': saved['branch'], 'tests': tests,
                'state_path': str(path), 'artifact': str(artifact)}
    except (OSError, KeyError, ValueError, RuntimeError, tools.Refused, subprocess.TimeoutExpired):
        return None
