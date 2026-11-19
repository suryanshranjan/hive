"""Freeze execution, transport checked manifests and remap eligible work on arrival."""

import hashlib
import json
from pathlib import Path
import re
import secrets
import subprocess
import tempfile
import time

from . import actions, build_receipts, projects, store, tasks, tools

CLOSED = ('succeeded', 'cancelled', 'handled', 'owner_confirmed', 'owner_reported_incomplete')


def read_manifest(path):
    data = json.loads(Path(path).read_text('utf-8'))
    if (
        not isinstance(data, dict)
        or data.get('version') != 1
        or not re.fullmatch('[0-9a-f]{24}', str(data.get('nonce', '')))
        or not re.fullmatch('[0-9a-f]{32}', str(data.get('project_id', '')))
    ):
        raise tools.Refused('Invalid handoff identity.')
    for item in data['builds']:
        if (
            not re.fullmatch('[0-9a-f]{12}', str(item['id']))
            or type(item['step']) is not int
            or item['step'] < 1
            or item.get('directory', f"{item['id']}-{item['step']}") != f"{item['id']}-{item['step']}"
        ):
            raise tools.Refused('Invalid build artifact location.')
    return data


def available(repo):
    if store.connect().execute('SELECT 1 FROM handoff_fences LIMIT 1').fetchone():
        raise tools.Refused('Hive is quiesced for handoff and will not overwrite the destination. Return ownership before continuing.')


def refs(repo):
    result = build_receipts.git(repo, 'for-each-ref', '--format=%(refname) %(objectname)', 'refs/heads')
    return dict(line.split() for line in result.splitlines())


def checkpoint(row):
    encoded = json.dumps(dict(row), sort_keys=True, separators=(',', ':')).encode()
    return {
        'id': row['id'],
        'state': row['state'],
        'active_step': row['active_step'],
        'digest': hashlib.sha256(encoded).hexdigest(),
    }


def freeze(repo):
    project = projects.path(repo)
    with store.transaction() as con:
        available(repo)
        pid = projects.ensure(repo)
        if not pid['repository'] or pid['repository'] != projects.repository(repo):
            raise tools.Refused('A checked handoff requires a Git repository.')
        rows = [
            checkpoint(r)
            for r in con.execute('SELECT * FROM tasks WHERE project=?', (project,))
            if r['state'] not in CLOSED
        ]
        current = tasks.ACTIVE_TASK.get()
        if con.execute("SELECT 1 FROM tasks WHERE state='running' AND id<>?",(current or '',)).fetchone():
            raise tools.Refused('A task is executing. Pause it at a checkpoint before handoff.')
        if con.execute(
            "SELECT 1 FROM execution_queue WHERE worker IS NOT NULL AND task_id<>?",
            (current or '',),
        ).fetchone():
            raise tools.Refused('Wait for the current worker to release its checkpoint.')
        if con.execute("SELECT 1 FROM memory_jobs WHERE state='running'").fetchone():
            raise tools.Refused('Memory extraction is running. Wait for it to reach its checkpoint.')
        for action in con.execute("SELECT id,project FROM actions WHERE state='executing'"):
            if action['id'] != actions.EXECUTING.get():
                raise tools.Refused('An external action is executing. Check its outcome before handoff.')
        if con.execute('SELECT 1 FROM browser_control').fetchone():
            raise tools.Refused('Return the browser to Hive before moving this project.')
        nonce = secrets.token_hex(12)
        action = actions.get(actions.EXECUTING.get()) if actions.EXECUTING.get() else None
        initiating_action = action['id'] if action and action['tool'] == 'cloud_on' else None
        con.execute(
            'INSERT INTO handoff_fences(project,nonce,initiating_task,initiating_action) VALUES(?,?,?,?)',
            (project, nonce, current, initiating_action),
        )
        return {
            'version': 1,
            'nonce': nonce,
            'project_id': pid['id'],
            'repository': pid['repository'],
            'memory_alias': pid['memory_alias'],
            'source': project,
            'machine': projects.machine(),
            'branch': build_receipts.git(repo, 'symbolic-ref', 'HEAD'),
            'refs': refs(repo),
            'tasks': rows,
            'builds': [],
            'frozen': True,
        }


def quiet_reader(repo, manifest):
    if not manifest['frozen']:
        return
    from . import telegram

    with store.transaction() as con:
        readers = con.execute("SELECT value FROM profile WHERE key LIKE 'telegram_reader:%'").fetchall()
    if not any(telegram._alive(json.loads(r[0])) for r in readers):
        return
    until = time.monotonic() + 35
    while time.monotonic() < until:
        row = (
            store.connect()
            .execute('SELECT reader_quiet FROM handoff_fences WHERE nonce=?', (manifest['nonce'],))
            .fetchone()
        )
        if row and row[0]:
            return
        time.sleep(0.1)
    raise tools.Refused('The Telegram listener did not reach a quiescent checkpoint.')


def release(manifest):
    store.connect().execute('DELETE FROM handoff_fences WHERE nonce=?', (manifest['nonce'],))


def listener_ready(repo, nonce, timeout=20):
    """Read back ownership and a live reader on the receiving installation."""
    from . import telegram

    until = time.monotonic() + timeout
    while True:
        if store.get('checked_handoff:' + nonce) == projects.path(repo):
            readers = (
                store.connect()
                .execute("SELECT value FROM profile WHERE key LIKE 'telegram_reader:%'")
                .fetchall()
            )
            if any(telegram._alive(json.loads(row[0])) for row in readers):
                return True
        if time.monotonic() >= until:
            return False
        time.sleep(0.25)


def prepare_return(repo, destination, folder, outbound_nonce):
    """Run on the sending machine. A retried pull uses the same quiescent checkpoint."""
    from .cloud import Target

    folder = Path(folder).resolve()
    folder.mkdir(exist_ok=True, parents=True)
    record = folder / 'handoff.json'
    if record.exists():
        return
    incoming = Path(store.path()).with_name('handoff.json')
    if incoming.exists():
        # A --no-start target has never accepted ownership. No target task can have run.
        data = read_manifest(incoming)
        if data['nonce'] != outbound_nonce:
            raise tools.Refused('Different handoff already present.')
        if store.get('checked_handoff:' + outbound_nonce) is None:
            store.put('retired_handoff:' + outbound_nonce, True)
            record.write_text(json.dumps({'unopened': outbound_nonce}), encoding='utf-8')
            return
    if not store.get('checked_handoff:' + outbound_nonce):
        raise tools.Refused('The return database does not contain this checked handoff.')
    data = freeze(repo)
    try:
        quiet_reader(repo, data)
        with tempfile.TemporaryDirectory() as temporary:
            export(Target(str(folder)), str(folder), temporary, data, destination)
    except BaseException:
        release(data)
        raise


def export(target, dst, temp, manifest, destination):
    """Copy only state JSON and Git bundles named by recorded build manifests."""
    manifest['destination'] = destination
    ids = {r['id'] for r in manifest['tasks']}
    ids.update(
        r[0]
        for r in store.connect().execute(
            "SELECT c.child FROM child_builds c JOIN tasks p ON c.parent=p.id WHERE p.project=? AND p.state='waiting_child'",
            (manifest['source'],),
        )
    )
    for row in (
        store.connect()
        .execute('SELECT * FROM build_manifests WHERE project=?', (manifest['source'],))
        .fetchall()
    ):
        if row['task_id'] not in ids:
            continue
        item = {
            'id': row['task_id'],
            'step': row['step'],
            'branch': row['branch'],
            'commit': row['result_sha'],
        }
        manifest['builds'].append(item)
        saved = Path(row['state_path'])
        if not saved.is_file() or not row['result_sha']:
            continue
        state = json.loads(saved.read_text('utf-8'))
        gitdir = Path(state['final']) / 'up.git'
        if (
            state.get('plan_task') != row['task_id']
            or not gitdir.is_dir()
            or build_receipts.git(gitdir, 'rev-parse', '--verify', state['b'], required=False)
            != row['result_sha']
        ):
            continue
        key = f"{row['task_id']}-{row['step']}"
        bundle = Path(temp) / (key + '.bundle')
        build_receipts.git(gitdir, 'bundle', 'create', str(bundle), state['b'])
        folder = f"{dst}/handoff-{manifest['nonce']}/{key}"
        target.put(str(bundle), folder + '/artifact.bundle')
        target.put(str(saved), folder + '/state.json')
        item['directory'] = key
    local = Path(temp) / 'handoff.json'
    local.write_text(json.dumps(manifest), encoding='utf-8')
    target.put(str(local), dst + '/handoff.json')


def restore(repo, manifest_path=None):
    manifest_path = Path(manifest_path or Path(store.path()).with_name('handoff.json'))
    if not manifest_path.exists():
        return
    data = read_manifest(manifest_path)
    if store.get('retired_handoff:' + data['nonce']):
        raise tools.Refused('Ownership was returned to the source machine.')
    checked = manifest_path.with_name('checked-' + data['nonce'] + '.json')
    if store.get('checked_handoff:' + data['nonce']) == projects.path(repo):
        manifest_path.replace(checked)
        return
    old, new = data['source'], projects.path(repo)
    dst = Path(data['destination'])
    expected = dst if dst.is_absolute() else Path.home() / dst
    if (
        data.get('version') != 1
        or projects.path(expected) != new
        or projects.repository(repo) != data['repository']
        or build_receipts.git(repo, 'symbolic-ref', 'HEAD') != data['branch']
    ):
        raise tools.Refused(
            'The destination path, repository identity or checked branch differs. Both snapshots are retained.'
        )
    current = refs(repo)
    if any(data['refs'].get(branch) != sha for branch, sha in current.items()) or build_receipts.git(
        repo, 'status', '--porcelain', '--untracked-files=normal'
    ):
        raise tools.Refused('The destination checkout diverged. Both snapshots are retained.')
    missing = []
    for branch, sha in data['refs'].items():
        if branch not in current:
            remote = 'refs/remotes/origin/' + branch.removeprefix('refs/heads/')
            if build_receipts.git(repo, 'rev-parse', '--verify', remote, required=False) != sha:
                raise tools.Refused('A recorded branch is missing on the destination.')
            missing.append((branch, sha))
    with store.transaction() as con:
        project = con.execute('SELECT * FROM projects WHERE id=?', (data['project_id'],)).fetchone()
        if (
            not project
            or project['repository'] != data['repository']
            or project['memory_alias'] != data['memory_alias']
        ):
            raise tools.Refused('The database does not match the handoff manifest.')
        binding = projects.mapped(repo)
        if binding and binding['id'] != project['id']:
            raise tools.Refused('The destination path already belongs to another project.')
        recorded = {item['id']: item for item in data['tasks']}
        actual = {
            r['id']: checkpoint(r)
            for r in con.execute('SELECT * FROM tasks WHERE project_id=?', (project['id'],))
            if r['state'] not in CLOSED
        }
        if actual != recorded:
            raise tools.Refused('Task checkpoints diverged. Both snapshots are retained.')
        con.execute(
            'INSERT OR IGNORE INTO project_paths VALUES(?,?,?)', (project['id'], projects.machine(), new)
        )
        remap(repo, old, new, project['id'])
        for item in data['builds']:

            def block():
                tasks.update(
                    item['id'],
                    state='blocked',
                    detail='A checked build artifact is unavailable at the destination.',
                )

            if not item.get('directory'):
                block()
                continue
            folder = manifest_path.parent / ('handoff-' + data['nonce']) / item['directory']
            statefile = folder / 'state.json'
            bundle = folder / 'artifact.bundle'
            if not statefile.is_file() or not bundle.is_file():
                block()
                continue
            state = json.loads(statefile.read_text('utf-8'))
            gitdir = folder / 'up.git'
            if not gitdir.exists():
                build_receipts.git(repo, 'clone', '--quiet', '--bare', str(bundle), str(gitdir))
            if (
                build_receipts.git(gitdir, 'rev-parse', state['b'], required=False) != item['commit']
                or state.get('plan_task') != item['id']
            ):
                block()
                continue
            state.update(repo=new, home=str(folder), final=str(folder))
            statefile.write_text(json.dumps(state), encoding='utf-8')
            con.execute(
                'UPDATE build_manifests SET project=?,state_path=? WHERE task_id=? AND step=?',
                (new, str(statefile), item['id'], item['step']),
            )
            task = tasks._decode(con.execute('SELECT * FROM tasks WHERE id=?', (item['id'],)).fetchone())
            if task['metadata'].get('build_state'):
                task['metadata']['build_state'] = state
                tasks.update(item['id'], metadata=task['metadata'])
        departure = con.execute(
            'SELECT initiating_task,initiating_action FROM handoff_fences WHERE nonce=?', (data['nonce'],)
        ).fetchone()
        if departure and departure['initiating_task'] and departure['initiating_action']:
            from . import verification

            verification.record(departure['initiating_task'], 0, 'handoff_readback', data['nonce'])
        con.execute('DELETE FROM handoff_fences WHERE nonce=?', (data['nonce'],))
        con.execute("DELETE FROM profile WHERE key LIKE 'telegram_reader:%'")
        store.put('checked_handoff:' + data['nonce'], new)
        if missing:
            updates = ''.join(f'create {branch} {sha}\n' for branch, sha in missing)
            subprocess.run(
                ['git', '-C', str(repo), 'update-ref', '--stdin'],
                input=updates.encode('utf-8'),
                check=True,
                capture_output=True,
            )
    manifest_path.replace(checked)


def remap(repo, old, new, pid):
    """Rewrite machine paths without granting new authority or changing action arguments."""
    con = store.connect()
    store.put('browser_profile:' + new, secrets.token_hex(16))
    store.put('browser_account:' + new, secrets.token_hex(16))
    for row in con.execute('SELECT * FROM tasks WHERE project_id=?', (pid,)).fetchall():
        task = tasks._decode(row)
        con.execute('UPDATE tasks SET project=? WHERE id=?', (new, task['id']))
        work = con.execute('SELECT context FROM execution_queue WHERE task_id=?', (task['id'],)).fetchone()
        if work:
            ctx = json.loads(work[0])
            ctx['project'] = new
            con.execute(
                'UPDATE execution_queue SET context=?,project=?,worker=NULL,started=NULL WHERE task_id=?',
                (
                    json.dumps(ctx),
                    'chat:' + task['chat_id'] if task['mode'] == 'conversation' else new,
                    task['id'],
                ),
            )
        if task['state'] in CLOSED:
            continue
        if (
            'browser' in task['bindings']
            or task['state'] == 'waiting_browser'
            or task['bindings'] != tasks.bindings(repo, task['steps'])
        ):
            tasks.update(
                task['id'],
                state='blocked',
                detail='Re-establish the destination account or browser login and review the request.',
            )
            con.execute('UPDATE execution_queue SET pending=0 WHERE task_id=?', (task['id'],))
    con.execute('UPDATE routines SET project=? WHERE project_id=?', (new, pid))
    con.execute('UPDATE trigger_events SET project=? WHERE project=?', (new, old))
    for job in con.execute('SELECT id,repo,context FROM memory_jobs').fetchall():
        ctx=json.loads(job['context'])
        bound_task=ctx.get('task_id') and con.execute('SELECT 1 FROM tasks WHERE id=? AND project_id=?',
                                                     (ctx['task_id'],pid)).fetchone()
        if bound_task or job['repo']==old or ctx.get('project')==old:
            ctx['project']=new
            con.execute('UPDATE memory_jobs SET repo=?,context=? WHERE id=?',(new,json.dumps(ctx),job['id']))
        elif job['repo']!=new:
            con.execute("UPDATE memory_jobs SET state='needs_input' WHERE id=?",(job['id'],))
    for action in con.execute('SELECT * FROM actions').fetchall():
        linked = con.execute(
            'SELECT 1 FROM task_actions a JOIN tasks t ON t.id=a.task_id '
            'WHERE a.action_id=? AND t.project_id=?',
            (action['id'], pid),
        ).fetchone()
        if not linked and action['project'] != old and projects.path(action['project']) != old:
            continue
        if action['state'] in ('proposed', 'approved'):
            if (
                action['tool'] not in ('mail_send', 'add_event')
                or actions.account_binding(action['tool'], repo) != action['account_binding']
            ):
                con.execute("UPDATE actions SET state='needs_input' WHERE id=?", (action['id'],))
        con.execute('UPDATE actions SET project=? WHERE id=?', (new, action['id']))
    con.execute('DELETE FROM browser_control WHERE project IN (?,?)', (old, new))
