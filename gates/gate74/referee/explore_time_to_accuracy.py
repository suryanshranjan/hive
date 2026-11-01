"""Exploratory: minutes until each arm's main first reaches a business hidden pass (intent probe) and engine visible."""
import json, os, subprocess, sys, collections, shutil
ROOT='/home/claude/hive'
def probe_at(up, h, oracle, seed, tmp):
    shutil.rmtree(tmp, ignore_errors=True); subprocess.run(['git','clone','-q',up,tmp],check=True); subprocess.run(['git','checkout','-q',h],cwd=tmp,check=True)
    out=tmp+'.json'; subprocess.run([sys.executable,f'{ROOT}/lab/intent.py','probe',oracle,tmp,out,str(seed)],cwd='/',capture_output=True,timeout=600)
    try: P=json.load(open(out))
    except Exception: return 0.0
    t=collections.defaultdict(list)
    for r in P: t[r['test']].append(r['ok'])
    return 100*sum(all(v) for v in t.values())/len(t)
for run, seed in (('g74a',74200000),('g74b',74400000)):
    teams=json.load(open(f'{ROOT}/runs/{run}/teams.json')); oracle=f'{ROOT}/private/{run}/oracle.py'
    for arm,v in teams.items():
        t0=v['team_start']; rows=[]
        for p in v['progress']:
            if p['t']<t0-5: continue
            b=probe_at(f'{ROOT}/runs/{run}/up{arm}.git',p['hash'],oracle,seed,f'/tmp/claude-0/-home-claude/8c8904c7-77e6-5db5-9267-c0fd993e2759/scratchpad/tta_{arm}')
            rows.append((round((p['t']-t0)/60,1),p['visible'],round(b,1)))
        final=rows[-1][2] if rows else 0
        first=lambda thr: next((m for m,vis,b in rows if b>=thr and vis>=0.95*1360), None)
        print(run,arm,'final business',final,'| first >=90%:',first(90),'>=95%:',first(95),'| reach final:',next((m for m,vis,b in rows if b>=final),None))
        print('   ', [(m,b) for m,vis,b in rows if b>0][:12])
