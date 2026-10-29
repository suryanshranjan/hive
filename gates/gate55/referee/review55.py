#!/usr/bin/env python3
"""Gate 55 steps: one code sheet, three reviews.

usage: review55.py pre   <run dir> <oracle.py>              the owner's policy in prose (R, the documenter), ask texts for N0
       review55.py after <run dir> <oracle.py> <N0's repo>  describer on N0's code -> D; then three separate reviews of D:
         CC  a careful owner, the rule list in a terminal (interview.confirm_sheet, as Gates 42 and 44)
         CS  a skimming owner, the same rule list in a terminal
         CT  the same skimming owner on the phone: Hive's conversational review (confirm_sheet with a chat channel:
             sections by area, Jarvis saying how each part works, his replies read in his own words)
       Each owner holds the policy as R's prose rules (never the oracle) and cannot run anything. The judge labels D, CC,
       CS, CT and R for every declared decision before any stage-2 build exists."""
import contextlib, html, io, json, os, re, shutil, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'lab'))
sys.path.insert(0, os.path.join(ROOT, 'gates', 'gate41', 'referee'))
import intent
import wind_tunnel as wt
from hive import interview, telegram

P = os.path.join(ROOT, 'gates', 'gate55', 'prompts')
say = wt.say
OWNER = 'claude -p --output-format json'.split()   # no tools: he reads, he does not run anything
NO_RULES = "There is no product owner to ask on this project: `tools/ask.py` will tell you so. Work from the spec and the examples."
MAX_REPLIES = 90

def section(arm, rules):
    return f'\n## {arm}\n{wt.NO_OWNER}' + interview.instructions(rules).replace('\n## ', '\n### ')

def owner_reply(brief, screen, cwd, log):
    reply, c = wt.agent(OWNER, cwd, brief.replace('{SCREEN}', screen[-14000:]), os.path.join(cwd, 'owner.log'))
    return reply.strip(), c

def terminal_review(D, brief, priv, name):
    od = os.path.join(priv, f'review_{name}'); shutil.rmtree(od, ignore_errors=True); os.makedirs(od)
    term, log, cost = io.StringIO(), [], [0.0]
    def ask(prompt):
        term.write(prompt)
        reply, c = owner_reply(brief, term.getvalue(), od, log); cost[0] += c
        typed = '' if reply.strip('`').upper() in ('ENTER', '(ENTER)', '') or reply.lower().startswith("yes, that's right") else reply
        term.write(typed + '\n'); log.append(dict(prompt=prompt[-1500:], typed=typed))
        say(f'{name} owner #{len(log)}: {typed[:80]!r}')
        if len(log) > MAX_REPLIES: raise RuntimeError('too many replies')
        return typed
    with contextlib.redirect_stdout(term):
        C = interview.confirm_sheet(list(D), ask=ask, title='What the built code does now, as rules',
                                    note='Each one is what the product will do. Mark any that is not your policy.', missing=True)
    return C, dict(replies=len(log), cost=round(cost[0], 3), log=log, transcript=term.getvalue())

def chat_review(D, brief, priv, name, spec):
    """Hive's phone review, driven through a chat channel whose other end is the synthetic owner."""
    od = os.path.join(priv, f'review_{name}'); shutil.rmtree(od, ignore_errors=True); os.makedirs(od)
    chat, log, cost, uid = [], [], [0.0], [0]
    def api(method, **p):
        if method == 'sendMessage':
            text = html.unescape(re.sub(r'<[^>]+>', '', p['text']))
            buttons = p.get('reply_markup')
            labels = []
            try:
                kb = json.loads(buttons) if isinstance(buttons, str) else buttons
                labels = [b.get('text') for row in (kb or {}).get('inline_keyboard', []) for b in row]
            except Exception:
                pass
            chat.append('Hive: ' + text + (f"\n   [buttons: {' | '.join(labels)}]" if labels else ''))
            return {'message_id': len(chat)}
        if method == 'getUpdates':
            if p.get('timeout') == 0:
                return []
            reply, c = owner_reply(brief, '\n\n'.join(chat), od, log); cost[0] += c
            if not reply or reply.strip('`').upper() in ('ENTER', '(ENTER)'):
                reply = "Yes, that's right"
            chat.append('You: ' + reply); log.append(dict(seen=chat[-2][-1500:] if len(chat) > 1 else '', typed=reply))
            say(f'{name} owner #{len(log)}: {reply[:80]!r}')
            if len(log) > MAX_REPLIES: raise RuntimeError('too many replies')
            uid[0] += 1
            return [{'update_id': uid[0], 'message': {'message_id': 5000 + uid[0], 'chat': {'id': 111}, 'text': reply}}]
        if method == 'getChat':
            return {'first_name': 'Owner'}
        return True
    ch = telegram.Channel({'chat_id': 111, 'token': 'x', 'address': 'sir'}, api=api)
    goal = "Add these business functions to our SQL engine:\n" + spec
    C = interview.confirm_sheet(list(D), ch, None, 1, title='What the build does now, as rules',
                                note='Each one is what the product will do. Mark any that is not your policy.', missing=True,
                                goal=goal, save=os.path.join(od, 'progress.json'))
    return C, dict(replies=len(log), cost=round(cost[0], 3), log=log, transcript='\n\n'.join(chat))

def pre(run, oracle_path):
    name = os.path.basename(run); priv = os.path.join(ROOT, 'private', name)
    o = intent.load_oracle(oracle_path); spec = wt.spec_lines(o, intent.Gen(o).CATS)
    d = os.path.join(priv, 'documenter'); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    shutil.copy(oracle_path, os.path.join(d, 'oracle.py'))
    say("documenter writing the owner's policy in prose...")
    _, c = wt.agent(wt.AGENT, d, open(os.path.join(P, 'documenter_brief.md')).read().replace('{DIR}', d).replace('{SPEC}', spec),
                    os.path.join(d, 'documenter.log'))
    R = [r.strip() for r in json.load(open(os.path.join(d, 'rules.json'))) if isinstance(r, str) and r.strip()]
    assert R, 'documenter wrote no rules'
    open(os.path.join(run, 'ask_texts.md'), 'w').write("# Gate 55 ask texts (gates/gate55/referee/review55.py)\n\n## N0\n" + NO_RULES + '\n')
    json.dump(dict(R=R, cost_usd=dict(documenter=c)), open(os.path.join(run, 'pre.json'), 'w'), indent=1)
    say(f'R: {len(R)} rules; ask text for N0 written')

def after(run, oracle_path, base_repo):
    name = os.path.basename(run); priv = os.path.join(ROOT, 'private', name)
    o = intent.load_oracle(oracle_path); spec = wt.spec_lines(o, intent.Gen(o).CATS)
    pre_rec = json.load(open(os.path.join(run, 'pre.json'))); R = pre_rec['R']; cost = dict(pre_rec['cost_usd'])
    dd = os.path.join(priv, 'describer'); shutil.rmtree(dd, ignore_errors=True); os.makedirs(dd)
    repo = os.path.join(dd, 'repo'); shutil.copytree(base_repo, repo)
    say("describer writing what N0's code does, as rules...")
    _, cost['describer'] = wt.agent(wt.AGENT, dd, open(os.path.join(P, 'describer_brief.md')).read()
                                    .replace('{BASE}', repo).replace('{OUT}', dd).replace('{SPEC}', spec), os.path.join(dd, 'describer.log'))
    D = [r.strip() for r in json.load(open(os.path.join(dd, 'rules.json'))) if isinstance(r, str) and r.strip()]
    assert D, 'describer wrote no rules'
    say(f'D: {len(D)} rules from the code')
    policy = '\n'.join(f'- {r}' for r in R)
    careful = open(os.path.join(P, 'owner_careful.md')).read().replace('{POLICY}', policy)
    skim = open(os.path.join(P, 'owner_skim.md')).read().replace('{POLICY}', policy)
    out = {}
    for arm, fn in (('CC', lambda: terminal_review(D, careful, priv, 'CC')), ('CS', lambda: terminal_review(D, skim, priv, 'CS')),
                    ('CT', lambda: chat_review(D, skim, priv, 'CT', spec))):
        t0 = time.time()
        try:
            C, rec = fn()
        except Exception as e:   # a review that breaks is a finding; its sheet stays D
            import traceback; C, rec = list(D), dict(replies=None, cost=None, error=traceback.format_exc())
        rec['minutes'] = round((time.time() - t0) / 60, 1); rec['rules'] = C; out[arm] = rec
        say(f'{arm}: {len(C)} rules after review, {rec.get("replies")} replies, {rec["minutes"]} min')
        cost[f'owner_{arm}'] = rec.get('cost')
    jd = os.path.join(priv, 'judge'); shutil.rmtree(jd, ignore_errors=True); os.makedirs(jd)
    shutil.copy(oracle_path, os.path.join(jd, 'oracle.py'))
    json.dump(dict(D=D, CC=out['CC']['rules'], CS=out['CS']['rules'], CT=out['CT']['rules'], R=R),
              open(os.path.join(jd, 'sheets.json'), 'w'), indent=1)
    say('judge labelling every declared decision...')
    _, cost['judge'] = wt.agent(wt.AGENT, jd, open(os.path.join(P, 'judge_brief.md')).read().replace('{DIR}', jd),
                                os.path.join(jd, 'judge.log'))
    labels = json.load(open(os.path.join(jd, 'labels.json')))['labels']
    with open(os.path.join(run, 'ask_texts.md'), 'a') as f:
        f.write(''.join(section(a, out[a]['rules']) for a in ('CC', 'CS', 'CT')))
    json.dump(dict(R=R, D=D, reviews=out, cost_usd=cost, labels=labels), open(os.path.join(run, 'sheet.json'), 'w'), indent=1)
    say('ask texts for CC, CS and CT written')

if __name__ == '__main__':
    {'pre': lambda: pre(sys.argv[2], sys.argv[3]), 'after': lambda: after(sys.argv[2], sys.argv[3], sys.argv[4])}[sys.argv[1]]()
