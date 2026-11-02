"""Gate 103a: the owner's-examples check replayed on 32 delivered Tiny Shop builds (Gates 95-99, 101).
usage: python3 gates/gate103/referee/replay103.py [--jobs 4]   (run from the hive repo; HIVE_DEV points at the code under test)"""
import glob, json, os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.environ.get('HIVE_DEV', '/home/claude/hive-dev'))
from hive import examples

R = 'runs'; OUT = os.path.join(R, 'g103_replay'); os.makedirs(OUT, exist_ok=True)
FLIGHTS = [f for f in sorted(glob.glob(f'{R}/g9[5-9]_*')) + sorted(glob.glob(f'{R}/g101_day*'))
           if glob.glob(f'{f}/hive_state/runs/*/state.json') and os.path.isdir(f'{f}/delivered')]

def hidden(f):
    g = os.path.basename(f); gate, name = g.split('_', 1); gate = gate[1:]
    d = json.load(open(f'gates/gate{gate}/results/{name}/flight.json'))
    a = d.get('after') or d.get('hidden'); return a['passed'], a['passed'] + a['failed']

def one(f):
    name = os.path.basename(f); dst = os.path.join(OUT, name + '.json')
    if os.path.exists(dst):
        return json.load(open(dst))
    home = glob.glob(f'{f}/hive_state/runs/*/state.json')[0].rsplit('/', 1)[0]
    st = json.load(open(f'{home}/state.json'))
    rules = examples.rules_of(home)
    got = examples.check(f'{f}/delivered', st['goal'], rules)
    p, t = hidden(f)
    r = dict(flight=name, hidden=p, of=t, rules=len(rules), result=got)
    json.dump(r, open(dst, 'w'), indent=1); print(name, p, t, got and (got['checks'], len(got['failing']), got['cost']), flush=True)
    return r

if __name__ == '__main__':
    jobs = int(sys.argv[sys.argv.index('--jobs') + 1]) if '--jobs' in sys.argv else 4
    with ThreadPoolExecutor(jobs) as ex:
        list(ex.map(one, FLIGHTS))
