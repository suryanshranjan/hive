# Does landing alongside an overlapping concurrent change raise the chance your code needs a fix soon after?
import pickle, math, numpy as np, re, datetime as dt
T=pickle.load(open('ccc_tasks2.pkl','rb')); T.sort(key=lambda t:t['t1'])
fixre=re.compile(r'\b(fix|regress|bug|crash|wrong|broken|incorrect|miscompil)',re.I)
for t in T: t['isfix']=bool(fixre.search(t['endc']['subj']))
print('share of tasks that are fixes: %.2f'%np.mean([t['isfix'] for t in T]))
W=12*3600; rows=[]
for i,a in enumerate(T):
    D=a['t1']-a['t0']
    if D<=60 or D>6*3600: continue
    ov=any(a['Fn']&b['Fn'] for b in T if b is not a and a['t0']<b['t1']<a['t1'])
    later=[b for b in T[i+1:] if b['t1']-a['t1']<W]
    if not later or T[-1]['t1']-a['t1']<W: continue
    fixed=any(b['isfix'] and (a['Fn']&b['Fn']) for b in later)
    touched=any(a['Fn']&b['Fn'] for b in later)  # placebo-ish: any later touch
    hot=sum(1 for b in T if abs(b['t1']-a['t1'])<86400 and b is not a and a['Fn']&b['Fn'])+1
    rows.append((fixed,touched,ov,math.log(hot),math.log(len(a['Fn'])),math.log(D),dt.datetime.fromtimestamp(a['t1'],dt.timezone.utc).strftime('%m%d')))
days=sorted({r[6] for r in rows})
X=np.array([[1,float(r[2]),r[3],r[4],r[5]]+[1.0 if r[6]==d else 0 for d in days[1:]] for r in rows]); X=X[:,X.any(axis=0)]
for col,lab in ((0,'later FIX touches your functions'),(1,'later ANY task touches your functions')):
    y=np.array([float(r[col]) for r in rows])
    b=np.linalg.lstsq(X,y,rcond=None)[0]; e=y-X@b; cov=(e@e/(len(y)-X.shape[1]))*np.linalg.pinv(X.T@X)
    print(f'{lab}: base rate {y.mean():.2f}; effect of concurrent overlap {b[1]:+.3f} (95% CI {b[1]-1.96*math.sqrt(cov[1,1]):+.3f}..{b[1]+1.96*math.sqrt(cov[1,1]):+.3f})')
print('n tasks',len(rows),' with overlap %.2f'%np.mean([r[2] for r in rows]))
