"""Hive's secrets, encrypted on disk (the audit, Nov 15: his bot token, mail password, payment and database keys, deploy
hooks and model keys all sat in plain JSON under ~/.hive, and chmod 600 does nothing on Windows).

Every file that holds a secret keeps its usual path, so the rest of Hive is unchanged, but its contents become
{"hive_vault": 1, "data": "<encrypted>"} (Fernet: AES-128 with an HMAC, from the `cryptography` package). The key is:
  1. HIVE_MASTER_KEY, when set (on Render: a setting in his own Render account, never on the disk);
  2. else in the computer's own keychain, if he chose it once with `hive secrets keychain` (Windows Credential Manager,
     macOS Keychain, the Linux secret service; the `keyring` package);
  3. else ~/.hive/vault.key, owner-only.
Without `cryptography` installed, files stay plain JSON as before, and `hive doctor` says so.

What this protects: copies of ~/.hive (a backup, a support bundle, a synced folder, a stray `cat`) no longer show his
keys, and a key in the environment or the keychain stays off the disk entirely. What it does not: a program running as
him can still ask for the key, which is why builders run in a container where Docker exists.

  hive secrets            where secrets are kept, and whether any file is still in plain text
  hive secrets migrate    encrypt every known secret file now (each is also encrypted the first time Hive reads it)
  hive secrets keychain   keep the key in this computer's keychain instead of ~/.hive/vault.key"""
import base64, json, os

SERVICE = 'hive'

def _home():
    return os.path.join(os.path.expanduser('~'), '.hive')

def _choice_path():
    return os.path.join(_home(), 'vault.json')

def _key_path():
    return os.path.join(_home(), 'vault.key')

class Locked(RuntimeError):
    """A secret is encrypted and its key is not here."""

def _private_write(path, data, binary=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    private_permissions(os.path.dirname(path), directory=True)
    tmp = f'{path}.{os.getpid()}.tmp'
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, 'O_BINARY', 0), 0o600)
    try:
        private_permissions(tmp)
    except BaseException:
        os.close(fd)
        raise
    with os.fdopen(fd, 'wb' if binary else 'w', **({} if binary else {'encoding': 'utf-8'})) as f:
        f.write(data)
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass

def _fernet_cls():
    try:
        from cryptography.fernet import Fernet
        return Fernet
    except Exception:
        return None


def private_permissions(path, directory=False):
    """Apply real Windows ACLs or POSIX mode bits before writing personal data."""
    if os.name != 'nt':
        os.chmod(path, 0o700 if directory else 0o600)
        return
    import getpass, subprocess
    user = getpass.getuser()
    domain = os.environ.get('USERDOMAIN')
    account = f'{domain}\\{user}' if domain else user
    permission = '(OI)(CI)F' if directory else 'F'
    result = subprocess.run(['icacls', path, '/inheritance:r', '/grant:r', f'{account}:{permission}'],
                            capture_output=True, timeout=10)
    if result.returncode:
        raise Locked('Could not make the personal-data path private on this machine.')

def _keyring():
    try:
        import keyring
        return keyring
    except Exception:
        return None

def _chosen():
    try:
        return json.load(open(_choice_path(), encoding='utf-8')).get('key_in')
    except (OSError, ValueError):
        return None

def where():
    """Where the key lives: 'env', 'keychain', 'file', or 'plain' (no encryption available)."""
    if _fernet_cls() is None:
        return 'plain'
    if os.environ.get('HIVE_MASTER_KEY'):
        return 'env'
    if _chosen() == 'keychain' and _keyring() is not None:
        return 'keychain'
    return 'file'

def _account():
    return 'master:' + os.path.abspath(_home())

def _key(create=True):
    """The key as bytes, or None (create=False and none yet)."""
    Fernet = _fernet_cls()
    w = where()
    if w == 'env':
        k = os.environ['HIVE_MASTER_KEY'].strip().encode()
        try:   # any passphrase works: one that is not already a Fernet key is stretched into one
            Fernet(k); return k
        except Exception:
            import hashlib
            return base64.urlsafe_b64encode(hashlib.pbkdf2_hmac('sha256', k, b'hive-vault', 200_000))
    if w == 'keychain':
        kr = _keyring(); k = kr.get_password(SERVICE, _account())
        if not k and create:
            k = Fernet.generate_key().decode(); kr.set_password(SERVICE, _account(), k)
        return k.encode() if k else None
    try:
        return open(_key_path(), 'rb').read().strip() or None
    except OSError:
        if not create:
            return None
    k = Fernet.generate_key()
    _private_write(_key_path(), k, binary=True)
    return k

def sealed(data):
    return isinstance(data, dict) and data.get('hive_vault') == 1 and 'data' in data

def save_json(path, data):
    """Write data (any JSON value) to path: encrypted when Hive can, else plain JSON, owner-only either way."""
    Fernet = _fernet_cls()
    if Fernet is None:
        raise Locked('Secret storage requires cryptography. Install hive-swarm[secure]; nothing was saved.')
    token = Fernet(_key()).encrypt(json.dumps(data, ensure_ascii=False).encode('utf-8')).decode()
    _private_write(path, json.dumps({'hive_vault': 1, 'data': token}))

def load_json(path, default=None):
    """The value stored at path (decrypted), or default if there is no readable file. A plain file is encrypted in
    place the first time it is read, when Hive can encrypt."""
    try:
        raw = json.load(open(path, encoding='utf-8'))
    except (OSError, ValueError):
        return default
    if not sealed(raw):
        if _fernet_cls() is None:
            raise Locked('Reading legacy secret files requires cryptography; install hive-swarm[secure].')
        save_json(path, raw)
        return raw
    Fernet = _fernet_cls()
    if Fernet is None:
        raise Locked(f'{path} is encrypted, and the cryptography package is not installed here '
                     '(pip install "hive-swarm[secure]").')
    k = _key(create=False)
    if not k:
        raise Locked(f'{path} is encrypted, but its key is not on this machine (HIVE_MASTER_KEY, the keychain, or '
                     '~/.hive/vault.key).')
    try:
        return json.loads(Fernet(k).decrypt(raw['data'].encode()).decode('utf-8'))
    except Exception:
        raise Locked(f'{path} is encrypted with a different key than the one here.') from None

def files():
    """Every file under ~/.hive that holds a secret."""
    h = _home(); out = []
    for name in ('telegram.json', 'fast.json', 'llm.json', 'google.json'):
        out.append(os.path.join(h, name))
    for d in ('mail', 'calendar', 'payments', 'access', 'deploy'):
        p = os.path.join(h, d)
        if os.path.isdir(p):
            out += [os.path.join(p, f) for f in sorted(os.listdir(p)) if f.endswith('.json')]
    return [p for p in out if os.path.exists(p)]

def status():
    """(where the key lives, files still in plain text)."""
    plain = []
    for p in files():
        try:
            if not sealed(json.load(open(p, encoding='utf-8'))):
                plain.append(p)
        except (OSError, ValueError):
            pass
    return where(), plain

def migrate():
    """Encrypt every known secret file now. Returns how many were encrypted."""
    if _fernet_cls() is None:
        return 0
    n = 0
    for p in files():
        try:
            raw = json.load(open(p, encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if not sealed(raw):
            save_json(p, raw); n += 1
    return n

def use_keychain():
    """Move the key from ~/.hive/vault.key into this computer's keychain. Returns a plain sentence."""
    kr, Fernet = _keyring(), _fernet_cls()
    if Fernet is None or kr is None:
        return 'This needs the keyring and cryptography packages: pip install "hive-swarm[secure]".'
    old = _key(create=False) if where() == 'file' else None
    k = (old or Fernet.generate_key()).decode()
    kr.set_password(SERVICE, _account(), k)
    if kr.get_password(SERVICE, _account()) != k:
        return "This computer's keychain did not keep the key, so nothing was changed."
    _private_write(_choice_path(), json.dumps({'key_in': 'keychain'}))
    if old:
        try:
            os.remove(_key_path())
        except OSError:
            pass
    return "The key is now in this computer's keychain, not on disk."

def main(args):
    if args and args[0] == 'migrate':
        n = migrate(); w, plain = status()
        print(f'Encrypted {n} file(s).' if w != 'plain' else
              'Nothing encrypted: install the cryptography package first (pip install "hive-swarm[secure]").')
        return 0 if not plain else 1
    if args and args[0] == 'keychain':
        print(use_keychain()); return 0
    w, plain = status()
    print({'env': 'Secrets are encrypted; the key comes from HIVE_MASTER_KEY.',
           'keychain': "Secrets are encrypted; the key is in this computer's keychain.",
           'file': 'Secrets are encrypted; the key is in ~/.hive/vault.key (owner-only). '
                   'For more: hive secrets keychain, or set HIVE_MASTER_KEY.',
           'plain': 'Secrets are in plain text: pip install "hive-swarm[secure]" to encrypt them.'}[w])
    for p in plain:
        print(f'  still plain: {p}')
    return 0
