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
check('the trade is said in plain words', ('speed of one builder' in law.trade(7), law.trade(1) == 'the cheapest way'), (True, True))
n, why = law.builders(5, cpus=16, decisions=4)
check('a small job gets few builders (about 3 decisions each)', (n, '4 decisions' in why), (2, True))
n, why = law.builders(1.4, cpus=8, parts=1)
check('a job that is one piece of work gets one builder, and says why (Gate 52)', (n, 'one piece of work' in why), (1, True))
n, why = law.builders(1.4, cpus=8, parts=3)
check('a job of 3 parts gets at most 3', (n, '3 parts' in why), (3, True))
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
check('size alone does not switch notes on (Gate 51: not faster at 12 builders)', law.notes(12)[0], False)
check('team notes switch on when this swarm keeps colliding, not on one early collision',
      (law.notes(4, 3, 5)[0], law.notes(4, 1, 1)[0]), (True, False))
home = tempfile.mkdtemp(); old_home = os.environ.get('HOME'); os.environ['HOME'] = home
check('no pace chosen yet: None', law.pace(), None)
check('cheap: one builder, whatever the machine allows (Gate 50: the cheapest way)', law.builders(5, cpus=16, pace='cheap'),
      (1, 'you asked for the cheapest builds'))
check('fast: the law picks as before', law.builders(5, cpus=16, pace='fast'), law.builders(5, cpus=16))
law.set_pace('cheap')
check('the choice is kept for later builds', law.pace(), 'cheap')
check('his reply in his own words: Enter is fast; money words are cheap; unclear is no choice',
      [law.read_pace(x) for x in ('', 'cheap please', 'save money', 'jaldi chahiye', 'fast', 'hmm not sure')],
      ['fast', 'cheap', 'cheap', 'fast', 'fast', None])
os.environ['HOME'] = old_home or ''
sys.exit(fail)
