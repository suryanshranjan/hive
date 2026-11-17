"""One dispatcher may attempt an event. Ambiguous delivery is never auto-retried."""
import time
from . import store


def claim(eid):
    with store.transaction() as con:
        con.execute("UPDATE notifications SET state='unknown',updated=? WHERE state='sending' AND updated<?",
                    (time.time(), time.time() - 120))
        return con.execute("INSERT OR IGNORE INTO notifications(event_id,state,updated) VALUES(?,'sending',?)",
                           (eid, time.time())).rowcount == 1


def finish(eid, state, receipt=''):
    store.connect().execute('UPDATE notifications SET state=?,updated=?,receipt=? WHERE event_id=?',
                            (state, time.time(), str(receipt), eid))


def deliver(ch, events, text, buttons=None):
    """Claim all included events before sending their exact, deterministic text."""
    claimed = [e for e in events if claim(e['id'])]
    if len(claimed) != len(events):
        for e in claimed:
            store.connect().execute("DELETE FROM notifications WHERE event_id=? AND state='sending'", (e['id'],))
        return False
    try:
        from .telegram import Channel
        receipt = ch.send(text, html=True, buttons=buttons, **({'retry': False} if isinstance(ch, Channel) else {}))
        if receipt is None:
            raise RuntimeError('No delivery receipt')
    except Exception:
        for e in events:
            finish(e['id'], 'unknown')
        return False
    with store.transaction() as con:
        for e in events:
            finish(e['id'], 'sent', receipt)
            con.execute("UPDATE pulse_events SET state='sent',sent_at=? WHERE id=?", (time.time(), e['id']))
    return True


def digest(ch):
    from . import pulse, telegram
    rows = [e for e in pulse.pending() if e['source'] not in pulse.settings()['muted']][:6]
    if not rows:
        return 0
    text = 'While you were away:\n' + '\n'.join('• ' + telegram.esc(e['title']) for e in rows)
    return len(rows) if deliver(ch, rows, text) else 0
