"""Parse `git log -p -U0 --format='@@@%H|%at|%ct|%s'` output into commit records.
Each record: hash, at, ct, subj, files{path: {'add':bool,'del':bool,'funcs':set,'lines':int}}"""
import re, pickle, sys
def parse(path):
    commits=[]; cur=None; curfile=None; minus=None
    hunk_re=re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@ ?(.*)$')
    with open(path,'r',errors='replace') as f:
        for line in f:
            if line.startswith('@@@'):
                h,at,ct,subj=line[3:].rstrip('\n').split('|',3)
                cur={'hash':h,'at':int(at),'ct':int(ct),'subj':subj,'files':{}}; commits.append(cur); curfile=None; continue
            if cur is None: continue
            if line.startswith('diff --git '):
                m=re.match(r'diff --git a/(.*) b/(.*)$',line.rstrip('\n'))
                curfile=m.group(2) if m else None
                if curfile: cur['files'].setdefault(curfile,{'add':False,'del':False,'funcs':set(),'lines':0,'hunks':[]})
                continue
            if curfile is None: continue
            if line.startswith('new file mode'): cur['files'][curfile]['add']=True; continue
            if line.startswith('deleted file mode'): cur['files'][curfile]['del']=True; continue
            if line.startswith('@@ '):
                m=hunk_re.match(line.rstrip('\n'))
                if m:
                    ctx=m.group(5).strip()
                    fn=None
                    mm=re.search(r'\bfn\s+([A-Za-z_][A-Za-z0-9_]*)',ctx)
                    if mm: fn=mm.group(1)
                    else:
                        mm=re.search(r'\b(impl|struct|enum|mod|trait)\b\s*(?:<[^>]*>\s*)?([A-Za-z_][A-Za-z0-9_:]*)',ctx)
                        if mm: fn=mm.group(1)+' '+mm.group(2)
                    ostart=int(m.group(1)); olen=int(m.group(2)) if m.group(2) is not None else 1
                    cur['files'][curfile]['hunks'].append((ostart,olen))
                    if fn: cur['files'][curfile]['funcs'].add(fn)
                continue
            if (line.startswith('+') and not line.startswith('+++')) or (line.startswith('-') and not line.startswith('---')):
                cur['files'][curfile]['lines']+=1
    return commits
if __name__=='__main__':
    c=parse(sys.argv[1]); pickle.dump(c,open(sys.argv[2],'wb')); print(len(c),'commits')
