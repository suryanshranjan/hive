import json, math, numpy as np, collections
R=json.load(open('expD.json'))
g=collections.defaultdict(list)
for r in R: g[(r['m'],r['zipf'],r['cov'],r['tau'],r['recover'])].append(r)
def nstar(rows):
    rows=sorted(rows,key=lambda r:r['N']); e0=rows[0]['eff']; half=e0/2
    for a,b in zip(rows,rows[1:]):
        if a['eff']>=half>b['eff']:
            # interpolate in log N
            x=math.log(a['N'])+(math.log(b['N'])-math.log(a['N']))*(a['eff']-half)/(a['eff']-b['eff'])
            return math.exp(x)
    return None
print('Bounce: cliff location N* (efficiency halves) vs prediction C/((1-cov)*kappa*tau)')
pts=[]
for key,rows in g.items():
    m,z,cov,tau,rec=key
    if rec!='bounce': continue
    ns=nstar(rows); k=rows[0]['kappa']; x=(1-cov)*k*tau
    pts.append((m,z,cov,tau,k,ns,x, ' '.join(f"{r['eff']:.2f}" for r in sorted(rows,key=lambda r:r['N']))))
train=[p for p in pts if p[1]==0.0 and p[5]]; test=[p for p in pts if p[1]>0 and p[5]]
C=math.exp(np.mean([math.log(p[5]*p[6]) for p in train]))
print(f'fitted C = {C:.2f} on {len(train)} uniform configs')
errs=[]
for p in sorted(pts,key=lambda p:p[6]):
    pred=C/p[6]; tag='train' if p[1]==0 else 'TEST '
    obs=f'{p[5]:.0f}' if p[5] else '>1024 or <8'
    if p[5] and p[1]>0: errs.append(max(pred/p[5],p[5]/pred))
    print(f' {tag} m={p[0]:3d} zipf={p[1]:.1f} cov={p[2]} tau={p[3]} kappa={p[4]:.3f}  N*obs={obs:>6s}  pred={pred:7.0f}   eff by N: {p[7]}')
print('held-out: n=%d, median error %.2fx, worst %.2fx'%(len(errs),np.median(errs),max(errs)) if errs else 'no held-out cliffs')
print('\nTraceback: live unseen bugs vs prediction landings*f*(1-cov)*tau  (no fitting)')
rat=[]
for key,rows in g.items():
    m,z,cov,tau,rec=key
    if rec!='traceback': continue
    for r in rows:
        pred=r['landed']*0.2*(1-cov)*tau*(1/(1-0.2*(1-0.2)*0+0))  # landed per time * f*(1-cov)*tau
        if r['live_uncov']>0.5: rat.append(r['live_uncov']/pred)
    if (m,z)==(64,1.0) and tau==2.0:
        print(f' cov={cov} tau={tau}: live unseen bugs by N', ' '.join(f"{r['live_uncov']:.1f}" for r in sorted(rows,key=lambda r:r['N'])), ' | eff', ' '.join(f"{r['eff']:.2f}" for r in sorted(rows,key=lambda r:r['N'])))
print(' observed/predicted over %d runs: median %.2f, range %.2f-%.2f'%(len(rat),np.median(rat),min(rat),max(rat)))
# power-law fit of the cliff location on uniform codebases, tested on skewed ones
X=[];y=[];Xt=[];yt=[]
for p in pts:
    if not p[5]: continue
    row=[1,math.log(1-p[2]),math.log(p[3]),math.log(p[4])]
    (X if p[1]==0 else Xt).append(row); (y if p[1]==0 else yt).append(math.log(p[5]))
b=np.linalg.lstsq(np.array(X),np.array(y),rcond=None)[0]
pr=np.exp(np.array(Xt)@b); ob=np.exp(np.array(yt)); r=np.maximum(pr/ob,ob/pr)
print('\npower fit on uniform: N* ~ (1-cov)^%.2f * tau^%.2f * kappa^%.2f ; held-out skewed: median %.2fx, worst %.2fx'%(b[1],b[2],b[3],np.median(r),r.max()))
