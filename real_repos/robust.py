import pickle, math, numpy as np, datetime as dt
exec(open('ccc_cost4.py').read().split('rows=[];sim=[]')[0])
def fit(filt):
    rows=[]
    for a in T:
        D=a['t1']-a['t0']
        if not filt(a,D): continue
        lands=sorted([b for b in T if b is not a and a['t0']<b['t1']<a['t1']],key=lambda x:x['t1'])
        ns=0; extra=0; last=a['t0']
        for b in lands:
            if strong(a,b): ns+=1; extra+=b['t1']-last; last=b['t1']
        rows.append((D/60,(D+extra)/60,len(lands),ns,math.log(len(a['Ff'])),math.log(len(a['A'])+len(a['R'])+1),dt.datetime.fromtimestamp(a['t1'],dt.timezone.utc).strftime('%m%d')))
    days=sorted({r[6] for r in rows})
    X=np.array([[1,r[2],r[3],r[4],r[5]]+[1.0 if r[6]==d else 0 for d in days[1:]] for r in rows]); X=X[:,X.any(axis=0)]
    out=[]
    for col in (0,1):
        y=np.array([r[col] for r in rows]); b=np.linalg.lstsq(X,y,rcond=None)[0]; out.append(b[2])
    return len(rows),out[0],out[1]
for lab,f in (('all <=6h',lambda a,D:60<D<=6*3600),('drop day 1',lambda a,D:60<D<=6*3600 and a['t1']>1769212800),('<=3h',lambda a,D:60<D<=3*3600),('<=90min',lambda a,D:60<D<=5400)):
    n,o,r=fit(f); print(f'{lab:12s} n={n}: observed {o:.1f} min/collision, restart model {r:.1f} -> {o/r:.2f} of a restart')
