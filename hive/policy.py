"""Request authority comes from the transport, never from model output."""
from contextvars import ContextVar
from collections import UserDict
from dataclasses import dataclass
from functools import wraps


@dataclass(frozen=True)
class RequestContext:
    origin: str = 'owner'
    owner: str = 'owner'
    chat: str = ''
    update_id: str = ''
    source_ref: str = ''
    project: str = ''
    text: str = ''
    task_id: str = ''


CURRENT = ContextVar('hive_request', default=None)
PROJECT = ContextVar('hive_listener_project', default=None)


class ProjectState(UserDict):
    """Legacy conversational state shared by requests within one listener project."""

    def __init__(self):
        self.projects = {}

    @property
    def data(self):
        return self.projects.setdefault(PROJECT.get(), {})


def context():
    return CURRENT.get() or RequestContext()


def request(fn):
    @wraps(fn)
    def wrapped(ch, repo, text, *args, **kwargs):
        parent = CURRENT.get()
        origin = kwargs.get('origin', args[4] if len(args) > 4 else 'owner')
        if parent and parent.origin != 'owner':
            origin = parent.origin
        ctx = RequestContext(
            origin=origin,
            owner=parent.owner if parent else 'owner',
            text=text,
            chat=str(getattr(ch, 'chat', '')),
            update_id=str(getattr(ch, 'last_update', '')),
            source_ref=str(getattr(ch, 'last_archive', '')),
            project=str(repo),
            task_id=parent.task_id if parent else '',
        )
        token = CURRENT.set(ctx)
        try:
            # All cloud paths (direct request, onboarding, away/handoff) share the boundary.
            from . import actions
            positional = list(args)
            poll = kwargs.get('poll', positional[0] if positional else 20)
            if kwargs.get('cloud'):
                kwargs['cloud'] = actions.cloud_callback(ch, kwargs['cloud'], poll)
            elif len(positional) > 3 and positional[3]:
                positional[3] = actions.cloud_callback(ch, positional[3], poll)
            return fn(ch, repo, text, *positional, **kwargs)
        finally:
            CURRENT.reset(token)
    return wrapped
