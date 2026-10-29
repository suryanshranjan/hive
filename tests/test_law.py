"""The swarm law picks the number of builders; the company's documents are read for the interview and the builders.
usage: python3 tests/test_law.py   (run from the hive repo root)"""
import os, sys, tempfile
sys.path.insert(0, os.getcwd())
from hive import docs, law

fail = 0
def check(name, got, want):
    global fail
    ok = got == want; fail |= not ok
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f' (got {got!r}, expected {want!r})'))

n, why = law.builders(60, cpus=24)
check('a slow suite limits the builders (the gate term)', (n, 'your tests take 60 s' in why), (2, True))
n, why = law.builders(10, cpus=4)
check('a small computer limits them when the tests are slow (each builder keeps 0.6 of a core busy)', (n, '4 cores' in why), (6, True))
n, why = law.builders(1.4, cpus=2)
check('with a fast suite, 2 cores do not limit them to 2 (Gate 50: 7 builders 3.0x faster than one)', n >= 7, True)
check('the scalability fit peaks near Gate 50\'s best team size', max(range(1, 65), key=law.speedup) in (7, 8), True)
check('the trade is said in plain words', ('speed of one builder' in law.trade(7), law.trade(1).startswith('one builder')), (True, True))
n, why = law.builders(5, cpus=16, decisions=4)
check('a small job gets few builders (about 3 decisions each)', (n, '4 decisions' in why), (2, True))
n, _ = law.builders(1, cpus=64)
check('never more than the largest swarm tested on a real codebase', n, law.CAP)
check('more builders never lower the landings in the model', all(law.throughput(k + 1, 0.5) >= law.throughput(k, 0.5)
                                                                for k in range(1, 30)), True)

d = tempfile.mkdtemp()
open(os.path.join(d, 'refunds.md'), 'w').write('Refunds are paid within 7 days.')
open(os.path.join(d, 'logo.png'), 'wb').write(b'\x89PNG')
text = docs.read(d)
check('documents are read as text, each under its name; images are skipped',
      ('### refunds.md' in text, 'Refunds are paid within 7 days.' in text, 'PNG' in text), (True, True, False))
check('builders are told silence is unknown, not "the standard" (Gate 16)', 'treat it as unknown' in docs.instructions(text), True)
check('no documents, nothing added', (docs.read(os.path.join(d, 'none')), docs.instructions('')), ('', ''))
from hive import law
check('team notes stay off for small swarms that rarely collide (Gates 43-44)', law.notes(6)[0], False)
check('team notes switch on for a large swarm', law.notes(12)[0], True)
check('team notes switch on when this swarm keeps colliding, not on one early collision',
      (law.notes(4, 3, 5)[0], law.notes(4, 1, 1)[0]), (True, False))
sys.exit(fail)
