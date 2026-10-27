# Per commit, per src file: hashes of added and removed line contents (non-trivial lines only)
import pickle, re, sys
out={}; cur=None; f=None
for line in open(sys.argv[1],errors='replace'):
    if line.startswith('@@@'):
        cur=line[3:].split('|',1)[0]; out[cur]={}; f=None; continue
    if line.startswith('diff --git '):
        m=re.match(r'diff --git a/(.*) b/(.*)$',line.rstrip('\n')); f=m.group(2) if m and m.group(2).startswith('src/') else None
        if f: out[cur].setdefault(f,[set(),set()])
        continue
    if f is None or line.startswith('+++') or line.startswith('---'): continue
    if line[:1] in '+-':
        s=line[1:].strip()
        if len(s)<12 or s in ('} else {',): continue
        out[cur][f][0 if line[0]=='+' else 1].add(hash(s))
pickle.dump(out,open(sys.argv[2],'wb')); print(len(out))
