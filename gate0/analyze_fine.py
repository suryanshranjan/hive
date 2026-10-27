# Fine windows: consecutive first-parent commits. Lifetimes in commits and hours; tests broken per event;
# whether the fix commit was by the same task that broke it (can't know), and the landing-count distribution.
import os, collections, statistics as st
rows=[]
for l in open('res2_fine2/log.txt'):
    p=l.split()
    if len(p)>3 and p[3]=='OK':
        i=int(p[0]); res={}
        for ext in ('txt','tor'):
            res.update({ext+':'+x.split()[0]:x.split()[1]=='PASS' for x in open(f'res2_fine2/{i}.{ext}')})
        rows.append((int(p[2]),i,res))
rows.sort(key=lambda r:-r[1])
# split into windows by index contiguity (indices descend with time)
wins=[]; cur=[rows[0]]
for r in rows[1:]:
    if cur[-1][1]-r[1]==1: cur.append(r)
    else: wins.append(cur); cur=[r]
wins.append(cur)
allev=[]; lifes_c=[]; lifes_h=[]; ks=[]
for w in wins:
    live={}; ev=collections.defaultdict(list)
    for j,(t,i,res) in enumerate(w):
        prev=w[j-1][2] if j else None
        for tn,ok in res.items():
            if prev is None: continue
            if prev.get(tn) and not ok: live[tn]=(j,t); ev[j].append(tn)
            elif ok and tn in live:
                j0,t0=live.pop(tn); lifes_c.append(j-j0); lifes_h.append((t-t0)/3600)
    for j,v in ev.items(): ks.append(len(v)); allev.append((w[0][1]-j, len(v), w[j][2] and None))
    print(f'window idx {w[0][1]}..{w[-1][1]} ({len(w)} commits, {(w[-1][0]-w[0][0])/3600:.1f} h): events {len(ev)}, unresolved at window end {len(live)}')
print('events',len(ks),' tests broken per event: median',st.median(ks),'max',max(ks),' dist',sorted(ks))
print('lifetimes in commits:',sorted(lifes_c))
print('lifetimes in hours:',[round(x,1) for x in sorted(lifes_h)])
print('median life %.1f commits, %.2f h; mean %.1f commits, %.2f h'%(st.median(lifes_c),st.median(lifes_h),st.mean(lifes_c),st.mean(lifes_h)))
n=sum(len(w)-1 for w in wins); print('regression events per landing (commit): %.4f (%d events / %d commits)'%(len(ks)/n,len(ks),n))
