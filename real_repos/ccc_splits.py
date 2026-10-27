import pickle, re
C=pickle.load(open('ccc.pkl','rb'))
ev=[]
for i,c in enumerate(C):
    new=[p for p,f in c['files'].items() if p.startswith('src/') and f['add'] and p.endswith('.rs') and not p.endswith('mod.rs')]
    big=[(p,f['lines']) for p,f in c['files'].items() if p.startswith('src/') and not f['add'] and f['lines']>300]
    if len(new)>=2 and big and re.search(r'split|extract|decompos|break up|move|modulari|reorgan',c['subj'],re.I):
        ev.append((i,c['ct'],c['subj'][:110],new,big))
print(len(ev),'split events')
for e in ev[:60]: print(e[0], e[2], '| new:',len(e[3]),'| src:',[p.split('/')[-2]+'/'+p.split('/')[-1] for p,_ in e[4]][:3])
pickle.dump(ev,open('ccc_splits.pkl','wb'))
