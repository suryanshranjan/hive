"""hive/vault.py: his secrets encrypted on disk, read back the same, old plain files encrypted on first read, and the key
kept where he chose (the audit, Nov 15). No network; the keychain is a stand-in, so the real one is never touched.
usage: python3 tests/test_vault.py   (run from the hive repo root)"""
import json, os, sys, tempfile, types
sys.path.insert(0, os.getcwd())
home = tempfile.mkdtemp(); os.environ['HOME'] = os.environ['USERPROFILE'] = home
os.environ.pop('HIVE_MASTER_KEY', None); os.environ.pop('HIVE_VAULT', None)
from hive import vault

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))

hive = os.path.join(home, '.hive'); os.makedirs(os.path.join(hive, 'mail'))
secret = {'user': 'asha@example.com', 'password': 'app-pass-123'}
p = os.path.join(hive, 'mail', 'p1.json')

if vault._fernet_cls() is None:
    print('skip the encrypted checks: the cryptography package is not installed (pip install "hive-swarm[secure]")')
    vault.save_json(p, secret)
    check('without cryptography: plain JSON, as before', json.load(open(p)), secret)
    check('without cryptography: said plainly', vault.where(), 'plain')
    sys.exit(fail)

# 1. encrypted on disk, the same when read
vault.save_json(p, secret)
raw = open(p).read()
check('the password is not on disk in readable form', ('app-pass-123' in raw, 'asha@' in raw), (False, False))
check('read back the same', vault.load_json(p), secret)
check('the key lives in ~/.hive/vault.key by default', (vault.where(), os.path.exists(os.path.join(hive, 'vault.key'))), ('file', True))
check('lists too (database sources)', (vault.save_json(p + '.l', [{'name': 'db', 'where': 'postgres://u:pw@h/d'}]),
                                       vault.load_json(p + '.l'))[1], [{'name': 'db', 'where': 'postgres://u:pw@h/d'}])

# 2. an old plain file is read as before, and encrypted in place on that first read
old = os.path.join(hive, 'telegram.json'); json.dump({'token': '123:abc', 'chat_id': 7}, open(old, 'w'))
check('an old plain file still reads', vault.load_json(old), {'token': '123:abc', 'chat_id': 7})
check('... and is encrypted from then on', ('123:abc' in open(old).read(), vault.sealed(json.load(open(old)))), (False, True))
json.dump({'api_key': 'sk-plain'}, open(os.path.join(hive, 'fast.json'), 'w'))
check('status names what is still plain', [os.path.basename(x) for x in vault.status()[1]], ['fast.json'])
check('migrate encrypts it', (vault.migrate(), vault.status()[1]), (1, []))
check('a missing file gives the default', vault.load_json(os.path.join(hive, 'nope.json'), {}), {})

# 3. a missing or wrong key is said plainly, never read as "not connected"
key = open(os.path.join(hive, 'vault.key'), 'rb').read(); os.remove(os.path.join(hive, 'vault.key'))
try:
    vault.load_json(p); said = ''
except vault.Locked as e:
    said = str(e)
check('no key here: a plain reason, nothing invented', 'key is not on this machine' in said, True)
open(os.path.join(hive, 'vault.key'), 'wb').write(vault._fernet_cls().generate_key())
try:
    vault.load_json(p); said = ''
except vault.Locked as e:
    said = str(e)
check('another key: said so', 'different key' in said, True)
open(os.path.join(hive, 'vault.key'), 'wb').write(key)
check('the right key again: read', vault.load_json(p), secret)

# 4. HIVE_MASTER_KEY: any passphrase, and nothing written to disk for it
os.environ['HIVE_MASTER_KEY'] = 'a long passphrase Render made'
e = os.path.join(hive, 'env.json'); vault.save_json(e, {'k': 'v'})
os.rename(os.path.join(hive, 'vault.key'), os.path.join(hive, 'vault.key.away'))
check('the env key: used, and no key file needed', (vault.where(), vault.load_json(e)), ('env', {'k': 'v'}))
os.environ.pop('HIVE_MASTER_KEY'); os.rename(os.path.join(hive, 'vault.key.away'), os.path.join(hive, 'vault.key'))

# 5. the keychain (a stand-in): the key moves there and off the disk, and secrets still read
store = {}
sys.modules['keyring'] = types.SimpleNamespace(get_password=lambda s, a: store.get((s, a)),
                                               set_password=lambda s, a, v: store.__setitem__((s, a), v))
print('  ' + vault.use_keychain())
check('keychain: the key left the disk', (vault.where(), os.path.exists(os.path.join(hive, 'vault.key'))), ('keychain', False))
check('keychain: secrets still read', vault.load_json(p), secret)
check('keychain: the key is kept per Hive home, under "hive"', [s for s, _ in store], ['hive'])

# 6. HIVE_VAULT=plain (a test or a machine that wants it): plain files
os.environ['HIVE_VAULT'] = 'plain'
q = os.path.join(hive, 'plain.json'); vault.save_json(q, {'a': 1})
check('HIVE_VAULT=plain writes plain JSON', json.load(open(q)), {'a': 1})
os.environ.pop('HIVE_VAULT')

# 7. owner-only file mode where the system has one
if os.name != 'nt':
    check('owner-only', oct(os.stat(p).st_mode & 0o777), '0o600')
sys.exit(fail)
