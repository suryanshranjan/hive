"""Persistent project identities and host-specific paths. Preserve legacy memory aliases."""

import os
from pathlib import Path
import secrets
import subprocess
import tempfile
from functools import lru_cache

from . import store


def machine():
    return _host_id(Path(store.path()).parent)


@lru_cache(maxsize=16)
def _host_id(folder):
    """A private installation ID stays on this host even when its database moves."""
    marker = folder / 'host-id'
    if not marker.exists():
        folder.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=folder, delete=False) as temporary:
            temporary.write(secrets.token_hex(32).encode('ascii'))
        try:
            try:
                os.link(temporary.name, marker)
            except FileExistsError:
                pass
        finally:
            os.unlink(temporary.name)
    return marker.read_text(encoding='ascii')


def path(repo):
    return os.path.normcase(os.path.realpath(os.path.abspath(repo)))


def repository(repo):
    proc = subprocess.run(
        ['git', '-C', str(repo), 'rev-list', '--max-parents=0', 'HEAD'], capture_output=True, text=True
    )
    return ' '.join(sorted(proc.stdout.split())) if proc.returncode == 0 else ''


def mapped(repo):
    return (
        store.connect()
        .execute(
            'SELECT p.* FROM project_paths m JOIN projects p ON p.id=m.project_id '
            'WHERE m.machine=? AND m.path=?',
            (machine(), path(repo)),
        )
        .fetchone()
    )


def ensure(repo):
    with store.transaction() as con:
        row = mapped(repo)
        if row:
            project = dict(row)
            if not project['repository']:
                roots = repository(repo)
                if roots:
                    con.execute('UPDATE projects SET repository=? WHERE id=?', (roots, project['id']))
                    project['repository'] = roots
            return project
        canonical = path(repo)
        roots = repository(repo)
        alias = roots.split()[0][:12] if roots else Path(repo).resolve().name or 'project'
        pid = secrets.token_hex(16)
        con.execute('INSERT INTO projects VALUES(?,?,?)', (pid, roots, alias))
        con.execute('INSERT INTO project_paths VALUES(?,?,?)', (pid, machine(), canonical))
        for table in ('tasks', 'routines'):
            con.execute(
                f'UPDATE {table} SET project_id=? WHERE project=? AND project_id IS NULL', (pid, canonical)
            )
        return {'id': pid, 'repository': roots, 'memory_alias': alias}
