# Experiment A: coupling. Does efficiency depend only on N*kappa (kappa = sum p^2), not on m or skew?
# Restart (old assumption) vs fixed cost per collision (measured in the C-compiler repo).
import itertools, json, multiprocessing as mp
from hive_sim import run
grid=[]
for m,z,col,d in itertools.product((16,64,256),(0.0,0.8,1.2),('restart','fixed'),(0.3,)):
    for N in (4,8,16,32,64,128,256,512,1024):
        grid.append(dict(N=N,m=m,zipf=z,collide=col,d=d))
for m,z,d in itertools.product((64,),(0.0,1.2),(0.1,0.6)):   # held-out collision costs
    for N in (4,8,16,32,64,128,256,512,1024):
        grid.append(dict(N=N,m=m,zipf=z,collide='fixed',d=d))
def job(cfg):
    out=[]
    for seed in (1,2):
        r=run(**cfg,seed=seed); out.append(r)
    res=dict(cfg); res['eff']=sum(o['eff'] for o in out)/2; res['kappa']=out[0]['kappa']; res['cpt']=sum(o['coll_per_task'] for o in out)/2
    return res
if __name__=='__main__':
    with mp.Pool(2) as p: R=p.map(job,grid,chunksize=4)
    json.dump(R,open('expA.json','w')); print(len(R),'runs')
