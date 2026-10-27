# Experiment B: verification. Serial gate vs sampled checks spread across agents vs the old fixed-delay referee.
import itertools, json, multiprocessing as mp
from hive_sim import run
Ns=(16,64,256,1024)
base=dict(m=64,zipf=1.0,collide='fixed',d=0.0,f=0.2,k=1)
grid=[]
for tg,B,N in itertools.product((0.01,0.05,0.2),(1,16),(4,16,64,256,1024)):
    grid.append(dict(base,arm='gate',mode='central',tg=tg,B=B,q=1.0,tau=1e9,N=N))
for tg,B,N in itertools.product((0.05,),(16,),(4,16,64,256,1024)):
    grid.append(dict(base,arm='gate_lowf',mode='central',tg=tg,B=B,q=1.0,tau=1e9,N=N,f=0.02))
for s,rec,N in itertools.product((0.005,0.01,0.03,0.1,0.3),('traceback','bounce'),Ns):
    grid.append(dict(base,arm='sample',mode='sample',s=s,tg=0.2,recover=rec,N=N))
for tau,rec,N in itertools.product((0.3,1.0,3.0),('traceback','bounce'),Ns):
    grid.append(dict(base,arm='fixed_tau',mode='central',tg=0.0,q=0.8,tau=tau,recover=rec,N=N))
def job(cfg):
    c=dict(cfg); arm=c.pop('arm'); out=[run(**c,seed=sd) for sd in (1,2)]
    res=dict(cfg)
    for key in ('eff','live_bugs','throughput','kappa'): res[key]=sum(o[key] for o in out)/len(out)
    return res
if __name__=='__main__':
    with mp.Pool(2) as p: R=p.map(job,grid,chunksize=2)
    json.dump(R,open('expB.json','w')); print(len(R))
