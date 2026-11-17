"""The owner's standing rulings, kept across builds: every answer, reviewed decision and settled contradiction, so
builders follow them next time and the owner is never asked the same thing twice (an idea from OpenClaw's memory files).

  hive rules              list the rulings kept for this project
  hive rules forget <n>   drop ruling number n (for example after a policy change)

Rulings live in ~/.hive/hive.db. The rules/<project>.json files are derived compatibility exports.
A project is identified by its first commit, so every clone shares the same rulings."""
import json, os, subprocess, time

def _store(fn, *a, **k):
    """Also keep it in the structured store (hive/store.py), which never stops the JSON write that builds rely on."""
    try:
        from . import store
        return getattr(store, fn)(*a, **k)
    except Exception:
        return None

DIR = os.path.join(os.path.expanduser('~'), '.hive', 'rules')
PROMPT_LIMIT = 40   # the most recent rulings that go into a build's instructions

def project_key(repo):
    roots = subprocess.run(['git', '-C', repo, 'rev-list', '--max-parents=0', 'HEAD'], capture_output=True,
                           text=True).stdout.split()
    return (sorted(roots)[0][:12] if roots else os.path.basename(os.path.abspath(repo))) or 'project'

GENERIC = {'backend', 'frontend', 'app', 'server', 'api', 'web', 'client', 'project', 'src', 'main', 'repo', 'code'}

def _names():
    return os.path.join(os.path.dirname(DIR), 'names.json')

def project_name(repo):
    """What the owner calls this project: the startup's name (the founder: "name the project {startupname}", not the
    folder). Set with `hive name`; until then, a guess from package.json or the README's title; '' if neither helps."""
    p = _names()
    named = json.load(open(p)).get(project_key(repo)) if os.path.exists(p) else None
    if named:
        return named
    guesses = []
    try:
        guesses.append(json.load(open(os.path.join(repo, 'package.json'), encoding='utf-8')).get('name') or '')
    except (OSError, ValueError, AttributeError):
        pass
    for readme in ('README.md', 'readme.md', 'README'):
        try:
            first = open(os.path.join(repo, readme), encoding='utf-8', errors='replace').readline()
        except OSError:
            continue
        if first.startswith('# '):
            guesses.append(first[2:].strip())
        break
    for g in guesses:
        g = (g or '').strip().lstrip('@').split('/')[-1]
        if g and g.lower() not in GENERIC and len(g) <= 40:
            return g.replace('-', ' ').title() if g.islower() else g
    return ''

def set_name(repo, name):
    p = _names()
    names = json.load(open(p)) if os.path.exists(p) else {}
    names[project_key(repo)] = name.strip()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(names, open(p, 'w'), indent=1)

def _path(repo):
    return os.path.join(DIR, project_key(repo) + '.json')

def _notes_path(repo):
    return os.path.join(DIR, project_key(repo) + '.notes.json')

def notes(repo):
    """SQLite is authoritative; import each legacy file once."""
    from . import store
    store.sync(repo)
    return [f['text'] for f in store.live_facts(project_key(repo))
            if f['kind'] != 'rule' and f['trust'] == 'owner']


def _export(repo):
    """Compatibility files are derived snapshots, never a second write authority."""
    from . import store
    if store.after_commit(lambda: _export(repo)):
        return
    os.makedirs(DIR, exist_ok=True)
    for path, rows in ((_notes_path(repo), notes(repo)[-60:]), (_path(repo), load(repo))):
        tmp = path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(rows, f, indent=1, ensure_ascii=False)
        os.replace(tmp, path)
        os.chmod(path, 0o600)


def add_note(repo, text, kind='note', source='chat', person=None, valid_until=None, trust='owner', source_ref='', scope='project'):
    from . import store
    store.sync(repo)
    fid = store.add_fact(text, kind, '' if scope == 'personal' else project_key(repo), source=source, source_ref=source_ref,
                         person=person, valid_until=valid_until, trust=trust)
    _export(repo)
    return fid


def load(repo):
    from . import store
    store.sync(repo)
    return [dict(text=f['text'], kind=f['source'], when=time.strftime('%Y-%m-%d', time.localtime(f['created'])),
                 feature=json.loads(f['extra']).get('feature', ''))
            for f in store.live_facts(project_key(repo), kinds=('rule',)) if f['trust'] == 'owner']


def _save(repo, rulings):
    from . import store
    store.sync(repo)
    project = project_key(repo)
    with store.transaction():
        have = store.live_facts(project, kinds=('rule',))
        wanted = {store.norm(r['text']) for r in rulings}
        for f in have:
            if f['project'] == project and f['norm'] not in wanted:
                store.forget(f['id'])
        for r in rulings:
            old = store.find_fact(r['text'], 'rule', project)
            if not old or old['deleted_at'] is not None or old['superseded_by'] is not None:
                from . import policy
                store.add_fact(r['text'], 'rule', project, source=r.get('kind', 'owner'),
                               source_ref=policy.context().source_ref, extra=r)
    _export(repo)


def _first_part(text):
    return (text or '').split('\n\n')[0].strip()

def record(repo, run, goal=''):
    """Add what the owner decided in this run (answers, reviews, settled contradictions); returns how many were new."""
    d = os.path.join(run, 'owner')
    rulings = load(repo); known = {r['text'] for r in rulings}; new = []
    def add(text, kind):
        text = ' '.join(text.split())
        if text and text not in known:
            known.add(text)
            new.append({'text': text, 'kind': kind, 'when': time.strftime('%Y-%m-%d'), 'feature': goal[:80]})
    for f in sorted(os.listdir(os.path.join(d, 'answers'))) if os.path.isdir(os.path.join(d, 'answers')) else []:
        a = json.load(open(os.path.join(d, 'answers', f)))
        q = json.load(open(os.path.join(d, 'questions', f)))
        add(f"Asked: {q['question']} The owner answered: {a['answer']}", 'answer')
    for f in sorted(os.listdir(os.path.join(d, 'reviews'))) if os.path.isdir(os.path.join(d, 'reviews')) else []:
        r = json.load(open(os.path.join(d, 'reviews', f)))
        if r.get('auto'):
            continue   # left as built without being looked at: not a ruling
        what = _first_part(r.get('shown_as')) or json.load(open(os.path.join(d, 'assumptions', f))).get('text', '')
        add(f"{what} The owner decided: {r['correction']}" if not r['ok'] else f"{what} The owner confirmed this as right.",
            'review')
    res = os.path.join(d, 'resolutions.json')
    for c in (json.load(open(res)) if os.path.exists(res) else []):
        add(f"{c['question']} The owner decided: {c['chosen']} (this settled a contradiction)", 'resolution')
    if new:
        _save(repo, rulings + new)
    return len(new)

def instructions(repo):
    """The text that goes into a build's goal: the owner's standing rulings, most recent last."""
    rulings = load(repo)[-PROMPT_LIMIT:]
    if not rulings:
        return ''
    return ("\n\n## The owner's standing rulings from earlier builds\nThe owner has already decided these. Follow them "
            "wherever they apply, do not ask about them again, and do not record them as your own assumptions. Do not "
            "stretch one beyond the situation it describes.\n\n" + '\n'.join(f'- {r["text"]}' for r in rulings) + '\n')

def show(repo='.'):
    rulings = load(repo)
    if not rulings:
        print('No rulings kept for this project yet. They are saved after each build you review.'); return 0
    for n, r in enumerate(rulings, 1):
        print(f"{n}. [{r['when']}] {r['text']}")
    print(f'\n{len(rulings)} ruling(s); they live in {_path(repo)}.'); return 0

def forget(repo, n):
    rulings = load(repo)
    if not 1 <= n <= len(rulings):
        print(f'There is no ruling {n}.'); return 1
    gone = rulings.pop(n - 1); _save(repo, rulings)
    f = _store('find_fact', gone['text'], 'rule', project_key(repo))
    if f:
        _store('forget', f['id'])
    print(f'Forgotten: {gone["text"]}'); return 0

def add(repo, text, kind='owner'):
    """Keep one ruling the owner gave directly (for example on Telegram, outside a build)."""
    rulings = load(repo)
    text = ' '.join(text.split())
    if text and text not in {r['text'] for r in rulings}:
        rulings.append({'text': text, 'kind': kind, 'when': time.strftime('%Y-%m-%d'), 'feature': ''})
        _save(repo, rulings)
    return len(rulings)

def replace(repo, old_indexes, text):
    """The owner changed his mind: drop the rulings he overrode (0-based indexes) and keep the new one."""
    from . import policy, store
    before = load(repo)
    project = project_key(repo)
    with store.transaction():
        new_id = store.add_fact(text, 'rule', project, source='changed', source_ref=policy.context().source_ref)
        for index in old_indexes:
            if 0 <= index < len(before):
                old = store.find_fact(before[index]['text'], 'rule', project)
                if old and old['id'] != new_id:
                    store.supersede(old['id'], new_id)
        _export(repo)
    return len(load(repo))


def forget_note(repo, text):
    from . import store
    project = project_key(repo)
    for f in store.live_facts(project):
        if f['project'] == project and store.norm(f['text']) == store.norm(text):
            store.forget(f['id'])
    _export(repo)
