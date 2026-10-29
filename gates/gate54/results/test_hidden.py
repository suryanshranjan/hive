"""Hidden acceptance tests for Tiny Shop's three features, written from policy.md before any build. Never shown to builders."""
import pytest
from shop.orders import Item, Order
from shop.refunds import refund
from shop.loyalty import points_earned
from shop.report import sales_summary


def o(price=1000, qty=1, ship=100, disc=0, paid='card', final=False):
    return Order('X', [Item('thing', price, qty)], shipping_fee=ship, discount_pct=disc, paid_with=paid, final_sale=final)

REFUNDS = [
    (dict(), 3, 'changed mind', 1000, 'card'), (dict(), 14, 'changed mind', 1000, 'card'),
    (dict(), 15, 'changed mind', 500, 'card'), (dict(), 31, 'changed mind', 0, 'card'),
    (dict(), 60, 'damaged', 1100, 'card'), (dict(), 91, 'damaged', 0, 'card'),
    (dict(disc=10), 20, 'changed mind', 450, 'card'), (dict(final=True), 3, 'changed mind', 0, 'card'),
    (dict(final=True), 3, 'damaged', 1100, 'card'), (dict(price=90, ship=0), 20, 'changed mind', 0, 'card'),
    (dict(paid='store_credit'), 3, 'changed mind', 1000, 'store_credit'), (dict(), -2, 'changed mind', 1000, 'card'),
]
@pytest.mark.parametrize('kw,days,reason,amount,method', REFUNDS)
def test_refund(kw, days, reason, amount, method):
    assert refund(o(**kw), days, reason) == {'amount': amount, 'method': method}

POINTS = [
    (dict(price=1000), 10), (dict(price=1099), 10), (dict(price=1000, ship=500), 10), (dict(price=1000, disc=10), 9),
    (dict(price=499), 0), (dict(price=500), 5), (dict(price=550, disc=10), 0), (dict(price=560, disc=10), 5), (dict(paid='store_credit'), 0),
    (dict(final=True), 20), (dict(price=250, qty=4), 10),
]
@pytest.mark.parametrize('kw,points', POINTS)
def test_points(kw, points):
    assert points_earned(o(**kw)) == points

def test_summary_mixed():
    orders = [o(price=1000, ship=100), o(price=500, ship=0, disc=10), o(price=2000, paid='store_credit')]
    assert sales_summary(orders) == {'orders': 3, 'revenue': 1550, 'average': 775}

def test_summary_rounds_down():
    orders = [o(price=100, ship=0), o(price=101, ship=0), o(price=100, ship=0)]
    assert sales_summary(orders) == {'orders': 3, 'revenue': 301, 'average': 100}

def test_summary_only_store_credit():
    assert sales_summary([o(paid='store_credit')]) == {'orders': 1, 'revenue': 0, 'average': 0}

def test_summary_empty():
    assert sales_summary([]) == {'orders': 0, 'revenue': 0, 'average': 0}
