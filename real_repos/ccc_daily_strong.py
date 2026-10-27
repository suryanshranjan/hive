import pickle, datetime as dt, collections, statistics as st, math, random
exec(open('ccc_cost4.py').read().split('rows=[];sim=[]')[0])
day=lambda t: dt.datetime.fromtimestamp(t,dt.timezone.utc).strftime('%m-%d')
by=collections.defaultdict(lambda:[0,0,0]); durs=[]
for a in T:
    D=a['t1']-a['t0']
    if 60<D<=6*3600: durs.append(D/60)
    for b in T:
        if b is not a and a['t0']<b['t1']<a['t1']:
            v=by[day(a['t1'])]; v[0]+=1; v[1]+=strong(a,b); v[2]+=bool(a['Ff']&b['Ff'])
print('task minutes: median %.1f mean %.1f'%(st.median(durs),st.mean(durs)))
print('day    pairs  kappa_line  kappa_file')
for d,(n,s_,f_) in sorted(by.items()):
    if n>=100: print(f'{d}  {n:5d}   {s_/n:.3f}      {f_/n:.3f}')
# split halves: first 7 days vs rest
first=[v for d,v in by.items() if d<='01-29']; last=[v for d,v in by.items() if d>'01-29']
for lab,g in (('01-23..01-29',first),('01-30..02-05',last)):
    n=sum(v[0] for v in g); s_=sum(v[1] for v in g); print(lab,'kappa_line %.3f (n=%d)'%(s_/n,n))
