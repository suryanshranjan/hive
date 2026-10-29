#!/usr/bin/env python3
"""Gate 54: a bigger flight. hive start, as shipped, on Tiny Shop with a three-part goal (refunds, loyalty points, a
sales summary), so a real swarm runs through the product. Gate 52's driver; the policy and 27 hidden acceptance tests
are private (private/g54) until scored.
usage: python3 gates/gate54/referee/flight3.py"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'lab')); sys.path.insert(0, os.path.join(ROOT, 'gates', 'gate52', 'referee'))
import run_gate, flight
run_gate.prereg_check('gates/gate54/prompts/PREDICTIONS.md')
flight.RUN = os.path.join(ROOT, 'runs', 'g54'); flight.PRIV = os.path.join(ROOT, 'private', 'g54')
flight.BRIEF = os.path.join(ROOT, 'gates', 'gate54', 'prompts', 'owner_brief.md'); flight.HIDDEN = 'test_hidden.py'
flight.GOAL = ("Add three things to the shop. (1) Refunds: `refund(order, days_since_delivery, reason)` in `shop/refunds.py`, "
               "returning `{'amount': <whole rupees>, 'method': 'card' or 'store_credit'}`; `reason` is the customer's "
               "reason, for example 'changed mind' or 'damaged'. (2) Loyalty points: `points_earned(order)` in "
               "`shop/loyalty.py`, the points a customer earns for an order. (3) A daily sales summary for me: "
               "`sales_summary(orders)` in `shop/report.py`, returning `{'orders': ..., 'revenue': ..., 'average': ...}` "
               "in whole rupees.")
sys.argv = [sys.argv[0], '--skip-prereg-check']
flight.main()
