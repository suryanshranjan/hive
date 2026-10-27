import pickle, collections, statistics as st
C=pickle.load(open('ccc.pkl','rb'))
def is_lock(p): return p.startswith('current_tasks/')
def is_meta(p): return is_lock(p) or p.startswith('ideas/') or p.endswith('.md') or p.endswith('.txt') and not p.startswith('src/') or p.startswith('tests/')
open_={}; tasks=[]
for i,c in enumerate(C):
    for p,fi in c['files'].items():
        if not is_lock(p) or p.endswith('.keep'): continue
        if fi['add']:
            open_[p]=(i,c)
        elif fi['del'] and p in open_:
            si,sc=open_.pop(p); tasks.append({'path':p,'si':si,'ei':i,'t0':sc['ct'],'t1':c['ct'],'endc':c})
print('tasks closed',len(tasks),'still open',len(open_))
# what does the closing commit contain?
work_in_close=sum(1 for t in tasks if any(not is_lock(p) for p in t['endc']['files']))
print('closing commit contains non-lock files:',work_in_close)
dur=[(t['t1']-t['t0'])/60 for t in tasks]
print('task duration min: median %.0f, p25 %.0f, p75 %.0f, p90 %.0f'%(st.median(dur),*[sorted(dur)[int(len(dur)*q)] for q in (0.25,0.75,0.9)]))
# look at gaps between consecutive commits' ct to see push batches
gaps=[C[i+1]['ct']-C[i]['ct'] for i in range(len(C)-1)]
print('ct gaps: <=5s',sum(g<=5 for g in gaps),' <=60s',sum(g<=60 for g in gaps),' neg',sum(g<0 for g in gaps))
pickle.dump(tasks,open('ccc_tasks.pkl','wb'))
