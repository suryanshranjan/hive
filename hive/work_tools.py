"""Scoped adapters for configured data sources, owner memory and sandboxed builds."""
import hashlib
import json
import time

from . import access, actions, buildplans, memory, payments, policy, store, tasks, tools
from .runtime_tools import STRING, Tool, schema


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def submit(repo, args):
    from . import dispatcher
    step = tasks.ACTIVE_STEP.get()
    aid = actions.EXECUTING.get()
    if not step or not aid:
        raise tools.Refused('A child build requires an approved parent step.')
    with store.transaction() as con:
        tasks.boundary(step[0])
        parent = con.execute('SELECT * FROM tasks WHERE id=? AND project=? AND owner_id=? AND chat_id=?',
                             (step[0], tasks._project(repo), policy.context().owner, policy.context().chat)).fetchone()
        if not parent or parent['active_step'] != step[1]:
            raise tools.Refused('The parent no longer owns this build step.')
        item = {'title': args['goal'], 'why': '', 'build': args['goal'], 'decide': '', 'seen': ''}
        ch = _ScopedChat(parent['chat_id'])
        tid = buildplans.save(ch, repo, {'steps': [item], 'goal': args['goal']})
        con.execute('INSERT INTO child_builds VALUES(?,?,?,?)', (*step, tid, aid))
        dispatcher.enqueue(tasks.get(tid, ch, repo), policy.context())
    return {'status':'done', 'data':{'child':tid}}


class _ScopedChat:
    def __init__(self, chat):
        self.chat = chat


def child_result(repo, tid, detail):
    from . import build_receipts
    task = tasks.get(tid, _ScopedChat(policy.context().chat), repo)
    if not task or task['mode'] != 'build':
        raise tools.Refused('That build is unavailable in this project.')
    data = {'id':tid, 'state':task['state'], 'detail':task['detail']}
    if detail:
        receipt = build_receipts.validate(tid, len(task['steps']), repo) if task['state'] == 'succeeded' else None
        if not receipt:
            return {'status':'needs_input','data':'A checked build result is unavailable.'}
        data['receipt'] = receipt
    return {'status':'done','data':data}


def edit_memory(repo, verb, args):
    project = memory.project_key(repo)
    with store.transaction() as con:
        if verb == 'add':
            fid = memory.add_note(repo, args['text'], source='owner')
        else:
            fid = args['id']
            row = con.execute('SELECT * FROM facts WHERE id=? AND project=? AND owner_id=? AND deleted_at IS NULL '
                              'AND superseded_by IS NULL AND text=?', (fid, project, policy.context().owner,
                              args['expected_text'])).fetchone()
            if not row:
                raise tools.Refused('The fact changed or belongs to another project.')
            if verb == 'forget':
                store.forget(fid)
            else:
                replacement = store.add_fact(args['text'], row['kind'], project, source='owner',
                                             owner=row['owner_id'], due_at=row['due_at'])
                if row['person_id']:
                    con.execute('UPDATE facts SET person_id=? WHERE id=?', (row['person_id'], replacement))
                store.supersede(fid, replacement)
                fid = replacement
            memory._export(repo)
    return {'status':'done','data':{'id':fid}}


def catalog(repo):
    sources = [s for s in access.load(repo) if s['kind'] in ('file','db','url')]
    out = []
    for name, kinds, desc in (
            ('business_query', {'db'}, 'Read a configured database with one read-only query.'),
            ('document_get', {'file','url'}, 'Read the document registered under this exact source name.')):
        by_name = {s['name']: s for s in sources if s['kind'] in kinds}
        if not by_name:
            continue
        props = {'source': {'type':'string','enum':sorted(by_name)}}
        if name == 'business_query':
            props['query'] = STRING
        def read(args, entries=by_name):
            source = entries[args['source']]
            data = access.run_sql(source['where'], args['query']) if source['kind'] == 'db' else access.read(source)
            return {'status':'done','data':data[:10000]}
        out.append(Tool(name, desc, schema(props, props), tools.READ, True, read, digest(by_name)))
    payment_accounts = payments.load(repo)
    if payment_accounts:
        def summary(args):
            until = time.time()
            rows = payments.fetch(repo, until - args['days'] * 86400, until)
            return {'status':'done', 'data':{'rows':len(rows), 'totals':payments.totals(rows), 'per_provider_cap':2000}}
        out.append(Tool('payment_summary', 'Summarize payments in the last N days by currency.',
                        schema({'days':{'type':'integer','minimum':1,'maximum':366}}, ['days']),
                        tools.READ, True, summary, digest(payment_accounts)))
    integer = {'type':'integer','minimum':1}
    for verb in ('add','update','forget'):
        props = {} if verb == 'add' else {'id':integer,'expected_text':STRING}
        if verb != 'forget':
            props['text'] = STRING
        out.append(Tool('memory_' + verb, verb.capitalize() + ' a project fact after exact owner approval.',
                        schema(props, props), tools.EXTERNAL, False, lambda a, v=verb: edit_memory(repo,v,a)))
    out.append(Tool('build_submit', 'Submit an approved build in the project sandbox and wait for its checked result.',
                    schema({'goal':STRING}, ['goal']), tools.EXTERNAL, False, lambda a: submit(repo,a)))
    for name in ('build_status','build_result'):
        out.append(Tool(name, 'Read a saved build by task ID.',
                        schema({'id':{'type':'string','pattern':'^[0-9a-f]{12}$'}}, ['id']),
                        tools.READ, True, lambda a, details=name=='build_result': child_result(repo,a['id'],details)))
    return out
