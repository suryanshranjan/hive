"""Validate an approved child build against a real local Git branch and its artifacts."""
import json
import os
from pathlib import Path
from contextlib import closing
import sqlite3
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.getcwd())
import test_tasks as fixtures
from hive import (actions, agent, build_receipts, buildplans, dispatcher, policy, runtime_tools,
                  store, tasks, tools, work_tools)


class BuildReceiptTests(unittest.TestCase):
    setUp = fixtures.TaskTests.setUp
    channel = fixtures.TaskTests.channel

    def build(self):
        repo = Path(self.repo)
        repo.mkdir()
        def git(*args, cwd=repo):
            return subprocess.check_output(['git','-c','user.name=Fixture','-c','user.email=t@fixture.invalid',
                                            '-C',str(cwd),*args], text=True).strip()
        git('init','-q','-b','main')
        git('commit','-q','--allow-empty','-m','base')
        base = git('rev-parse','HEAD')
        ch = self.ch
        token = policy.CURRENT.set(policy.RequestContext(chat=str(ch.chat),project=self.repo,update_id='test'))
        self.addCleanup(policy.CURRENT.reset,token)
        parent = agent.accept(ch,self.repo,'Build a report and summarize it')
        tasks.claim(parent['id'],ch,self.repo)
        tasks.append_step(parent['id'],ch,self.repo,{'tool':'build_submit','args':{'goal':'Report'},'retry_safe':False})
        tasks.begin_step(parent['id'],1)
        with tasks.executing(parent['id'],1):
            approved = {'tool':'build_submit','args':{'goal':'Report'},'identity':''}
            aid = actions.propose('agent_action',approved,ch)
            actions.bind(aid,15)
            self.assertTrue(actions.approve(aid,ch,15))
            outcome = actions.execute(aid,lambda a: runtime_tools.approved_external(self.repo,a))
            self.assertEqual(outcome.status,'succeeded')
        tasks.finish_step(parent['id'],1,{'status':'succeeded'})
        tid = store.connect().execute('SELECT child FROM child_builds').fetchone()[0]
        tasks.claim(tid,ch,self.repo)
        tasks.begin_step(tid,1)
        folder = Path(self.temp.name)/'run'
        folder.mkdir()
        artifact = folder/'up.git'
        git('clone','--quiet','--bare',str(repo),str(artifact))
        state = {'plan_task':tid,'repo':self.repo,'name':'fixture','final':str(folder),'b':'main',
                 'code':0,'home':str(folder),'test_cmd':'fixture'}
        (folder/'state.json').write_text(json.dumps(state),encoding='utf-8')
        with tasks.executing(tid,1):
            build_receipts.begin(self.repo,self.repo,'refs/heads/main','hive/fixture',folder)
            self.assertTrue(build_receipts.publish(state,self.repo,{'fixture.test':True}))
        return tid,parent['id'],base,git,folder

    def test_crash_after_publish_resumes_parent_without_building(self):
        tid,parent,sha,git,folder = self.build()
        store.close()
        tasks.recover(self.ch,self.repo)
        with patch('hive.assistant.background_build') as rebuild:
            self.assertEqual(buildplans.resume(self.ch,self.repo,tid),'done')
            rebuild.assert_not_called()
        dispatcher.Dispatcher(self.ch,self.repo,Mock()).completed_children()
        task = tasks.get(parent,self.ch,self.repo)
        self.assertEqual(task['state'],'queued')
        self.assertEqual(task['results']['1']['commit'],sha)
        self.assertEqual(task['next_step'],2)

    def test_incomplete_receipt_rechecks_once_divergence_and_missing_artifact_block(self):
        tid,parent,sha,git,folder = self.build()
        store.connect().execute('UPDATE build_manifests SET receipt=NULL WHERE task_id=?',(tid,))
        with patch('hive.start.run_tests',return_value={'fixture.test':True}) as validate:
            self.assertEqual(build_receipts.validate(tid,1,self.repo)['commit'],sha)
            self.assertEqual(build_receipts.validate(tid,1,self.repo)['commit'],sha)
            validate.assert_called_once()
            git('commit','-q','--allow-empty','-m','diverged')
            self.assertIsNone(build_receipts.validate(tid,1,self.repo))
            git('update-ref','refs/heads/main',sha)
            (folder/'up.git').rename(folder/'unavailable.git')
            self.assertIsNone(build_receipts.validate(tid,1,self.repo))

    def test_catalog_binds_sources_and_memory_edits_to_project(self):
        db = Path(self.temp.name)/'fixture.db'
        with closing(sqlite3.connect(db)) as con, con:
            con.execute('CREATE TABLE evidence(n INTEGER)')
            con.execute('INSERT INTO evidence VALUES(42)')
        entries = [{'kind':'db','name':'reports','where':str(db)},
                   {'kind':'cmd','name':'private','where':'unavailable'}]
        with patch('hive.access.load',return_value=entries):
            catalog = {t.name:t for t in work_tools.catalog(self.repo)}
            query = catalog['business_query']
            self.assertIn('42',query.call({'source':'reports','query':'SELECT n FROM evidence'})['data'])
            with self.assertRaises(tools.Refused):
                runtime_tools.validate(query,{'source':'private','query':'SELECT 1'})
            fid = catalog['memory_add'].call({'text':'original'})['data']['id']
            with self.assertRaises(tools.Refused):
                work_tools.edit_memory(self.repo+'-other','forget',{'id':fid,'expected_text':'original'})
            new = catalog['memory_update'].call({'id':fid,'expected_text':'original','text':'changed'})['data']['id']
            catalog['memory_forget'].call({'id':new,'expected_text':'changed'})


if __name__ == '__main__':
    unittest.main()
