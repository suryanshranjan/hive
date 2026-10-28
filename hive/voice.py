"""Voice notes: the owner answers Hive by talking. Speech is transcribed on this machine with Whisper (faster-whisper,
open source), so the owner's voice never leaves it.

Install once: pip install faster-whisper   (the first transcription downloads the model; HIVE_WHISPER picks its size,
default "small", which handles English mixed with Hindi; "base" is faster, "medium" more accurate)."""
import os

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
