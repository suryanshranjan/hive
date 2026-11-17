"""Host-side browser IPC and mount boundary check. Requires hive-browser:1.

Creates and removes one fresh profile volume; no account or external site is used.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.getcwd())
from hive import browser, policy, sandbox


class BrowserContainerTests(unittest.TestCase):
    def test_worker_protocol_private_profile_and_mounts(self):
        with tempfile.TemporaryDirectory(prefix='hive_browser_fixture_') as repo:
            key = hashlib.sha256((policy.context().owner + os.path.realpath(repo)).encode()).hexdigest()[:24]
            volume = 'hive-browser-profile-' + key
            session = None
            try:
                with patch.object(browser, 'config', return_value={'enabled': True}):
                    session = browser.Session(repo)
                    result = session.call('inspect', {})
                    self.assertEqual(result['status'], 'done')
                    self.assertEqual(result['data']['url'], 'about:blank')
                    raw = subprocess.check_output(sandbox.docker() + ['inspect', session.container], text=True)
                    info = json.loads(raw)[0]
                    mounts = info['Mounts']
                    self.assertEqual(len(mounts), 2)
                    package = next(m for m in mounts if m['Destination'] == '/opt/hive/hive')
                    self.assertFalse(package['RW'])
                    profile = next(m for m in mounts if m['Destination'] == '/profile')
                    self.assertEqual(profile['Type'], 'volume')
                    self.assertEqual(profile['Name'], volume)
                    self.assertEqual(info['Config']['User'], 'pwuser')
                    self.assertIn('ALL', info['HostConfig']['CapDrop'])
                    self.assertTrue(any('no-new-privileges' in x for x in info['HostConfig']['SecurityOpt']))
            finally:
                if session: session.close()
                subprocess.run(sandbox.docker() + ['volume', 'rm', volume], check=True, capture_output=True)


if __name__ == '__main__':
    unittest.main()
