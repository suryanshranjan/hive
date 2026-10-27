#!/bin/sh
# Gate 23: cached guard vs Gate 3's guard, 12 workers each, run together on a CPU-limited container.
# From the host, before:  docker update --cpus 4 <container>     after the swarm:  docker update --cpus <host cores> <container>  (--cpus 0 does not lift it)
# Inside the container, from the repo root:  sh gate23/run.sh swarm   then (after lifting the CPU limit)  sh gate23/run.sh score
set -e
case "$1" in
swarm)
  git fetch -q origin
  git ls-tree origin/main -- gate23/prompts/PREDICTIONS.md | grep -q . || { echo 'predictions not on origin/main'; exit 1; }
  git diff --quiet origin/main -- gate23/prompts/PREDICTIONS.md || { echo 'push gate23/prompts/PREDICTIONS.md first'; exit 1; }
  rm -rf runs/g23 /tmp/hive_guard_cache; mkdir -p runs/g23
  git clone -q gate3/seed_scale.bundle runs/g23/seed_cached
  cp gate23/tools/land.py runs/g23/seed_cached/tools/land.py
  git -C runs/g23/seed_cached -c user.name=hive -c user.email=hive@local commit -q -am 'tools/land.py: key the guard cache by code content (Gate 23)'
  python3 lab/make_swarm.py --run g23 --seed gate3/seed_scale.bundle --prompt gate3/prompts/prompt_scale.md --arm F12:12
  python3 lab/make_swarm.py --run g23 --seed runs/g23/seed_cached --prompt gate3/prompts/prompt_scale.md --arm K12:12
  nproc
  python3 lab/launch.py --run g23 ;;
score)
  test -d private/g10/hidden2 || { echo 'need the hidden suite in private/g10/hidden2 (gen2.py on SQLite 3.49: see gate10/RESULTS.md)'; exit 1; }
  for a in F12 K12; do python3 gate2/referee/evaluate.py runs/g23/up$a.git private/g10/hidden2 runs/g23/eval_$a.json > runs/g23/evaluate_$a.log 2>&1; done
  for a in F12 K12; do echo "== $a"; python3 gate10/referee/makespan.py runs/g23/eval_$a.json runs/g23/agents.csv; python3 gate21/referee/regressions.py runs/g23/eval_$a.json runs/g23/agents.csv | tail -1; done
  echo "== K12 guard cache:"; cat /tmp/hive_guard_cache/*/stats.log 2>/dev/null | sort | uniq -c ;;
*) echo 'usage: sh gate23/run.sh swarm|score'; exit 2 ;;
esac
