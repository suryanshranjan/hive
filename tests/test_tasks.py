"""Task recovery, duplicate delivery, scope boundaries and conversation context.

No models, external accounts or executable project code. Run from the repo root.
"""
import json
import os
import sqlite3
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, os.getcwd())
from hive import actions, assistant, audit, calendar_, explain, google, mail, memory, office, policy, register, router, store, tasks, telegram, tools
from test_telegram_fake import FakeTelegram, ME, tap


class TaskTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='hive_tasks_')
        self.addCleanup(self.temp.cleanup)
        for target, name, value in (
            (memory, 'DIR', os.path.join(self.temp.name, 'rules')),
            (register, 'PATH', os.path.join(self.temp.name, 'profile.json')),
            (telegram, 'CONVERSATION', os.path.join(self.temp.name, 'conversation.json')),
        ):
            mock = patch.object(target, name, value)
            mock.start(); self.addCleanup(mock.stop)
        for target, name, value in (
            (audit, 'path', os.path.join(self.temp.name, 'audit.jsonl')),
            (google, '_load', {'client_id': 'account-A'}),
            (mail, 'config', {'user': 'owner@example.invalid', 'smtp': 'mail.invalid'}),
            (calendar_, 'config', {'kind': 'google'}),
        ):
            mock = patch.object(target, name, return_value=value)
            mock.start(); self.addCleanup(mock.stop)
        self.addCleanup(store.close)
        self.repo = os.path.join(self.temp.name, 'project')
        self.ch = self.channel()

    def channel(self, chat=ME):
        return telegram.Channel({'chat_id': chat, 'token': 'fake'}, api=FakeTelegram([]))

    def newest(self):
        return dict(store.connect().execute('SELECT * FROM tasks ORDER BY created DESC LIMIT 1').fetchone())

    def read_step(self):
        return {'tool': 'mail_find', 'args': {'about': 'Asha'}}

    def write_step(self):
        return {'tool': 'mail_send', 'args': {'to': 'asha@example.invalid', 'say': 'Hello'}}

    def test_restart_between_steps_keeps_results_and_skips_completed_send(self):
        steps = [self.read_step(), self.write_step(),
                 {'tool': 'calendar_add', 'args': {'guests': ['$1.email']}}]
        begin = tasks.begin_step
        def crash_between(tid, n):
            if n == 3:
                raise KeyboardInterrupt()
            begin(tid, n)
        with patch.object(tasks, 'begin_step', side_effect=crash_between), patch.object(router, '_step', side_effect=[
            {'status': 'done', 'email': 'asha@example.invalid'}, {'status': 'succeeded'}]) as run:
            with self.assertRaises(KeyboardInterrupt):
                router.run_chain(self.ch, self.repo, steps, 'Find, send, then invite')
            self.assertEqual(run.call_count, 2)
        tid = self.newest()['id']
        store.close()
        self.assertEqual(tasks.recover(self.ch, self.repo), 1)
        with patch.object(router, '_step', return_value={'status': 'event_added'}) as run:
            result = router.resume_chain(self.ch, self.repo, tid)
            self.assertEqual(result, ['done', 'succeeded', 'event_added'])
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[2:4], ('calendar_add', {'guests': ['asha@example.invalid']}))
        self.assertEqual(tasks.get(tid, self.ch, self.repo)['state'], 'succeeded')

    def test_interrupted_send_is_never_replayed(self):
        with patch.object(router, '_step', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                router.run_chain(self.ch, self.repo, [self.write_step()], 'Send it')
        tid = self.newest()['id']
        store.close(); tasks.recover(self.ch, self.repo)
        with patch.object(router, '_step') as run:
            self.assertEqual(router.resume_chain(self.ch, self.repo, tid), ['unknown'])
            run.assert_not_called()
        self.assertEqual(tasks.get(tid, self.ch, self.repo)['state'], 'blocked')

    def test_interrupted_read_waits_for_explicit_resume(self):
        with patch.object(router, '_step', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                router.run_chain(self.ch, self.repo, [self.read_step()], 'Find Asha')
        tid = self.newest()['id']
        store.close()
        with patch.object(router, '_step', return_value={'status': 'done'}) as run:
            tasks.recover(self.ch, self.repo)
            run.assert_not_called()
            self.assertEqual(router.resume_chain(self.ch, self.repo, tid), ['done'])
            run.assert_called_once()

    def test_read_failure_is_saved_and_can_be_retried(self):
        with patch.object(router, '_step', side_effect=OSError('private provider error')):
            self.assertEqual(router.run_chain(self.ch, self.repo, [self.read_step()], 'Find'), ['failed'])
        task = self.newest()
        self.assertEqual(task['state'], 'paused')
        self.assertNotIn('private provider error', task['detail'])
        with patch.object(router, '_step', return_value={'status': 'done'}):
            self.assertEqual(router.resume_chain(self.ch, self.repo, task['id']), ['done'])

    def test_duplicate_update_reuses_task_even_when_model_plan_changes(self):
        self.ch.last_update = '123'
        with patch.object(router, '_step', return_value={'status': 'succeeded'}) as run:
            router.run_chain(self.ch, self.repo, [self.write_step()], 'Do it')
            router.run_chain(self.ch, self.repo, [self.read_step()], 'Do it')
            run.assert_called_once()
            self.ch.last_update = '124'
            router.run_chain(self.ch, self.repo, [self.write_step()], 'Do it')
            self.assertEqual(run.call_count, 2)

    def test_tasks_are_private_to_chat_project_and_owner(self):
        task = tasks.create(self.ch, self.repo, [self.read_step()], 'private instruction')
        self.assertIsNone(tasks.get(task['id'], self.channel(ME + 1), self.repo))
        self.assertIsNone(tasks.claim(task['id'], self.ch, self.repo + '_other', resume=True))
        token = policy.CURRENT.set(policy.RequestContext(owner='someone_else'))
        try:
            self.assertIsNone(tasks.get(task['id'], self.ch, self.repo))
        finally:
            policy.CURRENT.reset(token)

    def test_outside_content_cannot_create_inspect_or_resume_tasks(self):
        task = tasks.create(self.ch, self.repo, [self.read_step()], 'Find')
        token = policy.CURRENT.set(policy.RequestContext(origin='outside'))
        try:
            self.assertEqual(router.run_chain(self.ch, self.repo, [self.read_step()], 'Find'), ['refused'])
            self.assertEqual(router.task_command(self.ch, self.repo, 'tasks'), 'refused')
            self.assertEqual(router.task_command(self.ch, self.repo, 'resume task ' + task['id']), 'refused')
        finally:
            policy.CURRENT.reset(token)
        self.assertEqual(tasks.get(task['id'], self.ch, self.repo)['state'], 'queued')

    def test_invalid_later_reference_prevents_earlier_write(self):
        steps = [self.write_step(), {'tool': 'mail_send', 'args': {'to': '$3.email'}}]
        with patch.object(router, '_step') as run:
            self.assertEqual(router.run_chain(self.ch, self.repo, steps, 'Send twice'), ['refused'])
            run.assert_not_called()
        self.assertEqual(store.connect().execute('SELECT count(*) FROM tasks').fetchone()[0], 0)

    def test_malformed_plans_are_refused_before_execution(self):
        for steps in ([{'tool': [], 'args': {}}], [{'tool': 'mail_send', 'args': []}],
                      [self.read_step()] * 5, [{'tool': 'mail_send', 'args': {'to': ['$0.email']}}]):
            with self.subTest(steps=steps), self.assertRaises(tools.Refused):
                router.validate_steps(steps)

    def test_only_one_executor_claims_a_task(self):
        task = tasks.create(self.ch, self.repo, [self.read_step()], 'Find')
        claimed, errors = [], []
        def claim():
            try:
                claimed.append(bool(tasks.claim(task['id'], self.ch, self.repo, resume=True)))
            except Exception as e:
                errors.append(type(e).__name__)
        threads = [threading.Thread(target=claim) for _ in range(2)]
        for thread in threads: thread.start()
        for thread in threads: thread.join(5)
        self.assertFalse(any(t.is_alive() for t in threads))
        self.assertEqual(errors, [])
        self.assertEqual(sorted(claimed), [False, True])

    def test_changed_account_blocks_resume(self):
        task = tasks.create(self.ch, self.repo, [self.write_step()], 'Send')
        with patch.object(mail, 'config', return_value={'user': 'other@example.invalid'}), \
                patch.object(router, '_step') as run:
            router.resume_chain(self.ch, self.repo, task['id'])
            run.assert_not_called()
        self.assertEqual(tasks.get(task['id'], self.ch, self.repo)['state'], 'blocked')

    def test_resumed_send_uses_saved_recipient_and_still_needs_approval(self):
        for decision, sends in [('no', 0), ('yes', 1)]:
            with self.subTest(decision=decision):
                ch = telegram.Channel({'chat_id': ME, 'token': 'fake'}, api=FakeTelegram([tap('mls|' + decision)]))
                steps = [self.read_step(), {'tool': 'mail_send', 'args': {
                    'to': '$1.email', 'subject': 'Tasting', 'say': 'Thursday works.'}}]
                task = tasks.create(ch, self.repo, steps, 'Find Asha, then send the reply')
                tasks.claim(task['id'], ch, self.repo)
                tasks.begin_step(task['id'], 1)
                tasks.finish_step(task['id'], 1, {'status': 'done', 'email': 'asha@example.invalid'})
                store.close(); tasks.recover(ch, self.repo)
                with patch.object(office, '_send_result', return_value=actions.ActionResult('succeeded', 'receipt')) as send:
                    result = assistant.handle(ch, self.repo, 'resume task ' + task['id'], poll=1)
                    self.assertEqual(send.call_count, sends)
                    if sends:
                        self.assertEqual(send.call_args.args[1], {
                            'to': 'asha@example.invalid', 'subject': 'Tasting', 'body': 'Thursday works.'})
                        self.assertEqual(result, 'chain:done,succeeded')
                    assistant.handle(ch, self.repo, 'resume task ' + task['id'], poll=1)
                    self.assertEqual(send.call_count, sends)

    def test_mail_read_server_change_also_blocks_resume(self):
        task = tasks.create(self.ch, self.repo, [self.read_step()], 'Find')
        with patch.object(mail, 'config', return_value={
            'user': 'owner@example.invalid', 'smtp': 'mail.invalid', 'imap': 'another.invalid'}):
            self.assertIsNone(tasks.claim(task['id'], self.ch, self.repo, resume=True))
        self.assertEqual(tasks.get(task['id'], self.ch, self.repo)['state'], 'blocked')

    def test_missing_outcome_cannot_advance_to_next_step(self):
        with patch.object(router, '_step', return_value=None) as run:
            self.assertEqual(router.run_chain(self.ch, self.repo, [self.write_step(), self.read_step()], 'Do both'),
                             ['unknown'])
            run.assert_called_once()

    def test_explicit_task_commands_need_no_model_and_work_with_intent_router(self):
        task = tasks.create(self.ch, self.repo, [self.read_step()], 'Find')
        with patch.object(explain, 'ask_json', side_effect=AssertionError('No model needed')), \
                patch.object(router, '_step', return_value={'status': 'done'}), \
                patch.object(assistant, 'router_mode', return_value='intent'):
            self.assertEqual(assistant.handle(self.ch, self.repo, 'tasks'), 'tasks_shown')
            self.assertEqual(assistant.handle(self.ch, self.repo, 'task ' + task['id']), 'tasks_shown')
            self.assertEqual(assistant.handle(self.ch, self.repo, 'resume task ' + task['id']), 'chain:done')

    def test_schema_upgrade_retains_previous_data(self):
        con = sqlite3.connect(':memory:', isolation_level=None)
        try:
            con.executescript('CREATE TABLE schema_version(v INTEGER); INSERT INTO schema_version VALUES(3);' +
                              ''.join(store.MIGRATIONS[:3]))
            con.execute("INSERT INTO profile VALUES('owner','name','\"Asha\"',1)")
            store._migrate(con)
            self.assertEqual(con.execute('SELECT value FROM profile').fetchone()[0], '"Asha"')
            self.assertEqual(con.execute('SELECT count(*) FROM tasks').fetchone()[0], 0)
        finally:
            con.close()

    def test_long_instructions_and_corrections_survive_context_and_restart(self):
        self.ch.keep = True
        instruction = 'Details: ' + 'long requirements ' * 90 + 'Never email the customer before Friday.'
        self.ch.remember('owner', instruction)
        self.ch.remember('hive', 'I have the requirements.')
        self.ch.remember('owner', 'Actually, make that Monday.')
        reopened = telegram.Channel({'chat_id': ME, 'token': 'fake'})
        context = reopened.recent()
        self.assertIn(instruction, context)
        self.assertIn('Actually, make that Monday.', context)
        self.assertLess(context.index('before Friday'), context.index('Actually'))

    def test_context_budget_keeps_latest_entries_with_visible_omissions(self):
        for n in range(32):
            self.ch.remember('owner', f'Message {n}: ' + 'x' * 1000)
        context = self.ch.recent(max_chars=5000)
        self.assertLessEqual(len(context), 5000)
        self.assertIn('Message 31:', context)
        self.assertNotIn('Message 0:', context)
        self.assertIn('[Earlier conversation omitted', context)
        self.assertEqual(len(self.ch.history[0][1]), 1011)

    def test_oversized_latest_message_keeps_both_ends(self):
        self.ch.remember('owner', 'START ' + 'x' * 30000 + ' END: do not send')
        context = self.ch.recent(max_chars=2000)
        self.assertLessEqual(len(context), 2000)
        self.assertIn('START', context)
        self.assertIn('END: do not send', context)
        self.assertIn('[Middle of this message omitted', context)
        self.assertGreater(len(self.ch.history[-1][1]), 30000)


if __name__ == '__main__':
    unittest.main()
