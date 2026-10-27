"""Count protocol events per arm from workers' HIVE_LOG files. Run from the repo root:
    python gate10/referee/events.py <logs dir> <arm>
Lines look like '<unix time> EVENT ...' (CLAIM, LAND, CONFLICT, BLOCKED)."""
import collections, glob, os, sys

d, arm = sys.argv[1], sys.argv[2]
c = collections.Counter(); claims = []
for f in glob.glob(os.path.join(d, f'{arm}-w*.log')):
    for line in open(f, errors='ignore'):
        p = line.split()
        if len(p) >= 2 and p[1].isupper():
            c[p[1]] += 1
            if p[1] == 'CLAIM' and len(p) >= 4: claims.append((int(p[0]), os.path.basename(f)[:-4], p[3]))
lands = c['LAND'] or 1
print(f'{arm}: ' + ', '.join(f'{k} {v}' for k, v in sorted(c.items())) + f'; conflicts per landing {c["CONFLICT"] / lands:.2f}')
fam = lambda cats: {x.split('_')[0] for x in cats.split(',')}
first = sorted(claims)[:12]
print(f'{arm} first 12 claims, families: ' + ', '.join('/'.join(sorted(fam(cs))) for _, _, cs in first))
