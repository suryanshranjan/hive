#!/usr/bin/env python3
"""Gate 53: Gate 52's flight again, after its two fixes (the law sizes the team by the job's independent parts; the code
sheet replaces the one-by-one assumption review). Same project, goal, owner, policy and hidden tests.
usage: python3 gates/gate53/referee/flight2.py"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'lab')); sys.path.insert(0, os.path.join(ROOT, 'gates', 'gate52', 'referee'))
import run_gate, flight
run_gate.prereg_check('gates/gate53/prompts/PREDICTIONS.md')
flight.RUN = os.path.join(ROOT, 'runs', 'g53')
sys.argv = [sys.argv[0], '--skip-prereg-check']
flight.main()
