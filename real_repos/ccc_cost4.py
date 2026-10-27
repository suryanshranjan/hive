# Strong collision: your task removes/rewrites lines that a concurrent landing just added or removed.
import pickle, math, numpy as np, datetime as dt
T=pickle.load(open('ccc_tasks2.pkl','rb')); L=pickle.load(open('ccc_lines.pkl','rb')); C=pickle.load(open('ccc.pkl','rb'))
def lineset(t):
    add=set(); rem=set()
    for c in [t['endc']]:
        for p,(a,r) in L.get(c['hash'],{}).items(): add|={(p,x) for x in a}; rem|={(p,x) for x in r}
    return add,rem
for t in T: t['A'],t['R']=lineset(t)
def strong(a,b):  # a lands after b; a rewrites b's new lines, or both removed the same original lines
    return bool(a['R']&b['A']) or bool(a['R']&b['R'])
rows=[];sim=[];nstrong=0;npairs=0
for a in T:
    D=a['t1']-a['t0']
    if D<=60 or D>6*3600: continue
    lands=[b for b in T if b is not a and a['t0']<b['t1']<a['t1']]
    if len(lands)<3: continue
    st_=[b for b in lands if strong(a,b)]; nstrong+=len(st_); npairs+=len(lands)
    fr=len(st_)/len(lands)
    extra=0; last=a['t0']
    for b in sorted(st_,key=lambda x:x['t1']): extra+=b['t1']-last; last=b['t1']
    rows.append((math.log(D),fr,math.log(len(a['Ff'])),math.log(sum(len(v) for v in [a['A'],a['R']])+1),dt.datetime.fromtimestamp(a['t1'],dt.timezone.utc).strftime('%m%d'),math.log(D+extra)))
print('strong-collision share of concurrent pairs: %.3f (%d/%d)'%(nstrong/npairs,nstrong,npairs))
days=sorted({r[4] for r in rows})
X=np.array([[1,r[1],r[2],r[3]]+[1.0 if r[4]==d else 0 for d in days[1:]] for r in rows]); X=X[:,X.any(axis=0)]
for col,lab in ((0,'observed'),(5,'restart model')):
    y=np.array([r[col] for r in rows]); b=np.linalg.lstsq(X,y,rcond=None)[0]; e=y-X@b
    cov=(e@e/(len(y)-X.shape[1]))*np.linalg.pinv(X.T@X); se=math.sqrt(cov[1,1])
    print(f'{lab:14s}: 0->100% strong collisions changes duration x{math.exp(b[1]):.2f} (95% CI x{math.exp(b[1]-1.96*se):.2f}..x{math.exp(b[1]+1.96*se):.2f})')
print('tasks',len(rows),' tasks with >=1 strong collision: %.2f'%np.mean([r[1]>0 for r in rows]))
