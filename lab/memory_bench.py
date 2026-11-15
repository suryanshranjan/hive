"""Gate 118: the memory bench (memory 2.0 against Hive's memory before it). A mock business, "Dabba Days" (a tiffin
service; mock names only), over eight simulated weeks.

  python lab/memory_bench.py retrieval   R1 and R2: no model, deterministic, free
  python lab/memory_bench.py live        R3: the owner's own messages through the real model (about $1-2)

R1  30 facts he told Hive, spread over 8 weeks among 90 ordinary notes. For each fact, a question he would ask that
    shares a word or two with it. Hit: the answer's keyword is in what the reply is given. Arms: "last15" (Hive before
    memory 2.0: his 15 newest notes, whatever he asks) and "recall" (memory 2.0).
R2  6 questions that share no word with their fact ("who brings our lentils?" for the dal supplier). Keyword search
    has nothing to find; this measures that limit honestly.
R3  live: 16 messages in his words go through the real REMEMBER and REPLACES calls. 8 are later changes of mind ("we
    moved to Gupta Foods for dal"); 8 are controls on the same topics that change nothing. Scored: the change's new
    value is recalled and the old one is not; controls are never replaced; facts about a named person are linked to
    that person.
Writes gates/gate118/results_<part>.json."""
import json, os, random, subprocess, sys, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = 118
DAY = 86400

FACTS = [   # (what he told Hive, a question he would ask later, the keyword the answer needs)
    ('Our dal supplier is Sharma Traders in Indore.', 'who is our dal supplier?', 'Sharma'),
    ('Rice comes from Annapurna Mills, delivered every Thursday.', 'when does the rice delivery come?', 'Thursday'),
    ('Asha Mehta of Mehta Caterers orders 40 tiffins every Monday.', 'how many tiffins does Asha order?', '40'),
    ('Ravi Kumar is our delivery lead; he manages the six riders.', 'who manages the riders?', 'Ravi'),
    ('The monthly plan costs Rs 2,400 for lunch only.', 'what does the monthly lunch plan cost?', '2,400'),
    ('The weekly trial plan is Rs 699.', 'how much is the trial plan?', '699'),
    ('The FSSAI licence renewal is due on 30 November.', 'when is the licence renewal due?', '30 November'),
    ('GST is filed by our accountant, Neha Joshi.', 'who files our GST?', 'Neha'),
    ('Our kitchen is in Andheri East, near the metro station.', 'where is our kitchen?', 'Andheri'),
    ('Customers can pause their plan for up to 7 days a month.', 'how long can customers pause their plan?', '7 days'),
    ('He prefers updates in the morning, before 10 am.', 'when does he like his updates?', 'morning'),
    ('Investor Priya Shah expects the monthly report by the 5th.', 'when is the investor report due?', '5th'),
    ('The cook, Lakshmi, is on leave every second Saturday.', 'when is Lakshmi on leave?', 'second Saturday'),
    ('Our biggest corporate client is Kestrel Logistics, 120 meals a day.', 'how many meals does Kestrel take?', '120'),
    ('Packaging is from GreenBox, compostable boxes at Rs 6 each.', 'what do our boxes cost?', 'Rs 6'),
    ('The Diwali menu launches on 1 November.', 'when does the Diwali menu launch?', '1 November'),
    ('Refunds go back as wallet credit, not cash.', 'how do refunds work?', 'wallet credit'),
    ('Delivery stops at 1:30 pm; later orders move to the next day.', 'what is the delivery cut-off?', '1:30'),
    ('The Powai expansion needs a second kitchen by March.', 'what does the Powai expansion need?', 'second kitchen'),
    ('Instagram ads get the most sign-ups, about 60 a week.', 'which ads bring the most sign-ups?', 'Instagram'),
    ('Our cofounder Arjun handles all hiring.', 'who handles hiring?', 'Arjun'),
    ('The gas cylinder contract is with Bharat Gas, renewed yearly in June.', 'when is the gas contract renewed?', 'June'),
    ('Jain meals are made in a separate area, without onion or garlic.', 'how are Jain meals made?', 'onion'),
    ('The rent for the kitchen is Rs 85,000 a month.', 'what is the kitchen rent?', '85,000'),
    ('Our app is built by Ankit, a freelancer, paid per feature.', 'who builds our app?', 'Ankit'),
    ('Complaints must be answered within 2 hours.', 'how fast must complaints be answered?', '2 hours'),
    ('The salad add-on sells best on Wednesdays.', 'which day does the salad add-on sell best?', 'Wednesday'),
    ('Our bank is HDFC, account in the Andheri branch.', 'which bank do we use?', 'HDFC'),
    ('Riders are paid Rs 35 per delivery plus fuel.', 'how much are riders paid per delivery?', '35'),
    ('The annual food safety audit is in January.', 'when is the food safety audit?', 'January'),
]
PARAPHRASE = [   # (index into FACTS, a question that shares no word with the fact, the keyword)
    (0, 'who brings our lentils?', 'Sharma'),
    (8, 'which part of Mumbai do we cook from?', 'Andheri'),
    (15, 'when do the festival dishes start?', '1 November'),
    (20, 'who recruits new staff?', 'Arjun'),
    (24, 'which developer works on our software?', 'Ankit'),
    (28, 'what does each bike trip earn a rider?', '35'),
]
FILLER = ['Sign-ups were steady this week, about {n} new.', 'The team shipped small fixes to the menu page.',
          'Two riders were late on {d}; it was the rain.', 'We tried a new paneer recipe; feedback was mixed.',
          'Weekly sales were Rs {n},000.', 'A customer asked for brown rice; we noted it.',
          'Instagram posted {n} stories this week.', 'The kitchen was deep-cleaned on {d}.']

LIVE = [   # (his message, the change of mind that comes later or None, a question, kw before, kw after)
    ('we buy our dal from Sharma Traders in Indore', 'we moved to Gupta Foods for dal, Sharma kept delaying',
     'who is our dal supplier?', 'Sharma', 'Gupta'),
    ('the monthly lunch plan is 2400 rupees', 'from this month the monthly lunch plan is 2600',
     'what does the monthly lunch plan cost?', '2400', '2600'),
    ('Ravi Kumar leads delivery, he handles all six riders', 'Ravi left; Sameer is our new delivery lead',
     'who leads delivery?', 'Ravi', 'Sameer'),
    ('the licence renewal is due on 30 November', 'they extended it, licence renewal is now due 15 December',
     'when is the licence renewal due?', '30 November', '15 December'),
    ('delivery cut-off is 1:30 pm', 'we pushed the delivery cut-off to 2 pm',
     'what is the delivery cut-off?', '1:30', '2 pm'),
    ('Asha Mehta from Mehta Caterers takes 40 tiffins every Monday', 'Asha cut her order to 25 tiffins a week',
     'how many tiffins does Asha take?', '40', '25'),
    ('our app is built by Ankit, a freelancer', 'we stopped working with Ankit; Studio Nine builds the app now',
     'who builds our app?', 'Ankit', 'Studio Nine'),
    ('refunds go back as wallet credit, never cash', 'customers can now choose cash refunds instead of wallet credit',
     'how do refunds work?', 'wallet credit', 'cash'),
    # controls: same topics, nothing they replace
    ('rice comes from Annapurna Mills every Thursday', None, 'when does the rice come?', 'Thursday', None),
    ('the weekly trial plan is 699 rupees', None, 'how much is the trial plan?', '699', None),
    ('Lakshmi the cook is off every second Saturday', None, 'when is Lakshmi off?', 'second Saturday', None),
    ('the Diwali menu launches on 1 November', None, 'when does the Diwali menu launch?', '1 November', None),
    ('Kestrel Logistics takes 120 meals a day, our biggest client', None, 'how many meals does Kestrel take?', '120', None),
    ('complaints must be answered within 2 hours', None, 'how fast are complaints answered?', '2 hours', None),
    ('Neha Joshi our accountant files the GST', None, 'who files our GST?', 'Neha', None),
    ('the kitchen rent is 85000 a month', None, 'what is the kitchen rent?', '85000', None),
]
CONTROLS_AFTER = [   # said after the originals, on the same topics, changing nothing: must not replace anything
    'we also buy chana from Gupta Foods', 'the quarterly lunch plan is 6900 rupees', 'Sameer helps Ravi on busy days',
    'the trade licence is separate and renewed in April', 'Saturday delivery cut-off is the same as weekdays',
    'Mehta Caterers also asked about a dinner menu', 'Studio Nine pitched us a new website', 'wallet credit never expires',
]

# ---- Gate 119 (written before it ran): new paraphrases, and changes of mind about how the business works

HELDOUT = [   # (index into FACTS, a question sharing no content word with the fact, the keyword)
    (1, 'which day do the grains arrive?', 'Thursday'),
    (2, 'how big is the Mehta order?', '40'),
    (4, 'what is the price for a month of lunches?', '2,400'),
    (7, 'who handles our tax returns?', 'Neha'),
    (9, 'can a subscriber take a break, and for how long?', '7 days'),
    (11, 'when must the numbers reach our backer?', '5th'),
    (14, 'who makes our containers and at what price?', 'GreenBox'),
    (17, 'until what time do we take same-day orders?', '1:30'),
    (19, 'which channel gets us the most new customers?', 'Instagram'),
    (22, 'how do we cook for customers who avoid onion?', 'separate'),
    (25, 'how quickly do we reply to an unhappy customer?', '2 hours'),
    (29, 'when do the hygiene inspectors come?', 'January'),
]

LIVE2 = [   # (first message, change of mind or None, question, before, after); 4 changes are about how the business works
    ('we buy oil from Fortune Traders in Vashi', 'we switched our oil supplier to Gemini Edible Oils',
     'who supplies our oil?', 'Fortune', 'Gemini'),
    ('a customer can cancel until 9 am for the same day', 'cancellations now close at 7 am, not 9',
     'until when can a customer cancel?', '9 am', '7 am'),
    ('late deliveries get a free dessert', 'no more free dessert for late deliveries, we give 10% off the next order',
     'what do customers get for a late delivery?', 'dessert', '10%'),
    ('the minimum corporate order is 20 meals', 'we lowered the corporate minimum to 12 meals',
     'what is the minimum corporate order?', '20', '12'),
    ('Pooja runs our Instagram', 'Pooja moved to sales, Irfan runs Instagram now',
     'who runs our Instagram?', 'Pooja', 'Irfan'),
    ('referrals give both people one free meal', 'referrals now give Rs 100 wallet credit each instead of a free meal',
     'what does a referral give?', 'free meal', '100'),
    # controls: the same kind of facts, never changed
    ('the kitchen opens at 6 am', None, 'when does the kitchen open?', '6 am', None),
    ('weekend orders need 2 days notice', None, 'how much notice do weekend orders need?', '2 days', None),
    ('Farhan does our accounts audit every quarter', None, 'who audits our accounts?', 'Farhan', None),
    ('the festive box costs Rs 899', None, 'what does the festive box cost?', '899', None),
]
CONTROLS2_AFTER = ['we also buy ghee from Gemini Edible Oils', 'weekday cancellations for dinner close at 4 pm',
                   'Irfan also helps with packing on Sundays', 'the kitchen closes at 10 pm']

def heldout():
    """Gate 119 H: the held-out paraphrases, with words only and with meaning."""
    out = {}
    for arm, env in (('words', '0'), ('meaning', '')):
        os.environ['HIVE_EMBED'] = env
        home, repo = setup()
        from hive import memory, recall
        for f in FACTS:
            memory.add_note(repo, f[0])
        for i in range(60):
            memory.add_note(repo, f'Ordinary note {i}: the week went as usual.')
        hits = [kw.lower() in recall.render(recall.recall(repo, q)).lower() for _, q, kw in HELDOUT]
        out[arm] = {'hits': sum(hits), 'of': len(hits), 'missed': [HELDOUT[i][1] for i, h in enumerate(hits) if not h]}
        r1 = [kw.lower() in recall.render(recall.recall(repo, q)).lower() for _, q, kw in FACTS]
        out[arm]['R1'] = sum(r1)
    os.environ.pop('HIVE_EMBED', None)
    t0 = time.time()
    for _, q, _ in HELDOUT:
        recall.recall(repo, q)
    out['ms_per_recall'] = round(1000 * (time.time() - t0) / len(HELDOUT))
    return out

def live2():
    """Gate 119 L: the new changes of mind through the real model, scored from the store (is the old fact replaced?)."""
    home, repo = setup()
    from hive import assistant, explain, memory, recall, store, telegram
    sys.path.insert(0, os.path.join(ROOT, 'tests'))
    from test_telegram_fake import FakeTelegram, ME
    ch = lambda: telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=FakeTelegram([]))
    P = memory.project_key(repo)
    ids = lambda: {f['id'] for f in store.live_facts(P)}
    def say(text):
        before = ids(); assistant.remember(ch(), repo, text).join(180); return ids() - before
    spent0 = explain.SPENT[0]
    first = [say(m) for m, _, _, _, _ in LIVE2]
    for c in CONTROLS2_AFTER:
        say(c)
    later = [say(c) if c else set() for _, c, _, _, _ in LIVE2]
    live_now = ids(); rows = []
    for (m, change, q, before, after), f_ids, c_ids in zip(LIVE2, first, later):
        ctx = recall.render(recall.recall(repo, q)).lower()
        rows.append({'q': q, 'change': bool(change), 'first_kept': bool(f_ids),
                     'change_kept': bool(c_ids) if change else None,
                     'old_replaced': (bool(f_ids) and not (f_ids & live_now)) if change else None,
                     'control_live': (bool(f_ids) and f_ids <= live_now) if not change else None,
                     'answer_in_reply': (after or before).lower() in ctx})
    chg = [r for r in rows if r['change']]; co = [r for r in rows if not r['change']]
    return {'first_kept': sum(r['first_kept'] for r in rows), 'of': len(rows),
            'changes_kept': sum(r['change_kept'] for r in chg), 'old_replaced': sum(r['old_replaced'] for r in chg),
            'changes': len(chg), 'controls_live': sum(r['control_live'] for r in co), 'controls': len(co),
            'answer_in_reply': sum(r['answer_in_reply'] for r in rows),
            'rows': rows, 'live_facts': [f['text'] for f in store.live_facts(P)],
            'spent_usd': round(explain.SPENT[0] - spent0, 4)}

def setup():
    home = tempfile.mkdtemp(prefix='gate118_')
    # HOME stays his: the real model (Claude Code) logs in from it. Everything Hive writes goes to the temp folder.
    # (First live attempt: HOME pointed here too, Claude Code found no login, and every call failed: 0 kept, $0.)
    sys.path.insert(0, ROOT)
    from hive import embed, memory, numbers, register
    if embed.available():
        embed.wait()   # the bench measures recall with the model loaded, as after Hive has been up a minute
    memory.DIR = os.path.join(home, '.hive', 'rules')
    numbers.DIR = os.path.join(home, '.hive', 'numbers'); register.PATH = os.path.join(home, '.hive', 'profile.json')
    repo = os.path.join(home, 'dabba'); subprocess.run(['git', 'init', '-q', '-b', 'main', repo])
    subprocess.run(['git', '-C', repo, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'i'])
    return home, repo

def contexts(repo, question):
    """What a reply is given, by each arm."""
    from hive import memory, recall
    return {'last15': '\n'.join(memory.notes(repo)[-15:]),
            'recall': recall.render(recall.recall(repo, question))}

def retrieval():
    home, repo = setup()
    from hive import memory, store
    rnd = random.Random(SEED)
    start = time.time() - 56 * DAY
    items = [('fact', i, f[0]) for i, f in enumerate(FACTS)] + \
            [('filler', i, rnd.choice(FILLER).format(n=rnd.randint(10, 99), d=rnd.choice(['Monday', 'Friday'])) +
              f' (week {i // 12 + 1}, note {i})') for i in range(90)]
    rnd.shuffle(items)
    for k, (_, _, text) in enumerate(items):   # spread over eight weeks, oldest first
        when = start + k * (56 * DAY / len(items))
        memory.add_note(repo, text)
        f = store.find_fact(text, 'note', memory.project_key(repo))
        store.connect().execute('UPDATE facts SET created=? WHERE id=?', (when, f['id']))
    out = {'R1': {}, 'R2': {}, 'context_facts': []}
    for arm in ('last15', 'recall'):
        hits = []
        for text, q, kw in FACTS:
            hits.append(kw.lower() in contexts(repo, q)[arm].lower())
        out['R1'][arm] = {'hits': sum(hits), 'of': len(hits), 'missed': [FACTS[i][1] for i, h in enumerate(hits) if not h]}
        hits = [kw.lower() in contexts(repo, q)[arm].lower() for _, q, kw in PARAPHRASE]
        out['R2'][arm] = {'hits': sum(hits), 'of': len(hits)}
    from hive import recall
    out['context_facts'] = max(len(recall.recall(repo, q)) for _, q, _ in FACTS)
    return out

def live():
    home, repo = setup()
    from hive import assistant, explain, memory, recall, store, telegram
    sys.path.insert(0, os.path.join(ROOT, 'tests'))
    from test_telegram_fake import FakeTelegram, ME
    ch = lambda: telegram.Channel({'chat_id': ME, 'token': 'x', 'address': 'sir'}, api=FakeTelegram([]))
    spent0 = explain.SPENT[0] if isinstance(explain.SPENT, list) else 0
    def say(text):
        assistant.remember(ch(), repo, text).join(180)
    for msg, _, _, _, _ in LIVE:
        say(msg)
    kept_before = len(store.live_facts(memory.project_key(repo)))
    for c in CONTROLS_AFTER:
        say(c)
    for _, change, _, _, _ in LIVE:
        if change:
            say(change)
    rows = []
    for msg, change, q, before, after in LIVE:
        ctx = recall.render(recall.recall(repo, q)).lower()
        rows.append({'q': q, 'change': bool(change), 'new_in': (after or before).lower() in ctx,
                     'old_out': (before.lower() not in ctx) if change else None})
    changes = [r for r in rows if r['change']]; controls = [r for r in rows if not r['change']]
    asha = store.person('Asha Mehta') or store.person('Asha')
    live_texts = [f['text'] for f in store.live_facts(memory.project_key(repo))]
    return {'kept_lasting': kept_before, 'of': len(LIVE),
            'changes_new_recalled': sum(r['new_in'] for r in changes), 'changes_old_gone': sum(r['old_out'] for r in changes),
            'changes': len(changes), 'controls_still_recalled': sum(r['new_in'] for r in controls), 'controls': len(controls),
            'asha_linked': bool(asha and store.facts_about(asha['id'])),
            'facts_replaced': store.connect().execute('SELECT COUNT(*) FROM facts WHERE superseded_by IS NOT NULL').fetchone()[0],
            'spent_by': {k: round(v, 4) for k, v in explain.SPENT_BY.items()},
            'rows': rows, 'live_facts': live_texts,
            'spent_usd': round((explain.SPENT[0] if isinstance(explain.SPENT, list) else 0) - spent0, 4)}

if __name__ == '__main__':
    part = (sys.argv[1:] or ['retrieval'])[0]
    got = {'retrieval': retrieval, 'live': live, 'heldout': heldout, 'live2': live2}[part]()
    gate = 'gate119' if part in ('heldout', 'live2') else 'gate118'
    os.makedirs(os.path.join(ROOT, 'gates', gate), exist_ok=True)
    json.dump(got, open(os.path.join(ROOT, 'gates', gate, f'results_{part}.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in got.items() if k not in ('rows', 'live_facts')}, indent=1))
