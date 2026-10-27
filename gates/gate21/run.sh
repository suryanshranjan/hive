#!/bin/sh
# Gate 21: cached guard vs Gate 3's guard, 12 workers each, run together on a CPU-limited container.
# From the host, before:  docker update --cpus 4 <container>     after the swarm:  docker update --cpus 0 <container>
# Inside the container, from the repo root:  sh gates/gate21/run.sh swarm   then (after lifting the CPU limit)  sh gates/gate21/run.sh score
set -e
case "$1" in
swarm)
  git fetch -q origin
  git ls-tree origin/main -- gates/gate21/prompts/PREDICTIONS.md | grep -q . || { echo 'predictions not on origin/main'; exit 1; }
  git diff --quiet origin/main -- gates/gate21/prompts/PREDICTIONS.md || { echo 'push gates/gate21/prompts/PREDICTIONS.md first'; exit 1; }
  rm -rf runs/g21 /tmp/hive_guard_cache; mkdir -p runs/g21
  git clone -q gates/gate3/seed_scale.bundle runs/g21/seed_cached
  cp gates/gate21/tools/land.py runs/g21/seed_cached/tools/land.py
  git -C runs/g21/seed_cached -c user.name=hive -c user.email=hive@local commit -q -am 'tools/land.py: cache main results per commit (Gate 21)'
  python3 lab/make_swarm.py --run g21 --seed gates/gate3/seed_scale.bundle --prompt gates/gate3/prompts/prompt_scale.md --arm F12:12
  python3 lab/make_swarm.py --run g21 --seed runs/g21/seed_cached --prompt gates/gate3/prompts/prompt_scale.md --arm C12:12
  nproc
  python3 lab/launch.py --run g21 ;;
score)
  test -d private/g10/hidden2 || { echo 'need the hidden suite in private/g10/hidden2 (gen2.py on SQLite 3.49: see gates/gate10/RESULTS.md)'; exit 1; }
  for a in F12 C12; do python3 gates/gate2/referee/evaluate.py runs/g21/up$a.git private/g10/hidden2 runs/g21/eval_$a.json > runs/g21/evaluate_$a.log 2>&1; done
  for a in F12 C12; do echo "== $a"; python3 gates/gate10/referee/makespan.py runs/g21/eval_$a.json runs/g21/agents.csv; python3 gates/gate21/referee/regressions.py runs/g21/eval_$a.json runs/g21/agents.csv | tail -1; done
  echo "== C12 guard cache:"; cat /tmp/hive_guard_cache/*/stats.log 2>/dev/null | sort | uniq -c ;;
*) echo 'usage: sh gates/gate21/run.sh swarm|score'; exit 2 ;;
esac
