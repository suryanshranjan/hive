"""Tools exposed to the adaptive assistant. Metadata never grants authority."""
import json
from dataclasses import dataclass

from . import actions, policy, tools


def schema(properties, required=()):
    return {'type': 'object', 'properties': properties, 'required': list(required), 'additionalProperties': False}


STRING = {'type': 'string', 'minLength': 1, 'maxLength': 16000}


@dataclass
class Tool:
    name: str
    description: str
    schema: dict
    risk: str
    retry_safe: bool
    call: object
    identity: str = ''

    def public(self):
        return {'name': self.name, 'description': self.description, 'inputSchema': self.schema,
                'requires_approval': self.risk == tools.EXTERNAL}


def validate(tool, args):
    if not isinstance(args, dict):
        raise tools.Refused('Tool arguments must be an object.')
    from jsonschema import Draft202012Validator
    # Remote schemas may not cause implicit network fetches during validation.
    def refs(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in ('$ref', '$dynamicRef') and (not isinstance(child, str) or not child.startswith('#')):
                    raise tools.Refused('Tool schemas may only use local references.')
                refs(child)
        elif isinstance(value, list):
            for child in value: refs(child)
    refs(tool.schema)
    Draft202012Validator.check_schema(tool.schema)
    errors = list(Draft202012Validator(tool.schema).iter_errors(args))
    if errors:
        raise tools.Refused('Tool arguments do not match the declared schema.')


def catalog(repo):
    from . import calendar_, mail, recall
    def find(args):
        item = mail.find(repo, args['about'])
        if not item:
            return {'status': 'not_found', 'data': 'No matching email found.'}
        import email.utils
        return {'status': 'done', 'data': dict(item, email=email.utils.parseaddr(item.get('from', ''))[1])}
    def calendar(args):
        result = calendar_.answer(repo, args['when'])
        return {'status': 'done' if result.get('ok') else 'failed', 'data': result.get('say', '')}
    native = [
        Tool('mail_find', 'Find an email; returns its sender, subject and body.',
             schema({'about': STRING}, ['about']), tools.READ, True, find),
        Tool('calendar_check', 'Read calendar availability for a specified time or date.',
             schema({'when': STRING}, ['when']), tools.READ, True, calendar),
        Tool('memory_search', 'Find saved business facts and owner preferences.',
             schema({'query': STRING}, ['query']), tools.READ, True,
             lambda a: {'status': 'done', 'data': recall.recall(repo, a['query'])}),
        Tool('mail_send', 'Send a new email only after the owner confirms the exact recipient and text.',
             schema({'to': STRING, 'subject': STRING, 'body': STRING}, ['to', 'subject', 'body']),
             tools.EXTERNAL, False, lambda a: None),
        Tool('calendar_add', 'Create an event. start/end must be ISO timestamps with a time zone.',
             schema({'title': STRING, 'start': STRING, 'end': STRING, 'where': {'type': 'string'},
                     'guests': {'type': 'array', 'items': STRING, 'maxItems': 50}},
                    ['title', 'start', 'end', 'where', 'guests']), tools.EXTERNAL, False, lambda a: None),
    ]
    from . import browser, connectors
    return {t.name: t for t in native + browser.catalog(repo) + connectors.catalog(repo)}


def execute(ch, repo, tool, args, poll=20):
    if policy.context().origin != 'owner':
        raise tools.Refused('Outside content cannot initiate an assistant action.')
    validate(tool, args)
    if tool.risk == tools.READ:
        tools.allow('agent_read')
        return tool.call(args)
    tools.allow('agent_action')
    name = {'calendar_add': 'add_event'}.get(tool.name, tool.name)
    payload = args if name in ('mail_send', 'add_event') else {
        'tool': tool.name, 'args': args, 'identity': tool.identity}
    action_name = name if name in ('mail_send', 'add_event') else 'agent_action'
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if len(text) > 3200:
        raise tools.Refused('This action is too large to review in one approval. Split it into smaller actions.')
    from . import telegram
    aid = actions.confirm(ch, action_name, payload, telegram.esc('Approve this action?\n' + text), poll)
    if not aid:
        return {'status': 'cancelled', 'why': 'The action was not approved.'}
    output = {}
    def run(approved):
        if name == 'mail_send':
            from . import office
            return office._send_result(repo, approved)
        if name == 'add_event':
            import datetime as dt
            from . import google
            ok, receipt = google.add_event(approved['title'], dt.datetime.fromisoformat(approved['start']),
                                          dt.datetime.fromisoformat(approved['end']), approved['where'], approved['guests'])
            return actions.ActionResult('succeeded' if ok else 'unknown', receipt)
        return approved_external(repo, approved, output)
    result = actions.execute(aid, run)
    return dict(output, status=result.status, receipt=result.receipt, action_id=aid)


def approved_external(repo, approved, output=None):
    """Shared by immediate execution and an approval received after restart."""
    current = catalog(repo).get(approved['tool'])
    if not current or current.identity != approved['identity']:
        return actions.ActionResult('needs_input')
    validate(current, approved['args'])
    result = current.call(approved['args'])
    if output is not None:
        output.update(result)
    status = 'succeeded' if result.get('status') in ('done', 'succeeded') else 'unknown'
    return actions.ActionResult(status, json.dumps(result, ensure_ascii=False, default=str)[:3000])
