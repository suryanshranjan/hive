"""Hive swarm simulator v2. No scaling formulas are coded; only mechanics.

Time unit = mean task work time (1.0). Agents never talk; they pick a task, work, verify, land.

Mechanics
- Regions: m regions, popularity p_i ~ 1/i^zipf. Each task writes region w ~ p and reads region r ~ p.
- Collisions: when a change lands in region w, every other in-flight agent writing w pays a cost:
    'restart': redo all work since its last sync (the earlier Hive sim's assumption)
    'fixed'  : add d time units (resolve + re-test); ~0.3 measured in the C-compiler repo
- Bugs: each change carries a fresh bug with prob f. A bug breaks k tests of the suite.
- Verification modes
    'central': one serial gate runs the suite on main+batch (time tg per run, batch up to B;
               a failed batch costs ceil(log2 B) extra runs per culprit to bisect).
               Covered bugs (prob q) are caught at the gate; uncovered ones escape and are
               found after an exponential delay with mean tau (the earlier sim's referee model).
    'sample' : each agent, before landing, runs a random fraction s of the suite on main+its
               change (adds s*tg to its own time, in parallel; no serial gate). The sample can
               catch its own bug and any live escaped bug on main: P(detect) = 1-(1-s)^k per bug.
- Spread: a landing whose write or read region holds live bugs becomes infected and carries
  them into its write region.
- On detection: 'traceback' reverts only the source change; 'bounce' reverts the source plus
  every change infected by that bug.
Output: useful throughput (landed minus reverted, per time unit) after warm-up;
efficiency = throughput / N (1.0 = each agent lands one useful task per time unit).
"""
import heapq, random, math
import numpy as np


def zipf_p(m, a):
    w = np.array([1.0 / (i + 1) ** a for i in range(m)])
    return w / w.sum()


def run(N=64, m=64, zipf=0.0, collide='restart', d=0.3, f=0.0, k=1, mode='sample', s=0.0,
        tg=0.0, B=1, q=1.0, tau=1.0, recover='traceback', T=None, warm=None, seed=0, dist='uniform', cov=1.0):
    rng = random.Random(seed)
    p = zipf_p(m, zipf)
    cum = list(np.cumsum(p)); cum[-1] = 1.0
    import bisect
    def region():
        return bisect.bisect_left(cum, rng.random())
    if T is None:
        T = max(24.0, 6000.0 / N)
    if warm is None:
        warm = T / 3

    ev = []; seq = [0]
    def push(t, kind, payload):
        seq[0] += 1
        heapq.heappush(ev, (t, seq[0], kind, payload))

    w_of = [0] * N; r_of = [0] * N; fin = [0.0] * N; last = [0.0] * N; ver = [0] * N
    inflight = [set() for _ in range(m)]
    live = [set() for _ in range(m)]
    bug_regions = {}; bug_src = {}; bug_members = {}
    reverted = set(); uncovered = set()
    nchange = [0]
    st = dict(landed=0, rejected=0, reverted=0, detections=0, collisions=0, tasks=0, live_area=0.0, uncov_area=0.0)
    gate_q = []; gate_busy = [False]

    def start(a, t):
        w = region(); r = region()
        w_of[a] = w; r_of[a] = r
        work = (rng.uniform(0.5, 1.5) if dist == 'uniform' else rng.expovariate(1.0) if dist == 'exp' else rng.lognormvariate(-0.5, 1.0)) + (s * tg if mode == 'sample' else 0.0)
        fin[a] = t + work; last[a] = t; ver[a] += 1
        inflight[w].add(a)
        push(fin[a], 'done', (a, ver[a]))

    def kill_bug(b, t):
        if t >= warm: st['detections'] += 1
        victims = [bug_src[b]] if recover == 'traceback' else bug_members.get(b, [])
        for cid in victims:
            if cid not in reverted:
                reverted.add(cid)
                if t >= warm: st['reverted'] += 1
        for reg in bug_regions.pop(b, ()):
            live[reg].discard(b)
        uncovered.discard(b)
        bug_members.pop(b, None)

    def land(a, t, fresh_bug):
        w, r = w_of[a], r_of[a]
        cid = nchange[0]; nchange[0] += 1
        if t >= warm: st['landed'] += 1
        carried = live[w] | live[r]
        if fresh_bug:
            b = cid
            bug_src[b] = cid; bug_members[b] = []; bug_regions[b] = set()
            carried = carried | {b}
            if mode == 'central':
                push(t + rng.expovariate(1.0 / tau), 'found', b)
            elif fresh_bug == 'uncovered':
                uncovered.add(b)
                push(t + rng.expovariate(1.0 / tau), 'found', b)
        for b in carried:
            if b in bug_members:
                bug_members[b].append(cid)
                bug_regions[b].add(w)
        live[w] |= carried
        for o in inflight[w]:
            if o == a:
                continue
            st['collisions'] += 1
            add = (t - last[o]) if collide == 'restart' else d
            last[o] = t
            fin[o] += add; ver[o] += 1
            push(fin[o], 'done', (o, ver[o]))

    for a in range(N):
        start(a, 0.0)
    dp = 1.0 - (1.0 - s) ** k
    last_t = 0.0
    while ev:
        t, _, kind, payload = heapq.heappop(ev)
        if t > T:
            break
        if t > warm:
            st['live_area'] += len(bug_regions) * (t - max(last_t, warm))
            st['uncov_area'] += len(uncovered) * (t - max(last_t, warm))
        last_t = t
        if kind == 'done':
            a, v = payload
            if v != ver[a]:
                continue
            inflight[w_of[a]].discard(a)
            if t >= warm: st['tasks'] += 1
            fresh = rng.random() < f
            if mode == 'sample':
                if fresh and rng.random() >= cov:
                    fresh = 'uncovered'
                if fresh is True and rng.random() < dp:
                    if t >= warm: st['rejected'] += 1
                    start(a, t); continue
                if bug_regions and dp > 0:
                    vis = [b for b in bug_regions if b not in uncovered]
                    nb = len(vis)
                    hits = (np.random.default_rng(rng.getrandbits(32)).binomial(nb, dp) if nb > 20 else sum(rng.random() < dp for _ in range(nb))) if nb else 0
                    if hits:
                        for b in rng.sample(vis, hits):
                            kill_bug(b, t)
                land(a, t, fresh)
                start(a, t)
            else:
                gate_q.append((a, fresh))
                if not gate_busy[0]:
                    gate_busy[0] = True
                    push(t, 'gate', None)
        elif kind == 'gate':
            if not gate_q:
                gate_busy[0] = False
                continue
            batch = gate_q[:B]; del gate_q[:B]
            caught = [i for i, x in enumerate(batch) if x[1] and rng.random() < q]
            extra = len(caught) * math.ceil(math.log2(len(batch))) if len(batch) > 1 else 0
            push(t + tg * (1 + extra), 'gate_out', (batch, set(caught)))
        elif kind == 'gate_out':
            batch, caught = payload
            for i, (a, fresh) in enumerate(batch):
                if i in caught:
                    if t >= warm: st['rejected'] += 1
                else:
                    land(a, t, fresh)
                start(a, t)
            push(t, 'gate', None)
        elif kind == 'found':
            if payload in bug_regions:
                kill_bug(payload, t)
    span = T - warm
    useful = st['landed'] - st['reverted']
    return dict(throughput=useful / span, eff=useful / span / N, landed=st['landed'] / span,
                reverted=st['reverted'] / span, rejected=st['rejected'] / span,
                coll_per_task=st['collisions'] / max(1, st['tasks']),
                live_bugs=st['live_area'] / span, kappa=float((p ** 2).sum()),
                live_uncov=st['uncov_area'] / span)


if __name__ == '__main__':
    import time
    t0 = time.time()
    for N in (8, 16, 32, 46, 64, 128, 256):
        r = run(N=N, m=16, collide='restart'); print(N, N/16, round(r['eff'],3), round(time.time() - t0, 1))
