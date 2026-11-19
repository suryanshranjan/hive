"""Move a quiesced task database between real Git checkouts, preserving uncertain writes."""

import json
import os
from pathlib import Path
import sqlite3
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.getcwd())
import test_tasks as fixtures
import test_build_receipts as build_fixtures
from hive import (
    actions,
    build_receipts,
    buildplans,
    cloud,
    dispatcher,
    handoff,
    memory,
    policy,
    projects,
    store,
    tasks,
    tools,
)


class HandoffTests(unittest.TestCase):
    setUp = fixtures.TaskTests.setUp
    channel = fixtures.TaskTests.channel

    def test_telegram_departure_does_not_change_frozen_source(self):
        repo = Path(self.repo)
        repo.mkdir()
        self.git(repo, 'init', '-q', '-b', 'main')
        self.git(repo, 'commit', '-q', '--allow-empty', '-m', 'base')
        task = tasks.create(
            self.ch, repo, [{'tool': 'owner_message', 'args': {}}], 'move to cloud', mode='message'
        )
        active = tasks.ACTIVE_TASK.set(task['id'])
        self.addCleanup(tasks.ACTIVE_TASK.reset, active)
        context = policy.CURRENT.set(policy.RequestContext(project=str(repo), chat=str(self.ch.chat)))
        self.addCleanup(policy.CURRENT.reset, context)
        aid = actions.propose('cloud_on', {'repo': str(repo), 'on': True, 'args': [], 'options': {}}, self.ch)
        actions.bind(aid, 13)
        self.assertTrue(actions.approve(aid, self.ch, 13))
        snapshot = []

        def move(args):
            handoff.freeze(repo)
            snapshot.append(store.fingerprint())
            return actions.ActionResult('succeeded')

        self.assertEqual(actions.execute(aid, move).status, 'succeeded')
        self.ch.keep = True
        self.ch.remember('hive', 'Destination confirmed.')
        self.assertEqual(store.fingerprint(), snapshot[0])

    def test_portable_build_resumes_parent_without_rebuilding(self):
        tid, parent, sha, git, folder = build_fixtures.BuildReceiptTests.build(self)
        tasks.recover(self.ch, self.repo)
        data = handoff.freeze(self.repo)
        target = Path(self.temp.name) / 'receive-build'
        checkout = target / 'project'
        target.mkdir()
        git('clone', '--quiet', self.repo, str(checkout))
        home = target / 'user-data'
        handoff.export(cloud.Target(str(home)), str(home), self.temp.name, data, str(checkout))
        db = sqlite3.connect(home / 'hive.db')
        try:
            store.connect().backup(db)
        finally:
            db.close()
        with (
            patch.object(memory, 'DIR', str(home / 'rules')),
            patch.object(policy, 'context', return_value=policy.RequestContext()),
        ):
            handoff.restore(checkout, home / 'handoff.json')
            receipt = build_receipts.validate(tid, 1, checkout)
            self.assertEqual(receipt['commit'], sha)
            self.assertTrue(Path(receipt['artifact']).is_relative_to(home))
            with patch('hive.assistant.background_build') as rebuild:
                self.assertEqual(buildplans.resume(self.ch, str(checkout), tid), 'done')
                rebuild.assert_not_called()
            dispatcher.Dispatcher(self.ch, str(checkout), None).completed_children()
            self.assertEqual(tasks.get(parent, self.ch, checkout)['state'], 'queued')

    def test_upgrade_from_5_keeps_approval_and_historical_completion(self):
        db = sqlite3.connect(':memory:', isolation_level=None)
        try:
            db.executescript(
                'CREATE TABLE schema_version(v INTEGER); INSERT INTO schema_version VALUES(5);'
                + ''.join(store.MIGRATIONS[:5])
            )
            db.execute(
                "INSERT INTO tasks(id,owner_id,chat_id,project,instruction,steps,bindings,created,updated,state) "
                "VALUES('a','owner','1','old','old request','[]','{}',0,0,'succeeded')"
            )
            db.execute(
                "INSERT INTO actions(id,tool,args,proposal_hash,owner_id,chat_id,origin,state,created,expires,message_id,"
                "account_binding) VALUES('b','mail_send','{}','hash','owner','1','owner','proposed',0,123,19,'binding')"
            )
            db.execute("INSERT INTO task_actions VALUES('a',1,'b')")
            store._migrate(db)
            self.assertEqual(db.execute('SELECT state,criteria FROM tasks').fetchone(), ('succeeded', None))
            self.assertEqual(
                db.execute('SELECT message_id,account_binding,state FROM actions').fetchone(),
                (19, 'binding', 'proposed'),
            )
            self.assertEqual(db.execute('SELECT * FROM task_actions').fetchone(), ('a', 1, 'b'))
            self.assertEqual(db.execute('SELECT count(*) FROM task_evidence').fetchone()[0], 0)
        finally:
            db.close()

    @unittest.skipUnless(shutil.which('sh'), 'the mounted-host cloud transport requires sh')
    def test_cli_roundtrip_returns_only_eligible_tasks(self):
        source = Path(self.repo)
        source.mkdir()
        self.git(source, 'init', '-q', '-b', 'main')
        self.git(source, 'commit', '-q', '--allow-empty', '-m', 'base')
        folder = Path(self.temp.name)
        origin = folder / 'first-home'
        target = folder / 'second'
        destination = target / 'hive-cloud' / source.name

        def python(home, cwd, *args):
            env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), PYTHONPATH=os.getcwd())
            result = subprocess.run(
                [sys.executable, '-B', *args], cwd=cwd, env=env, text=True, capture_output=True
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return result.stdout.strip()

        setup = (
            "from hive import tasks,store,dispatcher,policy; from types import SimpleNamespace; "
            "ch=SimpleNamespace(chat=123); task=tasks.create(ch,'.',[],'summarize',mode='adaptive'); "
            "dispatcher.enqueue(task,policy.RequestContext(project='.')); print(task['id'])"
        )
        tid = python(origin, source, '-c', setup)
        python(origin, source, '-m', 'hive', 'cloud', '--to', str(target), '--no-start')
        python(
            target / 'hive-cloud',
            destination,
            '-c',
            "from hive import handoff,tasks; handoff.restore('.'); "
            + f"tasks.update({tid!r},state='waiting_verification',detail='outcome unknown')",
        )
        python(origin, source, '-m', 'hive', 'cloud', 'pull', '--from', str(target))
        query = (
            "from hive import handoff,tasks,projects; from types import SimpleNamespace; handoff.available('.'); "
            + f"task=tasks.get({tid!r},SimpleNamespace(chat=123),'.'); print(task['state'],task['project_id']==projects.mapped('.')['id'])"
        )
        self.assertEqual(python(origin, source, '-c', query), 'waiting_verification True')
        guard = "from hive import store; print(store.connect().execute('SELECT count(*) FROM handoff_fences').fetchone()[0])"
        self.assertEqual(python(target / 'hive-cloud', destination, '-c', guard), '1')

    def git(self, repo, *args):
        return subprocess.check_output(
            [
                'git',
                '-C',
                str(repo),
                '-c',
                'user.name=Fixture',
                '-c',
                'user.email=fixture@example.invalid',
                *args,
            ],
            text=True,
        ).strip()

    def prepare(self):
        repo = Path(self.repo)
        repo.mkdir()
        self.git(repo, 'init', '-q', '-b', 'main')
        self.git(repo, 'commit', '-q', '--allow-empty', '-m', 'base')
        alias = memory.project_key(repo)
        task = tasks.create(self.ch, repo, [], 'review evidence', mode='adaptive')
        context = policy.RequestContext(project=str(repo), chat=str(self.ch.chat), update_id='change')
        dispatcher.enqueue(task, context)
        with patch.object(policy, 'context', return_value=context):
            aid = actions.propose(
                'mail_send',
                {'to': 'fixture@example.invalid', 'subject': 'receipt', 'body': 'test', 'reply_to': None},
                self.ch,
            )
        store.connect().execute("UPDATE actions SET state='unknown' WHERE id=?", (aid,))
        tasks.update(task['id'], state='waiting_verification')
        data = handoff.freeze(repo)
        dest = Path(self.temp.name) / 'other-checkout'
        self.git(repo, 'clone', '--quiet', str(repo), str(dest))
        root = Path(self.temp.name) / 'remote-data'
        target = cloud.Target(str(root))
        handoff.export(target, str(root), self.temp.name, data, str(dest))
        db = sqlite3.connect(root / 'hive.db')
        try:
            store.connect().backup(db)
        finally:
            db.close()
        return task['id'], aid, alias, data, dest, root

    def test_restore_rebinds_paths_without_replaying_and_retains_alias(self):
        tid, aid, alias, manifest, dest, root = self.prepare()
        with self.assertRaises(tools.Refused):
            tasks.create(self.ch, self.repo, [], 'more work')
        with (
            patch.object(memory, 'DIR', str(root / 'rules')),
            patch.object(projects, 'machine', return_value='other-machine'),
        ):
            record = root / 'handoff.json'
            original = record.read_bytes()
            handoff.restore(dest, record)
            self.assertFalse(handoff.listener_ready(dest, manifest['nonce'], timeout=0))
            store.put('telegram_reader:' + str(self.ch.chat), os.getpid())
            self.assertTrue(handoff.listener_ready(dest, manifest['nonce'], timeout=0))
            self.assertEqual(memory.project_key(dest), alias)
            self.assertEqual(projects.mapped(dest)['id'], manifest['project_id'])
            self.assertEqual(tasks.get(tid, self.ch, dest)['state'], 'waiting_verification')
            self.assertEqual(actions.get(aid)['state'], 'unknown')
            self.assertEqual(actions.get(aid)['project'], projects.path(dest))
            queue = (
                store.connect()
                .execute('SELECT context FROM execution_queue WHERE task_id=?', (tid,))
                .fetchone()
            )
            self.assertEqual(json.loads(queue[0])['project'], projects.path(dest))
            record.write_bytes(original)
            handoff.restore(dest, record)
            self.assertFalse(record.exists())

    def test_refuse_dirty_divergent_or_wrong_repository_and_keep_both(self):
        tid, aid, alias, manifest, dest, root = self.prepare()
        with patch.object(memory, 'DIR', str(root / 'rules')):
            record = root / 'handoff.json'
            (dest / 'uncommitted.txt').write_text('local work')
            with self.assertRaises(tools.Refused):
                handoff.restore(dest, record)
            self.git(dest, 'add', 'uncommitted.txt')
            self.git(dest, 'commit', '-qm', 'local changes')
            with self.assertRaises(tools.Refused):
                handoff.restore(dest, record)
            with self.assertRaises(tools.Refused):
                handoff.restore(self.repo, record)
            self.assertTrue(record.exists())
            self.assertTrue((dest / 'uncommitted.txt').exists())
            self.assertEqual(actions.get(aid)['state'], 'unknown')

    def test_missing_artifact_blocks_the_build_and_account_change_blocks_the_action(self):
        tid, aid, alias, manifest, dest, root = self.prepare()
        with patch.object(memory, 'DIR', str(root / 'rules')):
            record = root / 'handoff.json'
            data = json.loads(record.read_text())
            data['builds'] = [
                {
                    'id': tid,
                    'step': 1,
                    'branch': 'refs/heads/hive/result',
                    'commit': data['refs']['refs/heads/main'],
                }
            ]
            record.write_text(json.dumps(data))
            store.connect().execute(
                "UPDATE actions SET state='approved',account_binding='different' WHERE id=?", (aid,)
            )
            handoff.restore(dest, record)
            self.assertEqual(tasks.get(tid, self.ch, dest)['state'], 'blocked')
            self.assertEqual(actions.get(aid)['state'], 'needs_input')


if __name__ == '__main__':
    unittest.main()
