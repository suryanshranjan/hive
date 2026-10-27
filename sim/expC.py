# Experiment C: zero-parameter test of the combined law on 80 random swarms it has never seen.
# Law (my model):  per-agent cost of coupling  1 + kappa*d*(N-1)        (USL contention; constant 1.00 from Exp A)
#                  sampled checks:   eff = (1-f)/(1+s*tg) / (1+kappa*d*(N-1))
#                  serial gate:      1/X = (1+kappa*d*(N-1))/(N*(1-f)) + tg/(1-f)   (resistors in series)
import json, random, math, multiprocessing as mp, numpy as np
from hive_sim import run, zipf_p
rnd=random.Random(7); cfgs=[]
for i in range(80):
    c=dict(N=int(round(math.exp(rnd.uniform(math.log(4),math.log(1024))))), m=rnd.choice((16,64,256)), zipf=rnd.uniform(0,1.2),
           collide='fixed', d=math.exp(rnd.uniform(math.log(0.05),math.log(0.6))), f=rnd.uniform(0.02,0.3), k=1,
           mode=rnd.choice(('sample','central')), tg=math.exp(rnd.uniform(math.log(0.005),math.log(0.2))), recover='traceback')
    if c['mode']=='sample': c['s']=math.exp(rnd.uniform(math.log(0.01),math.log(0.3)))
    else: c.update(q=1.0,tau=1e9,B=1)
    cfgs.append(c)
def law(c):
    p=zipf_p(c['m'],c['zipf']); k=float((p**2).sum()); N=c['N']; cc=1+k*c['d']*(N-1)
    if c['mode']=='sample': return (1-c['f'])/(1+c['s']*c['tg'])/cc
    X=1/(cc/(N*(1-c['f']))+c['tg']/(1-c['f'])); return X/N
def job(c):
    out=[run(**c,seed=s) for s in (1,2)]; return sum(o['eff'] for o in out)/2
if __name__=='__main__':
    with mp.Pool(2) as p: obs=p.map(job,cfgs,chunksize=2)
    pred=[law(c) for c in cfgs]
    o=np.array(obs); pr=np.array(pred); ratio=np.maximum(o/pr,pr/o)
    r2=1-((np.log(o)-np.log(pr))**2).sum()/((np.log(o)-np.log(o).mean())**2).sum()
    print(f'80 held-out swarms (no fitting): R2(log) {r2:.3f}; within 1.25x {np.mean(ratio<1.25):.0%}; within 2x {np.mean(ratio<2):.0%}; worst {ratio.max():.2f}x')
    for mode in ('sample','central'):
        idx=[i for i,c in enumerate(cfgs) if c['mode']==mode]
        print(f'  {mode}: n={len(idx)} median error {np.median(ratio[idx]):.2f}x, worst {ratio[idx].max():.2f}x, mean signed log err {np.mean(np.log(pr[idx]/o[idx])):+.2f}')
    worst=sorted(range(80),key=lambda i:-ratio[i])[:5]
    for i in worst: print('   worst:',{k:(round(v,3) if isinstance(v,float) else v) for k,v in cfgs[i].items() if k in ('N','m','zipf','d','f','mode','tg','s')}, 'obs %.3f pred %.3f'%(o[i],pr[i]))
    json.dump(dict(cfgs=cfgs,obs=obs,pred=pred),open('expC.json','w'))
