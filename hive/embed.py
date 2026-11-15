"""Meaning, not only words (memory 2.0; Gate 118 R2: keyword search found 3 of 6 questions worded differently from the
fact, "who brings our lentils?" for "our dal supplier is Sharma Traders").

A small embedding model (fastembed's BAAI/bge-small-en-v1.5: 384 numbers per sentence, about 70 MB, runs on the CPU on
this machine; nothing about him is sent anywhere) turns each fact and each question into a vector; a fact close in
meaning to the question is recalled even when they share no word.

Optional: pip install "hive-swarm[memory]". Without it Hive recalls by words, as before. HIVE_EMBED=0 turns it off.
A reply never waits for the model: it is loaded in the background (when Hive starts listening, or at the first
question), and until it is ready recall uses words alone. The download happens once per machine, into HIVE_MODELS
(default: a folder in the system's temp space; on Render, the service's disk)."""
import os, tempfile, threading

MODEL = os.environ.get('HIVE_EMBED_MODEL', 'BAAI/bge-small-en-v1.5')
_LOCK = threading.Lock()
_M = {}
_LOADING = {}

def available():
    if os.environ.get('HIVE_EMBED', '').strip().lower() in ('0', 'off', 'no'):
        return False
    try:
        import fastembed  # noqa: F401
        import numpy  # noqa: F401
        return True
    except Exception:
        return False

def cache_dir():
    return os.environ.get('HIVE_MODELS') or os.path.join(tempfile.gettempdir(), 'hive_models')

def _load():
    try:
        os.environ.setdefault('HF_HUB_DISABLE_SYMLINKS_WARNING', '1')
        os.environ.setdefault('HF_HUB_DISABLE_PROGRESS_BARS', '1')
        from fastembed import TextEmbedding
        os.makedirs(cache_dir(), exist_ok=True)
        m = TextEmbedding(MODEL, cache_dir=cache_dir())
        with _LOCK:
            _M[MODEL] = m
    except Exception as e:
        print(f'The meaning model could not load ({e!r}); recall uses words alone.', flush=True)
    finally:
        with _LOCK:
            _LOADING.pop(MODEL, None)

def warm():
    """Start loading the model in the background (once). Returns at once."""
    if not available():
        return
    with _LOCK:
        if MODEL in _M or MODEL in _LOADING:
            return
        t = _LOADING[MODEL] = threading.Thread(target=_load, daemon=True)
    t.start()

def ready():
    """True when the model is loaded; if not, its loading is started and recall goes on by words for now."""
    if MODEL in _M:
        return True
    warm()
    return False

def wait(seconds=300):
    """Load it now and wait (tests, benches): True when ready."""
    warm()
    t = _LOADING.get(MODEL)
    if t is not None:
        t.join(seconds)
    return MODEL in _M

def vectors(texts):
    """Unit vectors (numpy float32) for the texts, in order. Only call when ready()."""
    import numpy as np
    out = []
    for v in _M[MODEL].embed(list(texts)):
        v = np.asarray(v, dtype=np.float32)
        n = float(np.linalg.norm(v)) or 1.0
        out.append(v / n)
    return out
