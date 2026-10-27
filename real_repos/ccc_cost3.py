# Task-level robustness check: does the share of concurrent landings that overlap your functions predict a longer task?
import pickle, math, numpy as np, datetime as dt, random
T=pickle.load(open('ccc_tasks2.pkl','rb'))
def lines(t): return sum(fi['lines'] for p,fi in t['endc']['files'].items() if p.startswith('src/'))+1
rows=[]
for a in T:
    D=a['t1']-a['t0']
    if D<=60 or D>6*3600: continue
    lands=[b for b in T if b is not a and a['t0']<b['t1']<a['t1']]
    if len(lands)<3: continue
    fr=sum(1 for b in lands if a['Fn']&b['Fn'])/len(lands)
    rows.append((math.log(D),fr,math.log(len(a['Ff'])),math.log(lines(a)),dt.datetime.fromtimestamp(a['t1'],dt.timezone.utc).strftime('%m%d')))
days=sorted({r[4] for r in rows})
X=np.array([[1,r[1],r[2],r[3]]+[1.0 if r[4]==d else 0.0 for d in days[1:]] for r in rows]); y=np.array([r[0] for r in rows])
X=X[:,X.any(axis=0)]
b=np.linalg.lstsq(X,y,rcond=None)[0]; e=y-X@b; cov=(e@e/(len(y)-X.shape[1]))*np.linalg.pinv(X.T@X)
se=math.sqrt(cov[1,1])
print('tasks',len(rows),' mean overlap share %.2f'%np.mean(X[:,1]))
print('going from 0%% to 100%% overlapping landings changes duration x%.2f (95%% CI x%.2f..x%.2f)'%(math.exp(b[1]),math.exp(b[1]-1.96*se),math.exp(b[1]+1.96*se)))
# simulate what the restart model would produce on these same tasks: each overlapping landing at elapsed e adds e
sim=[]
for a in T:
    D=a['t1']-a['t0']
    if D<=60 or D>6*3600: continue
    lands=[b for b in T if b is not a and a['t0']<b['t1']<a['t1']]
    if len(lands)<3: continue
    ov=[b for b in lands if a['Fn']&b['Fn']]
    extra=0; last=a['t0']
    for b in sorted(ov,key=lambda x:x['t1']): extra+=b['t1']-last; last=b['t1']
    sim.append((math.log(D+extra),len(ov)/len(lands)))
ys=np.array([s[0] for s in sim]); bs=np.linalg.lstsq(X,ys,rcond=None)[0]
print('same regression on restart-model durations: x%.2f'%math.exp(bs[1]))
