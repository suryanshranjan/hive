"""Voice notes, both ways (P3 of docs/jarvis_plan.md).

In: the owner answers Hive by talking. Speech is transcribed on this machine with Whisper (faster-whisper, open source),
so his voice never leaves it. pip install faster-whisper (the first transcription downloads the model; HIVE_WHISPER
picks its size, default "small", which handles English mixed with Hindi; "base" is faster, "medium" more accurate).

Out: when he speaks to Hive, Hive answers in voice too (the text stays above it, to read or copy), unless the answer
carries a link, a long list or numbers he will want to copy. He can say "always reply in voice", "reply in voice when I
send voice" (the default) or "no voice replies".
  - Piper by default: a local voice (pip install piper-tts; the voice, about 60 MB, is downloaded once in the
    background, HIVE_PIPER_VOICE, default en_US-lessac-medium). Nothing he hears is made anywhere but this machine.
  - Or any OpenAI-style speech API: HIVE_TTS_KEY with HIVE_TTS_BASE_URL (default https://api.openai.com/v1),
    HIVE_TTS_MODEL (default gpt-4o-mini-tts) and HIVE_TTS_VOICE (default alloy). His replies' text goes to that provider.
Telegram plays OGG/Opus as a voice note: ffmpeg makes it (the system's, or the one in pip install imageio-ffmpeg)."""
import json, os, re, shutil, subprocess, tempfile, threading, time, urllib.request

_model = None

def available():
    try:
        import faster_whisper  # noqa: F401
        return True
    except Exception:
        return False

def transcribe(path):
    """The text of an audio file (a Telegram voice note is OGG/Opus), or None if Whisper is not installed or fails."""
    global _model
    try:
        from faster_whisper import WhisperModel
    except Exception:
        return None
    try:
        if _model is None:
            _model = WhisperModel(os.environ.get('HIVE_WHISPER', 'small'), device='cpu', compute_type='int8')
        segments, _ = _model.transcribe(path, beam_size=5, vad_filter=True)
        text = ' '.join(s.text.strip() for s in segments).strip()
        return text or None
    except Exception:
        return None

# ---------------------------------------------------------------------------------------------------- speaking

VOICE = os.environ.get('HIVE_PIPER_VOICE', 'en_US-lessac-medium')
_PIPER = {}
_LOADING = {}
_LOCK = threading.Lock()

def _voices_dir():
    from . import embed
    return os.path.join(embed.cache_dir(), 'piper')

def ffmpeg():
    exe = shutil.which('ffmpeg')
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None

def provider():
    """'api', 'piper', or None (no way to speak here)."""
    if os.environ.get('HIVE_TTS', '').lower() in ('0', 'off', 'no'):
        return None
    if os.environ.get('HIVE_TTS_KEY'):
        return 'api'
    try:
        import piper  # noqa: F401
    except Exception:
        return None
    return 'piper' if ffmpeg() else None

def _load_piper():
    try:
        from piper import PiperVoice
        d = _voices_dir(); os.makedirs(d, exist_ok=True)
        onnx = os.path.join(d, VOICE + '.onnx')
        if not os.path.exists(onnx):
            import sys
            subprocess.run([sys.executable, '-m', 'piper.download_voices', '--download-dir', d, VOICE],
                           capture_output=True, timeout=900)
        v = PiperVoice.load(onnx)
        with _LOCK:
            _PIPER[VOICE] = v
    except Exception as e:
        print(f'The local voice could not load ({e!r}); replies stay in text.', flush=True)
    finally:
        with _LOCK:
            _LOADING.pop(VOICE, None)

def warm():
    """Load the local voice in the background (once): no reply ever waits on its download."""
    if provider() != 'piper':
        return
    with _LOCK:
        if VOICE in _PIPER or VOICE in _LOADING:
            return
        t = _LOADING[VOICE] = threading.Thread(target=_load_piper, daemon=True)
    t.start()

def ready():
    p = provider()
    if p == 'api':
        return True
    if p == 'piper':
        if VOICE in _PIPER:
            return True
        warm()
    return False

def wait(seconds=900):
    warm()
    t = _LOADING.get(VOICE)
    if t is not None:
        t.join(seconds)
    return ready()

def _to_ogg(src, dst):
    exe = ffmpeg()
    p = subprocess.run([exe, '-y', '-loglevel', 'error', '-i', src, '-c:a', 'libopus', '-b:a', '32k', '-ac', '1', dst],
                       capture_output=True, timeout=120)
    return p.returncode == 0 and os.path.getsize(dst) > 0

def speakable(text):
    """What is said aloud: emoji, markup and the bee dropped; None when it is not one for the ear (a link, a long list,
    a code, or too long)."""
    t = re.sub(r'<[^>]+>', '', text or '')
    if re.search(r'https?://|www\.|`|\b[A-Z0-9]{12,}\b', t) or len(t) > 900 or t.count('\n') > 8:
        return None
    t = re.sub(r'[\U0001F000-\U0001FFFF☀-➿️]', '', t)
    t = re.sub(r'^\s*[-•▸]\s*', '', t, flags=re.M).replace('*', '').strip()
    return t or None

def synthesize(text):
    """A voice note of the text (an .ogg path), or None (nothing to speak with yet, or it failed). The caller deletes it."""
    say = speakable(text)
    if not say or not ready():
        return None
    out = os.path.join(tempfile.mkdtemp(prefix='hive_voice_'), 'reply.ogg')
    try:
        if provider() == 'api':
            body = json.dumps({'model': os.environ.get('HIVE_TTS_MODEL', 'gpt-4o-mini-tts'), 'input': say,
                               'voice': os.environ.get('HIVE_TTS_VOICE', 'alloy'), 'response_format': 'opus'}).encode()
            req = urllib.request.Request(os.environ.get('HIVE_TTS_BASE_URL', 'https://api.openai.com/v1').rstrip('/') +
                                         '/audio/speech', data=body, headers={
                                             'Authorization': f"Bearer {os.environ['HIVE_TTS_KEY']}",
                                             'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=60) as r:
                open(out, 'wb').write(r.read())
            return out if os.path.getsize(out) > 0 else None
        import wave
        wav = out[:-4] + '.wav'
        with wave.open(wav, 'wb') as w:
            _PIPER[VOICE].synthesize_wav(say, w)
        ok = _to_ogg(wav, out)
        os.remove(wav)
        return out if ok else None
    except Exception as e:
        print(f'Could not make the voice note ({e!r}); the text was sent.', flush=True)
        return None

# --------------------------------------------------------------------------------------------- his preference

PREF = re.compile(r"\b(always (?:reply|answer|talk|speak) (?:in|with|by) voice|(?:reply|answer) (?:in|with) voice when I "
                  r"(?:send|speak|talk)|(?:no|stop(?: the)?|don'?t send(?: me)?) voice (?:replies|notes|messages)|"
                  r"(?:reply|answer) in text( only)?|voice (?:replies|notes) (?:on|off))\b", re.I)

def preference():
    from . import store
    return store.get('voice_replies', 'when_voice')

def set_from(text):
    """His words to a preference: 'always', 'when_voice' or 'never'. Returns a plain sentence."""
    from . import store
    t = (text or '').lower()
    if re.search(r'always (reply|answer|talk|speak)|voice (replies|notes) on', t):
        store.put('voice_replies', 'always'); return "I'll answer in voice, with the text above it."
    if re.search(r"\bno voice|stop(?: the)? voice|don'?t send(?: me)? voice|text( only)?\b|voice (replies|notes) off", t):
        store.put('voice_replies', 'never'); return "Text only from now on."
    store.put('voice_replies', 'when_voice'); return "When you send me a voice note, I'll answer in voice too."

def wanted(heard_voice):
    p = preference()
    return p == 'always' or (p == 'when_voice' and heard_voice)
