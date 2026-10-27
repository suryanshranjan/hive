#!/bin/sh
# Gate 10: largest-first claiming vs Gate 3's claiming, 12 workers each, run at the same time on one machine.
# Run from the repo root inside the lab container, after the predictions are pushed.
set -e
git fetch -q origin
git diff --quiet origin/main -- gates/gate10/prompts/PREDICTIONS.md || { echo 'push gates/gate10/prompts/PREDICTIONS.md first'; exit 1; }
git ls-tree origin/main -- gates/gate10/prompts/PREDICTIONS.md | grep -q . || { echo 'predictions not on origin/main'; exit 1; }
rm -rf runs/g10
python3 lab/make_swarm.py --run g10 --seed gates/gate3/seed_scale.bundle --prompt gates/gate3/prompts/prompt_scale.md --arm F12:12
python3 lab/make_swarm.py --run g10 --seed gates/gate3/seed_scale.bundle --prompt gates/gate10/prompts/prompt_largest.md --arm L12:12
python3 lab/launch.py --run g10
mkdir -p private/g10
python3 gates/gate2/referee/gen2.py private/g10/hidden2 5000000 20     # regenerate Gate 2's hidden suite (never commit it)
for a in F12 L12; do python3 gates/gate2/referee/evaluate.py runs/g10/up$a.git private/g10/hidden2 runs/g10/eval_$a.json; done
for a in F12 L12; do python3 gates/gate10/referee/makespan.py runs/g10/eval_$a.json runs/g10/agents.csv; python3 gates/gate10/referee/events.py runs/g10/logs $a; done
