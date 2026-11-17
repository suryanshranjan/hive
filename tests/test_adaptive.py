"""Deterministic adaptive tasks, durable builds, schedules and approval recovery.

No model, external account or real build is invoked.
"""
import json
import os
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.getcwd())
import test_tasks as fixtures
from hive import actions, agent, assistant, browser, buildplans, connectors, explain, policy
from hive import routines, runtime_tools, screens, service_checks, store, tasks, tools, telegram, google


class AdaptiveTests(unittest.TestCase):
    setUp = fixtures.TaskTests.setUp
    channel = fixtures.TaskTests.channel
    newest = fixtures.TaskTests.newest

    def tool(self, name='lookup', risk=tools.READ, fn=None, identity='v1'):
        return runtime_tools.Tool(name, 'Fixture tool', runtime_tools.schema({'q': {'type': 'string'}}, ['q']),
                                  risk, risk == tools.READ, fn or Mock(return_value={'status': 'done'}), identity)

    def current(self):
        return tasks.get(self.newest()['id'], self.ch, self.repo)

    def confirm(self, ch, name, payload, *args, **kwargs):
        aid = actions.propose(name, payload, ch)
        actions.bind(aid, 123)
        self.assertTrue(actions.approve(aid, ch, 123))
        return aid

    def test_failed_read_replans_and_write_uses_observed_value(self):
        read = self.tool(fn=Mock(side_effect=[{'status': 'not_found'}, {'status': 'done', 'data': 'answer-42'}]))
        write = self.tool('record', tools.EXTERNAL)
        decisions = [{'tool': 'lookup', 'args': {'q': 'first'}}, {'tool': 'lookup', 'args': {'q': 'revised'}},
                     {'tool': 'record', 'args': {'q': 'answer-42'}}, {'done': 'Recorded answer-42.'}]
        with patch.object(runtime_tools, 'catalog', return_value={'lookup': read, 'record': write}), \
                patch.object(explain, 'ask_json', side_effect=decisions) as planner, \
                patch.object(actions, 'confirm', side_effect=self.confirm):
            self.assertEqual(agent.start(self.ch, self.repo, 'Find the answer and record it'),
                             ['not_found', 'done', 'succeeded'])
        self.assertIn('not_found', planner.call_args_list[1].args[0])
        self.assertIn('answer-42', planner.call_args_list[2].args[0])
        write.call.assert_called_once_with({'q': 'answer-42'})
        self.assertEqual(self.current()['state'], 'succeeded')

    def test_cancelled_write_stops_before_another_decision(self):
        tool = self.tool('record', tools.EXTERNAL)
        with patch.object(runtime_tools, 'catalog', return_value={'record': tool}), \
                patch.object(explain, 'ask_json', return_value={'tool': 'record', 'args': {'q': 'x'}}) as planner, \
                patch.object(actions, 'confirm', return_value=None):
            agent.start(self.ch, self.repo, 'Record x')
        tool.call.assert_not_called()
        self.assertEqual(planner.call_count, 1)
        self.assertEqual(self.current()['state'], 'blocked')

    def test_uncertain_write_is_never_repeated_on_resume(self):
        tool = self.tool('record', tools.EXTERNAL, Mock(side_effect=TimeoutError))
        with patch.object(runtime_tools, 'catalog', return_value={'record': tool}), \
                patch.object(explain, 'ask_json', return_value={'tool': 'record', 'args': {'q': 'x'}}), \
                patch.object(actions, 'confirm', side_effect=self.confirm):
            agent.start(self.ch, self.repo, 'Record x')
            tid = self.current()['id']
            store.close(); tasks.recover(self.ch, self.repo)
            agent.resume(self.ch, self.repo, tid)
        tool.call.assert_called_once()
        self.assertEqual(self.current()['results']['1']['status'], 'unknown')

    def test_action_receipt_recovers_crash_after_write_before_task_checkpoint(self):
        tool = self.tool('record', tools.EXTERNAL)
        with patch.object(runtime_tools, 'catalog', return_value={'record': tool}), \
                patch.object(explain, 'ask_json', return_value={'tool': 'record', 'args': {'q': 'x'}}), \
                patch.object(actions, 'confirm', side_effect=self.confirm), \
                patch.object(tasks, 'finish_step', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                agent.start(self.ch, self.repo, 'Record x')
        tid = self.current()['id']
        store.close(); tasks.recover(self.ch, self.repo)
        with patch.object(runtime_tools, 'catalog', return_value={'record': tool}), \
                patch.object(explain, 'ask_json', return_value={'done': 'Recorded.'}):
            agent.resume(self.ch, self.repo, tid)
        tool.call.assert_called_once()
        self.assertTrue(self.current()['results']['1']['recovered'])
        self.assertEqual(self.current()['state'], 'succeeded')

    def test_interrupted_read_retries_saved_decision(self):
        tool = self.tool(fn=Mock(side_effect=KeyboardInterrupt))
        with patch.object(runtime_tools, 'catalog', return_value={'lookup': tool}), \
                patch.object(explain, 'ask_json', return_value={'tool': 'lookup', 'args': {'q': 'saved'}}):
            with self.assertRaises(KeyboardInterrupt):
                agent.start(self.ch, self.repo, 'Look up saved')
        tid = self.current()['id']
        store.close(); tasks.recover(self.ch, self.repo)
        tool.call = Mock(return_value={'status': 'done', 'data': 'found'})
        with patch.object(runtime_tools, 'catalog', return_value={'lookup': tool}), \
                patch.object(explain, 'ask_json', return_value={'done': 'Found.'}) as planner:
            agent.resume(self.ch, self.repo, tid)
        tool.call.assert_called_once_with({'q': 'saved'})
        self.assertEqual(planner.call_count, 1)

    def test_changed_tool_identity_blocks_saved_decision(self):
        tool = self.tool(fn=Mock(side_effect=KeyboardInterrupt))
        with patch.object(runtime_tools, 'catalog', return_value={'lookup': tool}), \
                patch.object(explain, 'ask_json', return_value={'tool': 'lookup', 'args': {'q': 'saved'}}):
            with self.assertRaises(KeyboardInterrupt): agent.start(self.ch, self.repo, 'Read')
        tid = self.current()['id']; tasks.recover(self.ch, self.repo)
        replacement = self.tool(identity='v2')
        with patch.object(runtime_tools, 'catalog', return_value={'lookup': replacement}):
            agent.resume(self.ch, self.repo, tid)
        replacement.call.assert_not_called()
        self.assertEqual(self.current()['state'], 'paused')

    def test_step_limit_allows_final_answer_but_no_extra_tool(self):
        tool = self.tool()
        for ending, expected in (({'done': 'Found'}, 'succeeded'), ({'tool': 'lookup', 'args': {'q': 'new'}}, 'paused')):
            with patch.object(runtime_tools, 'catalog', return_value={'lookup': tool}), \
                    patch.object(explain, 'ask_json', side_effect=[{'tool': 'lookup', 'args': {'q': 'a'}}, ending]):
                agent.start(self.ch, self.repo, 'Read ' + expected, max_steps=1)
            self.assertEqual(self.current()['state'], expected)
        self.assertEqual(tool.call.call_count, 2)

    def test_cost_limit_stops_before_tool(self):
        tool = self.tool()
        def decide(*args):
            explain.SPENT[0] += 3
            return {'tool': 'lookup', 'args': {'q': 'a'}}
        with patch.object(runtime_tools, 'catalog', return_value={'lookup': tool}), \
                patch.object(explain, 'SPENT', [0]), patch.object(explain, 'ask_json', side_effect=decide):
            agent.start(self.ch, self.repo, 'Read')
        tool.call.assert_not_called()
        self.assertEqual(self.current()['state'], 'paused')

    def test_question_and_answer_survive_restart_and_stay_scoped(self):
        with patch.object(runtime_tools, 'catalog', return_value={}), \
                patch.object(explain, 'ask_json', return_value={'ask': 'Which region?'}):
            agent.start(self.ch, self.repo, 'Find availability')
        tid = self.current()['id']; store.close()
        agent.answer(self.ch, self.repo + '-other', tid, 'wrong')
        self.assertEqual(self.current()['metadata']['answers'], [])
        with patch.object(runtime_tools, 'catalog', return_value={}), \
                patch.object(explain, 'ask_json', return_value={'done': 'No tools for that region.'}) as planner:
            agent.answer(self.ch, self.repo, tid, 'North')
        self.assertIn('North', planner.call_args.args[0])

    def test_outside_content_cannot_call_tools_or_schedule(self):
        token = policy.CURRENT.set(policy.RequestContext(origin='outside'))
        try:
            with self.assertRaises(tools.Refused): runtime_tools.execute(self.ch, self.repo, self.tool(), {'q': 'x'})
            with self.assertRaises(tools.Refused): routines.create(self.ch, self.repo, 'send something', 300)
        finally:
            policy.CURRENT.reset(token)

    def test_schema_rejects_unknown_args_and_remote_refs(self):
        tool = self.tool()
        with self.assertRaises(tools.Refused): runtime_tools.validate(tool, {'q': 'x', 'shell': 'command'})
        tool.schema = {'$ref': 'https://example.invalid/schema.json'}
        with self.assertRaises(tools.Refused): runtime_tools.validate(tool, {})

    def test_pending_dynamic_approval_survives_restart(self):
        tool = self.tool('record', tools.EXTERNAL)
        task = tasks.create(self.ch, self.repo, [], 'Record', mode='adaptive',
                            metadata={'max_steps': 2, 'max_cost': 2, 'spent': 0, 'answers': []})
        tid = task['id']; tasks.claim(tid, self.ch, self.repo)
        tasks.append_step(tid, self.ch, self.repo, {'tool': 'record', 'args': {'q': 'x'}, 'retry_safe': False, 'identity': 'v1'})
        tasks.begin_step(tid, 1)
        with tasks.executing(tid, 1):
            aid = actions.propose('agent_action', {'tool': 'record', 'args': {'q': 'x'}, 'identity': 'v1'}, self.ch)
            actions.bind(aid, 123)
        store.close(); tasks.recover(self.ch, self.repo)
        with patch.object(runtime_tools, 'catalog', return_value={'record': tool}):
            self.assertTrue(actions.resume(self.ch, f'act|{aid}|yes', 123, self.repo))
            self.assertFalse(actions.resume(self.ch, f'act|{aid}|yes', 123, self.repo))
        tool.call.assert_called_once()
        self.assertEqual(tasks.reconcile(tid, self.ch, self.repo)['next_step'], 2)

    def test_routine_coalesces_and_never_overlaps(self):
        rid = routines.create(self.ch, self.repo, 'Read report', 300, now=100)
        self.assertEqual(routines.create(self.ch, self.repo, 'Read report', 300, now=101), rid)
        with patch.object(agent, 'run', side_effect=lambda ch, repo, tid: tasks.update(tid, state='paused')) as run:
            self.assertEqual(routines.tick(self.ch, self.repo, now=399), [])
            first = routines.tick(self.ch, self.repo, now=400)
            self.assertEqual(len(first), 1)
            self.assertEqual(routines.tick(self.ch, self.repo, now=400), [])
            store.close()
            self.assertEqual(routines.tick(self.ch, self.repo, now=900), [])
            self.assertEqual(run.call_count, 1)
            tasks.cancel(first[0], self.ch, self.repo)
            self.assertEqual(len(routines.tick(self.ch, self.repo, now=1500)), 1)
            self.assertEqual(run.call_count, 2)

    def test_routine_reuses_queued_task_after_crash_before_execution(self):
        routines.create(self.ch, self.repo, 'Read report', 300, now=0)
        with patch.object(agent, 'run', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt): routines.tick(self.ch, self.repo, now=300)
        tid = self.current()['id']; store.close()
        with patch.object(agent, 'run') as run:
            self.assertEqual(routines.tick(self.ch, self.repo, now=600), [tid])
            run.assert_called_once_with(self.ch, self.repo, tid)
        self.assertEqual(store.connect().execute('SELECT count(*) FROM tasks').fetchone()[0], 1)

    def test_paused_routine_can_run_once_without_reenabling(self):
        rid = routines.create(self.ch, self.repo, 'Read report', 300, now=0)
        routines.command(self.ch, self.repo, 'pause routine ' + rid)
        with patch.object(agent, 'run') as run:
            routines.tick(self.ch, self.repo, now=10**10); run.assert_not_called()
            routines.command(self.ch, self.repo, 'run routine ' + rid)
            self.assertEqual(len(routines.tick(self.ch, self.repo, now=10**10)), 1)
        self.assertFalse(routines.rows(self.ch, self.repo)[0]['enabled'])

    def test_build_restart_resumes_saved_branch_and_answers(self):
        assistant.PLAN.clear(); self.addCleanup(assistant.PLAN.clear)
        steps = [{'title': f'Step {n}', 'why': 'why', 'seen': 'file.py', 'build': f'build {n}', 'decide': ''} for n in range(1, 4)]
        tid = buildplans.save(self.ch, self.repo, {'goal': 'Goal', 'steps': steps, 'answers': ['yes', '', 'later']})
        state = {'repo': self.repo, 'name': 'saved', 'plan_task': tid, 'check': 'passed'}
        begin = tasks.begin_step
        def crash(t, n):
            if n == 2: raise KeyboardInterrupt
            begin(t, n)
        with patch.object(screens, 'available', return_value=False), \
                patch.object(assistant, 'background_build', return_value=Mock(wait=lambda: 0)) as build, \
                patch.object(assistant, 'latest_build', return_value=state), \
                patch.object(assistant, 'what_changed', return_value='changed'), patch.object(tasks, 'begin_step', side_effect=crash):
            with self.assertRaises(KeyboardInterrupt): buildplans.resume(self.ch, self.repo, tid)
        build.assert_called_once()
        store.close(); tasks.recover(self.ch, self.repo); assistant.PLAN.clear()
        buildplans.restore(self.ch, self.repo)
        self.assertEqual(assistant.PLAN['step'], 2)
        with patch.object(screens, 'available', return_value=False), \
                patch.object(assistant, 'background_build') as build, patch.object(assistant, 'latest_build') as latest, \
                patch.object(assistant, 'what_changed', return_value='changed'):
            apply = Mock(return_value=0)
            self.assertEqual(buildplans.resume(self.ch, self.repo, tid, apply), 'done')
        build.assert_not_called(); latest.assert_not_called()
        self.assertEqual(apply.call_count, 2)
        self.assertEqual(apply.call_args.args[0]['name'], 'saved')
        self.assertEqual(tasks.get(tid, self.ch, self.repo)['state'], 'succeeded')

    def test_read_only_service_probe_only_calls_read_endpoints(self):
        with patch.object(google, '_load', return_value={'refresh_token': 'fixture'}), \
                patch.object(google, 'connected', return_value=True), patch.object(google, 'call') as call, \
                patch.object(telegram, 'load', return_value={'token': 'fixture'}), patch.object(telegram, '_call') as bot:
            result = service_checks.check(live=True)
        self.assertEqual([c.args[0] for c in call.call_args_list], ['GET', 'GET'])
        bot.assert_called_once_with('fixture', 'getMe')
        self.assertEqual(result['gmail'], 'live_read_passed')

    def test_interrupted_build_step_is_not_replayed(self):
        assistant.PLAN.clear(); self.addCleanup(assistant.PLAN.clear)
        step = {'title': 'One', 'why': 'why', 'seen': 'file.py', 'build': 'build', 'decide': ''}
        tid = buildplans.save(self.ch, self.repo, {'goal': 'Build', 'steps': [step]})
        with patch.object(screens, 'available', return_value=False), \
                patch.object(assistant, 'background_build', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt): buildplans.resume(self.ch, self.repo, tid)
        store.close(); tasks.recover(self.ch, self.repo)
        with patch.object(assistant, 'background_build') as build:
            self.assertEqual(buildplans.resume(self.ch, self.repo, tid), 'blocked')
        build.assert_not_called()

    def test_stale_build_result_cannot_complete_plan(self):
        assistant.PLAN.clear(); self.addCleanup(assistant.PLAN.clear)
        step = {'title': 'One', 'why': 'why', 'seen': 'file.py', 'build': 'build', 'decide': ''}
        tid = buildplans.save(self.ch, self.repo, {'goal': 'Build', 'steps': [step]})
        with patch.object(screens, 'available', return_value=False), \
                patch.object(assistant, 'background_build', return_value=Mock(wait=lambda: 0)), \
                patch.object(assistant, 'latest_build', return_value={'repo': self.repo, 'plan_task': 'another-task'}):
            self.assertEqual(buildplans.resume(self.ch, self.repo, tid), 'failed')
        self.assertEqual(tasks.get(tid, self.ch, self.repo)['state'], 'blocked')

    def test_cancel_invalidates_pending_approval(self):
        task = tasks.create(self.ch, self.repo, [{'tool': 'record', 'args': {}}], 'Record')
        with tasks.executing(task['id'], 1):
            aid = actions.propose('agent_action', {'tool': 'record', 'args': {}, 'identity': 'v1'}, self.ch)
            actions.bind(aid, 123)
        tasks.cancel(task['id'], self.ch, self.repo)
        self.assertFalse(actions.approve(aid, self.ch, 123))

    def test_pausing_clears_manual_run_request(self):
        rid = routines.create(self.ch, self.repo, 'Read report', 300, now=0)
        routines.command(self.ch, self.repo, 'run routine ' + rid)
        routines.command(self.ch, self.repo, 'pause routine ' + rid)
        with patch.object(agent, 'run') as run:
            self.assertEqual(routines.tick(self.ch, self.repo, now=10**10), [])
            run.assert_not_called()

    def test_planner_keeps_prior_conversation_and_request_time_after_restart(self):
        self.ch.history = [('owner', 'The subject is a catering invoice.'), ('hive', 'Which region?')]
        with patch.object(runtime_tools, 'catalog', return_value={}), \
                patch.object(explain, 'ask_json', return_value={'ask': 'Which region?'}):
            agent.start(self.ch, self.repo, 'Find that for tomorrow')
        tid = self.current()['id']; store.close(); self.ch.history = []
        with patch.object(runtime_tools, 'catalog', return_value={}), \
                patch.object(explain, 'ask_json', return_value={'done': 'Done'}) as planner:
            agent.answer(self.ch, self.repo, tid, 'North')
        prompt = planner.call_args.args[0]
        self.assertIn('catering invoice', prompt)
        self.assertIn('Request received:', prompt)
        self.assertIn('Current time:', prompt)


if __name__ == '__main__':
    unittest.main()
