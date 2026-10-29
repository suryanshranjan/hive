"""A fast local reader for Jarvis (Gate 49): Laya, the open copy of Jev, trained on the owner's style, reads what a short
message means in about half a second on a laptop, where a Claude call takes four or five. Used only when it is installed
and confident; everything else goes to Claude as before.

Gate 49: trained on 444 owner-style messages, it read 77.5% of 120 held-out ones right (Claude 92.5%); answering only
at confidence 0.5 or more (fitted on a separate practice set), it answered 56% of messages, and Laya-then-Claude read
94.2% right. Its two risky misreads that passed the threshold (a stop, a cloud move) are both confirmed with a tap.

Set up: pip install laya, then point HIVE_FAST_READER (or ~/.hive/reader) at the trained checkpoint
(gates/gate49/referee/run49.py train). It knows Gate 48's 9 intents, not the builder commands added after it, so those
and anything that needs details (what to build, the rule itself) always go to Claude."""
import os

THRESHOLD = float(os.environ.get('HIVE_FAST_THRESHOLD', 0.5))   # Gate 49, fitted on the practice set
ACT_ALONE = {'greeting', 'status', 'reply', 'stop_build', 'cloud_on', 'cloud_off'}   # need no details from Claude
_AGENT = {}

def _path():
    p = os.environ.get('HIVE_FAST_READER') or os.path.join(os.path.expanduser('~'), '.hive', 'reader')
    return p if os.path.isfile(os.path.join(p, 'rl_agent_config.json')) else None

def available():
    """True when Laya and a trained reader are installed here."""
    if not _path():
        return False
    try:
        import laya  # noqa: F401
        return True
    except ImportError:
        return False

def read(history_text, text):
    """{'intent': ...} when the reader is installed, confident, and the meaning needs nothing more; else None (ask
    Claude). Never raises."""
    if not available():
        return None
    try:
        import laya
        if 'agent' not in _AGENT:   # loaded once and kept, as the listener runs for hours
            _AGENT['agent'] = laya.load(_path())
        from .assistant import INTENTS_V1
        q = {'intent': {'type': 'choice', 'instructions': 'A business owner is texting his software assistant, Hive, '
                        'often with typos or in Hindi-English. What does he mean by his newest message?',
                        'criteria': INTENTS_V1}}
        state = f'The conversation so far:\n{history_text or "(nothing yet)"}\n\nHis newest message: {text}'
        r = _AGENT['agent'].system_one(state, q)['answers']['intent']
    except Exception:
        return None
    if (r.get('confidence') or 0) < THRESHOLD or r.get('choice') not in ACT_ALONE:
        return None
    return {'intent': r['choice'], 'fast': True}
