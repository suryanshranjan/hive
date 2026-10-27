import pickle, collections, random, math, statistics as st
C=pickle.load(open('ccc.pkl','rb')); T=pickle.load(open('ccc_tasks.pkl','rb'))
def code(p): return p.startswith('src/')
def workset(t):
    files={}; i=t['ei']
    def add(c):
        for p,fi in c['files'].items():
            if code(p): files.setdefault(p,set()).update(fi['funcs'] or {'<top>'})
    add(C[i]); j=i-1
    while j>t['si'] and C[j+1]['ct']-C[j]['ct']<=5 and not any(p.startswith('current_tasks/') for p in C[j]['files']):
        add(C[j]); j-=1
    return files
for t in T: t['W']=workset(t); t['Ff']=set(t['W']); t['Fn']={p+'::'+f for p,fs in t['W'].items() for f in fs}
T=[t for t in T if t['Ff']]
print('tasks with code work:',len(T))
# file-touch distribution -> static kappa
cnt=collections.Counter(p for t in T for p in t['Ff']); tot=sum(cnt.values())
print('distinct src files touched:',len(cnt))
for p,n in cnt.most_common(8): print('  %5d %s'%(n,p))
# static pairwise collision probability for two random tasks (any shared file)
def overlap_rate(pairs,key):
    return sum(1 for a,b in pairs if a[key]&b[key])/max(1,len(pairs))
T.sort(key=lambda t:t['t1'])
conc=[]
for a in T:
    for b in T:
        if b is a: continue
        if a['t0']<b['t1']<a['t1']: conc.append((a,b))
print('concurrent (in-flight, landed) pairs:',len(conc))
random.seed(1)
# phase-matched baseline: b' landing within +-2 days of a's window but NOT during it
def baseline(days):
    out=[]
    for a,b in conc:
        cands=[x for x in T if x is not a and abs(x['t1']-a['t1'])<days*86400 and not (a['t0']<x['t1']<a['t1'])]
        if cands: out.append((a,random.choice(cands)))
    return out
for key,lab in (('Ff','file'),('Fn','function')):
    k=overlap_rate(conc,key)
    b1=overlap_rate(baseline(1),key); ball=overlap_rate([(a,random.choice(T)) for a,_ in conc],key)
    print(f'{lab:8s} kappa_concurrent={k:.3f}  baseline(+-1d)={b1:.3f}  baseline(any time)={ball:.3f}  herding H={k/b1:.2f}')
pickle.dump(T,open('ccc_tasks2.pkl','wb'))
