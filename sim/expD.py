# Experiment D: sampled checks catch covered bugs fast; bugs the suite can't see are found only after a
# delay tau. Prediction (my model): with bounce recovery the cliff returns at N* = C / ((1-cov)*kappa*tau),
# with one constant C. Fit C on the uniform-codebase configs, test on skewed codebases (held out).
# With traceback: live unseen bugs on main = landings/time * f * (1-cov) * tau  (no fitting).
import itertools, json, math, multiprocessing as mp, numpy as np
from hive_sim import run
Ns=(8,16,32,64,128,256,512,1024)
cases=[]
for (m,z),cov,tau in itertools.product(((64,0.0),(16,0.0),(64,1.0),(16,0.8),(256,1.2)),(0.8,0.95),(0.5,2.0)):
    cases.append(dict(m=m,zipf=z,cov=cov,tau=tau))
grid=[dict(c,N=N,recover=rec) for c in cases for N in Ns for rec in ('bounce','traceback')]
def job(g):
    out=[run(N=g['N'],m=g['m'],zipf=g['zipf'],collide='fixed',d=0.0,f=0.2,mode='sample',s=0.2,tg=0.2,
             recover=g['recover'],cov=g['cov'],tau=g['tau'],seed=sd,T=max(24.0,4000.0/g['N'])) for sd in (1,2)]
    r=dict(g)
    for k in ('eff','live_uncov','landed','kappa'): r[k]=sum(o[k] for o in out)/2
    return r
if __name__=='__main__':
    with mp.Pool(2) as p: R=p.map(job,grid,chunksize=2)
    json.dump(R,open('expD.json','w')); print(len(R))
