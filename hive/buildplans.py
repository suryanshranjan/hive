"""Durable execution of approved business-goal build plans."""
from . import memory, policy, store, tasks, telegram


def save(ch, repo, plan, approved=True):
    answers = plan.get('answers') or [''] * len(plan['steps'])
    steps = [{'tool': 'build_step', 'args': {'step': step, 'answer': answers[n]}}
             for n, step in enumerate(plan['steps'])]
    task = tasks.create(ch, repo, steps, plan['goal'], mode='build',
                        metadata={'approved': approved, 'build_state': None})
    return task['id']


def restore(ch, repo):
    from . import assistant
    assistant.PLAN.clear()
    rows = store.connect().execute("SELECT id FROM tasks WHERE owner_id=? AND chat_id=? AND project=? "
                                   "AND mode='build' AND state NOT IN ('succeeded','cancelled') ORDER BY created DESC LIMIT 1",
                                   tasks._scope(ch, repo)).fetchall()
    if not rows:
        return
    task = tasks.get(rows[0][0], ch, repo)
    assistant.PLAN.update(task_id=task['id'], goal=task['instruction'],
                          steps=[s['args']['step'] for s in task['steps']],
                          answers=[s['args']['answer'] for s in task['steps']],
                          step=task['next_step'], running=False)


def resume(ch, repo, tid, apply_build=None, wait=None, poll=20):
    from . import assistant, build_receipts, plan, screens, start, verification
    task = tasks.get(tid, ch, repo)
    if not task or task['mode'] != 'build':
        ch.send('That build plan is unavailable.'); return 'failed'
    if task['state'] == 'blocked':
        n = task['next_step']
        receipt = build_receipts.validate(tid, n, repo)
        if receipt and not task['control']:
            import json
            from pathlib import Path
            with store.transaction() as con:
                task = tasks.get(tid, ch, repo)
                if task['state'] == 'blocked' and task['next_step'] == n and not task['control']:
                    task['metadata']['build_state'] = json.loads(Path(receipt['state_path']).read_text('utf-8'))
                    task['results'][str(n)] = {'status':'done','recovered':True,'commit':receipt['commit']}
                    state = 'succeeded' if n == len(task['steps']) else 'paused'
                    con.execute('UPDATE tasks SET results=?,next_step=?,state=?,metadata=?,detail=? WHERE id=?',
                                (tasks._json(task['results']), n+1, state, tasks._json(task['metadata']),
                                 'Recovered checked build ' + receipt['commit'], tid))
                    verification.record(tid, n, 'build_receipt', receipt['commit'])
            task = tasks.get(tid, ch, repo)
    if task['next_step'] > 1 and task['state'] in ('queued','paused') and task['criteria']:
        if not build_receipts.validate(tid, task['next_step']-1, repo):
            tasks.update(tid, state='blocked', detail='The previous build branch or its checked artifacts changed.')
            ch.send(tasks.describe(tasks.get(tid,ch,repo))); return 'blocked'
    if not task['metadata']['approved']:
        ch.send('Build this plan?\n' + '\n'.join(s['args']['step']['title'] for s in task['steps']),
                buttons=[[('Build it', 'bpln|yes'), ('Not now', 'bpln|no')]])
        kind, value = telegram._wait(ch, poll, {'bpln|yes', 'bpln|no'})
        if kind != 'tap' or value != 'bpln|yes':
            return 'plan_held'
        for step in task['steps']:
            item = step['args']['step']
            if item.get('decide') and not step['args']['answer']:
                ch.send(item['decide'])
                kind, answer = telegram._wait(ch, poll, set())
                if kind != 'text' or not answer:
                    return 'plan_held'
                step['args']['answer'] = answer
                memory.add(repo, item['decide'] + ' ' + answer, 'plan')
                store.connect().execute('UPDATE tasks SET steps=? WHERE id=?', (tasks._json(task['steps']), tid))
        task['metadata']['approved'] = True
        with store.transaction() as con:
            con.execute('UPDATE tasks SET steps=?,metadata=? WHERE id=?',
                        (tasks._json(task['steps']), tasks._json(task['metadata']), tid))
    task = tasks.claim(tid, ch, repo, resume=True)
    if not task:
        saved = tasks.get(tid, ch, repo)
        ch.send(tasks.describe(saved)); return 'done' if saved['state'] == 'succeeded' else 'blocked'
    apply_build = apply_build or start.apply_ruling
    assistant.PLAN.update(task_id=tid, goal=task['instruction'], steps=[s['args']['step'] for s in task['steps']],
                          step=task['next_step'], running=True)
    see = screens.available() and screens.is_frontend(repo)
    meta = task['metadata']
    try:
        for n in range(task['next_step'], len(task['steps']) + 1):
            if assistant.PLAN.pop('cancel', False):
                tasks.update(tid, state='cancelled', detail='Cancelled by the owner.'); return 'cancelled'
            assistant.PLAN['step'] = n
            item = task['steps'][n - 1]['args']
            instruction = plan.instruction(item['step'], item['answer'])
            tasks.begin_step(tid, n)
            with tasks.executing(tid, n):
                if n == 1:
                    proc = assistant.background_build(repo, instruction, ch, interview=False, report=False, workers=1)
                    ok = (wait or proc.wait)() == 0
                    state = assistant.latest_build(repo) if ok else None
                    ok = ok and bool(state) and state.get('plan_task') == tid
                    if ok:
                        meta['build_state'] = state
                else:
                    state = meta.get('build_state')
                    if not state or tasks._project(state.get('repo', '')) != tasks._project(repo):
                        raise RuntimeError('The saved build state is missing or belongs to another project')
                    ch.send(f"🛠 Step {n} of {len(task['steps'])}: {item['step']['title']}. On it.")
                    ok = apply_build(state, instruction, None) in (0, None)
                receipt = build_receipts.validate(tid, n, repo) if ok and task['criteria'] else None
                if task['criteria']:
                    ok = ok and bool(receipt)
                with store.transaction():
                    if receipt:
                        verification.record(tid, n, 'build_receipt', receipt['commit'])
                    tasks.update(tid, metadata=meta)
                    tasks.finish_step(tid, n, {'status': 'done' if ok else 'failed'})
            if not ok:
                ch.send(f"Step {n} didn't pass its checks. Everything before it is built and safe. Task {tid} is saved.")
                return 'failed'
            head = f"✅ Step {n} of {len(task['steps'])} done: {item['step']['title']}."
            if see:
                assistant.show(ch, repo, intro=head)
            else:
                ch.send(head + ' ' + assistant.what_changed(repo, ch))
        ch.send(f"🎉 That's the plan done, sir. {(meta.get('build_state') or {}).get('check', '')}\nSay ship it for a pull request.")
        return 'done'
    except Exception:
        # A build may have changed a branch before failing; never silently restart it.
        current = tasks.get(tid, ch, repo)
        if current['active_step']:
            tasks.finish_step(tid, current['active_step'], {'status': 'unknown', 'why': 'Build interrupted; inspect the saved branch.'})
        raise
    finally:
        assistant.PLAN['running'] = False
