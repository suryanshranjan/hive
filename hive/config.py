"""Project configuration, read from .hive/config.json at the repository root.

{
  "test_cmd": "python -m pytest -q --junitxml=.hive/junit.xml",   # runs the whole suite, writes JUnit XML
  "branch": "main",                                                 # the shared branch (default: the remote's default branch)
  "junit": ".hive/junit.xml",                                       # where test_cmd writes it, relative to the repo
  "snapshot_links": ["node_modules", ".venv"],                      # dependency folders linked into main's snapshot
  "areas": {"payouts": ["tests/test_payout*"], "fees": ["tests/test_fee*"]}   # claimable groups of tests (globs)
}
"""
import json, os

DEFAULTS = {'junit': '.hive/junit.xml', 'snapshot_links': [], 'areas': {}}

def load(root='.'):
    path = os.path.join(root, '.hive', 'config.json')
    if not os.path.exists(path):
        raise SystemExit(f'no {path}: run `hive init` first')
    cfg = dict(DEFAULTS, **json.load(open(path)))
    if not cfg.get('test_cmd'):
        raise SystemExit(f'{path} needs "test_cmd"')
    return cfg
