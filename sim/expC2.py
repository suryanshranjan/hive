# Central gate: coupling and the gate don't add in series. Fit a p-norm blend on the 36 central swarms
# from Exp C, then test on 60 fresh central swarms.
import json, random, math, multiprocessing as mp, numpy as np
from scipy.optimize import minimize_scalar
from hive_sim import run, zipf_p
D=json.load(open('expC.json'))
def parts(c):
    p=zipf_p(c['m'],c['zipf']); k=float((p**2).sum()); N=c['N']
    Xa=N*(1-c['f'])/(1+k*c['d']*(N-1)); Xg=(1-c['f'])/c['tg']; return Xa,Xg,N
def pred(c,pn):
    Xa,Xg,N=parts(c); return (Xa**-pn+Xg**-pn)**(-1/pn)/N
train=[(c,o) for c,o in zip(D['cfgs'],D['obs']) if c['mode']=='central']
loss=lambda pn: sum((math.log(pred(c,pn))-math.log(o))**2 for c,o in train)
pn=minimize_scalar(loss,bounds=(0.5,20),method='bounded').x
print('fitted blend exponent p = %.2f  (p=1 is resistors in series, p=inf is pure bottleneck)'%pn)
rnd=random.Random(8); test=[]
for i in range(60):
    test.append(dict(N=int(round(math.exp(rnd.uniform(math.log(4),math.log(1024))))), m=rnd.choice((16,64,256)), zipf=rnd.uniform(0,1.2),
       collide='fixed', d=math.exp(rnd.uniform(math.log(0.05),math.log(0.6))), f=rnd.uniform(0.02,0.3), k=1, mode='central',
       tg=math.exp(rnd.uniform(math.log(0.005),math.log(0.2))), recover='traceback', q=1.0, tau=1e9, B=1))
def job(c): return sum(run(**c,seed=s)['eff'] for s in (3,4))/2
if __name__=='__main__':
    with mp.Pool(2) as p: obs=np.array(p.map(job,test,chunksize=2))
    for lab,pp in (('series p=1',1.0),('fitted p=%.2f'%pn,pn),('bottleneck p=50',50.0)):
        pr=np.array([pred(c,pp) for c in test]); ratio=np.maximum(obs/pr,pr/obs)
        r2=1-((np.log(obs)-np.log(pr))**2).sum()/((np.log(obs)-np.log(obs).mean())**2).sum()
        print(f'  {lab:16s} held-out n=60: R2(log) {r2:.3f}, within 1.25x {np.mean(ratio<1.25):.0%}, within 2x {np.mean(ratio<2):.0%}, worst {ratio.max():.2f}x')
