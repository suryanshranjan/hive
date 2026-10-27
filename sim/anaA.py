import json, numpy as np, math
from scipy.optimize import curve_fit
R=json.load(open('expA.json'))
def report(name, train, test, model, p0, xfun):
    xt=np.array([xfun(r) for r in train]); yt=np.array([r['eff'] for r in train])
    popt,_=curve_fit(model,xt,yt,p0=p0,maxfev=20000)
    xs=np.array([xfun(r) for r in test]); ys=np.array([r['eff'] for r in test]); pr=model(xs,*popt)
    ratio=np.maximum(pr/ys,ys/pr); r2=1-((np.log(ys)-np.log(pr))**2).sum()/((np.log(ys)-np.log(ys).mean())**2).sum()
    print(f'{name}: params {np.round(popt,3)} | held-out n={len(test)}  R2(log)={r2:.3f}  within 1.25x: {np.mean(ratio<1.25):.0%}  within 2x: {np.mean(ratio<2):.0%}  worst {ratio.max():.2f}x')
    return popt,pr,ys
# Restart model: eff = 1/(1+(x/x0)^b), x = N*kappa
rs=[r for r in R if r['collide']=='restart']
logistic=lambda x,x0,b: 1/(1+(x/x0)**b)
popt,_,_=report('restart, x=N*kappa  (train uniform, test skewed)', [r for r in rs if r['zipf']==0],[r for r in rs if r['zipf']>0], logistic,(1.5,1),lambda r:r['N']*r['kappa'])
print('   restart: half efficiency at N*kappa = %.2f  (agents per effective region)'%popt[0])
report('restart, x=N/m (old law, kappa=1/m)        ', [r for r in rs if r['zipf']==0],[r for r in rs if r['zipf']>0], logistic,(1.5,1),lambda r:r['N']/r['m'])
# Fixed-cost model: USL contention eff = 1/(1+a*kappa*d*(N-1))
fx=[r for r in R if r['collide']=='fixed']
usl=lambda x,a: 1/(1+a*x)
popt,_,_=report('fixed d, USL x=kappa*d*(N-1) (train uniform d=0.3, test skewed + d=0.1,0.6)', [r for r in fx if r['zipf']==0 and r['d']==0.3],[r for r in fx if not (r['zipf']==0 and r['d']==0.3)], usl,(1,),lambda r:r['kappa']*r['d']*(r['N']-1))
print('   fixed: alpha = %.2f * kappa * d  -> half efficiency at N = 1 + 1/(%.2f*kappa*d)'%(popt[0],popt[0]))
# show raw table for fixed vs restart, m=64
print('\nN     restart(m64,z0)  fixed(m64,z0)  restart(m64,z1.2) fixed(m64,z1.2)')
for N in (4,16,64,256,1024):
    g=lambda c,z:[r['eff'] for r in R if r['N']==N and r['m']==64 and r['zipf']==z and r['collide']==c and r['d']==0.3][0]
    print(f'{N:5d}   {g("restart",0.0):.3f}            {g("fixed",0.0):.3f}          {g("restart",1.2):.3f}            {g("fixed",1.2):.3f}')
