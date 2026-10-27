# Minutes added per line-level collision: duration ~ total landings during window + strong collisions + size + day FE
import pickle, math, numpy as np, datetime as dt
exec(open('ccc_cost4.py').read().split('rows=[];sim=[]')[0])  # reuse loading + strong()
rows=[]
for a in T:
    D=a['t1']-a['t0']
    if D<=60 or D>6*3600: continue
    lands=[b for b in T if b is not a and a['t0']<b['t1']<a['t1']]
    ns=sum(1 for b in lands if strong(a,b))
    rows.append((D/60,len(lands),ns,math.log(len(a['Ff'])),math.log(len(a['A'])+len(a['R'])+1),dt.datetime.fromtimestamp(a['t1'],dt.timezone.utc).strftime('%m%d')))
days=sorted({r[5] for r in rows})
X=np.array([[1,r[1],r[2],r[3],r[4]]+[1.0 if r[5]==d else 0 for d in days[1:]] for r in rows]); X=X[:,X.any(axis=0)]
y=np.array([r[0] for r in rows]); b=np.linalg.lstsq(X,y,rcond=None)[0]; e=y-X@b
cov=(e@e/(len(y)-X.shape[1]))*np.linalg.pinv(X.T@X)
print('tasks',len(rows),' median duration %.1f min, mean strong collisions/task %.2f, mean landings/task %.1f'%(np.median(y),np.mean(X[:,2]),np.mean(X[:,1])))
print('minutes per landing (exposure) %.2f; minutes per strong collision %.1f (95%% CI %.1f..%.1f)'%(b[1],b[2],b[2]-1.96*math.sqrt(cov[2,2]),b[2]+1.96*math.sqrt(cov[2,2])))
# same spec on restart-model durations (each strong collision adds the work elapsed since last sync)
ys=[]
for a in T:
    D=a['t1']-a['t0']
    if D<=60 or D>6*3600: continue
    lands=sorted([b for b in T if b is not a and a['t0']<b['t1']<a['t1']],key=lambda x:x['t1'])
    extra=0; last=a['t0']
    for b in lands:
        if strong(a,b): extra+=b['t1']-last; last=b['t1']
    ys.append((D+extra)/60)
ys=np.array(ys); bs=np.linalg.lstsq(X,ys,rcond=None)[0]; es=ys-X@bs; covs=(es@es/(len(ys)-X.shape[1]))*np.linalg.pinv(X.T@X)
print('restart model, same spec: minutes per strong collision %.1f (95%% CI %.1f..%.1f)'%(bs[2],bs[2]-1.96*math.sqrt(covs[2,2]),bs[2]+1.96*math.sqrt(covs[2,2])))
print('implied cost as fraction of a restart: %.2f'%(b[2]/bs[2]))
