import pickle, collections, statistics as st, random, datetime as dt
C=pickle.load(open('ccc.pkl','rb')); T=pickle.load(open('ccc_tasks2.pkl','rb'))
# live src files over time
live=set(); live_at={}
for c in C:
    for p,f in c['files'].items():
        if not p.startswith('src/'): continue
        if f['add']: live.add(p)
        if f['del']: live.discard(p)
    live_at[c['ct']]=len(live)
times=sorted(live_at)
def nfiles(t):
    import bisect; i=bisect.bisect_right(times,t)-1; return live_at[times[max(i,0)]]
day=lambda t: dt.datetime.utcfromtimestamp(t).strftime('%m-%d')
byday=collections.defaultdict(list)
for t in T: byday[day(t['t1'])].append(t)
print('day    tasks files  kF_conc kFn_conc  m_eff(F) m_eff(Fn)  static_kF  pairs')
rows=[]
for d in sorted(byday):
    ts=byday[d]
    pairs=[(a,b) for a in ts for b in T if b is not a and a['t0']<b['t1']<a['t1']]
    if len(pairs)<30: continue
    kf=sum(1 for a,b in pairs if a['Ff']&b['Ff'])/len(pairs)
    kn=sum(1 for a,b in pairs if a['Fn']&b['Fn'])/len(pairs)
    # static: random pairs of tasks that day
    rp=[(random.choice(ts),random.choice(ts)) for _ in range(4000)]; rp=[(a,b) for a,b in rp if a is not b]
    ks=sum(1 for a,b in rp if a['Ff']&b['Ff'])/len(rp)
    nf=nfiles(max(t['t1'] for t in ts))
    rows.append((d,len(ts),nf,kf,kn,ks))
    print(f'{d}  {len(ts):5d} {nf:5d}   {kf:.3f}    {kn:.3f}     {1/kf:5.1f}    {1/kn:5.1f}     {ks:.3f}   {len(pairs)}')
pickle.dump(rows,open('ccc_daily.pkl','wb'))
