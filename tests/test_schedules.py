"""Civil-time occurrences, durable event deduplication and approval previews."""

import datetime as dt
import hashlib
import hmac
import json
import os
import sys
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

sys.path.insert(0, os.getcwd())
import test_tasks as fixtures
from hive import actions, gateway, routines, schedules, store, tasks, tools


class ScheduleTests(unittest.TestCase):
    setUp = fixtures.TaskTests.setUp
    channel = fixtures.TaskTests.channel

    def test_gap_and_fold(self):
        zone = ZoneInfo('America/New_York')

        def upcoming(clock, start):
            definition, _ = schedules.parse(f'daily at {clock} America/New_York: report', self.repo)
            times = schedules.occurrences(definition, dt.datetime.fromisoformat(start).timestamp())
            return [dt.datetime.fromtimestamp(t, zone).isoformat() for t in times]

        self.assertEqual(upcoming('02:30', '2026-03-07T04:00:00-05:00')[0], '2026-03-09T02:30:00-04:00')
        autumn = upcoming('01:30', '2026-10-31T04:00:00-04:00')
        self.assertEqual(autumn[:2], ['2026-11-01T01:30:00-04:00', '2026-11-02T01:30:00-05:00'])
        self.assertEqual(upcoming('01:30', '2026-11-01T01:45:00-04:00')[0], autumn[1])

    def test_preview_precedes_save_and_weekdays_skip_weekends(self):
        cmd = 'weekdays at 09:00 Asia/Kolkata: prepare report'
        with patch.object(actions, 'confirm', return_value=None) as confirm:
            self.assertEqual(routines.command(self.ch, self.repo, cmd), 'routine_cancelled')
        self.assertEqual(routines.rows(self.ch, self.repo), [])
        preview = confirm.call_args.args[3]
        self.assertEqual(preview.count('+05:30'), 3)
        self.assertIn('Asia/Kolkata', preview)
        weekly, _ = schedules.parse('weekly on Mon, Fri at 17:45 UTC: summarize', self.repo)
        self.assertEqual(weekly['days'], [0, 4])
        with self.assertRaises(tools.Refused):
            schedules.parse('daily at 09:00 No/SuchZone: summarize', self.repo)

    def test_missed_occurrences_and_unverified_prior_task(self):
        definition, _ = schedules.parse('daily at 09:00 UTC: report', self.repo)
        rid = routines.create(self.ch, self.repo, 'report', 0, now=0, definition=definition)
        now = 30 * 86400
        (first,) = routines.tick(self.ch, self.repo, now=now, enqueue=True)
        tasks.update(first, state='waiting_verification')
        store.close()
        self.assertEqual(routines.tick(self.ch, self.repo, now=now + 400000, enqueue=True), [])
        self.assertEqual(len(routines.rows(self.ch, self.repo)), 1)
        tasks.update(first, state='owner_confirmed')
        (second,) = routines.tick(self.ch, self.repo, now=now + 400000, enqueue=True)
        self.assertNotEqual(first, second)
        self.assertGreater(routines.rows(self.ch, self.repo)[0]['next_run'], now + 400000)

    def test_signed_events_replay_scope_and_untrusted_observations(self):
        hook = {
            'fields': ['priority', 'note'],
            'project': tasks._project(self.repo),
            'key_env': 'HIVE_FIXTURE_SIGNING',
        }
        cfg = {'webhooks': {'invoice': hook}}
        body = b'{"priority":3,"note":"untrusted event text"}'
        with (
            patch.object(gateway, 'config', return_value=cfg),
            patch.dict(os.environ, HIVE_FIXTURE_SIGNING='fixture'),
        ):
            definition, instruction = schedules.parse(
                'on webhook.invoice where {"priority":{"gte":2}}: review invoices', self.repo
            )
            routines.create(self.ch, self.repo, instruction, 0, now=1, definition=definition)
            headers = {'x-hive-timestamp': '1000', 'x-hive-event-id': 'invoice-9'}
            self.assertFalse(schedules.webhook('invoice', headers, body, now=1000))
            headers['x-hive-signature'] = hmac.new(
                b'fixture', b'1000.invoice-9.' + body, hashlib.sha256
            ).hexdigest()
            self.assertFalse(schedules.webhook('invoice', headers, body, now=1400))
            self.assertTrue(schedules.webhook('invoice', headers, body, now=1001))
            store.close()
            self.assertTrue(schedules.webhook('invoice', headers, body, now=1002))
            (tid,) = routines.tick(self.ch, self.repo, now=1010, enqueue=True)
            task = tasks.get(tid, self.ch, self.repo)
            self.assertEqual(task['instruction'], 'review invoices')
            self.assertEqual(task['metadata']['trigger_event'], json.loads(body))
            self.assertEqual(store.connect().execute('SELECT count(*) FROM event_runs').fetchone()[0], 1)
            with self.assertRaises(tools.Refused):
                schedules.parse('on webhook.invoice where {"secret":true}: review', self.repo)
            with self.assertRaises(tools.Refused):
                schedules.fields_for('webhook.invoice', self.repo + '-other')
            self.assertFalse(schedules.matches({'priority': {'gte': 2}}, {'priority': True}))


if __name__ == '__main__':
    unittest.main()
